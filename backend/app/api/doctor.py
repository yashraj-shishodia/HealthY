import uuid
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.api.deps import get_current_user, require_doctor
from app.models.user import User
from app.models.doctor import DoctorProfile
from app.models.appointment import Appointment, AppointmentStatus, AISummaryStatus
from app.models.notification import MedicationReminder, ReminderStatus
from app.schemas.appointment import AppointmentResponse
from app.schemas.doctor_portal import CompleteAppointmentRequest
from app.workers.tasks import generate_post_visit_summary_task

router = APIRouter(prefix="/api/doctor", tags=["Doctor Portal"], dependencies=[Depends(require_doctor)])


async def get_doctor_profile_for_user(db: AsyncSession, user_id: uuid.UUID) -> DoctorProfile:
    """Helper to fetch doctor profile for authenticated doctor user."""
    result = await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == user_id))
    doctor = result.scalars().first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "DOCTOR_PROFILE_NOT_FOUND", "message": "Doctor profile not configured."}},
        )
    return doctor


@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_doctor_schedule(
    target_date: Optional[date] = Query(None, alias="date", description="Filter schedule by date"),
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status", description="Filter by appointment status"),
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
):
    """Fetch schedule of appointments for the logged-in doctor."""
    doctor = await get_doctor_profile_for_user(db, current_user.id)
    query = select(Appointment).where(Appointment.doctor_id == doctor.id)

    if target_date:
        query = query.where(Appointment.appointment_date == target_date)
    if status_filter:
        query = query.where(Appointment.status == status_filter)

    query = query.order_by(Appointment.appointment_date.asc(), Appointment.start_time.asc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_doctor_appointment_detail(
    appointment_id: uuid.UUID,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
):
    """Fetch detailed appointment record for clinician review (includes AI pre-visit summary)."""
    doctor = await get_doctor_profile_for_user(db, current_user.id)
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.doctor_id == doctor.id
        )
    )
    appointment = result.scalars().first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "APPOINTMENT_NOT_FOUND", "message": "Appointment not found or unauthorized."}},
        )
    return appointment


@router.post("/appointments/{appointment_id}/complete", response_model=AppointmentResponse)
async def complete_visit(
    appointment_id: uuid.UUID,
    req: CompleteAppointmentRequest,
    current_user: User = Depends(require_doctor),
    db: AsyncSession = Depends(get_db)
):
    """Doctor endpoint to enter clinical notes, prescription, and complete visit."""
    doctor = await get_doctor_profile_for_user(db, current_user.id)
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.doctor_id == doctor.id
        )
    )
    appointment = result.scalars().first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "APPOINTMENT_NOT_FOUND", "message": "Appointment not found or unauthorized."}},
        )

    appointment.status = AppointmentStatus.COMPLETED
    appointment.doctor_notes = req.doctor_notes
    appointment.prescription = req.prescription
    appointment.post_visit_summary_status = AISummaryStatus.PENDING

    # Schedule medication reminders if instructions provided
    now_utc = datetime.now(timezone.utc)
    for med in req.medication_instructions:
        reminder = MedicationReminder(
            id=uuid.uuid4(),
            appointment_id=appointment.id,
            patient_id=appointment.patient_id,
            medication_name=med.medication_name,
            dosage=med.dosage,
            frequency=med.frequency,
            next_run_at=now_utc + timedelta(hours=12),
            end_at=now_utc + timedelta(days=med.duration_days),
            status=ReminderStatus.ACTIVE,
        )
        db.add(reminder)

    await db.commit()
    await db.refresh(appointment)

    # Post-commit dispatch: trigger AI post-visit summary task
    try:
        generate_post_visit_summary_task.delay(str(appointment.id))
    except Exception:
        pass

    return appointment
