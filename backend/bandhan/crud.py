"""
This module contains CRUD (Create, Read, Update, Delete) operations for the hospital management system.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from .database import db, session_scope
from .models import (
    DischargeSummary,
    Doctor,
    FollowUp,
    FollowUpStatus,
    Patient,
    Prescription,
    ScheduleItem,
    Visit,
    VisitType,
)
from .utils import generate_identifier, hash_password


def get_doctor_by_identifier(doctor_id: str) -> Optional[Doctor]:
    """
    Retrieve a doctor from the database using their unique identifier.
    Args:
        doctor_id: The unique identifier of the doctor.
    Returns:
        A Doctor object if found, otherwise None.
    """
    return Doctor.query.filter_by(doctor_id=doctor_id).first()


def get_patient_by_identifier(patient_id: str) -> Optional[Patient]:
    """
    Retrieve a patient from the database using their unique identifier.
    Args:
        patient_id: The unique identifier of the patient.
    Returns:
        A Patient object if found, otherwise None.
    """
    return Patient.query.filter_by(patient_id=patient_id).first()


def create_doctor(data: dict) -> Doctor:
    """
    Create a new doctor in the database.
    Args:
        data: A dictionary containing the doctor's information.
    Returns:
        The newly created Doctor object.
    """
    with session_scope():
        doctor = Doctor(**data)
        doctor.doctor_id = generate_identifier(Doctor, "doctor")
        doctor.password_hash = hash_password(data["phone_number"])
        db.session.add(doctor)
        db.session.flush()
        return doctor


def update_doctor(doctor: Doctor, updates: dict) -> Doctor:
    """
    Update an existing doctor's information in the database.
    Args:
        doctor: The Doctor object to be updated.
        updates: A dictionary containing the fields to be updated.
    Returns:
        The updated Doctor object.
    """
    for key, value in updates.items():
        setattr(doctor, key, value)
    if "phone_number" in updates:
        doctor.password_hash = hash_password(updates["phone_number"])
    db.session.commit()
    return doctor


def delete_doctor(doctor: Doctor) -> None:
    """
    Delete a doctor from the database.
    Args:
        doctor: The Doctor object to be deleted.
    """
    db.session.delete(doctor)
    db.session.commit()


def create_patient(payload: dict) -> str:
    """
    Create a new patient and an initial visit record in the database.
    Args:
        payload: A dictionary containing the patient's information and visit details.
    Returns:
        The unique identifier of the newly created patient.
    """
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
    """
    Update an existing patient's information in the database.
    Args:
        patient: The Patient object to be updated.
        updates: A dictionary containing the fields to be updated.
    Returns:
        The updated Patient object.
    """
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


def record_visit(patient: Patient,
    visit_reason: str,
    visit_type: VisitType,
    doctor: Optional[Doctor],
    notes: Optional[str]) -> Visit:
    """
    Record a new visit for a patient in the database.
    Args:
        patient: The Patient object for whom the visit is being recorded.
        visit_reason: The reason for the visit.
        visit_type: The type of the visit (INPATIENT or OUTPATIENT).
        doctor: The Doctor object associated with the visit, if any.
        notes: Optional notes about the visit.
    Returns:
        The newly created Visit object.
    """
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


def add_prescription(patient: Patient,
    doctor: Doctor,
    medication: str,
    dosage: str,
    instructions: str) -> Prescription:
    """
    Add a new prescription for a patient in the database.
    Args:
        patient: The Patient object for whom the prescription is being added.
        doctor: The Doctor object who prescribed the medication.
        medication: The name of the medication.
        dosage: The dosage of the medication.
        instructions: Instructions for taking the medication.
    Returns:
        The newly created Prescription object.
    """
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
    """
    Create a new schedule item for a doctor in the database.
    Args:
        doctor: The Doctor object for whom the schedule is being created.
        data: A dictionary containing the schedule details (day_of_week, start_time, end_time).
    Returns:
        The newly created ScheduleItem object.
    """
    schedule = ScheduleItem(doctor=doctor, **data)
    db.session.add(schedule)
    db.session.commit()
    return schedule


def update_schedule(schedule: ScheduleItem, updates: dict) -> ScheduleItem:
    """
    Update an existing schedule item in the database.
    Args:
        schedule: The ScheduleItem object to be updated.
        updates: A dictionary containing the fields to be updated.
    Returns:
        The updated ScheduleItem object.
    """
    for key, value in updates.items():
        setattr(schedule, key, value)
    db.session.commit()
    return schedule


def delete_schedule(schedule: ScheduleItem) -> None:
    """
    Delete a schedule item from the database.
    Args:
        schedule: The ScheduleItem object to be deleted.
    """
    db.session.delete(schedule)
    db.session.commit()


def create_follow_up(doctor: Doctor,
    patient: Patient,
    scheduled_for: datetime,
    notes: Optional[str]) -> FollowUp:
    """
    Create a new follow-up record for a patient in the database.
    Args:
        doctor: The Doctor object who will conduct the follow-up.
        patient: The Patient object for whom the follow-up is scheduled.
        scheduled_for: The datetime when the follow-up is scheduled.
        notes: Optional notes about the follow-up.
    Returns:
        The newly created FollowUp object.
    """
    follow_up = FollowUp(
        doctor=doctor,
        patient=patient,
        scheduled_for=scheduled_for,
        notes=notes,
    )
    db.session.add(follow_up)
    db.session.commit()
    return follow_up


def update_follow_up(follow_up: FollowUp,
    status: FollowUpStatus,
    notes: Optional[str] = None) -> FollowUp:
    """
    Update an existing follow-up record in the database.
    Args:
        follow_up: The FollowUp object to be updated.
        status: The new status of the follow-up (e.g., SCHEDULED, COMPLETED, CANCELLED).
        notes: Optional notes about the follow-up.
    Returns:
        The updated FollowUp object.
    """
    follow_up.status = status
    if notes is not None:
        follow_up.notes = notes
    db.session.commit()
    return follow_up


def discharge_patient(patient: Patient,
    doctor: Doctor,
    recommendations: Optional[str],
    follow_up_date: Optional[datetime],
    summary_text: str) -> DischargeSummary:
    """
    Discharge a patient from the hospital and create a discharge summary.
    Args:
        patient: The Patient object to be discharged.
        doctor: The Doctor object responsible for the discharge.
        recommendations: Optional recommendations for the patient after discharge.
        follow_up_date: Optional date for a follow-up appointment.
        summary_text: A summary of the patient's treatment and condition at discharge.
    Returns:
        The newly created DischargeSummary object.
    """
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
