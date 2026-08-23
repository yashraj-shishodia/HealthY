# HealthY — Healthcare Appointment & Follow-up Manager

HealthY is an end-to-end, high-concurrency Healthcare Appointment & Follow-up Management application built with **FastAPI, Async SQLAlchemy, PostgreSQL, Redis, Celery, React (Vite), TypeScript, and Vanilla CSS Glassmorphism design**.

---

## 🌟 1. Project Overview & Key Features

HealthY simplifies doctor-patient engagement through automated AI pre-visit assessments, 5-minute atomic slot reservation holds, dual-participant Google Calendar sync, and idempotent transactional email notifications.

### Core Features:
- **Patient Portal:** Search doctors by specialisation, view available slots, reserve slots with a 5-minute hold timer, submit symptom intake forms, view AI pre-visit summaries and post-visit prescriptions.
- **Doctor Workstation:** Real-time schedule timeline, patient symptoms display, AI-generated clinical triage cards with urgency classification and 3 suggested questions, clinical notes editor, and prescription builder.
- **Admin Portal:** Manage doctor profiles, specialisations, slot duration, working hours, and doctor leave management with automated cascade cancellation.
- **Atomic Concurrency Protection:** Enforced by PostgreSQL partial unique index `uq_doctor_active_slot` on `(doctor_id, appointment_date, start_time) WHERE status IN ('HELD', 'BOOKED')`. Race conditions return HTTP 409 Conflict without database corruption.
- **LLM Fault Isolation:** Pre & post-visit LLM summaries execute in background workers with safe fallbacks. External LLM failures record `status = 'FAILED'` without corrupting appointments.
- **Dual-Participant Google Calendar Isolation:** Patient and doctor Google Calendar OAuth connections synchronize independently.
- **Idempotent Email Engine:** Notifications write audit logs with unique idempotency keys to prevent duplicate emails upon worker retries.

---

## 🏗️ 2. Architecture & Tech Stack

```
                                 ┌───────────────────────┐
                                 │ React + TS Frontend   │
                                 └───────────┬───────────┘
                                             │ REST API (Bearer JWT)
                                             ▼
                                 ┌───────────────────────┐
                                 │   FastAPI Backend     │
                                 └─────┬───────────┬─────┘
                                       │           │
                     ┌─────────────────┘           └─────────────────┐
                     ▼                                               ▼
         ┌───────────────────────┐                       ┌───────────────────────┐
         │ PostgreSQL / SQLite   │                       │ Redis Queue & Celery  │
         │ (Partial Unique Index)│                       │ (Async Notifications) │
         └───────────────────────┘                       └───────────────────────┘
```

- **Backend:** Python 3.11+, FastAPI, Pydantic v2, Async SQLAlchemy 2.0, Alembic, Passlib (Bcrypt), PyJWT.
- **Frontend:** React 18, TypeScript, Vite, React Router v6, Vanilla CSS (Glassmorphism design system).
- **Task Queue & Caching:** Celery, Redis.
- **Database:** PostgreSQL (Neon Serverless) / SQLite (aiosqlite for local development).
- **Integrations:** Google Gemini 1.5 Flash API, SendGrid Email API, Google Calendar OAuth 2.0.

---

## 📂 3. Project Structure

```
HealthY/
│
├── backend/
│   ├── app/
│   │   ├── api/            # REST API Endpoint Controllers (auth, doctors, appointments, admin)
│   │   ├── core/           # Config, Database Engine, Security, DB Seeder
│   │   ├── models/         # SQLAlchemy ORM Data Models & Constraints
│   │   ├── schemas/        # Pydantic Request/Response Schemas
│   │   └── services/       # Auth, Booking, LLM, Email, Calendar Services
│   ├── alembic/            # Database Migration Scripts
│   ├── tests/              # Pytest Automated Test Suite (17 Test Cases)
│   └── requirements.txt    # Python Backend Dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/     # Navbar, Sidebar, ProtectedRoute, AISummaryCard
│   │   ├── pages/          # Landing, Login, Register, Patient, Doctor, Admin Dashboards
│   │   ├── services/       # API Clients (authApi, bookingApi, doctorApi, calendarApi)
│   │   └── index.css       # Global Glassmorphism Design System Styles
│   ├── package.json        # Frontend Dependencies
│   └── vite.config.ts      # Vite Build Configuration
│
├── docs/
│   └── SYSTEM_DESIGN.md    # System Design Document (<= 800 words)
│
├── .env.example            # Environment Variables Template
├── .gitignore              # Git Ignore Security Specifications
├── docker-compose.yml      # Multi-container Docker Orchestration
└── README.md               # Evaluator Documentation Guide
```

---

## 🛠️ 4. Local Setup & Execution Guide

### Prerequisites:
- Python 3.11+
- Node.js 18+
- Redis Server (optional for background workers; fallback executes inline)

### Step 1: Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### Step 2: Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run Database Migrations & Seed Initial Accounts
python3 -m app.core.seed

# Start FastAPI Backend Server
uvicorn app.main:app --reload --port 8000
```
- **Backend API:** `http://localhost:8000`
- **Swagger Documentation:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`

### Step 3: Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- **Frontend App:** `http://localhost:5173`

---

## 🧪 5. Automated Test Suite

Run the full automated backend test suite (covering concurrency race conditions, slot validation, LLM fault isolation, calendar sync, leave cascades, email idempotency, and RBAC):

```bash
cd backend
PYTHONPATH=. pytest tests -v
```

---

## 🔌 6. Integration Setup Guide

### A. Google Gemini LLM API (AI Pre/Post-Visit Summaries)
1. Get a free API key at [Google AI Studio](https://aistudio.google.com/).
2. Add to `.env`:
   ```env
   LLM_PROVIDER=gemini
   LLM_API_KEY=your_gemini_api_key_here
   LLM_MODEL_NAME=gemini-1.5-flash
   ```
*(If omitted, HealthY automatically uses the built-in deterministic clinical mock AI).*

### B. SendGrid Email Setup
1. Create a free key at [SendGrid](https://signup.sendgrid.com/).
2. Add to `.env`:
   ```env
   EMAIL_PROVIDER=sendgrid
   EMAIL_API_KEY=SG.your_sendgrid_api_key_here
   EMAIL_FROM=noreply@healthyapp.com
   ```

### C. Google Calendar OAuth Setup
1. Create OAuth credentials in [Google Cloud Console](https://console.cloud.google.com/).
2. Add authorized redirect URI: `http://localhost:5173/calendar/callback`.
3. Add to `.env`:
   ```env
   GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   GOOGLE_REDIRECT_URI=http://localhost:5173/calendar/callback
   ```

---

## 🐳 7. Docker Deployment

Deploy the entire stack with Docker Compose:
```bash
docker-compose up --build
```
- **Frontend:** `http://localhost:3000`
- **Backend:** `http://localhost:8000`
