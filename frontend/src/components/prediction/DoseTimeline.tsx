import { Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ComposedChart, Legend } from 'recharts'
import type { TrendPoint } from "../../lib/api"

type Props = {
  data: TrendPoint[]
}

export default function DoseTimeline({ data }: Props) {
  if (!data || data.length === 0) return null

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', gridColumn: '1 / -1' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 700, letterSpacing: '0.05em', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
            GLUCOSE VS DOSE TREND
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Historical progression of fasting glucose against recommended insulin dosages
          </p>
        </div>
      </div>

      <div style={{ height: '320px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
            <defs>
              <linearGradient id="colorGlucose" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--accent-secondary)" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="var(--accent-secondary)" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorDose" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--accent-primary)" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="var(--accent-primary)" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-light)" />
            <XAxis dataKey="at" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} tickLine={false} axisLine={{ stroke: 'var(--border-light)' }} dy={5} />
            
            <YAxis 
              yAxisId="left" 
              tick={{ fontSize: 10, fill: 'var(--text-muted)' }} 
              tickFormatter={(val) => `${val}`} 
              width={50} 
              tickLine={false} 
              axisLine={{ stroke: 'var(--border-light)' }}
              label={{ value: 'Fasting Glucose (mg/dL)', angle: -90, position: 'insideLeft', offset: -5, fontSize: 10, fill: 'var(--text-muted)' }}
            />
            <YAxis 
              yAxisId="right" 
              orientation="right" 
              tick={{ fontSize: 10, fill: 'var(--text-muted)' }} 
              tickFormatter={(val) => `${val}`} 
              width={40} 
              tickLine={false} 
              axisLine={{ stroke: 'var(--border-light)' }}
              label={{ value: 'Dose (U)', angle: 90, position: 'insideRight', offset: -5, fontSize: 10, fill: 'var(--text-muted)' }}
            />
            
            <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '0.8125rem', fontWeight: 600 }} />
            <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid var(--border-light)', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)', fontSize: '0.8125rem' }} />
            
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="fasting_glucose_mgdl"
              name="Fasting Glucose"
              stroke="var(--accent-secondary)"
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#colorGlucose)"
              activeDot={{ r: 6, strokeWidth: 0, fill: 'var(--accent-secondary)' }}
              animationDuration={1000}
            />
            <Area
              yAxisId="right"
              type="monotone"
              dataKey="recommended_dose_units"
              name="Recommended Dose"
              stroke="var(--accent-primary)"
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#colorDose)"
              activeDot={{ r: 6, strokeWidth: 0, fill: 'var(--accent-primary)' }}
              animationDuration={1000}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
