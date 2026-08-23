# System Design & Architecture Specification

## 1. System Overview
HealthY is an enterprise-grade Healthcare Appointment and Follow-up Management system designed to solve high-concurrency booking collisions, LLM fault propagation, doctor schedule cascades, and third-party calendar desynchronization.

The architecture enforces a strict **separation between transactional database commits and asynchronous external side effects** (LLM inference, email delivery, third-party OAuth calendar synchronization).

```
                      +-------------------+
                      |   React + Vite    |
                      |   Frontend UI     |
                      +---------+---------+
                                | REST API
                                v
                      +-------------------+
                      |   FastAPI App     |
                      | (Async Engine)    |
                      +----+--------+-----+
                           |        |
        DB Transaction     |        | Celery Task Dispatch (Post-Commit)
        (FOR UPDATE Lock)  |        v
                           |   +----+--------------------------+
                           |   | Celery Workers + Redis Broker |
                           v   +----+---------------+----------+
                 +---------+---+--+ |               |
                 | PostgreSQL DB  | | LLM Summaries | Email / Calendar
                 | (Partial Index)| v               v
                 +----------------+ LLM Service   SendGrid / GCal OAuth
```

---

## 2. Dynamic Slot Generation Algorithm & Server Enforcement
Patients are strictly prohibited from submitting arbitrary start and end times. Slot availability is dynamically computed on the server using the following formula:

$$\text{Available Slots}(D, T) = \text{WorkingHours}(D, T) \setminus \Big(\text{Leaves}(D, T) \cup \text{Booked}(D, T) \cup \text{ActiveHolds}(D, T)\Big)$$

1. **Discrete Alignment:** Candidate slots are generated starting at `start_time` in increments of `slot_duration_minutes`.
2. **Server Validation:** Upon receiving a booking or hold request, the backend independently verifies that the requested interval $(t_{\text{start}}, t_{\text{end}})$ exactly matches a generated `AVAILABLE` slot.
3. **HTTP Distinction:**
   - **HTTP 400 (`INVALID_SLOT`):** Requested slot falls outside working hours, has incorrect duration, 15-minute alignment offset, or doctor is on leave.
   - **HTTP 409 (`SLOT_UNAVAILABLE`):** Slot matches valid working hours but is currently held or booked by another patient.

---

## 3. Concurrency Protection & Transaction Boundary
To guarantee zero double-bookings under intense parallel race conditions:

1. **Database-Level Partial Unique Index:**
   ```sql
   CREATE UNIQUE INDEX uq_doctor_active_slot 
   ON appointments (doctor_id, appointment_date, start_time) 
   WHERE status IN ('HELD', 'BOOKED');
   ```
2. **Transaction Boundary:**
   ```
   [BEGIN TRANSACTION]
     1. Lock Doctor Profile & Working Hours (SELECT FOR UPDATE)
     2. Validate Requested Slot Alignment
     3. Check Active Appointments / Holds for Overlap
     4. Insert / Update Appointment Row (status = 'BOOKED' or 'HELD')
   [COMMIT TRANSACTION]
   
   -- POST-COMMIT (Non-Blocking Async Dispatch) --
     -> Enqueue Celery: generate_pre_visit_summary_task.delay(appt_id)
     -> Enqueue Celery: send_booking_email_task.delay(appt_id)
     -> Enqueue Celery: sync_google_calendar_task.delay(appt_id, "CREATE")
   ```

---

## 4. LLM Pre/Post Visit Summarization & Non-Blocking Isolation
The system integrates LLMs for pre-visit triage and post-visit clinical summary translations using Pydantic structured outputs.

- **Pre-Visit Prompt Schema:** Extracts `urgency` (`Low`, `Medium`, `High`), `chief_complaint`, and exactly 3 `suggested_questions`.
- **Post-Visit Prompt Schema:** Translates clinical notes into patient-friendly summaries, medication schedules, and follow-up steps.
- **Fault Isolation:** External LLM timeouts, API quota limits, or malformed JSON outputs are trapped inside isolated task workers.
  - The database records `pre_visit_summary_status = 'FAILED'` and saves safe error diagnostics.
  - **Core appointment status remains intact in `BOOKED` state.**
  - The UI reads `FAILED` status and displays *"AI summary temporarily unavailable."*

---

## 5. Independent Dual-Participant Google Calendar OAuth & Synchronization
Google Calendar synchronization operates independently for the patient and doctor:

- **State Tracking:**
  - `patient_calendar_sync_status` (`NONE`, `PENDING`, `SYNCED`, `FAILED`)
  - `doctor_calendar_sync_status` (`NONE`, `PENDING`, `SYNCED`, `FAILED`)
  - `overall_calendar_sync_status` (`NOT_CONNECTED`, `PENDING`, `PARTIAL`, `SYNCED`, `FAILED`)
- **Participant Isolation:** A token expiry or API failure on the patient's Google Calendar account never prevents the doctor's calendar sync or invalidates the appointment.
- **Idempotency:** Re-running sync tasks checks `patient_calendar_event_id` / `doctor_calendar_event_id` and performs `UPDATE` instead of `CREATE` to prevent duplicate events.

---

## 6. Doctor Leave Management Cascade
When an administrator enters a leave date for a doctor:
1. An atomic DB transaction selects all active appointments (`HELD`, `BOOKED`) for that doctor on the leave date using row-level locks.
2. All affected appointments transition to `CANCELLED_BY_LEAVE`.
3. Post-commit workers asynchronously dispatch patient cancellation emails and remove calendar events.

---

## 7. Idempotent Notification Engine
All email dispatches log an audit record in `notification_logs` with a unique idempotency key:
$$\text{IdempotencyKey} = \text{AppointmentID} + ":" + \text{NotificationType} + ":" + \text{Recipient}$$
 Celery retries check for existing `SENT` status before re-dispatching, guaranteeing 100% idempotent delivery.
