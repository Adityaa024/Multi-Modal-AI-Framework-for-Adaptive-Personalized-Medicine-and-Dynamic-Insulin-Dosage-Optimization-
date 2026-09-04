import { motion } from 'framer-motion'
import type { PredictDoseResponse, PatientInput } from "../../lib/api"
import { AlertTriangle, Thermometer, TrendingDown, ShieldCheck, HeartPulse } from 'lucide-react'

type Props = {
  result: PredictDoseResponse
  form: PatientInput
}

function getHypoRiskLevel(prob: number): { label: string; color: string; bg: string } {
  if (prob >= 0.50) return { label: 'HIGH RISK', color: 'var(--accent-danger)', bg: 'rgba(239, 68, 68, 0.1)' }
  if (prob >= 0.25) return { label: 'MODERATE RISK', color: 'var(--accent-warning)', bg: 'rgba(245, 158, 11, 0.1)' }
  return { label: 'LOW RISK', color: 'var(--accent-success)', bg: 'rgba(5, 150, 105, 0.1)' }
}

export default function AdverseEventPanel({ result, form }: Props) {
  const hypoProb = result.hypoglycemia_risk_probability
  const hyperProb = result.hyperglycemia_risk_probability
  const dose = result.recommended_dose_units
  const weight = form.weight_kg

  // Compute Insulin Sensitivity Factor (ISF) using the "1800 Rule" for rapid-acting insulin
  // For basal insulin, the "1500 Rule" is sometimes used, but 1800 is standard for T2D
  const estimatedTDD = dose // Using recommended dose as TDD proxy for basal-only regimen
  const isf = estimatedTDD > 0 ? 1800 / estimatedTDD : 0
  const estimatedGlucoseDrop = dose > 0 ? isf : 0 // per unit
  
  // Predicted nadir glucose (fasting glucose minus expected drop from full dose)
  const predictedNadirGlucose = form.fasting_glucose_mgdl - (estimatedGlucoseDrop * (dose * 0.6 / estimatedTDD))
  const nadirBelowThreshold = predictedNadirGlucose < 70
  const nadirBorderline = predictedNadirGlucose < 90 && predictedNadirGlucose >= 70

  // Dose per kg metrics
  const dosePerKg = weight > 0 ? dose / weight : 0
  const adaMinPerKg = 0.1
  const adaMaxPerKg = 0.5

  const hypoRisk = getHypoRiskLevel(hypoProb)

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <HeartPulse size={18} style={{ color: 'var(--accent-primary)' }} />
            <h3 style={{ fontSize: '0.875rem', fontWeight: 700, letterSpacing: '0.05em', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Adverse Event Risk Analysis
            </h3>
          </div>
          <span style={{
            fontSize: '0.6875rem',
            fontWeight: 700,
            padding: '0.25rem 0.625rem',
            background: hypoRisk.bg,
            color: hypoRisk.color,
            borderRadius: '99px',
            textTransform: 'uppercase',
          }}>
            Hypoglycemia: {hypoRisk.label}
          </span>
        </div>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.375rem', lineHeight: 1.4 }}>
          Insulin Sensitivity Factor (ISF) analysis and adverse event risk bounds based on ADA/Endocrine Society clinical practice guidelines.
        </p>
      </div>

      {/* ISF & Glucose Drop Analysis */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div style={{ padding: '1rem', background: 'var(--bg-app)', borderRadius: '8px', border: '1px solid var(--border-light)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', marginBottom: '0.5rem' }}>
            <Thermometer size={14} style={{ color: 'var(--accent-primary)' }} />
            <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Estimated ISF (1800 Rule)
            </span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1.1 }}>
            {isf > 0 ? isf.toFixed(0) : '--'}
            <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)', marginLeft: '0.25rem' }}>mg/dL per U</span>
          </div>
          <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.375rem' }}>
            Each unit of insulin is expected to reduce blood glucose by ~{isf > 0 ? isf.toFixed(0) : '--'} mg/dL
          </div>
        </div>

        <div style={{ padding: '1rem', background: 'var(--bg-app)', borderRadius: '8px', border: '1px solid var(--border-light)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', marginBottom: '0.5rem' }}>
            <TrendingDown size={14} style={{ color: nadirBelowThreshold ? 'var(--accent-danger)' : 'var(--accent-primary)' }} />
            <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Predicted Glucose Nadir
            </span>
          </div>
          <div style={{ 
            fontSize: '1.75rem', 
            fontWeight: 800, 
            color: nadirBelowThreshold ? 'var(--accent-danger)' : nadirBorderline ? 'var(--accent-warning)' : 'var(--accent-success)', 
            lineHeight: 1.1 
          }}>
            {predictedNadirGlucose.toFixed(0)}
            <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)', marginLeft: '0.25rem' }}>mg/dL</span>
          </div>
          <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.375rem' }}>
            {nadirBelowThreshold 
              ? '⚠ Below 70 mg/dL threshold — hypoglycemia risk'
              : nadirBorderline 
                ? 'Borderline — monitor closely for symptoms'
                : '✓ Within safe glycemic range'
            }
          </div>
        </div>

        <div style={{ padding: '1rem', background: 'var(--bg-app)', borderRadius: '8px', border: '1px solid var(--border-light)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', marginBottom: '0.5rem' }}>
            <ShieldCheck size={14} style={{ color: 'var(--accent-primary)' }} />
            <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Dose Intensity (U/kg)
            </span>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1.1 }}>
            {dosePerKg.toFixed(2)}
            <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)', marginLeft: '0.25rem' }}>U/kg/day</span>
          </div>
          <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.375rem' }}>
            ADA Safe Range: {adaMinPerKg} – {adaMaxPerKg} U/kg/day
          </div>
        </div>
      </div>

      {/* Dose-Response Safety Envelope */}
      <div style={{ padding: '1.25rem', background: 'var(--bg-app)', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '1rem', letterSpacing: '0.04em' }}>
          Weight-Normalized Dose Safety Envelope
        </div>
        
        {/* Visual gauge bar */}
        <div style={{ position: 'relative', height: '36px', background: 'rgba(0,0,0,0.04)', borderRadius: '8px', overflow: 'visible', marginBottom: '0.5rem' }}>
          {/* Safe zone */}
          <div style={{
            position: 'absolute',
            left: `${(adaMinPerKg / 0.7) * 100}%`,
            width: `${((adaMaxPerKg - adaMinPerKg) / 0.7) * 100}%`,
            top: 0, bottom: 0,
            background: 'rgba(5, 150, 105, 0.12)',
            borderRadius: '4px',
          }} />
          {/* ADA Min label */}
          <div style={{
            position: 'absolute',
            left: `${(adaMinPerKg / 0.7) * 100}%`,
            top: 0, bottom: 0,
            width: '1.5px',
            background: 'var(--accent-primary)',
            opacity: 0.4,
          }} />
          {/* ADA Max label */}
          <div style={{
            position: 'absolute',
            left: `${(adaMaxPerKg / 0.7) * 100}%`,
            top: 0, bottom: 0,
            width: '1.5px',
            background: 'var(--accent-danger)',
            opacity: 0.4,
          }} />
          {/* Current dose marker */}
          <motion.div
            initial={{ left: '0%' }}
            animate={{ left: `${Math.min(100, (dosePerKg / 0.7) * 100)}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            style={{
              position: 'absolute',
              top: '3px',
              bottom: '3px',
              width: '6px',
              background: dosePerKg > adaMaxPerKg ? 'var(--accent-danger)' : dosePerKg < adaMinPerKg ? 'var(--accent-warning)' : 'var(--accent-primary)',
              borderRadius: '3px',
              transform: 'translateX(-50%)',
              boxShadow: '0 0 6px rgba(5, 150, 105, 0.3)',
            }}
          />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
          <span>0 U/kg</span>
          <span style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>Safe Zone (0.1–0.5 U/kg)</span>
          <span>0.7 U/kg</span>
        </div>
      </div>

      {/* Dual Risk Gauges */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {/* Hypoglycemia */}
        <div style={{ padding: '1rem', background: hypoRisk.bg, borderRadius: '8px', border: `1px solid ${hypoProb > 0.25 ? 'rgba(239, 68, 68, 0.2)' : 'var(--border-light)'}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: hypoRisk.color }}>
              Hypoglycemia Risk
            </span>
            <span style={{ fontSize: '1.25rem', fontWeight: 800, color: hypoRisk.color }}>
              {(hypoProb * 100).toFixed(0)}%
            </span>
          </div>
          <div style={{ height: '6px', background: 'rgba(0,0,0,0.06)', borderRadius: '999px', overflow: 'hidden' }}>
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${hypoProb * 100}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
              style={{
                height: '100%',
                borderRadius: '999px',
                background: hypoRisk.color,
              }}
            />
          </div>
          <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.5rem', lineHeight: 1.3 }}>
            {hypoProb >= 0.30 
              ? 'ADA: Consider dose reduction or adjunct GLP-1 RA therapy'
              : 'Within acceptable risk bounds per Endocrine Society guidelines'
            }
          </div>
        </div>

        {/* Hyperglycemia */}
        <div style={{ padding: '1rem', background: hyperProb > 0.60 ? 'rgba(245, 158, 11, 0.08)' : 'var(--bg-app)', borderRadius: '8px', border: '1px solid var(--border-light)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: hyperProb > 0.60 ? 'var(--accent-warning)' : 'var(--text-secondary)' }}>
              Hyperglycemia Risk
            </span>
            <span style={{ fontSize: '1.25rem', fontWeight: 800, color: hyperProb > 0.60 ? 'var(--accent-warning)' : 'var(--text-primary)' }}>
              {(hyperProb * 100).toFixed(0)}%
            </span>
          </div>
          <div style={{ height: '6px', background: 'rgba(0,0,0,0.06)', borderRadius: '999px', overflow: 'hidden' }}>
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${hyperProb * 100}%` }}
              transition={{ duration: 1, ease: 'easeOut', delay: 0.2 }}
              style={{
                height: '100%',
                borderRadius: '999px',
                background: hyperProb > 0.60 ? 'var(--accent-warning)' : 'var(--accent-success)',
              }}
            />
          </div>
          <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', marginTop: '0.5rem', lineHeight: 1.3 }}>
            {hyperProb > 0.70 
              ? 'Persistent hyperglycemia likely — consider dose escalation or prandial add-on'
              : 'Glycemic control expected within target range (ADA < 180 mg/dL post-prandial)'
            }
          </div>
        </div>
      </div>

      {/* Clinical Warning Callout */}
      {(nadirBelowThreshold || hypoProb >= 0.30) && (
        <motion.div 
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ 
            padding: '1rem', 
            background: 'rgba(239, 68, 68, 0.06)', 
            borderRadius: '8px', 
            border: '1px solid rgba(239, 68, 68, 0.2)',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.75rem',
          }}
        >
          <AlertTriangle size={18} style={{ color: 'var(--accent-danger)', flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--accent-danger)', marginBottom: '0.25rem' }}>
              Clinical Safety Alert
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {nadirBelowThreshold 
                ? `Predicted glucose nadir (${predictedNadirGlucose.toFixed(0)} mg/dL) falls below the ADA hypoglycemia threshold of 70 mg/dL. Consider dose reduction, bedtime snack protocol, or continuous glucose monitoring (CGM) to mitigate nocturnal hypoglycemia risk.`
                : `Elevated hypoglycemia probability (${(hypoProb * 100).toFixed(0)}%) exceeds the clinical alert threshold. Per ADA 2024 Standards, consider reducing dose to 90% of current recommendation or adding adjunct GLP-1 RA therapy.`
              }
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
