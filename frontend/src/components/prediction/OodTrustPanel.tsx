import { motion } from 'framer-motion'
import type { PredictDoseResponse, PatientInput } from "../../lib/api"
import { ShieldCheck, AlertTriangle, Activity, Fingerprint } from 'lucide-react'

type Props = {
  result: PredictDoseResponse
  form: PatientInput
}

/** Training cohort centroids (from synthetic dataset generation parameters) */
const COHORT_CENTROIDS = {
  fasting_glucose_mgdl: { mean: 140.0, std: 45.0, label: 'Fasting Glucose', unit: 'mg/dL' },
  hba1c: { mean: 8.0, std: 1.5, label: 'HbA1c', unit: '%' },
  creatinine_mgdl: { mean: 1.0, std: 0.4, label: 'Serum Creatinine', unit: 'mg/dL' },
  age: { mean: 58.0, std: 12.0, label: 'Patient Age', unit: 'yrs' },
  bmi: { mean: 30.0, std: 5.0, label: 'BMI', unit: 'kg/m²' },
}

function computeDeviation(value: number, mean: number, std: number): number {
  return Math.abs(value - mean) / std
}

function getDeviationColor(dev: number): string {
  if (dev <= 1.0) return 'var(--accent-success)'
  if (dev <= 2.0) return 'var(--accent-warning)'
  return 'var(--accent-danger)'
}

function getDeviationLabel(dev: number): string {
  if (dev <= 1.0) return 'Within 1σ'
  if (dev <= 2.0) return 'Within 2σ'
  return 'Outlier (>2σ)'
}

function getTrustColor(score: number): string {
  if (score >= 90) return 'var(--accent-success)'
  if (score >= 80) return 'var(--accent-warning)'
  return 'var(--accent-danger)'
}

function getTrustLabel(isInDist: boolean): string {
  return isInDist ? 'In-Distribution (Safe for Inference)' : 'Out-of-Distribution — Specialist Review Recommended'
}

