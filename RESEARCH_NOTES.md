# Research Notes: ICICCC-2026 Reviewer Feedback Resolution

This document summarizes how the reviewer feedback for "Multi-Modal AI Framework for Adaptive Personalized Medicine and Dynamic Insulin Dosage Optimization in Type 2 Diabetes Management" has been addressed within the codebase.

## 1. Synthetic Dataset Clinical Validity
**Reviewer Comment:** "The evaluation is based on a synthetic dataset; therefore, its clinical validity and generalizability should be discussed more clearly. The authors should briefly justify the data-generation process and acknowledge the need for validation on real clinical data."

**Resolution:**
- **Codebase:** Added explicit disclaimers to `README.md` acknowledging the theoretical nature of the current evaluation and the critical need for real-world clinical validation.
- **Manuscript Action Needed:** Ensure the limitations section of the paper explicitly discusses this point, mirroring the language now in the repository's README.

## 2. In-Text Citations
**Reviewer Comment:** "Appropriate in-text citations should be added, particularly in the Introduction and Related Work, to support claims regarding existing approaches."

**Resolution:**
- **Codebase:** Added a note in the `README.md` for authors as a reminder.
- **Manuscript Action Needed:** Add citations to the Introduction and Related Work sections as requested.

## 3. Data Generation & "Optimal" Dose Derivation
**Reviewer Comment:** "The derivation of the target/“optimal” insulin dose in the synthetic dataset should be clearly explained. Otherwise, the regression model may simply learn the rules used to generate its target values."

**Resolution:**
- **Codebase:** Expanded the docstrings in `scripts/generate_synthetic_t2d_data.py` (specifically `simulate_insulin_dose_and_response`) to clearly detail how the target dose is derived using independent clinical factors and Gaussian noise, which prevents the XGBoost regressor from trivially memorizing generation rules.

## 4. Safety Limits Justification
**Reviewer Comment:** "The fixed safety limits of 0.1–0.5 units/kg require stronger clinical justification, particularly across different patient conditions and insulin regimens."

**Resolution:**
- **Codebase:** Updated `app/api/routes/predictions.py` with expanded documentation around `_weight_based_safe_range`. The clinical rationale focuses on physiological basal insulin replacement ranges in outpatient settings.

## 5. Reproducibility & Overfitting
**Reviewer Comment:** "Report the exact train/validation/test split, hyperparameter optimization, class distribution, and cross-validation strategy to establish reproducibility and rule out overfitting."

**Resolution:**
- **Codebase:** Refactored `scripts/train_severity_model.py` and `scripts/train_dosage_model.py` to use `GridSearchCV`/`RandomizedSearchCV` with K-Fold Cross Validation. The scripts now explicitly log the exact sizes of train/validation/test splits and class distributions to the terminal, and save the cross-validation strategy details in the output.

## 6. Clinical Rules & Validation (Risk & Drugs)
**Reviewer Comment:** "The drug-recommendation and hypo/hyperglycemia risk modules require clearer clinical rules and validation."

**Resolution:**
- **Codebase:** 
  - Enhanced docstrings in `app/services/drug_recommender.py` to explicitly map rules to known clinical guidelines (e.g., Metformin avoidance for high creatinine, GLP-1 preference for high BMI).
  - Clarified the logic in `_compute_risk_probabilities` in `app/api/routes/predictions.py`, explaining the heuristic logits based on standard deviation boundaries.
- **Manuscript Action Needed:** Consider adding a small section detailing the rule sets and how they align with standard care guidelines (e.g., ADA guidelines).
