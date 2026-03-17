from dataclasses import dataclass

from app.services.ml.preprocessing import GlucoseFeatures


@dataclass
class DoseModelMetadata:
    """
    Metadata describing the insulin dosing model.

    Keeping metadata in a dedicated structure makes it easy to surface in
    API responses and to version research experiments over time.
    """

    name: str
    version: str


class SimpleHeuristicDoseModel:
    """
    Transparent baseline model for insulin dose suggestions.

    This model is intentionally simple and deterministic. It encodes a
    hand-crafted rule that:
    - Targets a nominal glucose range.
    - Modulates the dose based on trend and context flags.

    The design goal is to provide a *clear, auditable* reference baseline
    that can later be replaced by more sophisticated learned models.
    """

    def __init__(self, target_glucose_mgdl: float = 110.0) -> None:
        self.metadata = DoseModelMetadata(
            name="simple_glucose_proportional_heuristic",
            version="0.1.0",
        )
        self._target_glucose_mgdl = target_glucose_mgdl

    def predict_dose_units(self, features: GlucoseFeatures) -> float:
        """
        Compute a suggested dose in units from derived glucose features.

        The rule is purposely conservative and bounded:
        - Base dose grows linearly with deviation from the target glucose.
        - Upward trends and preprandial context gently increase the dose.
        - Bedtime context applies an upper cap.
        """

        deviation = max(0.0, features.current_glucose_mgdl - self._target_glucose_mgdl)

        # Scale factor encodes how aggressively to correct above-target glucose.
        base_dose = deviation / 50.0  # units per 50 mg/dL above target

        # Trend adjustment: if glucose is rising, gently increase the dose.
        if features.delta_glucose_mgdl is not None and features.delta_glucose_mgdl > 15:
            base_dose *= 1.2

        # Preprandial context: modestly increase correction.
        if features.is_preprandial:
            base_dose *= 1.1

        # Bedtime context: avoid large corrective doses.
        if features.is_bedtime:
            base_dose = min(base_dose, 4.0)

        # Enforce a small positive lower bound and a reasonable safety cap
        # to keep the heuristic numerically well-behaved.
        bounded_dose = min(max(base_dose, 0.5), 20.0)
        return float(round(bounded_dose, 1))


@dataclass
class AdaptiveDoseRecommendation:
    """
    Result of combining an ML-predicted dose with rule-based adjustments.

    This hybrid recommendation is designed for research and simulation:
    it makes the effect of explicit safety rules transparent while still
    leveraging an underlying predictive model.
    """

    final_dose_units: float
    adjustment_percent: float
    hypoglycemia_risk: bool


@dataclass
class AdvancedAdaptiveDoseRecommendation:
    """
    Result of physiological baseline estimation and treatment-response adjustment.
    
    Combines ML prediction with:
    - Physiological baseline (0.2 * weight_kg)
    - Treatment-response logic (ensure dose not lower than needed for control)
    - Detailed tracking of each adjustment stage for transparent explanation.
    """
    
    combined_dose_units: float  # After baseline combination, before treatment-response
    adjusted_dose_with_response: float  # After treatment-response adjustment
    final_adaptive_dose: float  # Final dose before safety clamp
    adjustment_percent: float
    adjustment_explanation: str
    adjustment_stages: dict  # Detailed breakdown of each stage


def compute_hybrid_adaptive_dose(
    base_dose_units: float,
    current_glucose_mgdl: float,
) -> AdaptiveDoseRecommendation:
    """
    Apply simple safety rules on top of an ML-predicted insulin dose.

    Rules:
    - If glucose > 250 mg/dL: increase dose by 10%.
    - If glucose < 80 mg/dL:  decrease dose by 15%.

    The function returns the adjusted dose, the net adjustment percentage,
    and a hypoglycemia risk flag that is raised when glucose is already
    low or when the adjusted dose is substantially higher than the base.
    """

    adjustment_percent = 0.0

    if current_glucose_mgdl > 250:
        adjustment_percent += 0.10
    elif current_glucose_mgdl < 80:
        adjustment_percent -= 0.15

    adjusted_dose = base_dose_units * (1.0 + adjustment_percent)
    final_dose = max(0.0, round(adjusted_dose, 1))

    hypoglycemia_risk = bool(
        current_glucose_mgdl < 80
        or (base_dose_units > 0 and final_dose > base_dose_units * 1.2)
    )

    return AdaptiveDoseRecommendation(
        final_dose_units=final_dose,
        adjustment_percent=adjustment_percent,
        hypoglycemia_risk=hypoglycemia_risk,
    )


