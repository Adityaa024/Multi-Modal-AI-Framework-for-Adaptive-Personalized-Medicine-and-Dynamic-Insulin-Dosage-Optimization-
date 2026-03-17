import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export type TrendPoint = {
  at: string
  fasting_glucose_mgdl: number
  recommended_dose_units: number
}

type Props = {
  data: TrendPoint[]
}

export default function TrendChart({ data }: Props) {
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="at" tick={{ fontSize: 12 }} />
          <YAxis
            yAxisId="glucose"
            tick={{ fontSize: 12 }}
            label={{ value: 'Glucose (mg/dL)', angle: -90, position: 'insideLeft' }}
          />
          <YAxis
            yAxisId="dose"
            orientation="right"
            tick={{ fontSize: 12 }}
            label={{ value: 'Dose (units)', angle: -90, position: 'insideRight' }}
          />
          <Tooltip />
          <Legend />
          <Line
            yAxisId="glucose"
            type="monotone"
            dataKey="fasting_glucose_mgdl"
            name="Fasting glucose"
            stroke="#0ea5e9"
            strokeWidth={2}
            dot={{ r: 2 }}
            activeDot={{ r: 5 }}
          />
          <Line
            yAxisId="dose"
            type="monotone"
            dataKey="recommended_dose_units"
            name="Recommended dose"
            stroke="#f97316"
            strokeWidth={2}
            dot={{ r: 2 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

