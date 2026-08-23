import uuid
from datetime import time, date
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class WorkingHoursSchema(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: time
    end_time: time

    model_config = ConfigDict(from_attributes=True)


class LeaveSchema(BaseModel):
    id: uuid.UUID
    leave_date: date
    reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CreateDoctorRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=250)
    specialisation: str = Field(..., min_length=2, max_length=100)
    bio: Optional[str] = None
    slot_duration_minutes: int = Field(30, ge=10, le=240)
    timezone: str = "UTC"
    working_hours: List[WorkingHoursSchema] = []


class UpdateDoctorRequest(BaseModel):
    specialisation: Optional[str] = None
    bio: Optional[str] = None
    slot_duration_minutes: Optional[int] = Field(None, ge=10, le=240)
    timezone: Optional[str] = None
    is_active: Optional[bool] = None


class AddLeaveRequest(BaseModel):
    leave_date: date
    reason: Optional[str] = None


class DoctorResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr
    full_name: str
    specialisation: str
    bio: Optional[str] = None
    slot_duration_minutes: int
    timezone: str
    is_active: bool
    working_hours: List[WorkingHoursSchema] = []
    leaves: List[LeaveSchema] = []

    model_config = ConfigDict(from_attributes=True)
