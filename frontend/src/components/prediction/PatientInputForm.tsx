import type { PatientInput } from '../../lib/api'
import { motion } from 'framer-motion'
import { Sparkles, Info } from 'lucide-react'

type Props = {
  form: PatientInput
  setForm: (val: PatientInput) => void
  onDone: () => void
}

const CLINICAL_PRESETS: Array<{ label: string; badge: string; description: string; data: PatientInput }> = [
  {
    label: 'Standard T2D Baseline',
    badge: 'Moderate',
    description: 'Moderate hyperglycemia with preserved renal function',
    data: {
      age: 62,
      weight_kg: 92,
      height_cm: 170,
      bmi: 31.8,
      fasting_glucose_mgdl: 185,
      hba1c: 8.6,
      creatinine_mgdl: 1.2,
      previous_insulin_dose_units: 18,
      glucose_after_dose_mgdl: 150,
      activity_level: 1,
      diet_adherence_score: 70,
    },
  },
  {
    label: 'Elderly Renal Impairment',
    badge: 'Renal CKD',
    description: 'Cr > 2.0 triggers Metformin/SGLT2 contraindications & DPP-4 fallback',
    data: {
      age: 72,
      weight_kg: 84,
      height_cm: 168,
      bmi: 29.8,
      fasting_glucose_mgdl: 195,
      hba1c: 9.1,
      creatinine_mgdl: 2.1,
      previous_insulin_dose_units: 22,
      glucose_after_dose_mgdl: 175,
      activity_level: 0,
      diet_adherence_score: 55,
    },
  },
  {
    label: 'Severe Obesity & Hyperglycemia',
    badge: 'GLP-1 Target',
    description: 'BMI > 34, severe hyperglycemia triggering GLP-1 and dose titration',
    data: {
      age: 52,
      weight_kg: 108,
      height_cm: 175,
      bmi: 35.3,
      fasting_glucose_mgdl: 235,
      hba1c: 9.7,
      creatinine_mgdl: 1.1,
      previous_insulin_dose_units: 34,
      glucose_after_dose_mgdl: 195,
      activity_level: 1,
      diet_adherence_score: 50,
    },
  },
  {
    label: 'Mild / Insulin-Naive Early Glycemia',
    badge: 'Lifestyle Focus',
    description: 'Early-stage T2D, HbA1c < 7.2%, lifestyle & non-insulin focus',
    data: {
      age: 46,
      weight_kg: 74,
      height_cm: 174,
      bmi: 24.4,
      fasting_glucose_mgdl: 122,
      hba1c: 6.8,
      creatinine_mgdl: 0.9,
      previous_insulin_dose_units: 0,
      glucose_after_dose_mgdl: 118,
      activity_level: 2,
      diet_adherence_score: 85,
    },
  },
]

