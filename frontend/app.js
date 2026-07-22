const API_BASE = "http://127.0.0.1:5000/api";

const doctorRegisterForm = document.getElementById("doctor-register-form");
const patientRegisterForm = document.getElementById("patient-register-form");
const loginForm = document.getElementById("login-form");
const contactForm = document.getElementById("contact-form");
const scheduleForm = document.getElementById("schedule-form");
const followupForm = document.getElementById("followup-form");
const prescriptionForm = document.getElementById("prescription-form");
const visitForm = document.getElementById("visit-form");
const dischargeForm = document.getElementById("discharge-form");

const doctorFeedback = document.querySelector('.form-feedback[data-role="doctor"]');
const patientFeedback = document.querySelector('.form-feedback[data-role="patient"]');
const loginFeedback = document.querySelector('.form-feedback[data-role="login"]');
const contactFeedback = document.querySelector('.form-feedback[data-role="contact"]');

const patientDashboard = document.getElementById("patient-dashboard");
const doctorDashboard = document.getElementById("doctor-dashboard");

const patientDetailsEl = document.getElementById("patient-details");
const patientPrescriptionsEl = document.getElementById("patient-prescriptions");
const patientVisitsEl = document.getElementById("patient-visits");
const patientDischargeEl = document.getElementById("patient-discharge");

const doctorPatientsEl = document.getElementById("doctor-patients");
const doctorSchedulesEl = document.getElementById("doctor-schedules");
const doctorFollowupsEl = document.getElementById("doctor-followups");

const yearEl = document.getElementById("year");

let currentDoctorId = null;
let currentPatientId = null;

async function postData(url = "", data = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "Request failed" }));
    throw new Error(error.error || "Request failed");
  }
  return response.json();
}

function toJSON(form) {
  const data = new FormData(form);
  return Object.fromEntries(data.entries());
}

function resetFeedback(el) {
  if (!el) return;
  el.textContent = "";
  el.classList.remove("error", "success");
}

function setFeedback(el, message, type = "success") {
  if (!el) return;
  el.textContent = message;
  el.classList.remove("error", "success");
  el.classList.add(type);
}

doctorRegisterForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  resetFeedback(doctorFeedback);
  const payload = toJSON(doctorRegisterForm);
  if (payload.years_experience === "") delete payload.years_experience;
  try {
    const data = await postData(`${API_BASE}/doctors/register`, payload);
    setFeedback(doctorFeedback, `Doctor created successfully. ID: ${data.doctor_id}`, "success");
    doctorRegisterForm.reset();
  } catch (error) {
    setFeedback(doctorFeedback, error.message, "error");
  }
});

patientRegisterForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  resetFeedback(patientFeedback);
  const payload = toJSON(patientRegisterForm);
  if (!payload.date_of_birth) delete payload.date_of_birth;
  if (!payload.gender) delete payload.gender;
  if (!payload.email) delete payload.email;
  if (!payload.address) delete payload.address;
  if (!payload.emergency_contact) delete payload.emergency_contact;
  if (!payload.medical_history) delete payload.medical_history;
  if (!payload.doctor_id) delete payload.doctor_id;
  try {
    const data = await postData(`${API_BASE}/patients/register`, payload);
    setFeedback(patientFeedback, `Patient registered successfully. ID: ${data.patient_id}`, "success");
    patientRegisterForm.reset();
  } catch (error) {
    setFeedback(patientFeedback, error.message, "error");
  }
});

loginForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  resetFeedback(loginFeedback);
  patientDashboard.hidden = true;
  doctorDashboard.hidden = true;

  const payload = toJSON(loginForm);
  try {
    const loginData = await postData(`${API_BASE}/login`, payload);
    setFeedback(loginFeedback, `Welcome ${loginData.display_name}!`, "success");

    if (loginData.role === "patient") {
      currentPatientId = loginData.reference_id;
      currentDoctorId = null;
      await loadPatientDashboard(loginData.reference_id);
      patientDashboard.hidden = false;
    } else {
      currentDoctorId = loginData.reference_id;
      currentPatientId = null;
      await loadDoctorDashboard(loginData.reference_id);
      doctorDashboard.hidden = false;
    }
  } catch (error) {
    setFeedback(loginFeedback, error.message, "error");
  }
});

contactForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  resetFeedback(contactFeedback);
  setTimeout(() => {
    setFeedback(contactFeedback, "Thanks for reaching out. We'll get back to you soon!", "success");
    contactForm.reset();
  }, 400);
});

