# A Multi-Modal AI Framework for Adaptive Insulin Dosage Optimization in Type 2 Diabetes Management

This repository provides a research-grade multimodal pipeline for Type 2 diabetes insulin dose optimization, combining a FastAPI backend, machine learning models, reproducible synthetic cohort generation, and a Vite/React frontend.

The implementation is designed for reproducible experimentation and publication-oriented evaluation, not for clinical deployment.

## Repository Layout

```text
app/
  api/
    deps.py
    routes/
      patients.py
      predictions.py
  core/
    config.py
  db/
    models.py
    session.py
  schemas/
    patient.py
    prediction.py
  services/
    ml/
      dose_model.py
      explainability.py
      preprocessing.py
  main.py

data/
  synthetic_t2d_patients.csv

frontend/
  src/
  public/
  package.json

scripts/
  generate_synthetic_t2d_data.py
  train_severity_model.py
  train_dosage_model.py
  stress_test_predict_dose_api.py
  test_normal_glucose_range.py
  evaluate_realistic_ieee.py
```

## Quick Start

### 1) Environment setup

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3) Run backend API

```bash
uvicorn app.main:app --reload
```

API URLs:
- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### 4) Run frontend

```bash
cd frontend
npm install
npm run dev
```

## ML Workflow

### Generate synthetic cohort (10,000 records)

```bash
python scripts/generate_synthetic_t2d_data.py
```

### Train models

```bash
python scripts/train_severity_model.py
python scripts/train_dosage_model.py
```

Model artifacts are saved to:
- `data/severity_model.pkl` (XGBoost multiclass severity model)
- `data/dosage_model.pkl` (engineered dose regressor artifact)

## Evaluation Workflow

### Stress test API endpoint

```bash
python scripts/stress_test_predict_dose_api.py
```

### Normal glucose cohort API test (80–250 mg/dL)

```bash
python scripts/test_normal_glucose_range.py
```

### Realistic IEEE-style offline evaluation (1500+ test cases)

```bash
python scripts/evaluate_realistic_ieee.py
```

This evaluation performs:
- strict train-test separation (no leakage),
- Gaussian measurement-noise perturbation with physiological clipping,
- explicit edge-case enrichment (very high/low glucose, obese/underweight, abnormal creatinine),
- classification, regression, safety, and stress metrics in one run.

## Latest Realistic Benchmark Snapshot

Most recent run of `scripts/evaluate_realistic_ieee.py` produced:

- Dataset size: `10000`
- Test size: `2502`

Classification (severity):
- Accuracy: `0.9229`
- ROC-AUC (OvR macro): `0.9322`
- Confusion matrix (Mild, Moderate, Severe):

```text
[[225,  67,   5],
 [ 18, 1623, 24],
 [  3,  76, 461]]
```

Regression (insulin dose):
- MAE: `2.2807`
- RMSE: `3.0966`
- R²: `0.9084`

Safety constraints (`dose_min=0.1*weight`, `dose_max=0.5*weight`):
- In range: `2502 / 2502`
- Violations: `0`

Stress test:
- Total randomized cases: `1600`
- Pass rate: `100.0%`

## Core API Endpoints

- `POST /api/v1/patients/` — create patient profile
- `GET /api/v1/patients/{patient_id}/history` — retrieve dose history
- `POST /api/v1/predictions/insulin-dose` — heuristic glucose-context dose suggestion
- `POST /api/v1/predictions/predict-dose` — multimodal severity + dose prediction with safety payload

## Research and Safety Notes

- This repository is intended for algorithm development, ablation studies, and evaluation reproducibility.
- Generated data and model outputs are synthetic and must not be interpreted as clinical advice.
- Dose recommendations are safety-clamped in serving logic using weight-scaled physiological bounds.

## Disclaimer

This project is strictly for research and educational use and must not be used for real-world clinical decision-making without formal clinical validation, regulatory clearance, and medical oversight.

## Deploy on Render

This repository is now deployment-ready for Render with:
- backend CORS configured via `ALLOWED_ORIGINS` in `app/main.py`,
- frontend API base URL configured via `VITE_API_BASE_URL` in `frontend/src/lib/api.ts`,
- infrastructure blueprint in `render.yaml`.

### Option A: Blueprint deploy (recommended)

1. Push this repository to GitHub.
2. In Render, choose **New +** -> **Blueprint**.
3. Select this repository.
4. Render reads `render.yaml` and creates:
  - `project5-api` (Python web service)
  - `project5-frontend` (static site)
5. Update service names/URLs in env vars after first deploy if Render assigns different names:
  - backend `ALLOWED_ORIGINS` should equal your frontend URL,
  - frontend `VITE_API_BASE_URL` should equal your backend URL.
6. Trigger redeploy for both services after env var updates.

### Option B: Manual deploy

Create two Render services manually:

Backend (`project5-api`):
- Environment: Python
- Build Command:

```bash
pip install -r requirements.txt
python scripts/generate_synthetic_t2d_data.py
python scripts/train_severity_model.py
python scripts/train_dosage_model.py
```

- Start Command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- Health Check Path: `/docs`
- Environment variables:
  - `PYTHON_VERSION=3.11.11`
  - `ALLOWED_ORIGINS=https://<your-frontend>.onrender.com`

Frontend (`project5-frontend` static site):
- Root Directory: `frontend`
- Build Command:

```bash
npm ci && npm run build
```

- Publish Directory: `dist`
- Environment variables:
  - `VITE_API_BASE_URL=https://<your-backend>.onrender.com`

### Post-deploy verification

1. Open frontend URL.
2. Submit a prediction from the UI.
3. Confirm browser network requests are sent to:
  - `https://<backend>/api/v1/predictions/predict-dose`
4. Confirm backend docs are live at:
  - `https://<backend>/docs`

### Notes

- For local development, keep `VITE_API_BASE_URL` empty (`frontend/.env.example`) so Vite proxy continues to work.
- SQLite is file-based (`data/app.db`). If persistent DB storage is required across redeploys, attach a Render disk and map it to the app data path.

