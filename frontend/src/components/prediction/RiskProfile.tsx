import { motion } from 'framer-motion'
import type { PredictDoseResponse } from "../../lib/api"
import { ShieldAlert } from 'lucide-react'

type Props = {
  result: PredictDoseResponse
}

export default function RiskProfile({ result }: Props) {
  const hypoRisk = result.hypoglycemia_risk_probability * 100
  const hyperRisk = result.hyperglycemia_risk_probability * 100
  
  const getRiskColor = (val: number, isHypo: boolean) => {
    // For Hypo, anything > 10% might be amber, >20% red
    if (isHypo) {
      if (val > 20) return 'var(--accent-danger)'
      if (val > 10) return 'var(--accent-warning)'
      return 'var(--accent-success)'
    } else {
      // Hyper: > 80% red, > 60% amber
      if (val > 80) return 'var(--accent-danger)'
      if (val > 60) return 'var(--accent-warning)'
      return 'var(--accent-success)'
    }
  }

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h3 style={{ fontSize: '0.875rem', fontWeight: 700, letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
          GLYCEMIC RISK PROFILE
        </h3>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        
        {/* Hypo */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 600 }}>
            <span>Hypoglycemia Risk</span>
            <span style={{ color: getRiskColor(hypoRisk, true) }}>{hypoRisk.toFixed(0)}%</span>
          </div>
          <div style={{ height: '8px', background: 'rgba(0,0,0,0.05)', borderRadius: '99px', overflow: 'hidden' }}>
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${hypoRisk}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
              style={{ height: '100%', background: getRiskColor(hypoRisk, true), borderRadius: '99px' }}
            />
          </div>
        </div>

        {/* Hyper */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 600 }}>
            <span>Hyperglycemia Risk</span>
            <span style={{ color: getRiskColor(hyperRisk, false) }}>{hyperRisk.toFixed(0)}%</span>
          </div>
          <div style={{ height: '8px', background: 'rgba(0,0,0,0.05)', borderRadius: '99px', overflow: 'hidden' }}>
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${hyperRisk}%` }}
              transition={{ duration: 1, ease: 'easeOut', delay: 0.2 }}
              style={{ height: '100%', background: getRiskColor(hyperRisk, false), borderRadius: '99px' }}
            />
          </div>
        </div>

      </div>

      <div style={{ padding: '1rem', background: 'var(--bg-app)', borderRadius: '8px', display: 'flex', alignItems: 'flex-start', gap: '0.75rem', marginTop: 'auto' }}>
        <ShieldAlert size={16} style={{ color: 'var(--text-secondary)', marginTop: '2px' }} />
        <div>
          <div style={{ fontSize: '0.75rem', fontWeight: 600 }}>Overall Severity: {result.severity.toUpperCase()}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem', lineHeight: 1.4 }}>
            Risk profile derived from multimodal feature fusion. Always correlate with clinical presentation.
          </div>
        </div>
      </div>

    </div>
  )
}
