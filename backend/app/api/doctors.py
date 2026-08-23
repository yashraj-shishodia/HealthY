import uuid
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.doctor import DoctorResponse
from app.schemas.availability import AvailabilityResponse
from app.services.doctor_service import list_doctors, get_doctor_by_id
from app.services.availability_service import get_doctor_availability

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])


def serialize_doctor(doctor) -> DoctorResponse:
    """Helper to convert DoctorProfile model with loaded relationships to DoctorResponse schema."""
    return DoctorResponse(
        id=doctor.id,
        user_id=doctor.user_id,
        email=doctor.user.email,
        full_name=doctor.user.full_name,
        specialisation=doctor.specialisation,
        bio=doctor.bio,
        slot_duration_minutes=doctor.slot_duration_minutes,
        timezone=doctor.timezone,
        is_active=doctor.is_active,
        working_hours=[
            {
                "day_of_week": wh.day_of_week,
                "start_time": wh.start_time,
                "end_time": wh.end_time,
            }
            for wh in doctor.working_hours
        ],
        leaves=[
            {
                "id": l.id,
                "leave_date": l.leave_date,
                "reason": l.reason,
            }
            for l in doctor.leaves
        ],
    )


@router.get("", response_model=List[DoctorResponse])
async def get_doctors(
    specialisation: Optional[str] = Query(None, description="Filter doctors by specialisation"),
    db: AsyncSession = Depends(get_db),
):
    """Public / Patient discovery endpoint to search and filter doctors."""
    doctors = await list_doctors(db, specialisation=specialisation, active_only=True)
    return [serialize_doctor(d) for d in doctors]


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor_detail(doctor_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Fetch details, working hours, and leave schedule for a specific doctor."""
    doctor = await get_doctor_by_id(db, doctor_id)
    if not doctor or not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "DOCTOR_NOT_FOUND", "message": "Doctor not found or inactive."}},
        )
    return serialize_doctor(doctor)


@router.get("/{doctor_id}/availability", response_model=AvailabilityResponse)
async def get_availability(
    doctor_id: uuid.UUID,
    date_str: date = Query(..., alias="date", description="Target availability date YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    """Computes valid discrete available slots for a doctor on a target date."""
    return await get_doctor_availability(db, doctor_id, date_str)