export default function PatientInputForm({ form, setForm, onDone }: Props) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    setForm({
      ...form,
      [name]: type === 'number' || type === 'range' ? Number(value) : value
    })
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
      style={{ padding: '2rem' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--text-primary)' }}>PATIENT DATA ENTRY</h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Enter multimodal clinical context or load a research clinical preset</p>
        </div>
        <button 
          onClick={onDone}
          style={{
            background: 'var(--accent-primary)',
            color: '#fff',
            border: 'none',
            padding: '0.5rem 1.25rem',
            borderRadius: '8px',
            fontSize: '0.875rem',
            fontWeight: 700,
            cursor: 'pointer'
          }}
        >
          View Summary & Predict
        </button>
      </div>

      {/* Preset Profiles Bar */}
      <div style={{ marginBottom: '2rem', padding: '1rem', background: 'var(--bg-app)', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', marginBottom: '0.75rem', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent-primary)', letterSpacing: '0.05em' }}>
          <Sparkles size={14} /> Quick Clinical Cohort Presets (1-Click Evaluation)
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem' }}>
          {CLINICAL_PRESETS.map((preset) => (
            <button
              key={preset.label}
              type="button"
              onClick={() => setForm(preset.data)}
              style={{
                textAlign: 'left',
                padding: '0.625rem 0.75rem',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-light)',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.25rem',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                <strong style={{ fontSize: '0.75rem', color: 'var(--text-primary)' }}>{preset.label}</strong>
                <span style={{ fontSize: '0.625rem', padding: '0.125rem 0.375rem', borderRadius: '4px', background: 'rgba(5, 150, 105, 0.1)', color: 'var(--accent-primary)', fontWeight: 700 }}>
                  {preset.badge}
                </span>
              </div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', lineHeight: 1.3 }}>
                {preset.description}
              </span>
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
        {/* Demographics */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <h4 style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)', borderBottom: '1px solid var(--border-light)', paddingBottom: '0.5rem' }}>Demographics</h4>
          
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Age (years)</label>
              <input type="number" name="age" value={form.age} onChange={handleChange} className="input-field" style={{ width: '80px', padding: '0.25rem', height: '28px' }} />
            </div>
            <input type="range" name="age" min="18" max="100" value={form.age} onChange={handleChange} className="slider-input" />
          </div>
          
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Weight (kg)</label>
              <input type="number" name="weight_kg" value={form.weight_kg} onChange={handleChange} className="input-field" style={{ width: '80px', padding: '0.25rem', height: '28px' }} />
            </div>
            <input type="range" name="weight_kg" min="40" max="200" value={form.weight_kg} onChange={handleChange} className="slider-input" />
          </div>
          
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Height (cm)</label>
              <input type="number" name="height_cm" value={form.height_cm} onChange={handleChange} className="input-field" style={{ width: '80px', padding: '0.25rem', height: '28px' }} />
            </div>
            <input type="range" name="height_cm" min="140" max="220" value={form.height_cm} onChange={handleChange} className="slider-input" />
          </div>
        </div>

        {/* Labs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <h4 style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)', borderBottom: '1px solid var(--border-light)', paddingBottom: '0.5rem' }}>Laboratory Signals</h4>
          
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Fasting Glucose (mg/dL)</label>
              <input type="number" name="fasting_glucose_mgdl" value={form.fasting_glucose_mgdl} onChange={handleChange} className="input-field" style={{ width: '80px', padding: '0.25rem', height: '28px', borderColor: form.fasting_glucose_mgdl > 300 ? 'var(--accent-warning)' : '' }} />
            </div>
            <input type="range" name="fasting_glucose_mgdl" min="70" max="400" value={form.fasting_glucose_mgdl} onChange={handleChange} className="slider-input" />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>HbA1c (%)</label>
              <input type="number" step="0.1" name="hba1c" value={form.hba1c} onChange={handleChange} className="input-field" style={{ width: '80px', padding: '0.25rem', height: '28px', borderColor: form.hba1c > 12 ? 'var(--accent-warning)' : '' }} />
            </div>
            <input type="range" name="hba1c" min="4" max="20" step="0.1" value={form.hba1c} onChange={handleChange} className="slider-input" />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Creatinine (mg/dL)</label>
              <input type="number" step="0.1" name="creatinine_mgdl" value={form.creatinine_mgdl} onChange={handleChange} className="input-field" style={{ width: '80px', padding: '0.25rem', height: '28px', borderColor: form.creatinine_mgdl > 2 ? 'var(--accent-danger)' : '' }} />
            </div>
            <input type="range" name="creatinine_mgdl" min="0.5" max="5" step="0.1" value={form.creatinine_mgdl} onChange={handleChange} className="slider-input" />
          </div>
        </div>

        {/* Behavior & Context */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <h4 style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)', borderBottom: '1px solid var(--border-light)', paddingBottom: '0.5rem' }}>Behavior & Context</h4>
          
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                Activity Level 
                <span className="tooltip-trigger" data-tooltip="0: Sedentary, 1: Low, 2: Moderate, 3: High"><Info size={12} /></span>
              </label>
              <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>{['Sedentary', 'Low', 'Moderate', 'High'][form.activity_level]}</span>
            </div>
            <input type="range" name="activity_level" min="0" max="3" value={form.activity_level} onChange={handleChange} className="slider-input" />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                Diet Adherence
                <span className="tooltip-trigger" data-tooltip="0-100 score of dietary compliance"><Info size={12} /></span>
              </label>
              <input type="number" name="diet_adherence_score" value={form.diet_adherence_score} onChange={handleChange} className="input-field" style={{ width: '80px', padding: '0.25rem', height: '28px' }} />
            </div>
            <input type="range" name="diet_adherence_score" min="0" max="100" value={form.diet_adherence_score} onChange={handleChange} className="slider-input" />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Previous Insulin (U)</label>
              <input type="number" name="previous_insulin_dose_units" value={form.previous_insulin_dose_units} onChange={handleChange} className="input-field" style={{ width: '80px', padding: '0.25rem', height: '28px' }} />
            </div>
            <input type="range" name="previous_insulin_dose_units" min="0" max="100" value={form.previous_insulin_dose_units} onChange={handleChange} className="slider-input" />
          </div>
          
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Post-dose Glucose (mg/dL)</label>
              <input type="number" name="glucose_after_dose_mgdl" value={form.glucose_after_dose_mgdl} onChange={handleChange} className="input-field" style={{ width: '80px', padding: '0.25rem', height: '28px' }} />
            </div>
            <input type="range" name="glucose_after_dose_mgdl" min="70" max="400" value={form.glucose_after_dose_mgdl} onChange={handleChange} className="slider-input" />
          </div>

        </div>
      </div>
    </motion.section>
  )
}