async function loadPatientDashboard(patientId) {
  try {
    const response = await fetch(`${API_BASE}/patients/${patientId}`);
    if (!response.ok) throw new Error("Unable to load patient dashboard");
    const data = await response.json();

    const patient = data.patient;
    patientDetailsEl.innerHTML = `
      <p><strong>Name:</strong> ${patient.first_name} ${patient.last_name}</p>
      <p><strong>Phone:</strong> ${patient.phone_number}</p>
      <p><strong>Email:</strong> ${patient.email || "—"}</p>
      <p><strong>Address:</strong> ${patient.address || "—"}</p>
      <p><strong>Doctor:</strong> ${patient.doctor ? `${patient.doctor.name} (${patient.doctor.department})` : "Not assigned"}</p>
      <p><strong>Status:</strong> ${patient.is_inpatient ? `Admitted to ward ${patient.ward || "—"}` : "Outpatient"}</p>
    `;

    patientPrescriptionsEl.innerHTML = data.prescriptions
      .map(
        (prescription) => `
        <li>
          <strong>${prescription.medication}</strong> - ${prescription.dosage}
          <div>${prescription.instructions}</div>
          <div>Prescribed by ${prescription.doctor_id} on ${new Date(prescription.created_at).toLocaleString()}</div>
        </li>
      `,
      )
      .join("") || "<li>No prescriptions yet.</li>";

    patientVisitsEl.innerHTML = data.visits
      .map(
        (visit) => `
        <li>
          <div><strong>${visit.visit_type.toUpperCase()}</strong> - ${visit.visit_reason}</div>
          <div>${new Date(visit.visit_time).toLocaleString()} | Doctor: ${visit.doctor_id || "—"}</div>
          <div>${visit.notes || ""}</div>
        </li>
      `,
      )
      .join("") || "<li>No visits recorded.</li>";

    patientDischargeEl.innerHTML = data.discharge_summary
      ? `
        <p><strong>Date:</strong> ${new Date(data.discharge_summary.discharge_date).toLocaleString()}</p>
        <p><strong>Doctor:</strong> ${data.discharge_summary.doctor_id}</p>
        <p><strong>Summary:</strong> ${data.discharge_summary.summary_text}</p>
        <p><strong>Recommendations:</strong> ${data.discharge_summary.recommendations || "—"}</p>
        <p><strong>Follow-up:</strong> ${data.discharge_summary.follow_up_date ? new Date(data.discharge_summary.follow_up_date).toLocaleDateString() : "—"}</p>
      `
      : "<p>No discharge summary available.</p>";
  } catch (error) {
    setFeedback(loginFeedback, error.message, "error");
  }
}

async function loadDoctorDashboard(doctorId) {
  try {
    const response = await fetch(`${API_BASE}/doctors/${doctorId}`);
    if (!response.ok) throw new Error("Unable to load doctor dashboard");
    const data = await response.json();

    doctorPatientsEl.innerHTML = data.patients
      .map(
        (patient) => `
        <li>
          <div><strong>${patient.name}</strong> (${patient.patient_id})</div>
          <div>${patient.phone_number}</div>
          <div>Visits: ${patient.visit_count} | Inpatient: ${patient.is_inpatient ? "Yes" : "No"}</div>
          <div>Ward: ${patient.ward || "—"} | Bed: ${patient.bed_number || "—"}</div>
        </li>
      `,
      )
      .join("") || "<li>No patients assigned.</li>";

    doctorSchedulesEl.innerHTML = data.schedules
      .map(
        (schedule) => `
        <li>
          <div><strong>${schedule.title}</strong></div>
          <div>${new Date(schedule.start_time).toLocaleString()} - ${new Date(schedule.end_time).toLocaleString()}</div>
          <div>${schedule.description || ""}</div>
          <div>Status: ${schedule.status}</div>
        </li>
      `,
      )
      .join("") || "<li>No schedule items yet.</li>";

    doctorFollowupsEl.innerHTML = data.followups
      .map(
        (followup) => `
        <li>
          <div><strong>${followup.patient_name}</strong> (${followup.patient_id})</div>
          <div>${new Date(followup.scheduled_for).toLocaleString()}</div>
          <div>Status: ${followup.status}</div>
          <div>${followup.notes || ""}</div>
        </li>
      `,
      )
      .join("") || "<li>No follow-ups scheduled.</li>";
  } catch (error) {
    setFeedback(loginFeedback, error.message, "error");
  }
}

scheduleForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const feedback = document.querySelector('.form-feedback[data-role="schedule"]');
  resetFeedback(feedback);
  if (!currentDoctorId) {
    setFeedback(feedback, "Login as a doctor to add schedules", "error");
    return;
  }
  const payload = toJSON(scheduleForm);
  try {
    payload.start_time = new Date(payload.start_time).toISOString();
    payload.end_time = new Date(payload.end_time).toISOString();
    await postData(`${API_BASE}/doctors/${currentDoctorId}/schedule`, payload);
    scheduleForm.reset();
    setFeedback(feedback, "Schedule created", "success");
    await loadDoctorDashboard(currentDoctorId);
  } catch (error) {
    setFeedback(feedback, error.message, "error");
  }
});

followupForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const feedback = document.querySelector('.form-feedback[data-role="followup"]');
  resetFeedback(feedback);
  if (!currentDoctorId) {
    setFeedback(feedback, "Login as a doctor to create follow-ups", "error");
    return;
  }
  const payload = toJSON(followupForm);
  try {
    payload.scheduled_for = new Date(payload.scheduled_for).toISOString();
    await postData(`${API_BASE}/doctors/${currentDoctorId}/followups`, payload);
    followupForm.reset();
    setFeedback(feedback, "Follow-up scheduled", "success");
    await loadDoctorDashboard(currentDoctorId);
  } catch (error) {
    setFeedback(feedback, error.message, "error");
  }
});

prescriptionForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const feedback = document.querySelector('.form-feedback[data-role="prescription"]');
  resetFeedback(feedback);
  if (!currentDoctorId) {
    setFeedback(feedback, "Login as a doctor to add prescriptions", "error");
    return;
  }
  const payload = toJSON(prescriptionForm);
  const patientId = payload.patient_id;
  delete payload.patient_id;
  payload.doctor_id = currentDoctorId;
  try {
    await postData(`${API_BASE}/patients/${patientId}/prescriptions`, payload);
    prescriptionForm.reset();
    setFeedback(feedback, "Prescription saved", "success");
    if (currentPatientId === patientId) {
      await loadPatientDashboard(patientId);
    }
  } catch (error) {
    setFeedback(feedback, error.message, "error");
  }
});

visitForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const feedback = document.querySelector('.form-feedback[data-role="visit"]');
  resetFeedback(feedback);
  if (!currentDoctorId) {
    setFeedback(feedback, "Login as a doctor to record visits", "error");
    return;
  }
  const payload = toJSON(visitForm);
  const patientId = payload.patient_id;
  delete payload.patient_id;
  payload.doctor_id = currentDoctorId;
  if (!payload.notes) delete payload.notes;
  try {
    await postData(`${API_BASE}/patients/${patientId}/visits`, payload);
    visitForm.reset();
    setFeedback(feedback, "Visit recorded", "success");
    if (currentPatientId === patientId) {
      await loadPatientDashboard(patientId);
    }
    await loadDoctorDashboard(currentDoctorId);
  } catch (error) {
    setFeedback(feedback, error.message, "error");
  }
});

dischargeForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const feedback = document.querySelector('.form-feedback[data-role="discharge"]');
  resetFeedback(feedback);
  if (!currentDoctorId) {
    setFeedback(feedback, "Login as a doctor to discharge patients", "error");
    return;
  }
  const payload = toJSON(dischargeForm);
  const patientId = payload.patient_id;
  delete payload.patient_id;
  payload.doctor_id = currentDoctorId;
  if (!payload.recommendations) delete payload.recommendations;
  if (!payload.follow_up_date) {
    delete payload.follow_up_date;
  } else {
    payload.follow_up_date = new Date(payload.follow_up_date).toISOString();
  }
  try {
    await postData(`${API_BASE}/patients/${patientId}/discharge`, payload);
    dischargeForm.reset();
    setFeedback(feedback, "Discharge receipt created", "success");
    if (currentPatientId === patientId) {
      await loadPatientDashboard(patientId);
    }
    await loadDoctorDashboard(currentDoctorId);
  } catch (error) {
    setFeedback(feedback, error.message, "error");
  }
});

function initCarousel() {
  const slides = Array.from(document.querySelectorAll(".carousel-slide"));
  const buttons = Array.from(document.querySelectorAll(".carousel-btn"));
  if (!slides.length) return;

  let current = 0;

  function showSlide(index) {
    slides[current].classList.remove("active");
    current = (index + slides.length) % slides.length;
    slides[current].classList.add("active");
  }

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const direction = button.dataset.direction === "next" ? 1 : -1;
      showSlide(current + direction);
    });
  });

  // Auto-rotate carousel
  setInterval(() => {
    showSlide(current + 1);
  }, 8000);
}

function initFooterYear() {
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear().toString();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initCarousel();
  initFooterYear();
});

