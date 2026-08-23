import uuid
from datetime import date, time
from typing import List
from pydantic import BaseModel, ConfigDict


class SlotSchema(BaseModel):
    start_time: time
    end_time: time
    status: str = "AVAILABLE"  # AVAILABLE, HELD, BOOKED

    model_config = ConfigDict(from_attributes=True)


class AvailabilityResponse(BaseModel):
    doctor_id: uuid.UUID
    appointment_date: date
    slot_duration_minutes: int
    is_on_leave: bool
    slots: List[SlotSchema]

    model_config = ConfigDict(from_attributes=True)
