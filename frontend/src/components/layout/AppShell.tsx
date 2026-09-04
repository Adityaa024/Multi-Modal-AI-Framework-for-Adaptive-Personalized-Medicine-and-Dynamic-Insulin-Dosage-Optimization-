import React from 'react'
import Sidebar from './Sidebar'
import TopHeader from './TopHeader'
import type { PredictDoseResponse } from "../../lib/api"

type Props = {
  children: React.ReactNode
  activeTab: string
  setActiveTab: (tab: string) => void
  onPredict: () => void
  loading: boolean
  primaryResult: PredictDoseResponse | null
}

export default function AppShell({ children, activeTab, setActiveTab, onPredict, loading, primaryResult }: Props) {
  return (
    <div className="app-layout">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="main-area">
        <TopHeader onPredict={onPredict} loading={loading} primaryResult={primaryResult} />
        <div className="content-wrapper">
          {children}
          <footer style={{ marginTop: '3.5rem', padding: '1.25rem 0', borderTop: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-primary)' }} />
              <span><strong>MediPredict AI v0.1.0</strong> • Clinical Decision Support Platform</span>
            </div>
            <div style={{ maxWidth: '640px', textAlign: 'right', lineHeight: 1.4 }}>
              <em>Investigational Medical AI: Follows ADA/EASD 2024 Standards of Care. Intended for algorithm benchmarking and clinical simulation only. Not approved for autonomous medical intervention.</em>
            </div>
          </footer>
        </div>
      </div>
    </div>
  )
}
