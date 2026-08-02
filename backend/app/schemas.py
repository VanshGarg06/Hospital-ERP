"""
Schema definitions for the response and request bodies of the API endpoints.
"""

from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from .models import FollowUpStatus, TaskStatus, VisitType

class BaseSchema(BaseModel):
    """
    Base shema that other schemas inherit from.
    """
    class Config:
        orm_mode = True

class DoctorCreate(BaseSchema):
    """
    Schema for creating a new doctor.
    """
    first_name: str
    last_name: str
    phone_number: str
    email: Optional[EmailStr] = None
    department: str
    specialization: Optional[str] = None
    years_experience: Optional[int] = Field(default=None, ge=0)

class DoctorRead(BaseSchema):
    """
    Schema for reading doctor information.
    """
    doctor_id: str
    first_name: str
    last_name: str
    phone_number: str
    email: Optional[str]
    department: str
    specialization: Optional[str]
    years_experience: Optional[int]
    created_at: datetime
    updated_at: datetime

class PatientCreate(BaseSchema):
    """
    Schema for creating a new patient.
    """
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone_number: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    medical_history: Optional[str] = None
    visit_reason: str
    visit_type: VisitType = VisitType.OUTPATIENT
    doctor_id: Optional[str] = None

class PatientRead(BaseSchema):
    """
    Schema for reading patient information.
    """
    patient_id: str
    first_name: str
    last_name: str
    phone_number: str
    email: Optional[str]
    gender: Optional[str]
    address: Optional[str]
    emergency_contact: Optional[str]
    medical_history: Optional[str]
    is_inpatient: bool
    ward: Optional[str]
    bed_number: Optional[str]
    admitted_at: Optional[datetime]
    discharged_at: Optional[datetime]
    doctor_id: Optional[str]
    created_at: datetime
    updated_at: datetime

class VisitCreate(BaseSchema):
    """
    Schema for creating a new visit record.
    """
    visit_reason: str
    visit_type: VisitType
    doctor_id: Optional[str] = None
    notes: Optional[str] = None

class VisitRead(BaseSchema):
    """
    Schema for reading visit information.
    """
    visit_reason: str
    visit_type: VisitType
    visit_time: datetime
    doctor_id: Optional[str]
    notes: Optional[str]

class PrescriptionCreate(BaseSchema):
    """
    Schema for creating a new prescription.
    """
    
    doctor_id: str
    medication: str
    dosage: str
    instructions: str

class PrescriptionRead(BaseSchema):
    """
    Schema for reading prescription information.
    """
    id: int
    medication: str
    dosage: str
    instructions: str
    doctor_id: str
    created_at: datetime

class ScheduleCreate(BaseSchema):
    """
    Schema for creating a new schedule/task.
    """
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING

class ScheduleRead(BaseSchema):
    """
    Schema for reading schedule/task information.
    """
    id: int
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    status: TaskStatus

class FollowUpCreate(BaseSchema):
    """
    Schema for creating a new follow-up record.
    """
    patient_id: str
    scheduled_for: datetime
    notes: Optional[str] = None

class FollowUpRead(BaseSchema):
    """
    Schema for reading follow-up information.
    """
    id: int
    patient_id: str
    scheduled_for: datetime
    status: FollowUpStatus
    notes: Optional[str]

class DischargeCreate(BaseSchema):
    """
    Schema for creating a new discharge record.
    """
    doctor_id: str
    recommendations: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    summary_text: str

class DischargeRead(BaseSchema):
    """
    Schema for reading discharge information.
    """
    id: int
    discharge_date: datetime
    recommendations: Optional[str]
    follow_up_date: Optional[datetime]
    summary_text: str
    doctor_id: str

class LoginRequest(BaseSchema):
    """
    Schema for login request.
    """ 
    username: str
    password: str
    role: str

class LoginResponse(BaseSchema):
    """
    Schema for login response.
    """
    token: str
    role: str
    display_name: str
    reference_id: str