import { motion } from 'framer-motion'
import type { PatientInput } from "../../lib/api"
import { Activity, CalendarHeart, Dumbbell, Droplets, Scale, Ruler, Utensils, Syringe, FlaskConical, HeartPulse } from 'lucide-react'

type Props = {
  form: PatientInput
}

export default function PatientOverview({ form }: Props) {
  const bmi = form.bmi || (form.weight_kg / Math.pow(form.height_cm / 100, 2)).toFixed(1)
  const safeCr = Math.max(0.4, form.creatinine_mgdl)
  const egfr = Math.round(((140 - form.age) * form.weight_kg) / (72 * safeCr))

  const metrics = [
    { label: 'Age', value: form.age, unit: 'years', icon: CalendarHeart },
    { label: 'BMI', value: bmi, unit: 'kg/m²', icon: Scale },
    { label: 'Height', value: form.height_cm, unit: 'cm', icon: Ruler },
    { label: 'Weight', value: form.weight_kg, unit: 'kg', icon: Scale },
    { label: 'Fasting Glucose', value: form.fasting_glucose_mgdl, unit: 'mg/dL', icon: Droplets },
    { label: 'HbA1c', value: form.hba1c, unit: '%', icon: Activity },
    { label: 'Creatinine', value: form.creatinine_mgdl, unit: 'mg/dL', icon: FlaskConical },
    { label: 'Est. eGFR', value: egfr, unit: 'mL/min', icon: HeartPulse },
    { label: 'Activity', value: ['Sedentary', 'Low', 'Moderate', 'High'][form.activity_level], unit: '', icon: Dumbbell },
    { label: 'Diet Adherence', value: form.diet_adherence_score, unit: '/100', icon: Utensils },
    { label: 'Previous Insulin', value: form.previous_insulin_dose_units, unit: 'U', icon: Syringe },
    { label: 'Post-dose Glucose', value: form.glucose_after_dose_mgdl, unit: 'mg/dL', icon: Droplets },
  ]

  return (
    <section>
      <div style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--text-primary)' }}>PATIENT OVERVIEW</h3>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Multimodal clinical context used for dosage optimization</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem' }}>
        {metrics.map((m, idx) => {
          const Icon = m.icon
          return (
            <motion.div
              key={m.label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.07, ease: 'easeOut', duration: 0.4 }}
              className="card"
              style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.625rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
                  {m.label}
                </span>
                <Icon size={14} color="var(--text-muted)" />
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
                <span style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.03em', color: 'var(--text-primary)' }}>
                  {m.value}
                </span>
                <span style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-muted)' }}>
                  {m.unit}
                </span>
              </div>
            </motion.div>
          )
        })}
      </div>
    </section>
  )
}
