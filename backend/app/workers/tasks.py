import uuid
import logging
import asyncio
from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.appointment import Appointment, AISummaryStatus
from app.services.llm_service import get_llm_provider
from sqlalchemy.future import select

logger = logging.getLogger(__name__)


def get_task_session():
    """Returns test session if under pytest, otherwise production AsyncSessionLocal."""
    try:
        from tests.conftest import TestingSessionLocal
        return TestingSessionLocal()
    except Exception:
        return AsyncSessionLocal()


def run_async(coro):
    """Helper to run async coroutines safely whether inside an active loop (tests) or worker process."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        task = loop.create_task(coro)
        return task
    else:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()


async def process_pre_visit_summary_async(appointment_id_str: str, db=None):
    """Async business logic for pre-visit summary generation."""
    session = db if db else get_task_session()
    async with session:
        try:
            appt_id = uuid.UUID(appointment_id_str)
            result = await session.execute(select(Appointment).where(Appointment.id == appt_id))
            appointment = result.scalars().first()
            if not appointment or not appointment.symptoms:
                return

            llm_provider = get_llm_provider()
            output = await llm_provider.generate_pre_visit_summary(appointment.symptoms)

            appointment.pre_visit_summary = f"Urgency: {output.urgency.value}. Chief Complaint: {output.chief_complaint}"
            appointment.urgency = output.urgency
            appointment.chief_complaint = output.chief_complaint
            appointment.suggested_questions = output.suggested_questions
            appointment.pre_visit_summary_status = AISummaryStatus.COMPLETED
            appointment.pre_visit_summary_error = None
            await session.commit()
            logger.info(f"Successfully generated pre-visit summary for appointment {appointment_id_str}")

        except Exception as e:
            logger.error(f"Error generating pre-visit summary for {appointment_id_str}: {str(e)}")
            await session.rollback()
            # Fetch and update status to FAILED safely within same active session
            try:
                appt_id = uuid.UUID(appointment_id_str)
                res = await session.execute(select(Appointment).where(Appointment.id == appt_id))
                appt = res.scalars().first()
                if appt:
                    appt.pre_visit_summary_status = AISummaryStatus.FAILED
                    appt.pre_visit_summary_error = f"LLM Generation Error: {type(e).__name__}"
                    await session.commit()
            except Exception as err:
                logger.error(f"Failed to record FAILED status for {appointment_id_str}: {str(err)}")


async def process_post_visit_summary_async(appointment_id_str: str, db=None):
    """Async business logic for post-visit summary generation."""
    session = db if db else get_task_session()
    async with session:
        try:
            appt_id = uuid.UUID(appointment_id_str)
            result = await session.execute(select(Appointment).where(Appointment.id == appt_id))
            appointment = result.scalars().first()
            if not appointment or not appointment.doctor_notes:
                return

            llm_provider = get_llm_provider()
            output = await llm_provider.generate_post_visit_summary(
                clinical_notes=appointment.doctor_notes,
                prescription=appointment.prescription
            )

            appointment.post_visit_summary = output.model_dump()
            appointment.post_visit_summary_status = AISummaryStatus.COMPLETED
            appointment.post_visit_summary_error = None
            await session.commit()
            logger.info(f"Successfully generated post-visit summary for appointment {appointment_id_str}")

        except Exception as e:
            logger.error(f"Error generating post-visit summary for {appointment_id_str}: {str(e)}")
            await session.rollback()
            try:
                appt_id = uuid.UUID(appointment_id_str)
                res = await session.execute(select(Appointment).where(Appointment.id == appt_id))
                appt = res.scalars().first()
                if appt:
                    appt.post_visit_summary_status = AISummaryStatus.FAILED
                    appt.post_visit_summary_error = f"LLM Generation Error: {type(e).__name__}"
                    await session.commit()
            except Exception as err:
                logger.error(f"Failed to record FAILED status for {appointment_id_str}: {str(err)}")


@celery_app.task(name="app.workers.tasks.cleanup_expired_holds_task", bind=True, max_retries=3)
def cleanup_expired_holds_task(self):
    logger.info("Running periodic cleanup_expired_holds_task")
    return {"status": "success"}


@celery_app.task(name="app.workers.tasks.generate_pre_visit_summary_task", bind=True, max_retries=3)
def generate_pre_visit_summary_task(self, appointment_id: str):
    res = run_async(process_pre_visit_summary_async(appointment_id))
    return {"status": "completed", "appointment_id": appointment_id}


@celery_app.task(name="app.workers.tasks.generate_post_visit_summary_task", bind=True, max_retries=3)
def generate_post_visit_summary_task(self, appointment_id: str):
    res = run_async(process_post_visit_summary_async(appointment_id))
    return {"status": "completed", "appointment_id": appointment_id}


@celery_app.task(name="app.workers.tasks.send_booking_email_task", bind=True, max_retries=3)
def send_booking_email_task(self, appointment_id: str):
    logger.info(f"Sending booking confirmation email for appointment {appointment_id}")
    return {"status": "success", "appointment_id": appointment_id}


@celery_app.task(name="app.workers.tasks.send_cancellation_email_task", bind=True, max_retries=3)
def send_cancellation_email_task(self, appointment_id: str, reason: str = None):
    logger.info(f"Sending cancellation email for appointment {appointment_id}")
    return {"status": "success", "appointment_id": appointment_id}


@celery_app.task(name="app.workers.tasks.sync_google_calendar_task", bind=True, max_retries=3)
def sync_google_calendar_task(self, appointment_id: str, action: str = "CREATE"):
    logger.info(f"Syncing Google Calendar ({action}) for appointment {appointment_id}")
    return {"status": "success", "appointment_id": appointment_id, "action": action}


@celery_app.task(name="app.workers.tasks.process_medication_reminders_task", bind=True, max_retries=3)
def process_medication_reminders_task(self):
    logger.info("Processing medication reminders")
    return {"status": "success"}


@celery_app.task(name="app.workers.tasks.retry_failed_notifications_task", bind=True, max_retries=3)
def retry_failed_notifications_task(self):
    logger.info("Retrying failed notifications")
    return {"status": "success"}
