import uuid
from datetime import date, time, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.appointment import (
    AppointmentStatus, AISummaryStatus, UrgencyLevel,
    CalendarSyncStatus, OverallCalendarSyncStatus
)


class HoldSlotRequest(BaseModel):
    doctor_id: uuid.UUID
    appointment_date: date
    start_time: time
    end_time: time


class ConfirmBookingRequest(BaseModel):
    appointment_id: Optional[uuid.UUID] = None
    hold_id: Optional[uuid.UUID] = None
    doctor_id: Optional[uuid.UUID] = None
    appointment_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    symptoms: str = Field(..., min_length=1, max_length=2000)


class RescheduleAppointmentRequest(BaseModel):
    new_date: date
    new_start_time: time
    new_end_time: time


class CancelAppointmentRequest(BaseModel):
    reason: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    patient_id: uuid.UUID
    appointment_date: date
    start_time: time
    end_time: time
    status: AppointmentStatus
    hold_expires_at: Optional[datetime] = None

    # Symptoms & Pre-visit
    symptoms: Optional[str] = None
    pre_visit_summary: Optional[str] = None
    pre_visit_summary_status: AISummaryStatus
    urgency: Optional[UrgencyLevel] = None
    chief_complaint: Optional[str] = None
    suggested_questions: Optional[List[str]] = None

    # Clinical & Post-visit
    doctor_notes: Optional[str] = None
    prescription: Optional[str] = None
    post_visit_summary: Optional[dict] = None
    post_visit_summary_status: AISummaryStatus

    # Calendar sync status
    patient_calendar_sync_status: CalendarSyncStatus
    doctor_calendar_sync_status: CalendarSyncStatus
    overall_calendar_sync_status: OverallCalendarSyncStatus

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
