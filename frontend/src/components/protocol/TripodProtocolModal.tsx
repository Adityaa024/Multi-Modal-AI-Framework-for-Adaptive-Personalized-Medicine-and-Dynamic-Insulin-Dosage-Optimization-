import { motion, AnimatePresence } from 'framer-motion'
import { X, FileText, ShieldCheck, Database, Award, Stethoscope } from 'lucide-react'

type Props = {
  isOpen: boolean
  onClose: () => void
}

export default function TripodProtocolModal({ isOpen, onClose }: Props) {
  if (!isOpen) return null

  return (
    <AnimatePresence>
      <div 
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(17, 24, 39, 0.65)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '1.5rem',
        }}
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: 12 }}
          transition={{ duration: 0.25, ease: 'easeOut' }}
          style={{
            margin: 'auto',
            backgroundColor: 'var(--bg-card)',
            borderRadius: '16px',
            maxWidth: '820px',
            width: '100%',
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            border: '1px solid var(--border-light)',
            overflow: 'hidden',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div style={{
            padding: '1.5rem 2rem',
            borderBottom: '1px solid var(--border-light)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'linear-gradient(to right, rgba(5, 150, 105, 0.05), transparent)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                background: 'rgba(5, 150, 105, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--accent-primary)'
              }}>
                <FileText size={20} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Clinical Study Protocol & TRIPOD+AI Statement
                </h3>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Transparent Reporting of a Multivariable Prediction Model for Individual Prognosis (TRIPOD+AI Checklist)
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                padding: '0.5rem',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <X size={20} />
            </button>
          </div>

          {/* Body Content */}
          <div style={{
            padding: '2rem',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '1.5rem',
            fontSize: '0.875rem',
            lineHeight: 1.6,
          }}>
            {/* Section 1: Study Classification */}
            <div style={{ padding: '1.25rem', background: 'var(--bg-app)', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <Award size={18} style={{ color: 'var(--accent-primary)' }} />
                <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  1. Study Design & Classification (TRIPOD+AI Item 3b)
                </h4>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>
                This platform implements a <strong>Stage-1 In Silico Algorithmic Feasibility Benchmark</strong> for personalized insulin dosage optimization in Type 2 Diabetes. 
                The system functions exclusively as an investigational Clinical Decision Support System (CDSS) prototype designed to evaluate multimodal sensor and laboratory fusion.
              </p>
            </div>

            {/* Section 2: Synthetic Cohort Justification */}
            <div style={{ padding: '1.25rem', background: 'var(--bg-app)', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <Database size={18} style={{ color: 'var(--accent-primary)' }} />
                <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  2. Synthetic Dataset Justification & Provenance (TRIPOD+AI Item 5a)
                </h4>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem', marginBottom: '0.75rem' }}>
                <strong>Why synthetic data was used:</strong> Publicly available electronic health records (EHRs) rarely contain simultaneously paired continuous glycemic logs, 
                serum creatinine/renal clearance, prior insulin dosing histories, and granular lifestyle/diet adherence scores due to patient privacy laws (HIPAA/GDPR) and institutional data silos.
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.75rem' }}>
                <div style={{ padding: '0.75rem', background: 'var(--bg-card)', borderRadius: '6px', border: '1px solid var(--border-light)' }}>
                  <strong>Epidemiological Calibration:</strong> Feature distributions were calibrated directly against the <strong>CDC NHANES</strong> (National Health and Nutrition Examination Survey) 
                  and the <strong>UCI Diabetes</strong> benchmarks (Age: 60 &plusmn; 10y, BMI: 31 &plusmn; 4 kg/m², HbA1c: 8.0 &plusmn; 1.0%).
                </div>
                <div style={{ padding: '0.75rem', background: 'var(--bg-card)', borderRadius: '6px', border: '1px solid var(--border-light)' }}>
                  <strong>Nonlinear Noise Injection:</strong> Zero-mean Gaussian biological stochasticity (&epsilon; ~ N(0, &sigma;²)) was injected to simulate inter-individual metabolic 
                  variability and prevent the regression model from trivial mathematical inverse memorization.
                </div>
              </div>
            </div>

            {/* Section 3: Safety Guardrails & Overbasalization Limits */}
            <div style={{ padding: '1.25rem', background: 'var(--bg-app)', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <ShieldCheck size={18} style={{ color: 'var(--accent-primary)' }} />
                <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  3. Physiological Safety Clamps (0.1 – 0.5 U/kg Clinical Rationale)
                </h4>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem', marginBottom: '0.5rem' }}>
                The weight-scaled safety boundaries are grounded in the <strong>American Diabetes Association (ADA)</strong> and <strong>EASD 2024 Standards of Care</strong>:
              </p>
              <ul style={{ paddingLeft: '1.25rem', color: 'var(--text-secondary)', fontSize: '0.8125rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <li><strong>Conservative Floor (0.1 U/kg/day):</strong> Protects insulin-naive or highly sensitive individuals from unintended acute hypoglycemia.</li>
                <li><strong>Overbasalization Ceiling (0.5 U/kg/day):</strong> Clinical guidelines mandate that escalating basal insulin beyond 0.5 U/kg/day produces diminishing glycemic returns while exponentially increasing hypoglycemia risk. When reaching 0.5 U/kg, guidelines mandate adjunct GLP-1 RA or prandial therapy rather than higher basal insulin.</li>
              </ul>
            </div>

            {/* Section 4: Prospective Validation Roadmap */}
            <div style={{ padding: '1.25rem', background: 'var(--bg-app)', borderRadius: '10px', border: '1px solid var(--border-light)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <Stethoscope size={18} style={{ color: 'var(--accent-primary)' }} />
                <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  4. Clinical Translation Roadmap (TRIPOD+AI Item 20)
                </h4>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>
                <strong>Phase 2 Validation:</strong> Prior to prospective bedside clinical trials, the framework requires external retrospective validation against real-world clinical data 
                (e.g., <strong>MIMIC-IV</strong> de-identified ICU/EHR records and institutional outpatient registries) to verify generalizability across multi-ethnic cohorts and diverse clinical practice patterns.
              </p>
            </div>
          </div>

          {/* Footer */}
          <div style={{
            padding: '1.25rem 2rem',
            borderTop: '1px solid var(--border-light)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'var(--bg-app)',
          }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              ICICCC-2026 Research Methodology Protocol • Version 2.4
            </span>
            <button
              onClick={onClose}
              style={{
                backgroundColor: 'var(--text-primary)',
                color: '#ffffff',
                border: 'none',
                padding: '0.5rem 1.25rem',
                borderRadius: '8px',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Close Protocol
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
