import uuid
from datetime import date
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.doctor import DoctorLeave
from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.doctor import AddLeaveRequest
from app.workers.tasks import send_cancellation_email_task, sync_google_calendar_task


async def add_doctor_leave_with_cascade(
    db: AsyncSession,
    doctor_id: uuid.UUID,
    req: AddLeaveRequest
) -> Tuple[DoctorLeave, List[Appointment]]:
    """Add doctor leave date and transition all affected active appointments to CANCELLED_BY_LEAVE."""
    # 1. Create leave entry
    leave = DoctorLeave(
        id=uuid.uuid4(),
        doctor_id=doctor_id,
        leave_date=req.leave_date,
        reason=req.reason,
    )
    db.add(leave)

    # 2. Lock affected appointments on date
    result = await db.execute(
        select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == req.leave_date,
            Appointment.status.in_([AppointmentStatus.HELD, AppointmentStatus.BOOKED])
        ).with_for_update()
    )
    affected_appointments = result.scalars().all()

    for appt in affected_appointments:
        appt.status = AppointmentStatus.CANCELLED_BY_LEAVE

    await db.commit()
    await db.refresh(leave)

    # 3. Post-commit dispatch: notifications and calendar removals
    for appt in affected_appointments:
        try:
            send_cancellation_email_task.delay(str(appt.id), f"Doctor on leave: {req.reason or 'Personal Leave'}")
            sync_google_calendar_task.delay(str(appt.id), "DELETE")
        except Exception:
            pass

    return leave, affected_appointments
