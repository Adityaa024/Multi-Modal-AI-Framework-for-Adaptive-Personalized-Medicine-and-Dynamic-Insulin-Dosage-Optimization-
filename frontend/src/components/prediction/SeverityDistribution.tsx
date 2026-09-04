import type { PredictDoseResponse } from "../../lib/api"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

type Props = {
  result: PredictDoseResponse
}

const CLASS_COLORS: Record<string, string> = {
  Mild: '#10b981',
  Moderate: '#f59e0b',
  Severe: '#ef4444',
}

export default function SeverityDistribution({ result }: Props) {
  const data = [
    {
      name: 'Mild',
      value: Number((result.severity_probabilities.mild * 100).toFixed(1)),
      color: CLASS_COLORS.Mild,
    },
    {
      name: 'Moderate',
      value: Number((result.severity_probabilities.moderate * 100).toFixed(1)),
      color: CLASS_COLORS.Moderate,
    },
    {
      name: 'Severe',
      value: Number((result.severity_probabilities.severe * 100).toFixed(1)),
      color: CLASS_COLORS.Severe,
    },
  ]

  const predictedClass = result.severity.charAt(0).toUpperCase() + result.severity.slice(1).toLowerCase()

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 700, letterSpacing: '0.05em', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
            SEVERITY PROBABILITY DISTRIBUTION
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Calibrated multi-class classification probabilities
          </p>
        </div>
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            padding: '0.25rem 0.625rem',
            borderRadius: '999px',
            background: `${CLASS_COLORS[predictedClass] || 'var(--accent-primary)'}18`,
            color: CLASS_COLORS[predictedClass] || 'var(--accent-primary)',
            border: `1px solid ${CLASS_COLORS[predictedClass] || 'var(--accent-primary)'}40`,
          }}
        >
          Predicted: {predictedClass}
        </span>
      </div>

      <div style={{ height: '210px', width: '100%', marginTop: '0.5rem' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 15, right: 15, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-light)" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 12, fontWeight: 600, fill: 'var(--text-primary)' }}
              tickLine={false}
              axisLine={{ stroke: 'var(--border-light)' }}
            />
            <YAxis
              unit="%"
              domain={[0, 100]}
              ticks={[0, 25, 50, 75, 100]}
              tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
              tickLine={false}
              axisLine={{ stroke: 'var(--border-light)' }}
            />
            <Tooltip
              formatter={(v) => [`${Number(v ?? 0).toFixed(1)}%`, 'Probability']}
              contentStyle={{
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border-light)',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                fontSize: '0.8125rem',
                fontWeight: 600,
              }}
            />
            <Bar dataKey="value" radius={[6, 6, 0, 0]} animationDuration={800}>
              {data.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={entry.color}
                  opacity={entry.name === predictedClass ? 1 : 0.6}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-light)' }}>
        {data.map((item) => (
          <div
            key={item.name}
            style={{
              textAlign: 'center',
              padding: '0.5rem 0.25rem',
              borderRadius: '6px',
              background: item.name === predictedClass ? `${item.color}10` : 'transparent',
              border: item.name === predictedClass ? `1px solid ${item.color}30` : '1px solid transparent',
            }}
          >
            <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-secondary)' }}>{item.name}</div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: item.color, marginTop: '0.125rem' }}>
              {item.value.toFixed(1)}%
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
