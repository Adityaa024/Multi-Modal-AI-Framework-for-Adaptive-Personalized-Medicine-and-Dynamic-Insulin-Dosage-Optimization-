import { motion } from 'framer-motion'
import { Activity, Brain, FileOutput, FlaskConical } from 'lucide-react'

type Props = {
  activeTab: string
  setActiveTab: (tab: string) => void
}

const NAV_ITEMS = [
  { id: 'prediction', label: 'Prediction', icon: Activity },
  { id: 'explainability', label: 'Explainability', icon: FileOutput },
  { id: 'evaluation', label: 'Evaluation', icon: Brain },
  { id: 'insights', label: 'Model Insights', icon: FlaskConical },
]

export default function Sidebar({ activeTab, setActiveTab }: Props) {
  return (
    <aside className="sidebar" style={{ padding: '2rem 1rem', justifyContent: 'space-between' }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0 1rem', marginBottom: '2.5rem' }}>
          <div style={{ width: '32px', height: '32px', background: 'var(--accent-primary)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' }}>
            <Activity size={18} />
          </div>
          <span style={{ fontWeight: 600, fontSize: '1.125rem', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
            MediPredict AI
          </span>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          {NAV_ITEMS.map((item) => {
            const isActive = activeTab === item.id
            const Icon = item.icon
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  position: 'relative',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.75rem 1rem',
                  border: 'none',
                  background: 'transparent',
                  cursor: 'pointer',
                  textAlign: 'left',
                  borderRadius: '8px',
                  color: isActive ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: '0.875rem',
                  transition: 'all 0.2s ease'
                }}
                onMouseOver={(e) => {
                  if (!isActive) e.currentTarget.style.backgroundColor = 'rgba(0,0,0,0.03)'
                  e.currentTarget.style.color = isActive ? 'var(--accent-primary)' : 'var(--text-primary)'
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent'
                  e.currentTarget.style.color = isActive ? 'var(--accent-primary)' : 'var(--text-secondary)'
                }}
              >
                {isActive && (
                  <motion.div
                    layoutId="active-nav"
                    style={{
                      position: 'absolute',
                      left: 0,
                      top: 0,
                      bottom: 0,
                      right: 0,
                      backgroundColor: 'rgba(5, 150, 105, 0.08)',
                      borderRadius: '8px',
                      zIndex: -1
                    }}
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
                {isActive && (
                  <motion.div
                    layoutId="active-indicator"
                    style={{
                      position: 'absolute',
                      left: 0,
                      top: '15%',
                      bottom: '15%',
                      width: '3px',
                      backgroundColor: 'var(--accent-primary)',
                      borderRadius: '0 4px 4px 0',
                    }}
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
                <Icon size={18} style={{ transition: 'transform 0.2s' }} />
                <span>{item.label}</span>
              </button>
            )
          })}
        </nav>
      </div>

      <div style={{ padding: '0 1rem' }}>
        <div style={{ fontSize: '0.625rem', fontWeight: 700, letterSpacing: '0.05em', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
          Research Mode
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem', lineHeight: 1.4 }}>
          Clinical decision-support prototype
        </div>
      </div>
    </aside>
  )
}
