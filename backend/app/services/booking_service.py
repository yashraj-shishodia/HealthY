import uuid
from datetime import date, time, datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.core.datetime_utils import get_now_utc
from app.models.appointment import (
    Appointment, AppointmentStatus, AISummaryStatus, CalendarSyncStatus, OverallCalendarSyncStatus
)
from app.schemas.appointment import HoldSlotRequest, ConfirmBookingRequest
from app.services.availability_service import validate_requested_slot
from app.workers.tasks import (
    generate_pre_visit_summary_task, send_booking_email_task,
    sync_google_calendar_task, send_cancellation_email_task
)


def ensure_tz_aware(dt: datetime) -> datetime:
    """Ensure datetime is timezone aware (UTC)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def create_slot_hold(
    db: AsyncSession,
    patient_id: uuid.UUID,
    req: HoldSlotRequest
) -> Appointment:
    """Reserve a slot for 5 minutes with HELD status."""
    # 1. Server-side validation of requested slot
    await validate_requested_slot(
        db, req.doctor_id, req.appointment_date, req.start_time, req.end_time
    )

    # 2. Check collision explicitly and expire stale holds
    now_utc = get_now_utc()
    existing_check = await db.execute(
        select(Appointment).where(
            Appointment.doctor_id == req.doctor_id,
            Appointment.appointment_date == req.appointment_date,
            Appointment.start_time == req.start_time,
            Appointment.status.in_([AppointmentStatus.HELD, AppointmentStatus.BOOKED])
        )
    )
    stale_found = False
    for appt in existing_check.scalars().all():
        exp = ensure_tz_aware(appt.hold_expires_at)
        if appt.status == AppointmentStatus.BOOKED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": {"code": "SLOT_UNAVAILABLE", "message": "The selected slot is no longer available."}},
            )
        elif appt.status == AppointmentStatus.HELD:
            if exp and exp > now_utc:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"error": {"code": "SLOT_UNAVAILABLE", "message": "The selected slot is currently held by another patient."}},
                )
            else:
                appt.status = AppointmentStatus.CANCELLED
                stale_found = True

    if stale_found:
        await db.flush()

    hold_expires = now_utc + timedelta(minutes=5)
    appointment = Appointment(
        id=uuid.uuid4(),
        doctor_id=req.doctor_id,
        patient_id=patient_id,
        appointment_date=req.appointment_date,
        start_time=req.start_time,
        end_time=req.end_time,
        status=AppointmentStatus.HELD,
        hold_expires_at=hold_expires,
        pre_visit_summary_status=AISummaryStatus.NOT_STARTED,
        post_visit_summary_status=AISummaryStatus.NOT_STARTED,
        patient_calendar_sync_status=CalendarSyncStatus.NONE,
        doctor_calendar_sync_status=CalendarSyncStatus.NONE,
        overall_calendar_sync_status=OverallCalendarSyncStatus.NOT_CONNECTED,
    )
    db.add(appointment)

    try:
        await db.commit()
        return appointment
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "SLOT_UNAVAILABLE", "message": "The selected slot is no longer available."}},
        )


async def confirm_booking(
    db: AsyncSession,
    patient_id: uuid.UUID,
    req: ConfirmBookingRequest
) -> Appointment:
    """Atomic booking confirmation transaction followed by post-commit side-effect dispatch."""
    now_utc = get_now_utc()

    # Path A: Confirming an existing HELD appointment
    held_id = req.appointment_id or req.hold_id
    if held_id:
        result = await db.execute(
            select(Appointment).where(
                Appointment.id == held_id,
                Appointment.patient_id == patient_id
            ).with_for_update()
        )
        appointment = result.scalars().first()
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "APPOINTMENT_NOT_FOUND", "message": "Held appointment not found."}},
            )

        if appointment.status == AppointmentStatus.BOOKED:
            return appointment

        if appointment.status != AppointmentStatus.HELD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "INVALID_APPOINTMENT_STATE", "message": "Appointment cannot be confirmed in current state."}},
            )

        exp = ensure_tz_aware(appointment.hold_expires_at)
        if exp and exp <= now_utc:
            appointment.status = AppointmentStatus.CANCELLED
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": {"code": "HOLD_EXPIRED", "message": "Slot hold has expired. Please select a slot again."}},
            )

        appointment.status = AppointmentStatus.BOOKED
        appointment.symptoms = req.symptoms
        appointment.pre_visit_summary_status = AISummaryStatus.PENDING

    # Path B: Direct booking with symptom submission
    else:
        if not req.doctor_id or not req.appointment_date or not req.start_time or not req.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "MISSING_SLOT_DETAILS", "message": "Slot details (doctor, date, times) are required."}},
            )

        await validate_requested_slot(
            db, req.doctor_id, req.appointment_date, req.start_time, req.end_time
        )

        # Collision Check for active slot and expire stale holds
        collision_result = await db.execute(
            select(Appointment).where(
                Appointment.doctor_id == req.doctor_id,
                Appointment.appointment_date == req.appointment_date,
                Appointment.start_time == req.start_time,
                Appointment.status.in_([AppointmentStatus.HELD, AppointmentStatus.BOOKED])
            ).with_for_update()
        )
        stale_found = False
        for appt in collision_result.scalars().all():
            exp = ensure_tz_aware(appt.hold_expires_at)
            if appt.status == AppointmentStatus.BOOKED:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"error": {"code": "SLOT_UNAVAILABLE", "message": "The selected slot was booked by another patient."}},
                )
            elif appt.status == AppointmentStatus.HELD:
                if exp and exp > now_utc:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={"error": {"code": "SLOT_UNAVAILABLE", "message": "The selected slot is currently held by another patient."}},
                    )
                else:
                    # Stale hold -> update ORM status
                    appt.status = AppointmentStatus.CANCELLED
                    stale_found = True

        if stale_found:
            await db.flush()

        appointment = Appointment(
            id=uuid.uuid4(),
            doctor_id=req.doctor_id,
            patient_id=patient_id,
            appointment_date=req.appointment_date,
            start_time=req.start_time,
            end_time=req.end_time,
            status=AppointmentStatus.BOOKED,
            symptoms=req.symptoms,
            pre_visit_summary_status=AISummaryStatus.PENDING,
            post_visit_summary_status=AISummaryStatus.NOT_STARTED,
            patient_calendar_sync_status=CalendarSyncStatus.NONE,
            doctor_calendar_sync_status=CalendarSyncStatus.NONE,
            overall_calendar_sync_status=OverallCalendarSyncStatus.NOT_CONNECTED,
        )
        db.add(appointment)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "SLOT_UNAVAILABLE", "message": "The selected slot was booked by another patient."}},
        )

    # -------------------------------------------------------------------
    # POST-COMMIT ASYNCHRONOUS SIDE-EFFECT DISPATCH
    # -------------------------------------------------------------------
    try:
        generate_pre_visit_summary_task.delay(str(appointment.id))
        send_booking_email_task.delay(str(appointment.id))
        sync_google_calendar_task.delay(str(appointment.id), "CREATE")
    except Exception:
        pass

    return appointment


async def get_appointment_by_id(db: AsyncSession, appointment_id: uuid.UUID) -> Optional[Appointment]:
    """Fetch single appointment record."""
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    return result.scalars().first()


async def cancel_appointment(
    db: AsyncSession,
    user_id: uuid.UUID,
    appointment_id: uuid.UUID,
    reason: Optional[str] = None
) -> Appointment:
    """Cancel an appointment."""
    appointment = await get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "APPOINTMENT_NOT_FOUND", "message": "Appointment not found."}},
        )

    if appointment.status in [AppointmentStatus.CANCELLED, AppointmentStatus.CANCELLED_BY_LEAVE]:
        return appointment

    appointment.status = AppointmentStatus.CANCELLED
    await db.commit()

    # Post-commit dispatch
    try:
        send_cancellation_email_task.delay(str(appointment.id), reason)
        sync_google_calendar_task.delay(str(appointment.id), "DELETE")
    except Exception:
        pass

    return appointment


async def reschedule_appointment(
    db: AsyncSession,
    patient_id: uuid.UUID,
    appointment_id: uuid.UUID,
    new_date: date,
    new_start_time: time,
    new_end_time: time
) -> Appointment:
    """Reschedule an appointment atomically to a new slot."""
    appointment = await get_appointment_by_id(db, appointment_id)
    if not appointment or appointment.patient_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "APPOINTMENT_NOT_FOUND", "message": "Appointment not found."}},
        )

    # Validate new slot
    await validate_requested_slot(db, appointment.doctor_id, new_date, new_start_time, new_end_time)

    appointment.appointment_date = new_date
    appointment.start_time = new_start_time
    appointment.end_time = new_end_time
    appointment.status = AppointmentStatus.BOOKED

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "SLOT_UNAVAILABLE", "message": "The selected new slot is no longer available."}},
        )

    # Post-commit dispatch
    try:
        sync_google_calendar_task.delay(str(appointment.id), "UPDATE")
        send_booking_email_task.delay(str(appointment.id))
    except Exception:
        pass

    return appointment
