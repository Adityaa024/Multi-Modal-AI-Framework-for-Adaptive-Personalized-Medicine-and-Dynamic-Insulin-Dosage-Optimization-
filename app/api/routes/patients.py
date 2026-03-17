from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import db_session_dependency
from app.db.models import DoseHistory, Patient
from app.schemas.patient import (
    DoseHistoryEntry,
    PatientCreate,
    PatientHistory,
    PatientRead,
)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post(
    "/",
    response_model=PatientRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient for research",
)
def register_patient(
    payload: PatientCreate,
    db: Session = Depends(db_session_dependency),
) -> PatientRead:
    """
    Register a new patient with basic demographic and baseline data.

    This endpoint is intentionally minimal and focused on research use;
    production systems would typically integrate with existing EHR records
    instead of duplicating patient entities.
    """

    patient = Patient(
        given_name=payload.given_name,
        family_name=payload.family_name,
        age_years=payload.age_years,
        sex=payload.sex,
        weight_kg=payload.weight_kg,
        height_cm=payload.height_cm,
        baseline_hba1c=payload.baseline_hba1c,
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    return PatientRead.model_validate(patient)


@router.get(
    "/{patient_id}/history",
    response_model=PatientHistory,
    summary="Retrieve insulin dose and glucose history for a patient",
)
def get_patient_history(
    patient_id: int,
    db: Session = Depends(db_session_dependency),
) -> PatientHistory:
    """
    Return a patient's insulin dose and proximate glucose history.

    The history includes both the patient metadata and a time-ordered series
    of dose/glucose events to facilitate downstream analysis.
    """

    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with id={patient_id} not found.",
        )

    history_entries = db.scalars(
        select(DoseHistory)
        .where(DoseHistory.patient_id == patient_id)
        .order_by(DoseHistory.timestamp.asc())
    ).all()

    return PatientHistory(
        patient=PatientRead.model_validate(patient),
        dose_history=[DoseHistoryEntry.model_validate(h) for h in history_entries],
    )

