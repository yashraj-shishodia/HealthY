import uuid
from datetime import date
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.user import User, UserRole
from app.models.doctor import DoctorProfile, DoctorWorkingHours, DoctorLeave
from app.core.security import get_password_hash
from app.schemas.doctor import CreateDoctorRequest, UpdateDoctorRequest, AddLeaveRequest, WorkingHoursSchema


async def create_doctor_profile(db: AsyncSession, req: CreateDoctorRequest) -> DoctorProfile:
    """Admin service to create a doctor user profile and initial working hours."""
    user = User(
        id=uuid.uuid4(),
        email=req.email.lower(),
        password_hash=get_password_hash(req.password),
        full_name=req.full_name,
        role=UserRole.DOCTOR,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    doctor = DoctorProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        specialisation=req.specialisation,
        bio=req.bio,
        slot_duration_minutes=req.slot_duration_minutes,
        timezone=req.timezone,
        is_active=True,
    )
    db.add(doctor)
    await db.flush()

    for wh in req.working_hours:
        working_hour = DoctorWorkingHours(
            id=uuid.uuid4(),
            doctor_id=doctor.id,
            day_of_week=wh.day_of_week,
            start_time=wh.start_time,
            end_time=wh.end_time,
        )
        db.add(working_hour)

    await db.commit()
    return await get_doctor_by_id(db, doctor.id)


async def get_doctor_by_id(db: AsyncSession, doctor_id: uuid.UUID) -> Optional[DoctorProfile]:
    """Fetch doctor details by doctor profile ID."""
    result = await db.execute(
        select(DoctorProfile)
        .options(
            selectinload(DoctorProfile.user),
            selectinload(DoctorProfile.working_hours),
            selectinload(DoctorProfile.leaves),
        )
        .where(DoctorProfile.id == doctor_id)
    )
    return result.scalars().first()


async def list_doctors(
    db: AsyncSession,
    specialisation: Optional[str] = None,
    active_only: bool = True
) -> List[DoctorProfile]:
    """List and filter doctors by specialization."""
    query = select(DoctorProfile).options(
        selectinload(DoctorProfile.user),
        selectinload(DoctorProfile.working_hours),
        selectinload(DoctorProfile.leaves),
    )
    if active_only:
        query = query.where(DoctorProfile.is_active == True)
    if specialisation:
        query = query.where(DoctorProfile.specialisation.ilike(f"%{specialisation}%"))

    result = await db.execute(query)
    return result.scalars().all()


async def update_doctor_profile(
    db: AsyncSession,
    doctor_id: uuid.UUID,
    req: UpdateDoctorRequest
) -> Optional[DoctorProfile]:
    """Update doctor attributes."""
    doctor = await get_doctor_by_id(db, doctor_id)
    if not doctor:
        return None

    if req.specialisation is not None:
        doctor.specialisation = req.specialisation
    if req.bio is not None:
        doctor.bio = req.bio
    if req.slot_duration_minutes is not None:
        doctor.slot_duration_minutes = req.slot_duration_minutes
    if req.timezone is not None:
        doctor.timezone = req.timezone
    if req.is_active is not None:
        doctor.is_active = req.is_active

    await db.commit()
    return await get_doctor_by_id(db, doctor_id)


async def set_doctor_working_hours(
    db: AsyncSession,
    doctor_id: uuid.UUID,
    working_hours: List[WorkingHoursSchema]
) -> DoctorProfile:
    """Replace doctor working hours schedule."""
    # Delete existing
    result = await db.execute(select(DoctorWorkingHours).where(DoctorWorkingHours.doctor_id == doctor_id))
    existing = result.scalars().all()
    for wh in existing:
        await db.delete(wh)

    for wh in working_hours:
        new_wh = DoctorWorkingHours(
            id=uuid.uuid4(),
            doctor_id=doctor_id,
            day_of_week=wh.day_of_week,
            start_time=wh.start_time,
            end_time=wh.end_time,
        )
        db.add(new_wh)

    await db.commit()
    return await get_doctor_by_id(db, doctor_id)


async def add_doctor_leave(
    db: AsyncSession,
    doctor_id: uuid.UUID,
    req: AddLeaveRequest
) -> DoctorLeave:
    """Add a leave date for a doctor."""
    leave = DoctorLeave(
        id=uuid.uuid4(),
        doctor_id=doctor_id,
        leave_date=req.leave_date,
        reason=req.reason,
    )
    db.add(leave)
    await db.commit()
    await db.refresh(leave)
    return leave


async def revoke_doctor_leave(db: AsyncSession, leave_id: uuid.UUID) -> bool:
    """Delete a doctor leave entry."""
    result = await db.execute(select(DoctorLeave).where(DoctorLeave.id == leave_id))
    leave = result.scalars().first()
    if not leave:
        return False
    await db.delete(leave)
    await db.commit()
    return True
