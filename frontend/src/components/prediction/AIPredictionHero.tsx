import { motion } from 'framer-motion'
import type { PredictDoseResponse } from "../../lib/api"
import { useEffect, useState } from 'react'
import { BrainCircuit, ShieldAlert } from 'lucide-react'

type Props = {
  result: PredictDoseResponse | null
  isPredicting: boolean
  previousDose: number
}

// Custom hook to animate the number from previous to recommended
function useAnimatedNumber(target: number, isPredicting: boolean, start: number) {
  const [current, setCurrent] = useState(start)

  useEffect(() => {
    if (isPredicting || !target) return
    
    let startTime: number
    const duration = 1500 // 1.5 seconds

    const animate = (time: number) => {
      if (!startTime) startTime = time
      const progress = Math.min((time - startTime) / duration, 1)
      
      // easeOutCubic
      const ease = 1 - Math.pow(1 - progress, 3)
      
      const nextValue = start + (target - start) * ease
      setCurrent(nextValue)

      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }

    requestAnimationFrame(animate)
  }, [target, isPredicting, start])

  return current
}

export default function AIPredictionHero({ result, isPredicting, previousDose }: Props) {
  const targetDose = result?.recommended_dose_units ?? 0
  const animatedDose = useAnimatedNumber(targetDose, isPredicting, previousDose)

  const hasResult = !!result
  const confidence = result ? (result.confidence_score * 100).toFixed(1) : '--'
  const uncertainty = result ? (result.uncertainty_entropy * 100).toFixed(1) : '--'
  
  const getSeverityColor = (sev?: string) => {
    if (!sev) return 'var(--text-muted)'
    const s = sev.toLowerCase()
    if (s === 'mild') return 'var(--accent-success)'
    if (s === 'moderate') return 'var(--accent-warning)'
    if (s === 'severe') return 'var(--accent-danger)'
    return 'var(--text-muted)'
  }

  return (
    <section>
      <div className="card" style={{ 
        padding: '3rem', 
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: isPredicting ? '0 0 0 2px var(--accent-primary), 0 8px 30px var(--border-glow)' : '0 4px 20px rgba(0,0,0,0.03)',
        transition: 'all 0.5s ease',
        background: 'linear-gradient(to bottom, #ffffff, #fbfbfb)'
      }}>
        
        <div style={{ position: 'absolute', top: '1.5rem', left: '1.5rem', display: 'flex', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.625rem', fontWeight: 700, padding: '0.25rem 0.5rem', background: 'rgba(5, 150, 105, 0.1)', color: 'var(--accent-primary)', borderRadius: '4px', textTransform: 'uppercase' }}>
            Multimodal Model
          </span>
          <span style={{ fontSize: '0.625rem', fontWeight: 700, padding: '0.25rem 0.5rem', background: 'var(--bg-app)', color: 'var(--text-secondary)', borderRadius: '4px', textTransform: 'uppercase' }}>
            Research Use Only
          </span>
        </div>

        <motion.div
          animate={isPredicting ? { opacity: [1, 0.5, 1], scale: [1, 0.98, 1] } : {}}
          transition={{ repeat: isPredicting ? Infinity : 0, duration: 2 }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', marginBottom: '1rem', color: 'var(--text-secondary)' }}>
            <BrainCircuit size={20} />
            <h2 style={{ fontSize: '1rem', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              AI Dosage Recommendation
            </h2>
          </div>

          <div style={{ fontSize: '6rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.04em', lineHeight: 1, margin: '2rem 0 1rem 0' }}>
            {hasResult || isPredicting ? (
              <>
                {animatedDose.toFixed(1)} <span style={{ fontSize: '3rem', color: 'var(--text-muted)' }}>U</span>
              </>
            ) : (
              <span style={{ color: 'var(--text-muted)' }}>--</span>
            )}
          </div>

          {hasResult && result.conformal_interval && (
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.35rem 0.85rem', background: 'rgba(5, 150, 105, 0.08)', border: '1px solid rgba(5, 150, 105, 0.2)', borderRadius: '20px', marginBottom: '1rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-primary)' }}>
                95% Conformal Prediction Bounds:
              </span>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                [{result.conformal_interval.lower_units.toFixed(1)} – {result.conformal_interval.upper_units.toFixed(1)} U]
              </span>
            </div>
          )}

          {hasResult && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.5 }}
              style={{ display: 'flex', justifyContent: 'center', gap: '2.5rem', marginTop: '1.5rem', flexWrap: 'wrap' }}
            >
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.25rem' }}>Confidence</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{confidence}%</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.25rem' }}>Uncertainty</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{uncertainty}%</div>
              </div>
              {result.ood_metric && (
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.25rem' }}>Clinical Trust (OOD)</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: result.ood_metric.is_in_distribution ? 'var(--accent-success)' : 'var(--accent-warning)' }}>
                    {result.ood_metric.trust_score_percent}%
                  </div>
                  <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                    {result.ood_metric.is_in_distribution ? 'In-Domain Safe' : 'Specialist Review'}
                  </div>
                </div>
              )}
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.25rem' }}>Severity</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: getSeverityColor(result.severity), textTransform: 'uppercase' }}>
                  {result.severity}
                </div>
              </div>
            </motion.div>
          )}
        </motion.div>

        {result?.hypoglycemia_alert && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            style={{ position: 'absolute', top: '1.5rem', right: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--accent-danger)', borderRadius: '99px' }}
          >
            <ShieldAlert size={16} />
            <span style={{ fontSize: '0.75rem', fontWeight: 700 }}>Risk Alert Detected</span>
          </motion.div>
        )}
      </div>
    </section>
  )
}