export default function OodTrustPanel({ result, form }: Props) {
  const ood = result.ood_metric
  const conformal = result.conformal_interval

  if (!ood) return null

  const bmi = form.bmi || (form.weight_kg / Math.pow(form.height_cm / 100, 2))

  const featureDeviations = [
    { key: 'fasting_glucose_mgdl', value: form.fasting_glucose_mgdl, ...COHORT_CENTROIDS.fasting_glucose_mgdl },
    { key: 'hba1c', value: form.hba1c, ...COHORT_CENTROIDS.hba1c },
    { key: 'creatinine_mgdl', value: form.creatinine_mgdl, ...COHORT_CENTROIDS.creatinine_mgdl },
    { key: 'age', value: form.age, ...COHORT_CENTROIDS.age },
    { key: 'bmi', value: bmi, ...COHORT_CENTROIDS.bmi },
  ].map(f => ({
    ...f,
    deviation: computeDeviation(f.value, f.mean, f.std),
  }))

  const maxDeviation = Math.max(...featureDeviations.map(f => f.deviation))

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Fingerprint size={18} style={{ color: 'var(--accent-primary)' }} />
            <h3 style={{ fontSize: '0.875rem', fontWeight: 700, letterSpacing: '0.05em', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Out-of-Distribution Detection & Clinical Trust
            </h3>
          </div>
          <span style={{
            fontSize: '0.6875rem',
            fontWeight: 700,
            padding: '0.25rem 0.625rem',
            background: ood.is_in_distribution ? 'rgba(5, 150, 105, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            color: ood.is_in_distribution ? 'var(--accent-success)' : 'var(--accent-danger)',
            borderRadius: '99px',
            textTransform: 'uppercase',
          }}>
            {ood.is_in_distribution ? '✓ In-Domain' : '⚠ OOD Warning'}
          </span>
        </div>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.375rem', lineHeight: 1.4 }}>
          Measures how closely this patient's clinical profile matches the synthetic training cohort using Mahalanobis distance. 
          High trust scores indicate the model is operating within its validated domain.
        </p>
      </div>

      {/* Trust Score Gauge */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '1.5rem', 
        padding: '1.25rem', 
        background: 'var(--bg-app)', 
        borderRadius: '10px', 
        border: `1.5px solid ${ood.is_in_distribution ? 'rgba(5, 150, 105, 0.25)' : 'rgba(239, 68, 68, 0.25)'}` 
      }}>
        {/* Circular Gauge */}
        <div style={{ position: 'relative', width: '80px', height: '80px', flexShrink: 0 }}>
          <svg viewBox="0 0 36 36" style={{ transform: 'rotate(-90deg)', width: '100%', height: '100%' }}>
            <circle cx="18" cy="18" r="15.5" fill="none" stroke="rgba(0,0,0,0.06)" strokeWidth="3" />
            <motion.circle 
              cx="18" cy="18" r="15.5" fill="none" 
              stroke={getTrustColor(ood.trust_score_percent)} 
              strokeWidth="3" 
              strokeLinecap="round"
              strokeDasharray={`${(ood.trust_score_percent / 100) * 97.4} 97.4`}
              initial={{ strokeDasharray: '0 97.4' }}
              animate={{ strokeDasharray: `${(ood.trust_score_percent / 100) * 97.4} 97.4` }}
              transition={{ duration: 1.2, ease: 'easeOut' }}
            />
          </svg>
          <div style={{ 
            position: 'absolute', 
            top: '50%', 
            left: '50%', 
            transform: 'translate(-50%, -50%)', 
            textAlign: 'center' 
          }}>
            <div style={{ fontSize: '1.125rem', fontWeight: 800, color: getTrustColor(ood.trust_score_percent), lineHeight: 1 }}>
              {ood.trust_score_percent}%
            </div>
            <div style={{ fontSize: '0.5rem', fontWeight: 600, color: 'var(--text-muted)', marginTop: '2px' }}>TRUST</div>
          </div>
        </div>

        {/* Metrics */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8125rem' }}>
            <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>Mahalanobis Distance</span>
            <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'monospace' }}>
              {ood.mahalanobis_distance.toFixed(2)} / {ood.threshold.toFixed(1)}
            </span>
          </div>
          <div style={{ height: '6px', background: 'rgba(0,0,0,0.06)', borderRadius: '999px', overflow: 'hidden', position: 'relative' }}>
            {/* Threshold marker */}
            <div style={{ 
              position: 'absolute', 
              left: `${Math.min(100, (ood.threshold / 4.0) * 100)}%`, 
              top: 0, bottom: 0, 
              width: '2px', 
              background: 'var(--text-muted)',
              zIndex: 1,
            }} />
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(100, (ood.mahalanobis_distance / 4.0) * 100)}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
              style={{
                height: '100%',
                borderRadius: '999px',
                background: getTrustColor(ood.trust_score_percent),
              }}
            />
          </div>
          <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
            <span>0 (Centroid)</span>
            <span>Threshold: {ood.threshold}</span>
          </div>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.375rem', 
            fontSize: '0.75rem', 
            fontWeight: 600, 
            color: ood.is_in_distribution ? 'var(--accent-success)' : 'var(--accent-danger)',
            marginTop: '0.25rem',
          }}>
            {ood.is_in_distribution ? <ShieldCheck size={14} /> : <AlertTriangle size={14} />}
            {getTrustLabel(ood.is_in_distribution)}
          </div>
        </div>
      </div>

      {/* Per-Feature Deviation Breakdown */}
      <div>
        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '0.75rem', letterSpacing: '0.04em' }}>
          Feature-Level Deviation from Training Cohort
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
          {featureDeviations.map((f, idx) => (
            <div key={f.key} style={{ display: 'grid', gridTemplateColumns: '140px 90px 1fr 70px', alignItems: 'center', gap: '0.75rem', fontSize: '0.8125rem' }}>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{f.label}</span>
              <span style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                {f.value.toFixed(1)} {f.unit}
              </span>
              <div style={{ height: '6px', background: 'rgba(0,0,0,0.05)', borderRadius: '999px', overflow: 'hidden' }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(100, (f.deviation / Math.max(maxDeviation, 3.0)) * 100)}%` }}
                  transition={{ delay: idx * 0.08, duration: 0.7, ease: 'easeOut' }}
                  style={{
                    height: '100%',
                    borderRadius: '999px',
                    background: getDeviationColor(f.deviation),
                  }}
                />
              </div>
              <span style={{ fontSize: '0.6875rem', fontWeight: 600, color: getDeviationColor(f.deviation), textAlign: 'right' }}>
                {getDeviationLabel(f.deviation)}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Conformal Prediction Interval */}
      {conformal && (
        <div style={{ padding: '1rem', background: 'var(--bg-app)', borderRadius: '8px', border: '1px solid var(--border-light)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <Activity size={16} style={{ color: 'var(--accent-primary)' }} />
            <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              95% Conformal Prediction Interval
            </span>
          </div>
          <div style={{ position: 'relative', height: '32px', background: 'rgba(0,0,0,0.04)', borderRadius: '8px', overflow: 'hidden' }}>
            {/* Safe range background */}
            <div style={{
              position: 'absolute',
              left: `${Math.max(0, ((conformal.lower_units - 0) / 60) * 100)}%`,
              width: `${((conformal.upper_units - conformal.lower_units) / 60) * 100}%`,
              top: 0, bottom: 0,
              background: 'rgba(5, 150, 105, 0.12)',
              borderRadius: '6px',
            }} />
            {/* Point estimate marker */}
            <motion.div
              initial={{ left: '0%' }}
              animate={{ left: `${Math.max(0, Math.min(100, (result.recommended_dose_units / 60) * 100))}%` }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
              style={{
                position: 'absolute',
                top: '4px',
                bottom: '4px',
                width: '4px',
                background: 'var(--accent-primary)',
                borderRadius: '2px',
                transform: 'translateX(-50%)',
              }}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.375rem', fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
            <span>Lower: <strong style={{ color: 'var(--text-primary)' }}>{conformal.lower_units.toFixed(1)} U</strong></span>
            <span>Point Estimate: <strong style={{ color: 'var(--accent-primary)' }}>{result.recommended_dose_units.toFixed(1)} U</strong></span>
            <span>Upper: <strong style={{ color: 'var(--text-primary)' }}>{conformal.upper_units.toFixed(1)} U</strong></span>
          </div>
          <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.5rem', lineHeight: 1.4 }}>
            Interval width of <strong>{(conformal.upper_units - conformal.lower_units).toFixed(1)} U</strong> at 
            {' '}{(conformal.confidence_level * 100).toFixed(0)}% coverage guarantees the true optimal dose falls within these bounds 
            with the stated probability under exchangeability assumptions (Vovk et al., 2005).
          </div>
        </div>
      )}
    </div>
  )
}