def compute_advanced_adaptive_dose(
    ml_predicted_dose_units: float,
    weight_kg: float,
    previous_insulin_dose_units: float,
    glucose_after_dose_mgdl: float,
) -> AdvancedAdaptiveDoseRecommendation:
    """
    Advanced dose calculation integrating physiological baseline and treatment-response.
    
    Pipeline:
    1. Compute physiological baseline: baseline_dose = 0.2 * weight_kg
    2. Combine ML prediction with baseline: combined = 0.6 * ml + 0.4 * baseline
    3. Ensure minimum physiological dose: combined = max(combined, 0.1 * weight_kg)
    4. Treatment-response adjustment: if glucose_after_dose > 180 and previous dose known,
       ensure new dose >= previous_dose * 1.1 (prevent inappropriate dose reduction)
    5. Return detailed adjustment information for explanation generation.
    
    This approach addresses the problem where RandomForest models predict very low doses,
    causing safety clamps to dominate the final output and potentially reduce doses 
    below what's needed for glycemic control.
    """
    
    stages = {}
    
    # Stage 1: Physiological baseline estimation
    physiological_baseline = 0.2 * weight_kg
    stages["physiological_baseline_units"] = physiological_baseline
    stages["ml_predicted_units"] = ml_predicted_dose_units
    
    # Stage 2: Combine ML prediction with baseline (weighted average)
    combined_dose = (0.6 * ml_predicted_dose_units) + (0.4 * physiological_baseline)
    stages["combined_dose_before_minimum"] = combined_dose
    
    # Stage 3: Ensure physiological minimum
    physiological_minimum = 0.1 * weight_kg
    combined_dose = max(combined_dose, physiological_minimum)
    stages["combined_dose_after_minimum"] = combined_dose
    stages["physiological_minimum_units"] = physiological_minimum
    
    # Track if baseline had significant impact
    baseline_applied = combined_dose > (0.6 * ml_predicted_dose_units + 0.01)
    stages["baseline_stabilization_applied"] = baseline_applied
    
    # Stage 4: Treatment-response adjustment
    treatment_response_adjustment = False
    adjusted_dose = combined_dose
    
    if (glucose_after_dose_mgdl > 180 and 
        previous_insulin_dose_units > 0):
        # Poor glycemic control: ensure dose doesn't inappropriately decrease
        min_dose_for_response = previous_insulin_dose_units * 1.1
        if adjusted_dose < min_dose_for_response:
            adjusted_dose = min_dose_for_response
            treatment_response_adjustment = True
            stages["treatment_response_minimum"] = min_dose_for_response
            stages["glucose_after_dose_mgdl"] = glucose_after_dose_mgdl
    
    stages["treatment_response_applied"] = treatment_response_adjustment
    stages["adjusted_dose_before_clamp"] = adjusted_dose
    
    # Calculate adjustment metrics relative to original ML dose
    # Note: adjustment_percent will be recalculated in predictions.py after rounding
    # to ensure it matches the final dose change exactly
    initial_ml_dose = ml_predicted_dose_units
    if initial_ml_dose > 0.01:
        adjustment_percent = ((adjusted_dose - initial_ml_dose) / initial_ml_dose) * 100.0
    else:
        adjustment_percent = 0.0
    
    # Build explanation of what adjustments were applied
    explanation_parts = []
    
    if baseline_applied:
        explanation_parts.append(
            f"Physiological baseline ({physiological_baseline:.1f} U) combined with ML prediction "
            f"({ml_predicted_dose_units:.1f} U) to stabilize dose."
        )
    
    if treatment_response_adjustment:
        explanation_parts.append(
            f"Post-dose glucose {glucose_after_dose_mgdl:.0f} mg/dL indicates poor control; "
            f"ensuring dose ({adjusted_dose:.1f} U) does not fall below 110% of previous dose "
            f"({previous_insulin_dose_units * 1.1:.1f} U)."
        )
    
    if not explanation_parts:
        explanation_parts.append(
            f"ML prediction {ml_predicted_dose_units:.1f} U combined with physiological baseline "
            f"stabilization."
        )
    
    adjustment_explanation = " ".join(explanation_parts)
    
    return AdvancedAdaptiveDoseRecommendation(
        combined_dose_units=combined_dose,
        adjusted_dose_with_response=adjusted_dose,
        final_adaptive_dose=adjusted_dose,
        adjustment_percent=adjustment_percent,
        adjustment_explanation=adjustment_explanation,
        adjustment_stages=stages,
    )


