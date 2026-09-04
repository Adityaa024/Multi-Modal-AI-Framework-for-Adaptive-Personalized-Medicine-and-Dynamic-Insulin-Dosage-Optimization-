import { Sparkles, Loader2 } from 'lucide-react'
import type { PredictDoseResponse } from "../../lib/api"

type Props = {
  onPredict: () => void
  loading: boolean
  primaryResult: PredictDoseResponse | null
}

export default function TopHeader({ onPredict, loading, primaryResult }: Props) {
  const getSeverityColor = (sev?: string) => {
    if (!sev) return 'transparent'
    const s = sev.toLowerCase()
    if (s === 'mild') return 'var(--accent-success)'
    if (s === 'moderate') return 'var(--accent-warning)'
    if (s === 'severe') return 'var(--accent-danger)'
    return 'var(--text-muted)'
  }
  
  const getSeverityBg = (sev?: string) => {
    if (!sev) return 'transparent'
    const s = sev.toLowerCase()
    if (s === 'mild') return 'rgba(16, 185, 129, 0.1)'
    if (s === 'moderate') return 'rgba(245, 158, 11, 0.1)'
    if (s === 'severe') return 'rgba(239, 68, 68, 0.1)'
    return 'transparent'
  }

  return (
    <header className="topbar">
      <div style={{ flex: 1 }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 600 }}>MediPredict AI</h2>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Multimodal insulin dosage optimization</div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', flex: 1, justifyContent: 'center' }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600 }}>Patient</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>62 years • Type 2 Diabetes</div>
        </div>
        
        {primaryResult && (
          <div style={{
            padding: '0.25rem 0.75rem',
            borderRadius: '99px',
            backgroundColor: getSeverityBg(primaryResult.severity),
            color: getSeverityColor(primaryResult.severity),
            fontSize: '0.75rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            {primaryResult.severity}
          </div>
        )}
      </div>

      <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }}>
        <button
          onClick={onPredict}
          disabled={loading}
          className={!primaryResult && !loading ? 'animate-soft-pulse' : ''}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            backgroundColor: 'var(--text-primary)',
            color: 'white',
            border: 'none',
            padding: '0.5rem 1.25rem',
            borderRadius: '8px',
            fontSize: '0.875rem',
            fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.7 : 1,
            transition: 'all 0.2s',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}
          onMouseOver={(e) => {
            if (!loading) e.currentTarget.style.transform = 'scale(1.02)'
          }}
          onMouseOut={(e) => {
            if (!loading) e.currentTarget.style.transform = 'scale(1)'
          }}
        >
          {loading ? (
            <Loader2 size={16} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
          ) : (
            <Sparkles size={16} />
          )}
          {loading ? 'Analyzing...' : 'Predict'}
        </button>
      </div>
    </header>
  )
}
