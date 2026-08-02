from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy.exc import NoResultFound
from .database import db, session_scope
from .models import (
    DischargeSummary,
    Doctor,
    FollowUp,
    FollowUpStatus,
    Patient,
    Prescription,
    ScheduleItem,
    TaskStatus,
    Visit,
    VisitType,
)
from .utils import generate_identifier, hash_password


def get_doctor_by_identifier(doctor_id: str) -> Optional[Doctor]:
    return Doctor.query.filter_by(doctor_id=doctor_id).first()


def get_patient_by_identifier(patient_id: str) -> Optional[Patient]:
    return Patient.query.filter_by(patient_id=patient_id).first()


def create_doctor(data: dict) -> Doctor:
    with session_scope():
        doctor = Doctor(**data)
        doctor.doctor_id = generate_identifier(Doctor, "doctor")
        doctor.password_hash = hash_password(data["phone_number"])
        db.session.add(doctor)
        db.session.flush()
        return doctor


def update_doctor(doctor: Doctor, updates: dict) -> Doctor:
    for key, value in updates.items():
        setattr(doctor, key, value)
    if "phone_number" in updates:
        doctor.password_hash = hash_password(updates["phone_number"])
    db.session.commit()
    return doctor


def delete_doctor(doctor: Doctor) -> None:
    db.session.delete(doctor)
    db.session.commit()


def create_patient(payload: dict) -> str:
    visit_reason = payload.pop("visit_reason")
    visit_type = payload.pop("visit_type", VisitType.OUTPATIENT)
    doctor_identifier = payload.pop("doctor_id", None)

    with session_scope() as session:
        doctor = None
        if doctor_identifier:
            doctor = (
                session.query(Doctor)
                .filter_by(doctor_id=doctor_identifier)
                .first()
            )

        patient = Patient(**payload)
        patient.patient_id = generate_identifier(Patient, "patient")
        patient.password_hash = hash_password(payload["phone_number"])

        if doctor:
            patient.doctor = doctor

        if visit_type == VisitType.INPATIENT:
            patient.is_inpatient = True
            patient.admitted_at = datetime.utcnow()

        session.add(patient)
        session.flush()          # Generates primary key if needed

        patient_id = patient.patient_id

        visit = Visit(
            patient=patient,
            doctor=doctor,
            visit_reason=visit_reason,
            visit_type=visit_type,
        )

        session.add(visit)

        return patient_id

def update_patient(patient: Patient, updates: dict) -> Patient:
    doctor_identifier = updates.pop("doctor_id", None)
    if doctor_identifier:
        doctor = get_doctor_by_identifier(doctor_identifier)
        patient.doctor = doctor
    for key, value in updates.items():
        setattr(patient, key, value)
    if "phone_number" in updates:
        patient.password_hash = hash_password(updates["phone_number"])
    db.session.commit()
    return patient


def record_visit(patient: Patient, visit_reason: str, visit_type: VisitType, doctor: Optional[Doctor], notes: Optional[str]) -> Visit:
    visit = Visit(
        patient=patient,
        doctor=doctor,
        visit_reason=visit_reason,
        visit_type=visit_type,
        notes=notes,
        visit_time=datetime.utcnow(),
    )
    if visit_type == VisitType.INPATIENT:
        patient.is_inpatient = True
        if patient.admitted_at is None:
            patient.admitted_at = datetime.utcnow()
    else:
        patient.is_inpatient = False
    db.session.add(visit)
    db.session.commit()
    return visit


def add_prescription(patient: Patient, doctor: Doctor, medication: str, dosage: str, instructions: str) -> Prescription:
    prescription = Prescription(
        patient=patient,
        doctor=doctor,
        medication=medication,
        dosage=dosage,
        instructions=instructions,
    )
    db.session.add(prescription)
    db.session.commit()
    return prescription


def create_schedule(doctor: Doctor, data: dict) -> ScheduleItem:
    schedule = ScheduleItem(doctor=doctor, **data)
    db.session.add(schedule)
    db.session.commit()
    return schedule


def update_schedule(schedule: ScheduleItem, updates: dict) -> ScheduleItem:
    for key, value in updates.items():
        setattr(schedule, key, value)
    db.session.commit()
    return schedule


def delete_schedule(schedule: ScheduleItem) -> None:
    db.session.delete(schedule)
    db.session.commit()


def create_follow_up(doctor: Doctor, patient: Patient, scheduled_for: datetime, notes: Optional[str]) -> FollowUp:
    follow_up = FollowUp(
        doctor=doctor,
        patient=patient,
        scheduled_for=scheduled_for,
        notes=notes,
    )
    db.session.add(follow_up)
    db.session.commit()
    return follow_up


def update_follow_up(follow_up: FollowUp, status: FollowUpStatus, notes: Optional[str] = None) -> FollowUp:
    follow_up.status = status
    if notes is not None:
        follow_up.notes = notes
    db.session.commit()
    return follow_up


def discharge_patient(patient: Patient, doctor: Doctor, recommendations: Optional[str], follow_up_date: Optional[datetime], summary_text: str) -> DischargeSummary:
    patient.is_inpatient = False
    patient.discharged_at = datetime.utcnow()
    discharge_summary = DischargeSummary(
        patient=patient,
        doctor=doctor,
        recommendations=recommendations,
        follow_up_date=follow_up_date,
        summary_text=summary_text,
        discharge_date=datetime.utcnow(),
    )
    db.session.add(discharge_summary)
    db.session.commit()
    return discharge_summary

