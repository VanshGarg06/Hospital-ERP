"""
This module defines the database models 
for the hospital management system,
including doctors, patients, visits, 
prescriptions, schedules, follow-ups, and discharge summaries.
"""

from __future__ import annotations
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import db

class TimestampMixin:
    """
    Mixin class to add created_at and updated_at timestamps to models.
    """
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )


class VisitType(enum.StrEnum):
    OUTPATIENT = "outpatient"
    INPATIENT = "inpatient"

class TaskStatus(enum.StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class FollowUpStatus(enum.StrEnum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Doctor(TimestampMixin, db.Model):
    """
    Represents a doctor in the hospital management system.
    """
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[str] = mapped_column(unique=True, index=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    phone_number: Mapped[str]
    email: Mapped[Optional[str]]
    department: Mapped[str]
    specialization: Mapped[Optional[str]]
    years_experience: Mapped[Optional[int]]
    password_hash: Mapped[str]

    patients: Mapped[list["Patient"]] = relationship("Patient", back_populates="doctor")
    schedules: Mapped[list["ScheduleItem"]] = relationship(
        "ScheduleItem", back_populates="doctor", cascade="all, delete-orphan"
    )
    follow_ups: Mapped[list["FollowUp"]] = relationship(
        "FollowUp", back_populates="doctor", cascade="all, delete-orphan"
    )


class Patient(TimestampMixin, db.Model):
    """
    Represents a patient in the hospital management system.
    """
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[str] = mapped_column(unique=True, index=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    date_of_birth: Mapped[Optional[datetime]]
    gender: Mapped[Optional[str]]
    phone_number: Mapped[str]
    email: Mapped[Optional[str]]
    address: Mapped[Optional[str]]
    emergency_contact: Mapped[Optional[str]]
    medical_history: Mapped[Optional[str]]
    is_inpatient: Mapped[bool] = mapped_column(default=False)
    ward: Mapped[Optional[str]]
    bed_number: Mapped[Optional[str]]
    admitted_at: Mapped[Optional[datetime]]
    discharged_at: Mapped[Optional[datetime]]
    password_hash: Mapped[str]

    doctor_id: Mapped[Optional[int]] = mapped_column(
        db.ForeignKey("doctors.id", ondelete="SET NULL")
    )

    doctor: Mapped[Optional[Doctor]] = relationship("Doctor", back_populates="patients")
    visits: Mapped[list["Visit"]] = relationship(
        "Visit", back_populates="patient", cascade="all, delete-orphan"
    )
    prescriptions: Mapped[list["Prescription"]] = relationship(
        "Prescription", back_populates="patient", cascade="all, delete-orphan"
    )
    discharge_summaries: Mapped[list["DischargeSummary"]] = relationship(
        "DischargeSummary", back_populates="patient", cascade="all, delete-orphan"
    )
    follow_ups: Mapped[list["FollowUp"]] = relationship(
        "FollowUp", back_populates="patient", cascade="all, delete-orphan"
    )


class Visit(TimestampMixin, db.Model):
    """
    Represents a visit of a patient to the hospital.
    """
    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(db.ForeignKey("patients.id"))
    doctor_id: Mapped[int | None] = mapped_column(db.ForeignKey("doctors.id"), nullable=True)
    visit_type: Mapped[VisitType]
    visit_reason: Mapped[str]
    visit_time: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    notes: Mapped[Optional[str]]

    patient: Mapped[Patient] = relationship("Patient", back_populates="visits")
    doctor: Mapped[Optional[Doctor]] = relationship("Doctor")


class Prescription(TimestampMixin, db.Model):
    """
    Represents a prescription given to a patient by a doctor.
    """
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(db.ForeignKey("patients.id"))
    doctor_id: Mapped[int] = mapped_column(db.ForeignKey("doctors.id"))
    medication: Mapped[str]
    dosage: Mapped[str]
    instructions: Mapped[str]

    patient: Mapped[Patient] = relationship("Patient", back_populates="prescriptions")
    doctor: Mapped[Doctor] = relationship("Doctor")


class ScheduleItem(TimestampMixin, db.Model):
    """
    Represents a schedule or task for a doctor.
    """
    __tablename__ = "schedule_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(db.ForeignKey("doctors.id"))
    title: Mapped[str]
    description: Mapped[Optional[str]]
    start_time: Mapped[datetime]
    end_time: Mapped[datetime]
    location: Mapped[Optional[str]]
    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.PENDING)

    doctor: Mapped[Doctor] = relationship("Doctor", back_populates="schedules")


class FollowUp(TimestampMixin, db.Model):
    """
    Represents a follow-up appointment for a patient with a doctor.
    """
    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(db.ForeignKey("doctors.id"))
    patient_id: Mapped[int] = mapped_column(db.ForeignKey("patients.id"))
    scheduled_for: Mapped[datetime]
    status: Mapped[FollowUpStatus] = mapped_column(default=FollowUpStatus.SCHEDULED)
    notes: Mapped[Optional[str]]

    doctor: Mapped[Doctor] = relationship("Doctor", back_populates="follow_ups")
    patient: Mapped[Patient] = relationship("Patient", back_populates="follow_ups")


class DischargeSummary(TimestampMixin, db.Model):
    """
    Represents a discharge summary for a patient.
    """
    __tablename__ = "discharge_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(db.ForeignKey("patients.id"))
    doctor_id: Mapped[int] = mapped_column(db.ForeignKey("doctors.id"))
    discharge_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    recommendations: Mapped[Optional[str]]
    follow_up_date: Mapped[Optional[datetime]]
    summary_text: Mapped[str]

    patient: Mapped[Patient] = relationship("Patient", back_populates="discharge_summaries")
    doctor: Mapped[Doctor] = relationship("Doctor")
