export type PatientInput = {
  age: number
  weight_kg: number
  height_cm: number
  bmi?: number | null
  fasting_glucose_mgdl: number
  hba1c: number
  creatinine_mgdl: number
  previous_insulin_dose_units: number
  glucose_after_dose_mgdl: number
  activity_level: number
  diet_adherence_score: number
  feature_mode?: 'structured' | 'structured_labs' | 'full'
}

export type SeverityProbabilities = {
  mild: number
  moderate: number
  severe: number
}

export type SafetyGuardrails = {
  safe_min_units: number
  safe_max_units: number
  was_clamped: boolean
  within_safe_range: boolean
  exceeds_max_allowed: boolean
  warning_message: string | null
}

export type SafeRange = {
  min: number
  max: number
}

export type DrugRecommendation = {
  primary_therapy: string
  adjunct_drug: string
  contraindications: string[]
  confidence: number
  explanation: string
}

export type PredictDoseResponse = {
  severity: 'Mild' | 'Moderate' | 'Severe' | string
  feature_mode: 'structured' | 'structured_labs' | 'full'
  ml_predicted_dose_units: number
  recommended_dose_units: number
  adjustment_percent: number
  adjustment_display: string
  adjustment_explanation: string | null
  confidence_score: number
  severity_probabilities: SeverityProbabilities
  uncertainty_entropy: number
  explanation: string
  risk_alert: boolean
  hypoglycemia_alert: boolean
  hypoglycemia_risk_probability: number
  hyperglycemia_risk_probability: number
  safe_range: SafeRange
  safety: SafetyGuardrails
  drug_recommendation: DrugRecommendation
}

export type RocCurveSeries = {
  label: string
  fpr: number[]
  tpr: number[]
}

export type EvaluationDashboardResponse = {
  mae: number
  rmse: number
  roc_auc_ovr_macro: number
  roc_curves: RocCurveSeries[]
  confusion_matrix: {
    labels: string[]
    matrix: number[][]
  }
  shap_summary: Array<{ feature: string; mean_abs_shap: number }>
}

export type TrendPoint = {
  at: string
  fasting_glucose_mgdl: number
  recommended_dose_units: number
}

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

function apiUrl(path: string): string {
  if (!API_BASE) {
    return path
  }
  return `${API_BASE}${path}`
}

export async function predictDose(input: PatientInput): Promise<PredictDoseResponse> {
  const res = await fetch(apiUrl('/api/v1/predictions/predict-dose'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `Request failed with status ${res.status}`)
  }

  return (await res.json()) as PredictDoseResponse
}

export async function getEvaluationDashboard(): Promise<EvaluationDashboardResponse> {
  const res = await fetch(apiUrl('/api/v1/predictions/evaluation-dashboard'))

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `Request failed with status ${res.status}`)
  }

  return (await res.json()) as EvaluationDashboardResponse
}

