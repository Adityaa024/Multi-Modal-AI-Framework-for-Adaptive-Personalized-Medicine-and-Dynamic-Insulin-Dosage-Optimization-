import { motion } from 'framer-motion'
import type { PredictDoseResponse } from "../../lib/api"
import { ArrowDown, Layers, AlertCircle, ShieldCheck, Cpu } from 'lucide-react'

type Props = {
  resultsByMode: Record<string, PredictDoseResponse>
}

export default function InsightsView({ resultsByMode }: Props) {
  const hasResults = Object.keys(resultsByMode).length > 0

  const progression = [
    { 
      key: 'structured', 
      label: 'Stage 1: Structured Demographics', 
      desc: 'Age, body weight, height, and computed BMI',
      features: ['Age', 'Weight', 'Height', 'BMI'] 
    },
    { 
      key: 'structured_labs', 
      label: 'Stage 2: Biochemical Lab Integration', 
      desc: 'Incorporates glycemic indicators & renal function',
      features: ['Fasting Glucose', 'HbA1c', 'Serum Creatinine'] 
    },
    { 
      key: 'full', 
      label: 'Stage 3: Full Multimodal Fusion', 
      desc: 'Integrates patient behavior, activity, and treatment history',
      features: ['Prior Insulin Dose', 'Post-dose Glucose', 'Activity Level', 'Diet Adherence'] 
    }
  ]

  const fullDose = resultsByMode['full']?.recommended_dose_units
  const structuredDose = resultsByMode['structured']?.recommended_dose_units

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ duration: 0.4 }}
      style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}
    >
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
          <Layers size={18} style={{ color: 'var(--accent-primary)' }} />
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Multimodal Research Synthesis
          </span>
        </div>
        <h2 style={{ fontSize: '1.625rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
          ABLATION STUDIES & ARCHITECTURAL INSIGHTS
        </h2>
        <p style={{ color: 'var(--text-secondary)', marginTop: '0.375rem', fontSize: '0.875rem' }}>
          Empirical validation demonstrating incremental value of fusing biological, laboratory, and behavioral signals.
        </p>
      </div>

      {/* Feature Modality Hierarchy Grid */}
      <div className="card">
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
          Four-Tier Clinical Modality Hierarchy
        </h3>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
          How diverse physiological data streams are encoded and passed into the decision pipeline
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
          <div style={{ padding: '1rem', background: 'var(--bg-app)', borderRadius: '8px', border: '1px solid var(--border-light)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase' }}>
              Modality A: Demographics
            </div>
            <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.25rem' }}>
              Vitals & Body Metrics
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem', lineHeight: 1.4 }}>
              Age, weight (kg), height (cm), and derived BMI defining metabolic volume.
            </p>
          </div>

          <div style={{ padding: '1rem', background: 'var(--bg-app)', borderRadius: '8px', border: '1px solid var(--border-light)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-secondary)', textTransform: 'uppercase' }}>
              Modality B: Biochemical
            </div>
            <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.25rem' }}>
              Endocrine & Renal Markers
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem', lineHeight: 1.4 }}>
              Fasting glucose, HbA1c (glycated hemoglobin), and serum creatinine clearance.
            </p>
          </div>

          <div style={{ padding: '1rem', background: 'var(--bg-app)', borderRadius: '8px', border: '1px solid var(--border-light)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#f59e0b', textTransform: 'uppercase' }}>
              Modality C: Historical
            </div>
            <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.25rem' }}>
              Treatment-Response Loop
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem', lineHeight: 1.4 }}>
              Previous daily insulin dosage and 2-hour post-dose glycemic excursion.
            </p>
          </div>

          <div style={{ padding: '1rem', background: 'var(--bg-app)', borderRadius: '8px', border: '1px solid var(--border-light)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#8b5cf6', textTransform: 'uppercase' }}>
              Modality D: Behavioral
            </div>
            <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.25rem' }}>
              Lifestyle Adherence
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem', lineHeight: 1.4 }}>
              Physical activity category and dietary compliance index (0-100 score).
            </p>
          </div>
        </div>
      </div>

      {/* Incremental Ablation Progression Card */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Active Patient Ablation Progression
            </h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              Comparing dosage optimization outputs across progressive feature inclusions
            </p>
          </div>

          {hasResults && fullDose !== undefined && structuredDose !== undefined && (
            <div style={{ padding: '0.375rem 0.75rem', background: 'rgba(5, 150, 105, 0.1)', border: '1px solid rgba(5, 150, 105, 0.25)', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-primary)' }}>
              Ablation Refinement Delta: {(fullDose - structuredDose >= 0 ? '+' : '') + (fullDose - structuredDose).toFixed(1)} U
            </div>
          )}
        </div>

        {!hasResults ? (
          <div style={{ padding: '3rem 1.5rem', textAlign: 'center', background: 'var(--bg-app)', borderRadius: '8px', border: '1px dashed var(--border-light)' }}>
            <AlertCircle size={32} style={{ color: 'var(--text-muted)', margin: '0 auto 0.75rem auto' }} />
            <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              No Active Prediction Data Loaded
            </h4>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', maxWidth: '420px', margin: '0.375rem auto 0 auto', lineHeight: 1.5 }}>
              Click <strong>Predict</strong> on the Prediction tab to execute the ablation inference pipeline across all 3 feature modalities simultaneously.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', marginTop: '1.5rem' }}>
            {progression.map((stage, idx) => {
              const res = resultsByMode[stage.key]
              const hasNext = idx < progression.length - 1
              const isFinal = idx === progression.length - 1

              return (
                <div key={stage.key} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', maxWidth: '640px' }}>
                  <motion.div 
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: idx * 0.15, type: 'spring' }}
                    style={{ 
                      width: '100%',
                      padding: '1.25rem 1.5rem',
                      background: isFinal ? 'rgba(5, 150, 105, 0.05)' : 'var(--bg-card)',
                      border: `1.5px solid ${isFinal ? 'var(--accent-primary)' : 'var(--border-light)'}`,
                      borderRadius: '12px',
                      boxShadow: isFinal ? '0 4px 12px rgba(5, 150, 105, 0.08)' : '0 1px 3px rgba(0,0,0,0.04)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      gap: '1rem',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontSize: '0.9375rem', fontWeight: 700, color: isFinal ? 'var(--accent-primary)' : 'var(--text-primary)' }}>
                          {stage.label}
                        </span>
                        {isFinal && (
                          <span style={{ fontSize: '0.6875rem', fontWeight: 700, padding: '0.125rem 0.375rem', background: 'var(--accent-primary)', color: 'white', borderRadius: '4px' }}>
                            Full Fusion
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                        {stage.desc}
                      </div>
                      <div style={{ display: 'flex', gap: '0.375rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
                        {stage.features.map((feat) => (
                          <span key={feat} style={{ fontSize: '0.6875rem', padding: '0.125rem 0.375rem', background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: '4px', color: 'var(--text-muted)' }}>
                            {feat}
                          </span>
                        ))}
                      </div>
                    </div>

                    {res ? (
                      <div style={{ textAlign: 'right', minWidth: '120px' }}>
                        <div style={{ fontSize: '1.75rem', fontWeight: 800, color: isFinal ? 'var(--accent-primary)' : 'var(--text-primary)', lineHeight: 1.1 }}>
                          {res.recommended_dose_units.toFixed(1)} <span style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-muted)' }}>U</span>
                        </div>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                          Severity: <strong>{res.severity}</strong>
                        </div>
                        <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                          Conf: {(res.confidence_score * 100).toFixed(0)}%
                        </div>
                      </div>
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>Evaluating...</span>
                    )}
                  </motion.div>
                  
                  {hasNext && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      transition={{ delay: idx * 0.15 + 0.1 }}
                      style={{ padding: '0.5rem 0', color: 'var(--text-muted)' }}
                    >
                      <ArrowDown size={20} />
                    </motion.div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Safety and Architecture Blueprint */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
        <div className="card" style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
          <Cpu size={24} style={{ color: 'var(--accent-primary)', flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h4 style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Dual-Stage Hybrid Architecture
            </h4>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem', lineHeight: 1.5 }}>
              Stage 1 executes an XGBoost multi-class severity classifier with temperature-scaled probabilities. Stage 2 evaluates an engineered feature matrix through regularized regression with clinical response anchoring.
            </p>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
          <ShieldCheck size={24} style={{ color: 'var(--accent-primary)', flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h4 style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Physiological Weight-Scaled Guardrails
            </h4>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem', lineHeight: 1.5 }}>
              Recommended doses are rigorously bounded to standard outpatient basal limits (0.1 - 0.5 U/kg). Extreme hypoglycemia triggers automatic dose caps to prevent unchecked recommendations.
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
