"""
This module defines the API routes for the hospital management system.
It includes endpoints for managing doctors, patients, 
schedules, follow-ups, visits, prescriptions, and authentication.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Callable, Dict
from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload
from . import schemas
from .crud import (
    add_prescription,
    create_doctor,
    create_follow_up,
    create_patient,
    create_schedule,
    delete_doctor,
    delete_schedule,
    discharge_patient,
    get_doctor_by_identifier,
    get_patient_by_identifier,
    record_visit,
    update_doctor,
    update_follow_up,
    update_patient,
    update_schedule,
)
from .models import DischargeSummary, Doctor, FollowUp, FollowUpStatus, Patient, ScheduleItem
from .utils import generate_session_token, verify_password

api_bp = Blueprint("api", __name__)

SessionStore = dict[str, dict[str, Any]]
SESSIONS: SessionStore = {}

def validate(schema_cls: Callable[..., Any], payload: Dict[str, Any]):
    """
    Validate the payload against the provided Pydantic schema class.
    Returns the validated data or an error message.
    """
    try:
        return schema_cls(**payload)
    except Exception as exc:  # noqa: BLE001
        return str(exc)


def parse_request(schema_cls):
    """
    Parse and validate the incoming JSON request against the provided schema class.
    Returns the validated data or an error response.
    """
    payload = request.get_json(silent=True) or {}
    validation = validate(schema_cls, payload)
    if isinstance(validation, str):
        return None, (jsonify({"error": validation}), 400)
    return validation, None


@api_bp.route("/doctors/register", methods=["POST"])
def register_doctor():
    """
    Endpoint to register a new doctor.
    Expects a JSON payload matching the DoctorCreate schema.
    Returns the created doctor's identifier or an error message.
    """
    data, error = parse_request(schemas.DoctorCreate)
    if error:
        return error

    doctor = create_doctor(data.dict())
    return jsonify({"doctor_id": doctor.doctor_id}), 201


@api_bp.route("/doctors/<doctor_id>", methods=["GET"])
def get_doctor_details(doctor_id: str):
    """
    Endpoint to retrieve details of a specific doctor, 
    including their patients, schedules, and follow-ups.
    Returns a JSON response with the doctor's information 
    or an error message if not found.
    """
    
    doctor = (
        Doctor.query.options(
            joinedload(Doctor.patients).joinedload(Patient.visits),
            joinedload(Doctor.schedules),
            joinedload(Doctor.follow_ups).joinedload(FollowUp.patient),
        )
        .filter_by(doctor_id=doctor_id)
        .first()
    )
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    patients = [
        {
            "patient_id": patient.patient_id,
            "name": f"{patient.first_name} {patient.last_name}",
            "phone_number": patient.phone_number,
            "visit_count": len(patient.visits),
            "is_inpatient": patient.is_inpatient,
            "ward": patient.ward,
            "bed_number": patient.bed_number,
            "follow_ups": [
                {
                    "follow_up_id": follow.id,
                    "scheduled_for": follow.scheduled_for.isoformat(),
                    "status": follow.status.value,
                }
                for follow in patient.follow_ups
                if follow.doctor_id == doctor.id
            ],
        }
        for patient in doctor.patients
    ]

    schedules = [
        {
            "id": schedule.id,
            "title": schedule.title,
            "description": schedule.description,
            "start_time": schedule.start_time.isoformat(),
            "end_time": schedule.end_time.isoformat(),
            "location": schedule.location,
            "status": schedule.status.value,
        }
        for schedule in doctor.schedules
    ]

    followups = [
        {
            "id": follow.id,
            "patient_id": follow.patient.patient_id,
            "patient_name": f"{follow.patient.first_name} {follow.patient.last_name}",
            "scheduled_for": follow.scheduled_for.isoformat(),
            "status": follow.status.value,
            "notes": follow.notes,
        }
        for follow in doctor.follow_ups
    ]

    return jsonify(
        {
            "doctor": {
                "doctor_id": doctor.doctor_id,
                "first_name": doctor.first_name,
                "last_name": doctor.last_name,
                "department": doctor.department,
                "specialization": doctor.specialization,
                "phone_number": doctor.phone_number,
                "email": doctor.email,
            },
            "patients": patients,
            "schedules": schedules,
            "followups": followups,
        }
    )


@api_bp.route("/doctors/<doctor_id>", methods=["PUT"])
def update_doctor_profile(doctor_id: str):
    """
    Endpoint to update a doctor's profile.
    Expects a JSON payload with the fields to update.
    Returns a success message or an error if the doctor is not found.
    """
    doctor = get_doctor_by_identifier(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    updates = request.get_json(silent=True) or {}
    doctor = update_doctor(doctor, updates)
    return jsonify({"message": "Doctor updated", "doctor_id": doctor.doctor_id})


@api_bp.route("/doctors/<doctor_id>", methods=["DELETE"])
def remove_doctor_profile(doctor_id: str):
    """
    Endpoint to delete a doctor's profile.
    Returns a success message or an error if the doctor is not found.
    """
    doctor = get_doctor_by_identifier(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404
    delete_doctor(doctor)
    return jsonify({"message": "Doctor deleted"})


@api_bp.route("/doctors/<doctor_id>/schedule", methods=["POST"])
def add_doctor_schedule(doctor_id: str):
    """
    Endpoint to add a new schedule item for a doctor.
    Expects a JSON payload matching the ScheduleCreate schema.
    Returns the created schedule item's identifier or an error message.
    """
    doctor = get_doctor_by_identifier(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    data, error = parse_request(schemas.ScheduleCreate)
    if error:
        return error

    schedule = create_schedule(doctor, data.dict())
    return jsonify({"schedule_id": schedule.id}), 201


@api_bp.route("/doctors/<doctor_id>/schedule/<int:schedule_id>", methods=["PUT"])
def modify_schedule(doctor_id: str, schedule_id: int):
    """
    Endpoint to update an existing schedule item for a doctor.
    Expects a JSON payload with the fields to update.
    Returns a success message or an error if the doctor or schedule item is not found.
    """
    doctor = get_doctor_by_identifier(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    schedule = ScheduleItem.query.filter_by(id=schedule_id, doctor_id=doctor.id).first()
    if not schedule:
        return jsonify({"error": "Schedule item not found"}), 404

    updates = request.get_json(silent=True) or {}
    update_schedule(schedule, updates)
    return jsonify({"message": "Schedule updated"})


@api_bp.route("/doctors/<doctor_id>/schedule/<int:schedule_id>", methods=["DELETE"])
def remove_schedule(doctor_id: str, schedule_id: int):
    """
    Endpoint to delete a schedule item for a doctor.
    Returns a success message or an error if the doctor or schedule item is not found.
    """
    doctor = get_doctor_by_identifier(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    schedule = ScheduleItem.query.filter_by(id=schedule_id, doctor_id=doctor.id).first()
    if not schedule:
        return jsonify({"error": "Schedule item not found"}), 404
    delete_schedule(schedule)
    return jsonify({"message": "Schedule deleted"})


@api_bp.route("/doctors/<doctor_id>/followups", methods=["POST"])
def create_followup(doctor_id: str):
    """
    Endpoint to create a new follow-up for a doctor.
    Expects a JSON payload matching the FollowUpCreate schema.
    Returns the created follow-up's identifier or an error message.
    """
    doctor = get_doctor_by_identifier(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    data, error = parse_request(schemas.FollowUpCreate)
    if error:
        return error

    patient = get_patient_by_identifier(data.patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    follow_up = create_follow_up(
        doctor=doctor,
        patient=patient,
        scheduled_for=data.scheduled_for,
        notes=data.notes,
    )
    return jsonify({"follow_up_id": follow_up.id}), 201


@api_bp.route("/doctors/<doctor_id>/followups/<int:follow_up_id>", methods=["PATCH"])
def update_followup(doctor_id: str, follow_up_id: int):
    """
    Endpoint to update an existing follow-up for a doctor.
    Expects a JSON payload with the fields to update (status and/or notes).
    Returns a success message or an error if the doctor or follow-up is not found.
    """
    
    doctor = get_doctor_by_identifier(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    follow_up = FollowUp.query.filter_by(id=follow_up_id, doctor_id=doctor.id).first()
    if not follow_up:
        return jsonify({"error": "Follow-up not found"}), 404

    payload = request.get_json(silent=True) or {}
    status_str = payload.get("status")
    notes = payload.get("notes")
    if not status_str:
        return jsonify({"error": "Status is required"}), 400
    try:
        status = FollowUpStatus(status_str)
    except ValueError:
        return jsonify({"error": "Invalid follow-up status"}), 400

    update_follow_up(follow_up, status=status, notes=notes)
    return jsonify({"message": "Follow-up updated"})


@api_bp.route("/patients/register", methods=["POST"])
def register_patient():
    """
    Endpoint to register a new patient.
    Expects a JSON payload matching the PatientCreate schema.
    Returns the created patient's identifier or an error message.
    """
    data, error = parse_request(schemas.PatientCreate)
    if error:
        print("Parsing Error")
        return error

    patient_payload = data.dict()
    if patient_payload.get("date_of_birth"):
        patient_payload["date_of_birth"] = datetime.combine(
            patient_payload["date_of_birth"], datetime.min.time()
        )
    patient_id = create_patient(patient_payload)
    return jsonify({"patient_id": patient_id}), 201


@api_bp.route("/patients/<patient_id>", methods=["GET"])
def get_patient_details(patient_id: str):
    """
    Endpoint to retrieve details of a specific patient,
    including their visits, prescriptions, and discharge summary.
    Returns a JSON response with the patient's information
    or an error message if not found.
    """
    
    patient = (
        get_patient_by_identifier(patient_id)
    )
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    visits = [
        {
            "visit_id": visit.id,
            "visit_type": visit.visit_type.value,
            "visit_reason": visit.visit_reason,
            "visit_time": visit.visit_time.isoformat(),
            "doctor_id": visit.doctor.doctor_id if visit.doctor else None,
            "notes": visit.notes,
        }
        for visit in patient.visits
    ]

    prescriptions = [
        {
            "id": prescription.id,
            "medication": prescription.medication,
            "dosage": prescription.dosage,
            "instructions": prescription.instructions,
            "doctor_id": prescription.doctor.doctor_id,
            "created_at": prescription.created_at.isoformat(),
        }
        for prescription in patient.prescriptions
    ]

    latest_discharge = (
        DischargeSummary.query.filter_by(patient_id=patient.id)
        .order_by(DischargeSummary.discharge_date.desc())
        .first()
    )

    discharge_data = (
        {
            "discharge_date": latest_discharge.discharge_date.isoformat(),
            "recommendations": latest_discharge.recommendations,
            "follow_up_date": latest_discharge.follow_up_date.isoformat()
            if latest_discharge.follow_up_date
            else None,
            "summary_text": latest_discharge.summary_text,
            "doctor_id": latest_discharge.doctor.doctor_id,
        }
        if latest_discharge
        else None
    )

    doctor_info = (
        {
            "doctor_id": patient.doctor.doctor_id,
            "name": f"{patient.doctor.first_name} {patient.doctor.last_name}",
            "department": patient.doctor.department,
            "phone_number": patient.doctor.phone_number,
        }
        if patient.doctor
        else None
    )

    return jsonify(
        {
            "patient": {
                "patient_id": patient.patient_id,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "phone_number": patient.phone_number,
                "email": patient.email,
                "address": patient.address,
                "medical_history": patient.medical_history,
                "is_inpatient": patient.is_inpatient,
                "ward": patient.ward,
                "bed_number": patient.bed_number,
                "admitted_at": patient.admitted_at.isoformat() if patient.admitted_at else None,
                "discharged_at": patient.discharged_at.isoformat() 
                if patient.discharged_at else None,
                "doctor": doctor_info,
            },
            "visits": visits,
            "prescriptions": prescriptions,
            "discharge_summary": discharge_data,
        }
    )


@api_bp.route("/patients/<patient_id>", methods=["PUT"])
def update_patient_details(patient_id: str):
    """
    Endpoint to update a patient's details.
    Expects a JSON payload with the fields to update.
    Returns a success message or an error if the patient is not found.
    """
    patient = get_patient_by_identifier(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    updates = request.get_json(silent=True) or {}
    if "admitted_at" in updates and updates["admitted_at"]:
        updates["admitted_at"] = datetime.fromisoformat(updates["admitted_at"])
    if "discharged_at" in updates and updates["discharged_at"]:
        updates["discharged_at"] = datetime.fromisoformat(updates["discharged_at"])

    patient = update_patient(patient, updates)
    return jsonify({"message": "Patient updated"})


@api_bp.route("/patients/<patient_id>/visits", methods=["POST"])
def add_patient_visit(patient_id: str):
    """
    Endpoint to record a new visit for a patient.
    Expects a JSON payload matching the VisitCreate schema.
    Returns the created visit's identifier or an error message.
    """
    patient = get_patient_by_identifier(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    data, error = parse_request(schemas.VisitCreate)
    if error:
        return error

    doctor = None
    if data.doctor_id:
        doctor = get_doctor_by_identifier(data.doctor_id)
        if not doctor:
            return jsonify({"error": "Doctor not found"}), 404

    visit = record_visit(
        patient=patient,
        visit_reason=data.visit_reason,
        visit_type=data.visit_type,
        doctor=doctor,
        notes=data.notes,
    )
    return jsonify({"visit_id": visit.id}), 201


@api_bp.route("/patients/<patient_id>/prescriptions", methods=["POST"])
def create_patient_prescription(patient_id: str):
    """
    Endpoint to create a new prescription for a patient.
    Expects a JSON payload matching the PrescriptionCreate schema.
    Returns the created prescription's identifier or an error message.
    """
    patient = get_patient_by_identifier(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    data, error = parse_request(schemas.PrescriptionCreate)
    if error:
        return error

    doctor = get_doctor_by_identifier(data.doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    prescription = add_prescription(
        patient=patient,
        doctor=doctor,
        medication=data.medication,
        dosage=data.dosage,
        instructions=data.instructions,
    )
    return jsonify({"prescription_id": prescription.id}), 201


@api_bp.route("/patients/<patient_id>/discharge", methods=["POST"])
def discharge_patient_endpoint(patient_id: str):
    """
    Endpoint to discharge a patient.
    Expects a JSON payload matching the DischargeCreate schema.
    Returns a discharge summary or an error message.
    """
    patient = get_patient_by_identifier(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    data, error = parse_request(schemas.DischargeCreate)
    if error:
        return error

    doctor = get_doctor_by_identifier(data.doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    discharge_summary = discharge_patient(
        patient=patient,
        doctor=doctor,
        recommendations=data.recommendations,
        follow_up_date=data.follow_up_date,
        summary_text=data.summary_text,
    )

    receipt = {
        "patient_id": patient.patient_id,
        "doctor_id": doctor.doctor_id,
        "discharge_date": discharge_summary.discharge_date.isoformat(),
        "summary_text": discharge_summary.summary_text,
        "recommendations": discharge_summary.recommendations,
        "follow_up_date": discharge_summary.follow_up_date.isoformat()
        if discharge_summary.follow_up_date
        else None,
    }

    return jsonify({"message": "Patient discharged", "receipt": receipt}), 200


@api_bp.route("/login", methods=["POST"])
def login():
    """
    Endpoint for user login.
    Expects a JSON payload matching the LoginRequest schema.
    Returns a session token and user details if successful, or an error message.
    """
    data, error = parse_request(schemas.LoginRequest)
    if error:
        return error

    role = data.role.lower()
    if role not in {"doctor", "patient"}:
        return jsonify({"error": "Invalid role"}), 400

    if role == "doctor":
        doctor = get_doctor_by_identifier(data.username)
        if not doctor or not verify_password(doctor.password_hash, data.password):
            return jsonify({"error": "Invalid credentials"}), 401
        token = generate_session_token()
        SESSIONS[token] = {
            "doctor_id": doctor.doctor_id,
            "role": "doctor",
            "issued_at": datetime.utcnow().isoformat(),
        }
        return jsonify(
            schemas.LoginResponse(
                token=token,
                role="doctor",
                display_name=f"{doctor.first_name} {doctor.last_name}",
                reference_id=doctor.doctor_id,
            ).dict()
        )

    patient = get_patient_by_identifier(data.username)
    if not patient or not verify_password(patient.password_hash, data.password):
        return jsonify({"error": "Invalid credentials"}), 401
    token = generate_session_token()
    SESSIONS[token] = {
        "patient_id": patient.patient_id,
        "role": "patient",
        "issued_at": datetime.utcnow().isoformat(),
    }
    return jsonify(
        schemas.LoginResponse(
            token=token,
            role="patient",
            display_name=f"{patient.first_name} {patient.last_name}",
            reference_id=patient.patient_id,
        ).dict()
    )