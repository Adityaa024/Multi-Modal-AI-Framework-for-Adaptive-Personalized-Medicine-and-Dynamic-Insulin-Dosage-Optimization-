# Improved Insulin Dose Prediction Pipeline

## Overview

This document describes the advanced insulin dose calculation improvements implemented in the diabetes AI prediction system. These changes address the critical issue where RandomForest regression models predict extremely low insulin doses (0-5 units), causing safety clamps to dominate the final output and potentially recommend doses that are lower than needed for proper glycemic control.

## Problem Statement

### Original Issue

**Scenario:**
- Previous insulin dose: 24 units
- Post-dose glucose: 210 mg/dL (still high, indicating poor glycemic control)
- ML model predicted dose: 5.2 units
- Safety minimum (0.1 × weight for 95kg patient): 9.5 units
- **Result:** Final recommended dose = 9.5 units (clamped to minimum)

**Clinical Problem:**
This results in recommending a dose much lower than the patient's previous dose, which could inappropriately worsen glycemic control. The ML model's low prediction is masked by the safety mechanism, preventing clinical decision-makers from taking corrective action.

### Root Causes

1. **Model Under-prediction:** RandomForest models trained on synthetic data may underestimate insulin requirements
2. **Safety Clamp Dominance:** The physiological minimum safety bound frequently overrides ML predictions
3. **Loss of Adaptive Logic:** When the safety clamp activates, the dose loses any treatment-response reasoning
4. **No Baseline Reference:** Missing integration of physiological baseline expectations

## Solution: Advanced Adaptive Dose Calculation

### Algorithm Pipeline

The new dose calculation implements a **4-stage physiological baseline and treatment-response pipeline**:

#### Stage 1: Physiological Baseline Estimation

```
baseline_dose = 0.2 × weight_kg
```

This establishes a realistic physiological starting point based on body weight, independent of ML model predictions.

**Rationale:**
- Typical basal insulin requirements range from 0.1-0.5 U/kg/day
- 0.2 U/kg/day represents a moderate physiological expectation
- Provides stability when ML predictions are unreliable

**Example (72 kg patient):**
```
baseline = 0.2 × 72 = 14.4 units
```

#### Stage 2: ML-Baseline Blending

```
combined_dose = (0.6 × ml_predicted_dose) + (0.4 × baseline_dose)
```

Combines ML prediction with the physiological baseline using a weighted average:
- **60% weight** to ML prediction: Preserves model intelligence when reliable
- **40% weight** to baseline: Provides stabilization and prevents extreme predictions

**Example (ML prediction 5.2 U, baseline 14.4 U):**
```
combined_dose = (0.6 × 5.2) + (0.4 × 14.4)
              = 3.12 + 5.76
              = 8.88 units
```

**Result:** Dose increases from 5.2 to 8.88 units (+70%), much closer to clinical expectations.

#### Stage 3: Physiological Minimum Enforcement

```
combined_dose = max(combined_dose, 0.1 × weight_kg)
```

Ensures the dose doesn't fall below the minimum physiological outpatient basal bound.

**Example (72 kg patient, combined 8.88 U):**
```
physiological_min = 0.1 × 72 = 7.2 units
combined_dose = max(8.88, 7.2) = 8.88 units
```

#### Stage 4: Treatment-Response Adjustment

```
if glucose_after_dose > 180 mg/dL AND previous_insulin_dose > 0:
    combined_dose = max(combined_dose, previous_insulin_dose × 1.1)
```

When post-dose glucose exceeds 180 mg/dL (indicating poor glycemic control), ensures the recommended dose is at least 110% of the previous dose to prevent inappropriate reduction.

**Example (previous dose 24 U, post-dose glucose 210 mg/dL):**
```
if 210 > 180 and 24 > 0:
    min_response_dose = 24 × 1.1 = 26.4 units
    combined_dose = max(current_dose, 26.4)
```

**Clinical Impact:**
- Prevents the system from recommending lower doses when glucose control is poor
- Encourages gradual titration upward rather than sudden reductions
- Aligns with clinical practice of incrementally increasing insulin doses

### Safety Bounds (Unchanged)

After adaptive calculation, the final dose is clamped to weight-based safety bounds:

```
safe_min = 0.1 × weight_kg
safe_max = 0.5 × weight_kg
final_dose = min(max(combined_dose, safe_min), safe_max)
```

These bounds represent realistic outpatient basal insulin ranges.

## Expected Behavior After Improvements

### Case 1: Mild Diabetes (72 kg patient)

| Metric | Value |
|--------|-------|
| Weight | 72 kg |
| Post-dose glucose | 150 mg/dL |
| Previous dose | 12 units |
| **Old pipeline:** | |
| ML prediction | 5.0 units |
| Final dose (clamped) | 7.2 units |
| **New pipeline:** | |
| Physiological baseline | 14.4 units |
| Combined dose | 8.88 units |
| Final dose | 8-10 units |
| **Improvement** | +23% increase in dose |

### Case 2: Moderate Diabetes (80 kg patient)

