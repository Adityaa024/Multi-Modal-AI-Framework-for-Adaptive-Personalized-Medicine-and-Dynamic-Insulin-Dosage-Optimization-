import { useEffect, useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import SeverityBadge from './components/SeverityBadge'
import TrendChart, { type TrendPoint } from './components/TrendChart'
import {
  getEvaluationDashboard,
  predictDose,
  type EvaluationDashboardResponse,
  type PatientInput,
  type PredictDoseResponse,
} from './lib/api'

type FormState = PatientInput

function nowLabel(): string {
  const d = new Date()
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function clamp(n: number, min: number, max: number): number {
  return Math.min(Math.max(n, min), max)
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'prediction' | 'evaluation'>('prediction')
  const [form, setForm] = useState<FormState>({
    age: 62,
    weight_kg: 92,
    height_cm: 170,
    bmi: null,
    fasting_glucose_mgdl: 185,
    hba1c: 8.6,
    creatinine_mgdl: 1.2,
    previous_insulin_dose_units: 18,
    glucose_after_dose_mgdl: 150,
    activity_level: 1,
    diet_adherence_score: 70,
  })

  const computedBmi = useMemo(() => {
    const heightM = form.height_cm / 100
    if (!heightM) return null
    return form.weight_kg / (heightM * heightM)
  }, [form.height_cm, form.weight_kg])

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resultsByMode, setResultsByMode] = useState<Record<string, PredictDoseResponse>>({})
  const [selectedModes, setSelectedModes] = useState<Record<'structured' | 'structured_labs' | 'full', boolean>>({
    structured: false,
    structured_labs: false,
    full: true,
  })
  const [trend, setTrend] = useState<TrendPoint[]>([])
  const [evaluationLoading, setEvaluationLoading] = useState(false)
  const [evaluationError, setEvaluationError] = useState<string | null>(null)
  const [evaluationData, setEvaluationData] = useState<EvaluationDashboardResponse | null>(null)

  const selectedModeList = useMemo(
    () => (Object.keys(selectedModes) as Array<'structured' | 'structured_labs' | 'full'>).filter((key) => selectedModes[key]),
    [selectedModes],
  )

  const primaryResult = useMemo(() => {
    const firstMode = selectedModeList[0]
    return firstMode ? resultsByMode[firstMode] ?? null : null
  }, [resultsByMode, selectedModeList])

  useEffect(() => {
    if (activeTab !== 'evaluation' || evaluationData || evaluationLoading) return

    setEvaluationError(null)
    setEvaluationLoading(true)
    getEvaluationDashboard()
      .then((payload) => setEvaluationData(payload))
      .catch((e) => setEvaluationError(e instanceof Error ? e.message : 'Failed to load evaluation dashboard'))
      .finally(() => setEvaluationLoading(false))
  }, [activeTab, evaluationData, evaluationLoading])

  async function onPredict() {
    if (selectedModeList.length === 0) {
      setError('Select at least one ablation mode before prediction.')
      setResultsByMode({})
      return
    }

    setError(null)
    setLoading(true)
    try {
      const nextResults: Record<string, PredictDoseResponse> = {}

      for (const mode of selectedModeList) {
        const payload: PatientInput = {
          ...form,
          bmi: form.bmi ?? null,
          feature_mode: mode,
        }
        const prediction = await predictDose(payload)
        nextResults[mode] = prediction
      }

      setResultsByMode(nextResults)

      const primary = nextResults[selectedModeList[0]]
      if (primary) {
        const payload: PatientInput = {
          ...form,
          bmi: form.bmi ?? null,
        }
        setTrend((prev) => {
          const next: TrendPoint[] = [
            ...prev,
            {
              at: nowLabel(),
              fasting_glucose_mgdl: payload.fasting_glucose_mgdl,
              recommended_dose_units: primary.recommended_dose_units,
            },
          ]
          return next.slice(-20)
        })
      }
    } catch (e) {
      setResultsByMode({})
      setError(e instanceof Error ? e.message : 'Prediction failed')
    } finally {
      setLoading(false)
    }
  }

  const confidencePct = primaryResult ? clamp(primaryResult.confidence_score * 100, 0, 100) : null
  const uncertaintyPct = primaryResult ? clamp(primaryResult.uncertainty_entropy * 100, 0, 100) : null
  const probabilityChartData = primaryResult
    ? [
        { name: 'Mild', value: primaryResult.severity_probabilities.mild * 100 },
        { name: 'Moderate', value: primaryResult.severity_probabilities.moderate * 100 },
        { name: 'Severe', value: primaryResult.severity_probabilities.severe * 100 },
      ]
    : []

  const hasAnyResult = Object.keys(resultsByMode).length > 0

  return (
    <div className="min-h-full bg-gradient-to-b from-slate-50 via-slate-50 to-slate-100 text-slate-900">
      <header className="sticky top-0 z-10 border-b border-slate-200/70 bg-white/85 backdrop-blur">
        <div className="mx-auto max-w-6xl px-4 py-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="min-w-[240px]">
              <div className="flex items-center gap-3">
                <div className="grid h-9 w-9 place-items-center rounded-xl bg-slate-900 text-white shadow-sm">
                  <StethoscopeIcon />
                </div>
                <div>
                  <h1 className="text-base font-semibold tracking-tight">
                    Doctor Dashboard
                  </h1>
                  <p className="mt-0.5 text-xs text-slate-600">
                    Adaptive insulin dose recommendation (research use only)
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {primaryResult ? (
                <div className="hidden items-center gap-2 sm:flex">
                  <span className="text-xs text-slate-600">Severity</span>
                  <SeverityBadge severity={primaryResult.severity} />
                </div>
              ) : null}
              <div className="inline-flex rounded-xl border border-slate-200 bg-white p-1">
                <button
                  type="button"
                  onClick={() => setActiveTab('prediction')}
                  className={[
                    'rounded-lg px-3 py-1.5 text-xs font-semibold',
                    activeTab === 'prediction' ? 'bg-slate-900 text-white' : 'text-slate-600',
                  ].join(' ')}
                >
                  Prediction
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('evaluation')}
                  className={[
                    'rounded-lg px-3 py-1.5 text-xs font-semibold',
                    activeTab === 'evaluation' ? 'bg-slate-900 text-white' : 'text-slate-600',
                  ].join(' ')}
                >
                  Evaluation
                </button>
              </div>
              <button
                type="button"
                onClick={onPredict}
                disabled={loading}
                className={[
                  'inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold shadow-sm',
                  'bg-slate-900 text-white hover:bg-slate-800',
                  'disabled:cursor-not-allowed disabled:opacity-60',
                ].join(' ')}
              >
                <SparkIcon />
                {loading ? 'Predicting…' : 'Predict'}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        {activeTab === 'evaluation' ? (
          <EvaluationDashboardPanel
            loading={evaluationLoading}
            error={evaluationError}
            data={evaluationData}
          />
        ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
          {/* Form */}
          <section className="lg:col-span-2">
            <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-sm font-semibold text-slate-900">Patient form</h2>
                  <p className="mt-1 text-xs text-slate-600">
                    Structured, lab, and behavioral signals used for early fusion.
                  </p>
                </div>
                <div className="text-right text-[11px] text-slate-500">
                  <div className="font-mono">/api/v1/predictions/predict-dose</div>
                </div>
              </div>

              <div className="mt-4 space-y-5">
                <Section title="Structured">
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <Field
                      label="Age"
                      unit="years"
                      value={form.age}
                      step={1}
                      onChange={(v) => setForm((s) => ({ ...s, age: v }))}
                    />
                    <SelectField
                      label="Activity level"
                      value={form.activity_level}
                      options={[
                        { value: 0, label: '0 — Sedentary' },
                        { value: 1, label: '1 — Low' },
                        { value: 2, label: '2 — Moderate' },
                        { value: 3, label: '3 — High' },
                      ]}
                      onChange={(v) => setForm((s) => ({ ...s, activity_level: v }))}
                    />
                    <Field
                      label="Weight"
                      unit="kg"
                      value={form.weight_kg}
                      step={0.1}
                      onChange={(v) => setForm((s) => ({ ...s, weight_kg: v }))}
                    />
                    <Field
                      label="Height"
                      unit="cm"
                      value={form.height_cm}
                      step={0.1}
                      onChange={(v) => setForm((s) => ({ ...s, height_cm: v }))}
                    />
                    <Field
                      label="BMI (optional)"
                      hint={computedBmi ? `Computed: ${computedBmi.toFixed(1)}` : undefined}
                      value={form.bmi ?? ''}
                      step={0.1}
                      placeholder={computedBmi ? computedBmi.toFixed(1) : 'auto'}
                      onChange={(v) =>
                        setForm((s) => ({ ...s, bmi: Number.isFinite(v) ? v : null }))
                      }
                    />
                  </div>
                </Section>

                <Section title="Labs">
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <Field
                      label="Fasting glucose"
                      unit="mg/dL"
                      value={form.fasting_glucose_mgdl}
                      step={1}
                      onChange={(v) => setForm((s) => ({ ...s, fasting_glucose_mgdl: v }))}
                    />
                    <Field
                      label="HbA1c"
                      unit="%"
                      value={form.hba1c}
                      step={0.1}
                      onChange={(v) => setForm((s) => ({ ...s, hba1c: v }))}
                    />
                    <Field
                      label="Creatinine"
                      unit="mg/dL"
                      value={form.creatinine_mgdl}
                      step={0.01}
                      onChange={(v) => setForm((s) => ({ ...s, creatinine_mgdl: v }))}
                    />
                  </div>
                </Section>

                <Section title="Behavioral">
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <Field
                      label="Diet adherence"
                      unit="/100"
                      value={form.diet_adherence_score}
                      step={1}
                      onChange={(v) => setForm((s) => ({ ...s, diet_adherence_score: v }))}
                    />
                  </div>
                </Section>

                <Section title="Insulin context">
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <Field
                      label="Previous insulin dose"
                      unit="units"
                      value={form.previous_insulin_dose_units}
                      step={0.1}
                      onChange={(v) =>
                        setForm((s) => ({ ...s, previous_insulin_dose_units: v }))
                      }
                    />
                    <Field
                      label="Glucose after dose"
                      unit="mg/dL"
                      value={form.glucose_after_dose_mgdl}
                      step={1}
                      onChange={(v) =>
                        setForm((s) => ({ ...s, glucose_after_dose_mgdl: v }))
                      }
                    />
                  </div>
                </Section>

                <Section title="Research ablation mode">
                  <div className="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <AblationCheck
                      checked={selectedModes.structured}
                      label="Structured only"
                      onChange={(checked) =>
                        setSelectedModes((s) => ({ ...s, structured: checked }))
                      }
                    />
                    <AblationCheck
                      checked={selectedModes.structured_labs}
                      label="Structured + Labs"
                      onChange={(checked) =>
                        setSelectedModes((s) => ({ ...s, structured_labs: checked }))
                      }
                    />
                    <AblationCheck
                      checked={selectedModes.full}
                      label="Full Multi-modal"
                      onChange={(checked) => setSelectedModes((s) => ({ ...s, full: checked }))}
                    />
                  </div>
                </Section>
              </div>

              {error ? (
                <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900">
                  <div className="flex items-start gap-2">
                    <div className="mt-0.5 text-rose-700">
                      <AlertIcon />
                    </div>
                    <div>
                      <div className="font-semibold">Request failed</div>
                      <div className="mt-1 whitespace-pre-wrap text-xs">{error}</div>
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          </section>

          {/* Results + chart */}
          <section className="lg:col-span-3">
            <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-sm font-semibold text-slate-900">Prediction</h2>
                  <p className="mt-1 text-xs text-slate-600">
                    Severity, recommended dose, confidence, and explanation.
                  </p>
                </div>
                {primaryResult ? <SeverityBadge severity={primaryResult.severity} /> : null}
              </div>

              {!hasAnyResult ? (
                <div className="mt-6 rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-600">
                  Submit patient data to generate a prediction.
                </div>
              ) : (
                <>
                  {primaryResult?.hypoglycemia_alert ? (
                    <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900">
                      <div className="flex items-start gap-2">
                        <div className="mt-0.5 text-rose-700">
                          <AlertIcon />
                        </div>
                        <div>
                          <div className="font-semibold">Risk alert</div>
                          <div className="mt-1 text-xs">
                            Hypoglycemia risk flagged by the hybrid safety rules.
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : null}

                  {primaryResult?.safety.warning_message ? (
                    <div className="mt-4 rounded-xl border border-rose-300 bg-rose-50 p-3 text-sm text-rose-900">
                      <div className="font-semibold">{primaryResult.safety.warning_message}</div>
                    </div>
                  ) : null}

                  <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
                    {selectedModeList
                      .filter((mode) => resultsByMode[mode])
                      .map((mode) => (
                        <HybridComparisonCard key={mode} mode={mode} result={resultsByMode[mode]} />
                      ))}
                  </div>

                  <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
                    <Metric
                      label="Recommended dose"
                      value={`${primaryResult?.recommended_dose_units.toFixed(1)} units`}
                    />
                    <ConfidenceCard value={confidencePct ?? 0} />
                    <Metric
                      label="Uncertainty (entropy)"
                      value={`${(uncertaintyPct ?? 0).toFixed(1)}%`}
                    />
                  </div>

                  <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <Metric
                      label="Hypoglycemia Risk"
                      value={`${((primaryResult?.hypoglycemia_risk_probability ?? 0) * 100).toFixed(0)}%`}
                    />
                    <Metric
                      label="Hyperglycemia Risk"
                      value={`${((primaryResult?.hyperglycemia_risk_probability ?? 0) * 100).toFixed(0)}%`}
                    />
                  </div>

                  {primaryResult ? (
                    <div className="mt-5">
                      <DrugRecommendationCard result={primaryResult} />
                    </div>
                  ) : null}

                  <div className="mt-5 rounded-xl border border-slate-200 bg-white p-4">
                    <div className="text-xs font-semibold text-slate-700">
                      Severity probability distribution
                    </div>
                    <div className="mt-3 h-56">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={probabilityChartData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis unit="%" domain={[0, 100]} />
                          <Tooltip formatter={(v) => `${Number(v ?? 0).toFixed(1)}%`} />
                          <Bar dataKey="value" fill="#0f172a" radius={[8, 8, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <div className="text-xs font-semibold text-slate-700">
                      Explanation (SHAP)
                    </div>
                    <p className="mt-2 text-sm leading-relaxed text-slate-800">
                      {primaryResult?.explanation}
                    </p>
                  </div>

                  <div className="mt-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-semibold text-slate-900">
                          Glucose vs dose trend
                        </div>
                        <div className="mt-1 text-xs text-slate-600">
                          Last {trend.length} predictions (up to 20).
                        </div>
                      </div>
                    </div>
                    <div className="mt-3 rounded-xl border border-slate-200 p-3">
                      <TrendChart data={trend} />
                    </div>
                  </div>
                </>
              )}
            </div>
          </section>
        </div>
        )}
      </main>

      <footer className="mx-auto max-w-6xl px-4 pb-8 pt-4 text-xs text-slate-500">
        Research use only — clinical decisions must be confirmed by licensed healthcare professionals.
      </footer>
    </div>
  )
}

function DrugRecommendationCard({ result }: { result: PredictDoseResponse }) {
  const recommendation = result.drug_recommendation
  const contraindications = recommendation.contraindications
  const hasContraindications = contraindications.length > 0
  const confidencePct = clamp(recommendation.confidence * 100, 0, 100)

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm font-semibold text-slate-900">Drug Recommendation</div>
        {hasContraindications ? (
          <span className="rounded-full bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-700 ring-1 ring-rose-200">
            Contraindication warning
          </span>
        ) : (
          <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200">
            No major contraindications
          </span>
        )}
      </div>

      <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Metric label="Primary Therapy" value={recommendation.primary_therapy} />
        <Metric label="Adjunct Drug" value={recommendation.adjunct_drug} />
      </div>

      {hasContraindications ? (
        <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900">
          <div className="text-xs font-semibold uppercase tracking-wide">Contraindications</div>
          <ul className="mt-2 list-inside list-disc space-y-1 text-xs">
            {contraindications.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
        <div className="flex items-center justify-between gap-3">
          <div className="text-xs font-semibold text-slate-700">Recommendation Confidence</div>
          <div className="text-sm font-semibold tabular-nums text-slate-900">{confidencePct.toFixed(1)}%</div>
        </div>
        <div className="mt-2 h-2 w-full rounded-full bg-slate-200">
          <div className="h-2 rounded-full bg-slate-900" style={{ width: `${confidencePct}%` }} />
        </div>
      </div>

      <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
        <div className="text-xs font-semibold text-slate-700">Explanation</div>
        <p className="mt-2 text-sm leading-relaxed text-slate-800">{recommendation.explanation}</p>
      </div>
    </div>
  )
}

function AblationCheck({
  checked,
  label,
  onChange,
}: {
  checked: boolean
  label: string
  onChange: (checked: boolean) => void
}) {
  return (
    <label className="flex items-center gap-2 text-sm text-slate-700">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="h-4 w-4 rounded border-slate-300"
      />
      {label}
    </label>
  )
}

function HybridComparisonCard({
  mode,
  result,
}: {
  mode: string
  result: PredictDoseResponse
}) {
  const modeLabel: Record<string, string> = {
    structured: 'Structured only',
    structured_labs: 'Structured + Labs',
    full: 'Full Multi-modal',
  }
  const isSafetyOverride = result.adjustment_display === 'Safety override applied'

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="text-xs font-semibold text-slate-600">{modeLabel[mode] ?? mode}</div>
      <div className="mt-2 space-y-1 text-sm text-slate-800">
        <div>ML Dose: {result.ml_predicted_dose_units.toFixed(1)} units</div>
        <div>Adaptive Dose: {result.recommended_dose_units.toFixed(1)} units</div>
        <div>
          Adjustment:{' '}
          <span
            className={
              isSafetyOverride
                ? 'text-amber-700'
                : result.adjustment_display.startsWith('-')
                  ? 'text-rose-700'
                  : 'text-emerald-700'
            }
          >
            {result.adjustment_display}
          </span>
        </div>
        {result.adjustment_explanation ? (
          <div className="text-xs text-slate-600">{result.adjustment_explanation}</div>
        ) : null}
      </div>
    </div>
  )
}

function EvaluationDashboardPanel({
  loading,
  error,
  data,
}: {
  loading: boolean
  error: string | null
  data: EvaluationDashboardResponse | null
}) {
  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading evaluation dashboard…
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-900 shadow-sm">
        {error}
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Metric label="MAE" value={data.mae.toFixed(3)} />
        <Metric label="RMSE" value={data.rmse.toFixed(3)} />
        <Metric label="ROC-AUC (OvR Macro)" value={data.roc_auc_ovr_macro.toFixed(3)} />
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="text-sm font-semibold text-slate-900">ROC Curve</div>
        <div className="mt-3 grid grid-cols-1 gap-4 lg:grid-cols-3">
          {data.roc_curves.map((series) => {
            const chartData = series.fpr.map((fpr, idx) => ({
              fpr,
              tpr: series.tpr[idx] ?? 0,
            }))
            return (
              <div key={series.label} className="rounded-xl border border-slate-200 p-3">
                <div className="mb-2 text-xs font-semibold text-slate-600">{series.label}</div>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="fpr" domain={[0, 1]} type="number" />
                      <YAxis domain={[0, 1]} type="number" />
                      <Tooltip />
                      <Line type="monotone" dataKey="tpr" stroke="#0f172a" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-sm font-semibold text-slate-900">Confusion Matrix</div>
          <div className="mt-3 overflow-x-auto">
            <table className="min-w-full border-collapse text-sm">
              <thead>
                <tr>
                  <th className="border border-slate-200 bg-slate-50 px-3 py-2 text-left">True \ Pred</th>
                  {data.confusion_matrix.labels.map((label) => (
                    <th key={label} className="border border-slate-200 bg-slate-50 px-3 py-2 text-left">
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.confusion_matrix.matrix.map((row, rowIdx) => (
                  <tr key={data.confusion_matrix.labels[rowIdx]}>
                    <td className="border border-slate-200 px-3 py-2 font-semibold">
                      {data.confusion_matrix.labels[rowIdx]}
                    </td>
                    {row.map((value, colIdx) => (
                      <td key={`${rowIdx}-${colIdx}`} className="border border-slate-200 px-3 py-2">
                        {value}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-sm font-semibold text-slate-900">SHAP Summary Plot</div>
          <div className="mt-3 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={[...data.shap_summary].reverse()}
                layout="vertical"
                margin={{ top: 10, right: 10, left: 20, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis type="category" dataKey="feature" width={150} />
                <Tooltip formatter={(v) => Number(v ?? 0).toFixed(4)} />
                <Bar dataKey="mean_abs_shap" fill="#0f172a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="text-xs font-semibold text-slate-600">{label}</div>
      <div className="mt-1 text-lg font-semibold tracking-tight text-slate-900">
        {value}
      </div>
    </div>
  )
}

function ConfidenceCard({ value }: { value: number }) {
  const v = clamp(value, 0, 100)
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="text-xs font-semibold text-slate-600">Confidence</div>
        <div className="text-sm font-semibold tabular-nums text-slate-900">
          {v.toFixed(1)}%
        </div>
      </div>
      <div className="mt-3 h-2 w-full rounded-full bg-slate-100">
        <div
          className="h-2 rounded-full bg-slate-900 transition-[width]"
          style={{ width: `${v}%` }}
        />
      </div>
      <div className="mt-2 text-[11px] text-slate-500">
        Maximum class probability from the severity model.
      </div>
    </div>
  )
}

function Field(props: {
  label: string
  unit?: string
  hint?: string
  value: number | string
  step: number
  placeholder?: string
  onChange: (next: number) => void
}) {
  const { label, unit, hint, value, step, placeholder, onChange } = props
  return (
    <label className="block">
      <div className="flex items-end justify-between gap-2">
        <span className="text-xs font-semibold text-slate-700">{label}</span>
        {hint ? <span className="text-[11px] text-slate-500">{hint}</span> : null}
      </div>
      <div className="relative mt-1">
        <input
          className={[
            'w-full rounded-xl border border-slate-200 bg-white px-3 py-2 pr-14 text-sm',
            'outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200',
          ].join(' ')}
          inputMode="decimal"
          type="number"
          step={step}
          value={value}
          placeholder={placeholder}
          onChange={(e) =>
            onChange(e.target.value === '' ? NaN : Number(e.target.value))
          }
        />
        {unit ? (
          <div className="pointer-events-none absolute inset-y-0 right-0 grid place-items-center px-3 text-xs font-semibold text-slate-500">
            {unit}
          </div>
        ) : null}
      </div>
    </label>
  )
}

function SelectField(props: {
  label: string
  value: number
  options: Array<{ value: number; label: string }>
  onChange: (next: number) => void
}) {
  const { label, value, options, onChange } = props
  return (
    <label className="block">
      <span className="text-xs font-semibold text-slate-700">{label}</span>
      <select
        className={[
          'mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm',
          'outline-none focus:border-slate-400 focus:ring-2 focus:ring-slate-200',
        ].join(' ')}
        value={String(value)}
        onChange={(e) => onChange(Number(e.target.value))}
      >
        {options.map((o) => (
          <option key={o.value} value={String(o.value)}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-2">
        <div className="h-px flex-1 bg-slate-200" />
        <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-600">
          {title}
        </div>
        <div className="h-px flex-1 bg-slate-200" />
      </div>
      <div className="mt-3">{children}</div>
    </div>
  )
}

function AlertIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M10 2.5c.4 0 .8.2 1 .6l7.6 13.2c.4.7-.1 1.7-1 1.7H2.4c-.9 0-1.4-1-1-1.7L9 3.1c.2-.4.6-.6 1-.6Z"
        fill="currentColor"
        opacity="0.2"
      />
      <path
        d="M10 7.1c.5 0 .9.4.9.9v4.6a.9.9 0 0 1-1.8 0V8c0-.5.4-.9.9-.9Zm0 9a1.1 1.1 0 1 0 0-2.2 1.1 1.1 0 0 0 0 2.2Z"
        fill="currentColor"
      />
    </svg>
  )
}

function SparkIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M10 2l1.2 4.2L15.5 7.5l-4.3 1.3L10 13l-1.2-4.2L4.5 7.5l4.3-1.3L10 2Z"
        fill="currentColor"
      />
      <path
        d="M16.7 11.1l.7 2.3 2.3.7-2.3.7-.7 2.3-.7-2.3-2.3-.7 2.3-.7.7-2.3Z"
        fill="currentColor"
        opacity="0.8"
      />
    </svg>
  )
}

function StethoscopeIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M6 2.8a.9.9 0 0 1 .9.9V8a3.1 3.1 0 0 0 6.2 0V3.7a.9.9 0 1 1 1.8 0V8a4.9 4.9 0 0 1-4 4.8v1.4a2.3 2.3 0 1 0 4.6 0 .9.9 0 1 1 1.8 0 4.1 4.1 0 1 1-8.2 0v-1.4A4.9 4.9 0 0 1 5.1 8V3.7a.9.9 0 0 1 .9-.9Z"
        fill="currentColor"
      />
    </svg>
  )
}
