from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """
    Base class for all ORM models.

    Declared here (rather than in a separate `base.py`) to keep the data
    layer compact for this research scaffold.
    """

    pass


class Patient(Base):
    """
    Minimal patient entity used for research purposes.

    Only non-identifying, coarse-grained information is stored by default.
    Downstream projects can extend this model as needed.
    """

    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Basic demographic / anthropometric information
    given_name: Mapped[str] = mapped_column(String(64))
    family_name: Mapped[str] = mapped_column(String(64))
    age_years: Mapped[int] = mapped_column(Integer)
    sex: Mapped[str] = mapped_column(String(16))  # e.g. "female", "male", "other"
    weight_kg: Mapped[float] = mapped_column(Float)
    height_cm: Mapped[float] = mapped_column(Float)

    # Optional baseline metabolic marker for research stratification
    baseline_hba1c: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationship to historical insulin doses and glucose readings
    dose_history: Mapped[list["DoseHistory"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan"
    )


class DoseHistory(Base):
    """
    Historical record linking insulin doses to proximal glucose measurements.

    This table is intentionally generic to support many experimental designs:
    it records a free-form `context_label` column that can encode protocol
    information (e.g. "pre-breakfast", "post-dinner", "correction").
    """

    __tablename__ = "dose_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )

    # Glucose metrics (mg/dL) close to the time of the dose
    glucose_mgdl: Mapped[float] = mapped_column(Float)
    glucose_previous_mgdl: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Delivered insulin dose in units
    insulin_units: Mapped[float] = mapped_column(Float)

    # Optional free-form context label for experimental design
    context_label: Mapped[str | None] = mapped_column(String(64), nullable=True)

    patient: Mapped[Patient] = relationship(back_populates="dose_history")

