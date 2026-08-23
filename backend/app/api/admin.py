import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import require_admin
from app.schemas.doctor import (
    CreateDoctorRequest, UpdateDoctorRequest, DoctorResponse, AddLeaveRequest,
    LeaveSchema, WorkingHoursSchema
)
from app.services.doctor_service import (
    create_doctor_profile, get_doctor_by_id, list_doctors, update_doctor_profile,
    set_doctor_working_hours, add_doctor_leave, revoke_doctor_leave
)
from app.api.doctors import serialize_doctor

router = APIRouter(prefix="/api/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


@router.post("/doctors", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_doctor(req: CreateDoctorRequest, db: AsyncSession = Depends(get_db)):
    """Admin endpoint to create a new doctor user profile and schedule."""
    doctor = await create_doctor_profile(db, req)
    return serialize_doctor(doctor)


@router.get("/doctors", response_model=List[DoctorResponse])
async def admin_list_doctors(db: AsyncSession = Depends(get_db)):
    """Admin endpoint to list all doctors (active and inactive)."""
    doctors = await list_doctors(db, active_only=False)
    return [serialize_doctor(d) for d in doctors]


@router.patch("/doctors/{doctor_id}", response_model=DoctorResponse)
async def admin_update_doctor(
    doctor_id: uuid.UUID,
    req: UpdateDoctorRequest,
    db: AsyncSession = Depends(get_db)
):
    """Admin endpoint to edit doctor profile or deactivate profile."""
    doctor = await update_doctor_profile(db, doctor_id, req)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "DOCTOR_NOT_FOUND", "message": "Doctor profile not found."}},
        )
    return serialize_doctor(doctor)


@router.put("/doctors/{doctor_id}/working-hours", response_model=DoctorResponse)
async def admin_update_working_hours(
    doctor_id: uuid.UUID,
    working_hours: List[WorkingHoursSchema],
    db: AsyncSession = Depends(get_db)
):
    """Admin endpoint to configure weekly working hours."""
    doctor = await get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "DOCTOR_NOT_FOUND", "message": "Doctor profile not found."}},
        )
    updated = await set_doctor_working_hours(db, doctor_id, working_hours)
    return serialize_doctor(updated)


@router.post("/doctors/{doctor_id}/leave", response_model=LeaveSchema, status_code=status.HTTP_201_CREATED)
async def admin_add_leave(
    doctor_id: uuid.UUID,
    req: AddLeaveRequest,
    db: AsyncSession = Depends(get_db)
):
    """Admin endpoint to add leave day for doctor."""
    doctor = await get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "DOCTOR_NOT_FOUND", "message": "Doctor profile not found."}},
        )
    # Check duplicate leave date
    for l in doctor.leaves:
        if l.leave_date == req.leave_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "LEAVE_EXISTS", "message": "Doctor is already on leave for this date."}},
            )
    leave = await add_doctor_leave(db, doctor_id, req)
    return leave


@router.delete("/doctors/leave/{leave_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_revoke_leave(leave_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Admin endpoint to revoke a leave date."""
    success = await revoke_doctor_leave(db, leave_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "LEAVE_NOT_FOUND", "message": "Leave entry not found."}},
        )
