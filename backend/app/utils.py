"""
Utility functions for the application.
"""

from __future__ import annotations
import secrets
from typing import Literal
from werkzeug.security import check_password_hash, generate_password_hash
from .database import db
from .models import Doctor, Patient


ID_PREFIXES: dict[str, str] = {
    "patient": "PAT",
    "doctor": "DOC",
}

def generate_identifier(model: type[Patient] | 
    type[Doctor], 
    kind: Literal["patient", "doctor"]) -> str:
    """
    Generate a unique identifier for a patient or doctor.
    """
    
    prefix = ID_PREFIXES[kind]
    latest = (
        db.session.query(model)
        .order_by(model.id.desc())
        .with_entities(model.id)
        .first()
    )
    next_id = (latest[0] + 1) if latest else 1
    return f"{prefix}-{next_id:05d}"

def hash_password(plain_password: str) -> str:
    """
    Hash a plain password using Werkzeug's generate_password_hash function.
    """
    
    if not plain_password:
        raise ValueError("Password cannot be empty")
    return generate_password_hash(plain_password)

def verify_password(password_hash: str, plain_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    """
    return check_password_hash(password_hash, plain_password)

def generate_session_token() -> str:
    """
    Generate a secure random session token.
    """
    return secrets.token_urlsafe(32)