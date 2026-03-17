from datetime import datetime

from pydantic import BaseModel, Field


class PatientBase(BaseModel):
    """
    Common fields shared between patient creation and read models.

    These fields intentionally avoid direct identifiers (e.g. MRN) so that
    the API stays focused on research rather than clinical operations.
    """

    given_name: str = Field(..., max_length=64)
    family_name: str = Field(..., max_length=64)
    age_years: int = Field(..., ge=0, le=120)
    sex: str = Field(..., max_length=16)
    weight_kg: float = Field(..., gt=0)
    height_cm: float = Field(..., gt=0)
    baseline_hba1c: float | None = Field(
        default=None,
        description=(
            "Baseline HbA1c percentage if available; useful for cohort "
            "stratification in research analyses."
        ),
    )


class PatientCreate(PatientBase):
    """
    Payload for registering a new patient.

    Separated from `PatientRead` so that future fields (e.g. consent flags)
    can be added without leaking internal DB identifiers.
    """

    pass


class PatientRead(PatientBase):
    """
    Public representation of a patient returned by the API.
    """

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DoseHistoryEntry(BaseModel):
    """
    Single entry in a patient's dose/glucose history.
    """

    id: int
    timestamp: datetime
    glucose_mgdl: float
    glucose_previous_mgdl: float | None = None
    insulin_units: float
    context_label: str | None = None

    class Config:
        from_attributes = True


class PatientHistory(BaseModel):
    """
    Aggregated history for a given patient.
    """

    patient: PatientRead
    dose_history: list[DoseHistoryEntry]

