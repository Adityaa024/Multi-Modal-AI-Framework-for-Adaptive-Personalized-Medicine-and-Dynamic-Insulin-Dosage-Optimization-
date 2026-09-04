import { motion } from 'framer-motion'
import type { PredictDoseResponse, PatientInput } from "../../lib/api"
import { User, TestTube, Activity, Syringe, BrainCircuit, CheckCircle2, ArrowDown } from 'lucide-react'
import { useEffect, useState } from 'react'

type Props = {
  form: PatientInput
  result: PredictDoseResponse | null
  isPredicting: boolean
}

export default function MultimodalFusion({ form, result, isPredicting }: Props) {
  const [step, setStep] = useState(0)
  
  useEffect(() => {
    if (isPredicting) {
      setStep(1)
      const timer = setInterval(() => {
        setStep(s => (s < 7 ? s + 1 : s))
      }, 300) // ~2 seconds total
      return () => clearInterval(timer)
    } else if (result) {
      setStep(7)
    } else {
      setStep(0)
    }
  }, [isPredicting, result])

  const modalities = [
    {
      id: 'profile',
      title: 'PATIENT PROFILE',
      icon: User,
      data: [
        { label: 'Age', value: form.age },
        { label: 'Weight', value: `${form.weight_kg}kg` },
      ],
      stepThreshold: 1
    },
    {
      id: 'labs',
      title: 'LABORATORY SIGNALS',
      icon: TestTube,
      data: [
        { label: 'Fasting Glucose', value: `${form.fasting_glucose_mgdl} mg/dL` },
        { label: 'HbA1c', value: `${form.hba1c}%` },
      ],
      stepThreshold: 2
    },
    {
      id: 'behavior',
      title: 'BEHAVIORAL SIGNALS',
      icon: Activity,
      data: [
        { label: 'Activity Level', value: form.activity_level },
        { label: 'Diet Adherence', value: form.diet_adherence_score },
      ],
      stepThreshold: 3
    },
    {
      id: 'context',
      title: 'INSULIN CONTEXT',
      icon: Syringe,
      data: [
        { label: 'Prev Dose', value: `${form.previous_insulin_dose_units} U` },
        { label: 'Post Glucose', value: `${form.glucose_after_dose_mgdl} mg/dL` },
      ],
      stepThreshold: 4
    }
  ]

  return (
    <section className="card" style={{ padding: '2rem' }}>
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, letterSpacing: '0.05em' }}>MULTIMODAL SIGNAL FUSION</h3>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
          Four complementary signal groups inform the dosage recommendation.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', position: 'relative', zIndex: 2 }}>
        {modalities.map((mod) => {
          const isActive = step >= mod.stepThreshold
          const Icon = mod.icon
          return (
            <motion.div
              key={mod.id}
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              whileHover={{ y: -5, boxShadow: '0 10px 25px rgba(0,0,0,0.05)' }}
              style={{
                background: isActive ? 'var(--bg-app)' : 'var(--bg-card)',
                border: `1px solid ${isActive ? 'var(--accent-primary)' : 'var(--border-light)'}`,
                borderRadius: '12px',
                padding: '1.25rem',
                transition: 'all 0.3s ease',
                position: 'relative'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: isActive ? 'var(--accent-primary)' : 'var(--text-secondary)' }}>
                  <Icon size={16} />
                  <span style={{ fontSize: '0.625rem', fontWeight: 700, letterSpacing: '0.05em' }}>{mod.title}</span>
                </div>
                {isActive && <CheckCircle2 size={14} color="var(--accent-primary)" />}
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {mod.data.map(d => (
                  <div key={d.label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>{d.label}</span>
                    <span style={{ fontWeight: 600 }}>{d.value}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          )
        })}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', margin: '2rem 0', position: 'relative' }}>
        <motion.div
          animate={{ opacity: step >= 5 ? 1 : 0.3, y: step >= 5 ? [0, 5, 0] : 0 }}
          transition={{ repeat: step >= 5 ? Infinity : 0, duration: 2 }}
          style={{ color: step >= 5 ? 'var(--accent-primary)' : 'var(--border-light)' }}
        >
          <ArrowDown size={32} />
        </motion.div>
        
        <motion.div 
          animate={{
            scale: step >= 5 ? 1.05 : 1,
            boxShadow: step >= 5 ? '0 0 20px var(--accent-primary-glow)' : 'none'
          }}
          style={{
            marginTop: '1rem',
            padding: '1rem 3rem',
            background: step >= 5 ? 'var(--text-primary)' : 'var(--bg-app)',
            color: step >= 5 ? 'white' : 'var(--text-secondary)',
            borderRadius: '99px',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            fontWeight: 600,
            transition: 'all 0.5s'
          }}
        >
          <BrainCircuit size={20} />
          <span>MULTIMODAL AI ENGINE</span>
        </motion.div>

        <motion.div
          animate={{ opacity: step >= 6 ? 1 : 0.3, y: step >= 6 ? [0, 5, 0] : 0 }}
          transition={{ repeat: step >= 6 ? Infinity : 0, duration: 2 }}
          style={{ color: step >= 6 ? 'var(--accent-primary)' : 'var(--border-light)', marginTop: '1rem' }}
        >
          <ArrowDown size={32} />
        </motion.div>

        <motion.div 
          animate={{
            scale: step >= 7 ? 1.1 : 1,
            color: step >= 7 ? 'var(--text-primary)' : 'var(--text-muted)'
          }}
          style={{
            marginTop: '1rem',
            fontWeight: 700,
            fontSize: '1rem',
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
            transition: 'all 0.5s'
          }}
        >
          Dosage Optimization
        </motion.div>
      </div>

    </section>
  )
}
