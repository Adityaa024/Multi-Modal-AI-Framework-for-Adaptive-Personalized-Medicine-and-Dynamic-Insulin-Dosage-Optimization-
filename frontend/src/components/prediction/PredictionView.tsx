import { motion } from 'framer-motion'
import { useState } from 'react'
import type { PredictDoseResponse, PatientInput } from "../../lib/api"
import PatientOverview from './PatientOverview'
import AIPredictionHero from './AIPredictionHero'
import MultimodalFusion from './MultimodalFusion'
import RiskProfile from './RiskProfile'
import SeverityDistribution from './SeverityDistribution'
import TreatmentRecommendation from './TreatmentRecommendation'
import DoseTimeline from './DoseTimeline'
import PatientInputForm from './PatientInputForm'
import type { TrendPoint } from "../../lib/api"
import { Edit3, Download, Printer } from 'lucide-react'
import OodTrustPanel from './OodTrustPanel'
import AdverseEventPanel from './AdverseEventPanel'

type Props = {
  form: PatientInput
  setForm: (form: PatientInput) => void
  result: PredictDoseResponse | null
  isPredicting: boolean
  error: string | null
  trendData: TrendPoint[]
}

export default function PredictionView({ form, setForm, result, isPredicting, error, trendData }: Props) {
  const [isEditing, setIsEditing] = useState(false)

  const handleExportJson = () => {
    if (!result) return
    const dossier = {
      export_timestamp: new Date().toISOString(),
      platform: "MediPredict AI - Multimodal Clinical Decision Support",
      patient_profile: form,
      clinical_recommendation: {
        recommended_dose_units: result.recommended_dose_units,
        severity: result.severity,
        confidence_score: result.confidence_score,
        uncertainty_entropy: result.uncertainty_entropy,
        safe_range: result.safe_range,
        safety_guardrails: result.safety,
        glycemic_risk: {
          hyperglycemia_risk: result.hyperglycemia_risk_probability,
          hypoglycemia_risk: result.hypoglycemia_risk_probability,
        },
        drug_recommendation: result.drug_recommendation,
        rationale: result.explanation,
      },
    }
    const blob = new Blob([JSON.stringify(dossier, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `medipredict_dossier_${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handlePrint = () => {
    window.print()
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      style={{ display: 'flex', flexDirection: 'column', gap: '2.25rem' }}
    >
      {/* 1. Patient Context */}
      {isEditing ? (
        <PatientInputForm form={form} setForm={setForm} onDone={() => setIsEditing(false)} />
      ) : (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div>
              <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Patient Clinical Profile
              </span>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.125rem' }}>
                Active baseline demographics, laboratory markers, and behavioral features
              </p>
            </div>
            <button 
              onClick={() => setIsEditing(true)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.625rem',
                background: 'var(--bg-card)',
                border: '1.5px solid var(--accent-primary)',
                color: 'var(--accent-primary)',
                padding: '0.625rem 1.35rem',
                borderRadius: '8px',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: 'pointer',
                boxShadow: '0 2px 5px rgba(5, 150, 105, 0.08)',
                transition: 'all 0.2s ease',
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = 'var(--accent-primary)'
                e.currentTarget.style.color = '#ffffff'
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = 'var(--bg-card)'
                e.currentTarget.style.color = 'var(--accent-primary)'
              }}
            >
              <Edit3 size={16} />
              <span>Edit Patient Data</span>
            </button>
          </div>
          <PatientOverview form={form} />
        </div>
      )}
      
      {/* Error state */}
      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'var(--accent-danger)', padding: '1rem', borderRadius: '12px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
          <strong style={{ display: 'block', marginBottom: '0.25rem' }}>Prediction Failed</strong>
          <span style={{ fontSize: '0.875rem' }}>{error}</span>
        </div>
      )}

      {/* 2. Hero Prediction & Pipeline */}
      {!result && !isPredicting ? (
        <div className="card" style={{ padding: '4rem 2rem', textAlign: 'center', background: 'var(--bg-app)', border: '2px dashed var(--border-light)', marginTop: '1rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Ready for Prediction</h3>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '400px', margin: '0 auto', fontSize: '0.875rem', lineHeight: 1.5 }}>
            The Multimodal AI engine is standing by. Review the patient data and click the <strong>Predict</strong> button to generate a dosage optimization recommendation.
          </p>
        </div>
      ) : (
        <>
          <AIPredictionHero result={result} isPredicting={isPredicting} previousDose={form.previous_insulin_dose_units} />
          <MultimodalFusion form={form} isPredicting={isPredicting} result={result} />
        </>
      )}

      {/* 4. Downstream Clinical Decision Support */}
      {result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', padding: '1rem 1.25rem', background: 'var(--bg-card)', border: '1px solid var(--border-light)', borderRadius: '12px' }}>
            <div>
              <strong style={{ fontSize: '0.875rem', color: 'var(--text-primary)', display: 'block' }}>Clinical Decision Dossier Generated</strong>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Structured dosage recommendation, safety overrides, and contraindications</span>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button 
                type="button" 
                onClick={handleExportJson}
                style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', padding: '0.4375rem 0.875rem', fontSize: '0.75rem', fontWeight: 600, borderRadius: '6px', border: '1px solid var(--border-light)', background: 'var(--bg-app)', color: 'var(--text-primary)', cursor: 'pointer' }}
              >
                <Download size={14} /> Export JSON Dossier
              </button>
              <button 
                type="button" 
                onClick={handlePrint}
                style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', padding: '0.4375rem 0.875rem', fontSize: '0.75rem', fontWeight: 600, borderRadius: '6px', border: '1px solid var(--border-light)', background: 'var(--bg-app)', color: 'var(--text-primary)', cursor: 'pointer' }}
              >
                <Printer size={14} /> Print Summary
              </button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2rem' }}>
            <RiskProfile result={result} />
            <OodTrustPanel result={result} form={form} />
            <AdverseEventPanel result={result} form={form} />
            <SeverityDistribution result={result} />
            <TreatmentRecommendation result={result} />
          </div>
          <DoseTimeline data={trendData} />
        </div>
      )}
    </motion.div>
  )
}
