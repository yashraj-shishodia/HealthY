import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.api.deps import get_current_user, require_patient
from app.models.user import User
from app.models.appointment import Appointment
from app.schemas.appointment import (
    HoldSlotRequest, ConfirmBookingRequest, RescheduleAppointmentRequest,
    CancelAppointmentRequest, AppointmentResponse
)
from app.services.booking_service import (
    create_slot_hold, confirm_booking, get_appointment_by_id,
    cancel_appointment, reschedule_appointment
)

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


@router.post("/hold", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def hold_slot(
    req: HoldSlotRequest,
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    """Reserves a slot for 5 minutes (HELD state)."""
    appointment = await create_slot_hold(db, current_user.id, req)
    return appointment


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    req: ConfirmBookingRequest,
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    """Confirms appointment booking with symptoms and triggers post-commit side effects."""
    appointment = await confirm_booking(db, current_user.id, req)
    return appointment


@router.get("/my", response_model=List[AppointmentResponse])
async def get_my_appointments(
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    """Lists appointment history strictly belonging to authenticated patient."""
    result = await db.execute(
        select(Appointment)
        .where(Appointment.patient_id == current_user.id)
        .order_by(Appointment.appointment_date.desc(), Appointment.start_time.desc())
    )
    return result.scalars().all()


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch details for a specific appointment with strict ownership authorization and inline LLM fallbacks."""
    appointment = await get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "APPOINTMENT_NOT_FOUND", "message": "Appointment not found."}},
        )
    
    # Strict Authorization: Patient owns or Doctor owns or Admin
    if current_user.role == "PATIENT" and appointment.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "You do not have access to this appointment."}},
        )
    if current_user.role == "DOCTOR":
        from app.services.doctor_service import get_doctor_by_user_id
        doc = await get_doctor_by_user_id(db, current_user.id)
        if not doc or appointment.doctor_id != doc.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "FORBIDDEN", "message": "You do not have access to this appointment."}},
            )

    # Inline fallback 1: Process PENDING pre-visit summary if background worker didn't run
    if (appointment.pre_visit_summary_status in ["PENDING", "PROCESSING", None]) and appointment.symptoms:
        try:
            from app.workers.tasks import process_pre_visit_summary_async
            await process_pre_visit_summary_async(str(appointment.id), db)
            await db.refresh(appointment)
        except Exception:
            pass

    # Inline fallback 2: Process PENDING post-visit summary if background worker didn't run
    if (appointment.post_visit_summary_status in ["PENDING", "PROCESSING"]) and appointment.doctor_notes:
        try:
            from app.workers.tasks import process_post_visit_summary_async
            await process_post_visit_summary_async(str(appointment.id), db)
            await db.refresh(appointment)
        except Exception:
            pass

    return appointment


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_my_appointment(
    appointment_id: uuid.UUID,
    req: CancelAppointmentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel an appointment."""
    return await cancel_appointment(db, current_user.id, appointment_id, req.reason)


@router.post("/{appointment_id}/reschedule", response_model=AppointmentResponse)
async def reschedule_my_appointment(
    appointment_id: uuid.UUID,
    req: RescheduleAppointmentRequest,
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    """Reschedule an appointment atomically to a new slot."""
    return await reschedule_appointment(
        db, current_user.id, appointment_id, req.new_date, req.new_start_time, req.new_end_time
    )