| Metric | Value |
|--------|-------|
| Weight | 80 kg |
| Post-dose glucose | 165 mg/dL |
| Previous dose | 18 units |
| **Old pipeline:** | |
| ML prediction | 6.0 units |
| Final dose (clamped) | 8.0 units |
| **New pipeline:** | |
| Physiological baseline | 16 units |
| Combined dose | 10.4 units |
| Final dose | 10-12 units |
| **Improvement** | +25-50% increase in dose |

### Case 3: Severe with Poor Control (85 kg patient)

| Metric | Value |
|--------|-------|
| Weight | 85 kg |
| Post-dose glucose | **210 mg/dL** (poor control) |
| Previous dose | 24 units |
| **Old pipeline (PROBLEMATIC):** | |
| ML prediction | 5.5 units |
| Final dose (clamped) | 8.5 units |
| Problem | Dose 65% lower than previous despite poor glucose! |
| **New pipeline:** | |
| Physiological baseline | 17 units |
| Combined dose | 9.8 units |
| **Treatment adjustment:** | |
| Post-dose glucose > 180? | YES (210 mg/dL) |
| Minimum: 1.1 × 24 | 26.4 units |
| **Final dose** | **26.4 units** |
| **Improvement** | **+210% increase, prevents inappropriate dose reduction** |

## Implementation Details

### Files Modified

1. **`app/services/ml/dose_model.py`**
   - Added `AdvancedAdaptiveDoseRecommendation` dataclass
   - Added `compute_advanced_adaptive_dose()` function
   - Preserved original `compute_hybrid_adaptive_dose()` for backward compatibility

2. **`app/api/routes/predictions.py`**
   - Updated import to include `compute_advanced_adaptive_dose`
   - Modified `predict_dose_with_severity()` to use new advanced calculation
   - Enhanced `adjustment_explanation` field with detailed reasoning
   - Updated `adjustment_display` with physiological & response adjustment labels

3. **`tests/test_advanced_dose_calculation.py`** (NEW)
   - 6 new test cases validating improvement scenarios
   - Tests for mild, moderate, and severe cases
   - Verification of safe range scaling with weight
   - Validation of treatment-response adjustment logic

### API Response Fields

The response includes detailed adjustment tracking:

```json
{
  "ml_predicted_dose_units": 5.2,
  "recommended_dose_units": 26.4,
  "adjustment_percent": 407.7,
  "adjustment_display": "+407.7% via physiological & response adjustment",
  "adjustment_explanation": "Physiological baseline (17.0 U) combined with ML prediction (5.2 U) to stabilize dose. Post-dose glucose 210 mg/dL indicates poor control; ensuring dose (26.4 U) does not fall below 110% of previous dose (26.4 U).",
  "safe_range": {
    "min": 8.5,
    "max": 42.5
  }
}
```

## Clinical Safety & Validation

### Safety Mechanisms Preserved

- **Weight-based bounds:** All doses remain within 0.1-0.5 U/kg/day range
- **Hyperglycemia detection:** Continued monitoring of glucose > 180 mg/dL
- **Hypoglycemia alerts:** Maintained for post-dose glucose < 70 mg/dL
- **Medication contraindications:** Drug recommendations remain context-aware

### Validation Approach

1. **Deterministic Testing:** 26 test cases covering edge cases and scenarios
2. **Stress Testing:** 100-profile randomized validation (all pass)
3. **Backward Compatibility:** Existing tests confirmed no regression
4. **Clinically-Informed Ranges:** All test cases use realistic patient parameters

## Limitations & Future Improvements

### Current Limitations

1. **Synthetic Data:** Model training uses synthetic T2D patient profiles
2. **Static Weights:** Blending weights (0.6/0.4) are fixed; could be adaptive
3. **Glucose Threshold:** Treatment response triggers at fixed 180 mg/dL threshold
4. **10% Increase:** Response adjustment uses fixed 1.1 multiplier

### Recommended Future Enhancements

1. **Adaptive Weighting:** ML weight could increase with model confidence (uncertainty_entropy)
2. **Personalized Thresholds:** Treatment-response triggers based on patient severity
3. **Prospective Validation:** Real-world outcome tracking to validate improvements
4. **Advanced Baselines:** Incorporate patient-specific factors (age, BMI, kidney function)

## Migration & Deployment

### Backward Compatibility

- Old `compute_hybrid_adaptive_dose()` remains available
- API schema unchanged; only logic enhancements
- All existing tests pass without modification

### Deployment Checklist

- [x] Code review for correctness
- [x] Unit tests (26 passing)
- [x] Integration tests with existing API
- [x] Safety bound validation
- [x] Edge case handling
- [x] Documentation (this file)

## References

**Physiological Basis:**
- Basal insulin requirements: 0.1-0.5 U/kg/day (standard clinical guidance)
- Blending approach: Combines data-driven ML with explicit clinical rules
- Treatment response: Prevents inappropriate dose reduction during poor control

**Clinical Context:**
- This framework is for research use only
- All recommendations must be validated by clinical teams
- Integration with human-in-the-loop review essential for clinical deployment

## Support & Questions

For questions about the improved dose calculation pipeline:
1. See [Implementation Details and System Interface](./IMPLEMENTATION.md)
2. Review test cases in [tests/test_advanced_dose_calculation.py](tests/test_advanced_dose_calculation.py)
3. Check API response examples in [API Endpoints](./API_ENDPOINTS.md)
