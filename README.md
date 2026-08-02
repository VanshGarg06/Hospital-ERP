# MediBridge Hospital ERP

Role-based hospital ERP prototype that streamlines patient and doctor workflows. The backend uses Flask, SQLite, SQLAlchemy, and Pydantic to expose REST APIs; the frontend is a single-page HTML/CSS/JavaScript experience with role-specific dashboards.

## Features

- **Landing experience** with hero carousel, About and Contact sections
- **Patient intake** with personal details, medical history, visit tracking, and doctor assignment
- **Doctor management** including registration, department assignment, and profile maintenance
- **Dashboards**
  - Doctors view assigned patients, OPD schedules, follow-ups, and can manage tasks, visits, prescriptions, and discharges
  - Patients review demographics, visits, prescriptions, and discharge summaries
- **Scheduling tools** for doctor day-to-day activities, OPD consultation, and follow-ups
- **Discharge workflow** generating patient receipts with recommendations and follow-up appointments

## Project Layout

```
hospital_erp/
├── backend/
│   ├── app.py                # Flask entry point
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py       # application factory + blueprint wiring
│       ├── crud.py           # database operations
│       ├── database.py       # SQLAlchemy instance & session scope helper
│       ├── models.py         # SQLAlchemy models & enums
│       ├── routes.py         # REST API endpoints
│       ├── schemas.py        # Pydantic request/response schemas
│       └── utils.py          # ID generation & password helpers
├── frontend/
│   ├── index.html            # landing page + dashboards + forms
│   ├── styles.css
│   └── app.js                # UI logic + API integration
└── README.md
```

## Getting Started

### 1. Backend API

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python app.py  # starts Flask at http://127.0.0.1:5000
```

The first launch creates `hospital_erp.db` (SQLite) inside the backend folder.

### 2. Frontend

Open `frontend/index.html` directly in a browser while the backend is running. All forms use `fetch` to interact with the Flask API running on `http://127.0.0.1:5000`.

## Key API Endpoints

| Method | Endpoint | Purpose |
| ------ | -------- | ------- |
| POST | `/api/doctors/register` | Register a doctor and generate `DOC-xxxxx` ID |
| POST | `/api/patients/register` | Register a patient, capture visit data, assign doctor |
| POST | `/api/login` | Authenticate patients (`PAT-...` + phone) or doctors (`DOC-...` + phone) |
| GET | `/api/doctors/<doctor_id>` | Doctor dashboard payload (patients, schedules, follow-ups) |
| GET | `/api/patients/<patient_id>` | Patient dashboard payload (profile, visits, prescriptions, discharge) |
| POST | `/api/patients/<patient_id>/visits` | Record new visit (in/outpatient) |
| POST | `/api/patients/<patient_id>/prescriptions` | Add prescription authored by doctor |
| POST | `/api/doctors/<doctor_id>/schedule` | Add schedule item for doctor |
| POST | `/api/doctors/<doctor_id>/followups` | Plan follow-up with patient |
| POST | `/api/patients/<patient_id>/discharge` | Discharge patient and emit receipt |

Full endpoint list lives in `backend/app/routes.py`.

## Suggested Workflow

1. Register a doctor to obtain an ID (`DOC-00001`).
2. Register patients with personal details, visit reason, and optionally assign the doctor.
3. Log in as the doctor using the generated ID (username) and phone number (password).
4. Use the doctor dashboard to plan schedules, create follow-ups, capture visits, prescribe medication, and discharge patients.
5. Log in as a patient with `PAT-xxxxx` / phone to review records in real time.

## Next Steps

- Add persistent session management and role-based authorization middleware.
- Create admin/staff modules for ward management and bed allocation.
- Integrate notification systems (SMS/email) for follow-ups and discharge instructions.
- Package the frontend with a bundler or migrate to React/Next.js for richer UX.

## Github Actions

- Demonstrated the workflows and how github actions works as well

## Screenshots
<img width="1917" height="870" alt="ERP1" src="https://github.com/user-attachments/assets/472e8240-9a03-4e77-a2e9-f83d360444e0" />
<img width="1917" height="857" alt="ERP2" src="https://github.com/user-attachments/assets/18fe24a7-0bf2-4e69-80e3-e15e529dd4c6" />
<img width="1917" height="867" alt="ERP3" src="https://github.com/user-attachments/assets/6296575d-1347-44d0-9879-feb90e4c67c6" />
<img width="1917" height="856" alt="ERP4" src="https://github.com/user-attachments/assets/5bd2d44f-75c0-46d5-9d59-488d2953af5a" />
<img width="1917" height="862" alt="ERP5" src="https://github.com/user-attachments/assets/ea7d8b13-748c-40a6-b067-a51df4792d37" />
<img width="1917" height="847" alt="ERP6" src="https://github.com/user-attachments/assets/156e038e-c6af-47ec-8d0a-232de5d54dce" />






