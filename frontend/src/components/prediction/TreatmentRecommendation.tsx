import { motion } from 'framer-motion'
import type { PredictDoseResponse } from "../../lib/api"
import { CheckCircle2, AlertTriangle, Info } from 'lucide-react'

type Props = {
  result: PredictDoseResponse
}

export default function TreatmentRecommendation({ result }: Props) {
  const rec = result.drug_recommendation
  const hasContras = rec.contraindications.length > 0
  const confidence = rec.confidence * 100

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <h3 style={{ fontSize: '0.875rem', fontWeight: 700, letterSpacing: '0.05em', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
          TREATMENT STRATEGY
        </h3>
        
        {hasContras ? (
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-danger)', background: 'rgba(239, 68, 68, 0.1)', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>
            <AlertTriangle size={14} /> Contraindications
          </span>
        ) : (
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-success)', background: 'rgba(16, 185, 129, 0.1)', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>
            <CheckCircle2 size={14} /> No major contraindications
          </span>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600, marginBottom: '0.25rem' }}>Primary Therapy</div>
          <div style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--text-primary)' }}>{rec.primary_therapy}</div>
        </div>

        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600, marginBottom: '0.25rem' }}>Adjunct Drug</div>
          <div style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-primary)' }}>{rec.adjunct_drug}</div>
        </div>
      </div>

      {rec.explanation && (
        <div style={{ padding: '0.875rem 1rem', background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.375rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Clinical Rationale & Drug Recommendation Explanation
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-primary)', lineHeight: 1.55 }}>
            {rec.explanation}
          </p>
        </div>
      )}

      {hasContras && (
        <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-danger)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>Detected Contraindications</div>
          <ul style={{ fontSize: '0.75rem', color: 'var(--text-primary)', paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
            {rec.contraindications.map(c => <li key={c}>{c}</li>)}
          </ul>
        </div>
      )}

      <div style={{ marginTop: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.75rem', fontWeight: 600 }}>
          <span style={{ color: 'var(--text-secondary)' }}>Recommendation Confidence</span>
          <span>{confidence.toFixed(1)}%</span>
        </div>
        <div style={{ height: '6px', background: 'rgba(0,0,0,0.05)', borderRadius: '99px', overflow: 'hidden' }}>
          <motion.div 
            initial={{ width: 0 }}
            animate={{ width: `${confidence}%` }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
            style={{ height: '100%', background: 'var(--accent-primary)', borderRadius: '99px' }}
          />
        </div>
      </div>

      <div style={{ padding: '0.75rem', background: 'var(--bg-app)', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
        <Info size={14} style={{ color: 'var(--accent-secondary)' }} />
        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Clinical review required</span>
      </div>

    </div>
  )
}
