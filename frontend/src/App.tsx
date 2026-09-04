import { useEffect, useMemo, useState } from 'react'
import {
  getEvaluationDashboard,
  predictDose,
  type EvaluationDashboardResponse,
  type PatientInput,
  type PredictDoseResponse,
  type TrendPoint,
} from "./lib/api"
import AppShell from './components/layout/AppShell'
import PredictionView from './components/prediction/PredictionView'
import ExplainabilityView from './components/explainability/ExplainabilityView'
import EvaluationView from './components/evaluation/EvaluationView'
import InsightsView from './components/insights/InsightsView'

type FormState = PatientInput

function nowLabel(): string {
  const d = new Date()
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function App() {
  const [activeTab, setActiveTab] = useState('prediction')
  
  // App state
  const [form, setForm] = useState<FormState>({
    age: 62,
    weight_kg: 92,
    height_cm: 170,
    bmi: 31.8,
    fasting_glucose_mgdl: 185,
    hba1c: 8.6,
    creatinine_mgdl: 1.2,
    previous_insulin_dose_units: 18,
    glucose_after_dose_mgdl: 150,
    activity_level: 1,
    diet_adherence_score: 70,
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Results
  const [resultsByMode, setResultsByMode] = useState<Record<string, PredictDoseResponse>>({})
  const [trend, setTrend] = useState<TrendPoint[]>([])
  
  // Evaluation Data
  const [evaluationLoading, setEvaluationLoading] = useState(false)
  const [evaluationError, setEvaluationError] = useState<string | null>(null)
  const [evaluationData, setEvaluationData] = useState<EvaluationDashboardResponse | null>(null)

  const primaryResult = useMemo(() => {
    return resultsByMode['full'] ?? null
  }, [resultsByMode])

  useEffect(() => {
    if (evaluationData || evaluationLoading) return

    setEvaluationError(null)
    setEvaluationLoading(true)
    getEvaluationDashboard()
      .then((payload) => setEvaluationData(payload))
      .catch((e) => setEvaluationError(e instanceof Error ? e.message : 'Failed to load evaluation dashboard'))
      .finally(() => setEvaluationLoading(false))
  }, [evaluationData, evaluationLoading])

  async function onPredict() {
    setError(null)
    setLoading(true)
    try {
      const nextResults: Record<string, PredictDoseResponse> = {}
      const modes = ['structured', 'structured_labs', 'full'] as const
      
      const predictions = await Promise.all(
        modes.map((mode) => predictDose({ ...form, feature_mode: mode }))
      )

      modes.forEach((mode, idx) => {
        nextResults[mode] = predictions[idx]
      })

      setResultsByMode(nextResults)

      const primary = nextResults['full']
      if (primary) {
        setTrend((prev) => {
          const next: TrendPoint[] = [
            ...prev,
            {
              at: nowLabel(),
              fasting_glucose_mgdl: form.fasting_glucose_mgdl,
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

  const renderView = () => {
    if (activeTab === 'prediction') {
      return (
        <PredictionView 
          form={form} 
          setForm={setForm} 
          result={primaryResult} 
          isPredicting={loading} 
          error={error} 
          trendData={trend}
        />
      )
    }
    if (activeTab === 'explainability') {
      return (
        <ExplainabilityView 
          result={primaryResult} 
          evaluationData={evaluationData} 
          form={form} 
          loading={evaluationLoading} 
          error={evaluationError} 
        />
      )
    }
    if (activeTab === 'evaluation') {
      return <EvaluationView data={evaluationData} loading={evaluationLoading} error={evaluationError} />
    }
    if (activeTab === 'insights') {
      return <InsightsView resultsByMode={resultsByMode} />
    }
    
    return null
  }

  return (
    <AppShell
      activeTab={activeTab}
      setActiveTab={setActiveTab}
      onPredict={onPredict}
      loading={loading}
      primaryResult={primaryResult}
    >
      {renderView()}
    </AppShell>
  )
}
