import uuid
from datetime import date, time, datetime, timedelta, timezone
from typing import List, Tuple, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.core.datetime_utils import get_now_utc
from app.models.doctor import DoctorProfile, DoctorWorkingHours, DoctorLeave
from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.availability import SlotSchema, AvailabilityResponse


def parse_date(d: Union[date, str]) -> date:
    if isinstance(d, str):
        return date.fromisoformat(d)
    return d


def parse_time(t: Union[time, str]) -> time:
    if isinstance(t, str):
        return time.fromisoformat(t)
    return t


def add_minutes_to_time(t: time, minutes: int) -> time:
    """Add integer minutes to a datetime.time object."""
    dt = datetime.combine(date.today(), t) + timedelta(minutes=minutes)
    return dt.time()


async def get_doctor_availability(
    db: AsyncSession,
    doctor_id: uuid.UUID,
    target_date: Union[date, str]
) -> AvailabilityResponse:
    """Compute discrete available slots for a doctor on a given date."""
    target_date = parse_date(target_date)

    # 1. Fetch doctor
    doctor_result = await db.execute(select(DoctorProfile).where(DoctorProfile.id == doctor_id))
    doctor = doctor_result.scalars().first()
    if not doctor or not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "DOCTOR_NOT_FOUND", "message": "Doctor profile not found or inactive."}},
        )

    # 2. Check if doctor is on leave
    leave_result = await db.execute(
        select(DoctorLeave).where(
            DoctorLeave.doctor_id == doctor_id,
            DoctorLeave.leave_date == target_date
        )
    )
    is_on_leave = leave_result.scalars().first() is not None
    if is_on_leave:
        return AvailabilityResponse(
            doctor_id=doctor_id,
            appointment_date=target_date,
            slot_duration_minutes=doctor.slot_duration_minutes,
            is_on_leave=True,
            slots=[],
        )

    # 3. Check working hours for target day of week (0=Monday .. 6=Sunday)
    day_of_week = target_date.weekday()
    wh_result = await db.execute(
        select(DoctorWorkingHours).where(
            DoctorWorkingHours.doctor_id == doctor_id,
            DoctorWorkingHours.day_of_week == day_of_week
        )
    )
    working_hours_list = wh_result.scalars().all()
    if not working_hours_list:
        return AvailabilityResponse(
            doctor_id=doctor_id,
            appointment_date=target_date,
            slot_duration_minutes=doctor.slot_duration_minutes,
            is_on_leave=False,
            slots=[],
        )

    # 4. Fetch existing active appointments & holds
    now_utc = get_now_utc()
    appt_result = await db.execute(
        select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == target_date,
            Appointment.status.in_([AppointmentStatus.HELD, AppointmentStatus.BOOKED])
        )
    )
    existing_appts = appt_result.scalars().all()

    # Filter out expired holds
    active_appts = []
    for appt in existing_appts:
        if appt.status == AppointmentStatus.BOOKED:
            active_appts.append(appt)
        elif appt.status == AppointmentStatus.HELD and appt.hold_expires_at:
            exp_time = appt.hold_expires_at
            if exp_time.tzinfo is None:
                exp_time = exp_time.replace(tzinfo=timezone.utc)
            if exp_time > now_utc:
                active_appts.append(appt)

    # 5. Generate candidate slots
    slots: List[SlotSchema] = []
    slot_duration = doctor.slot_duration_minutes

    for wh in working_hours_list:
        curr_start = wh.start_time
        while curr_start < wh.end_time:
            curr_end = add_minutes_to_time(curr_start, slot_duration)
            if curr_end > wh.end_time:
                break

            # Check collision with active appointments
            collided = False
            slot_status = "AVAILABLE"
            for appt in active_appts:
                # Check overlap
                if not (curr_end <= appt.start_time or curr_start >= appt.end_time):
                    collided = True
                    slot_status = appt.status.value
                    break

            if not collided:
                slots.append(SlotSchema(start_time=curr_start, end_time=curr_end, status="AVAILABLE"))

            curr_start = curr_end

    return AvailabilityResponse(
        doctor_id=doctor_id,
        appointment_date=target_date,
        slot_duration_minutes=doctor.slot_duration_minutes,
        is_on_leave=False,
        slots=slots,
    )


async def validate_requested_slot(
    db: AsyncSession,
    doctor_id: uuid.UUID,
    target_date: Union[date, str],
    start_time: Union[time, str],
    end_time: Union[time, str]
) -> bool:
    """Strictly validate that requested (start_time, end_time) matches working hours & availability.
    - If doctor on leave or slot misaligned / out of bounds -> HTTP 400 Bad Request (INVALID_SLOT).
    - If slot matches valid working hours BUT is occupied/held/booked -> HTTP 409 Conflict (SLOT_UNAVAILABLE).
    """
    target_date = parse_date(target_date)
    start_time = parse_time(start_time)
    end_time = parse_time(end_time)

    # 1. Fetch doctor & working hours
    doctor_result = await db.execute(select(DoctorProfile).where(DoctorProfile.id == doctor_id))
    doctor = doctor_result.scalars().first()
    if not doctor or not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "DOCTOR_NOT_FOUND", "message": "Doctor profile not found or inactive."}},
        )

    leave_result = await db.execute(
        select(DoctorLeave).where(
            DoctorLeave.doctor_id == doctor_id,
            DoctorLeave.leave_date == target_date
        )
    )
    if leave_result.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_SLOT", "message": "Doctor is on leave on the selected date."}},
        )

    wh_result = await db.execute(
        select(DoctorWorkingHours).where(
            DoctorWorkingHours.doctor_id == doctor_id,
            DoctorWorkingHours.day_of_week == target_date.weekday()
        )
    )
    working_hours_list = wh_result.scalars().all()
    if not working_hours_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_SLOT", "message": "Doctor does not work on the selected day of week."}},
        )

    # Verify requested start_time and end_time match a working hours discrete slot boundary
    valid_boundary = False
    slot_duration = doctor.slot_duration_minutes
    for wh in working_hours_list:
        curr_start = wh.start_time
        while curr_start < wh.end_time:
            curr_end = add_minutes_to_time(curr_start, slot_duration)
            if curr_end > wh.end_time:
                break
            if curr_start == start_time and curr_end == end_time:
                valid_boundary = True
                break
            curr_start = curr_end
        if valid_boundary:
            break

    if not valid_boundary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_SLOT", "message": "The requested slot does not match doctor working hours or slot duration."}},
        )

    # Slot boundary is valid! Check if it is currently occupied/held/booked by an active appointment.
    now_utc = get_now_utc()
    appt_result = await db.execute(
        select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == target_date,
            Appointment.status.in_([AppointmentStatus.HELD, AppointmentStatus.BOOKED])
        )
    )
    for appt in appt_result.scalars().all():
        if not (end_time <= appt.start_time or start_time >= appt.end_time):
            if appt.status == AppointmentStatus.BOOKED:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"error": {"code": "SLOT_UNAVAILABLE", "message": "The selected slot is already booked by another patient."}},
                )
            elif appt.status == AppointmentStatus.HELD and appt.hold_expires_at:
                exp_time = appt.hold_expires_at
                if exp_time.tzinfo is None:
                    exp_time = exp_time.replace(tzinfo=timezone.utc)
                if exp_time > now_utc:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={"error": {"code": "SLOT_UNAVAILABLE", "message": "The selected slot is currently held by another patient."}},
                    )

    return True
