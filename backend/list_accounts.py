#!/usr/bin/env python3
"""
Script to list all doctors and patients with their login credentials.
This helps identify usernames (IDs) and passwords (phone numbers) for login.
"""

import sqlite3
import sys
from pathlib import Path

# Path to the database
db_path = Path(__file__).parent / "instance" / "hospital_erp.db"

if not db_path.exists():
    print(f"Database not found at {db_path}")
    print("Please make sure the backend has been run at least once to create the database.")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("HOSPITAL ERP - LOGIN CREDENTIALS")
print("=" * 80)
print()

# Get all doctors
print("DOCTORS:")
print("-" * 80)
cursor.execute("""
    SELECT doctor_id, first_name, last_name, phone_number, email, department
    FROM doctor
    ORDER BY doctor_id
""")
doctors = cursor.fetchall()

if doctors:
    print(
        f"{'Username (ID)':<15} "
        f"{'Name':<30} " 
        f"{'Phone (Password)':<20} " 
        f"{'Email':<25} " 
        f"{'Department':<20} "
    )
    print("-" * 80)
    for doc_id, first_name, last_name, phone, email, dept in doctors:
        name = f"{first_name} {last_name}"
        print(f"{doc_id:<15} {name:<30} {phone:<20} {email or 'N/A':<25} {dept or 'N/A':<20}")
else:
    print("No doctors registered yet.")
    print("Register a doctor first using the registration form.")

print()
print()

# Get all patients
print("PATIENTS:")
print("-" * 80)
cursor.execute("""
    SELECT patient_id, first_name, last_name, phone_number, email, date_of_birth
    FROM patient
    ORDER BY patient_id
""")
patients = cursor.fetchall()

if patients:
    print(f"{'Username (ID)':<15} {'Name':<30} {'Phone (Password)':<20} {'Email':<25} {'DOB':<15}")
    print("-" * 80)
    for pat_id, first_name, last_name, phone, email, dob in patients:
        name = f"{first_name} {last_name}"
        dob_str = dob if dob else "N/A"
        print(f"{pat_id:<15} {name:<30} {phone:<20} {email or 'N/A':<25} {dob_str:<15}")
else:
    print("No patients registered yet.")
    print("Register a patient first using the registration form.")

print()
print("=" * 80)
print("LOGIN INSTRUCTIONS:")
print("=" * 80)
print("1. Username: Use the ID shown above (e.g., DOC-00001 or PAT-00001)")
print("2. Password: Use the phone number shown above")
print("3. Role: Select 'doctor' for doctor accounts or 'patient' for patient accounts")
print("=" * 80)

conn.close()