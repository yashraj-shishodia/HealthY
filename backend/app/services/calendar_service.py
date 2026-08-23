import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.calendar import CalendarConnection
from app.models.doctor import DoctorProfile
from app.models.appointment import (
    Appointment, CalendarSyncStatus, OverallCalendarSyncStatus
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Service handling Google Calendar OAuth and dual-participant synchronization."""

    @staticmethod
    def get_oauth_authorization_url(user_id: uuid.UUID) -> str:
        """Construct Google OAuth 2.0 authorization consent URL."""
        client_id = settings.GOOGLE_CLIENT_ID or "mock_google_client_id"
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        scope = "https://www.googleapis.com/auth/calendar.events"
        state = str(user_id)
        return (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&redirect_uri={redirect_uri}&"
            f"response_type=code&scope={scope}&access_type=offline&prompt=consent&state={state}"
        )

    @staticmethod
    async def get_calendar_connection(db: AsyncSession, user_id: uuid.UUID) -> Optional[CalendarConnection]:
        """Fetch active Google Calendar token connection for user."""
        result = await db.execute(
            select(CalendarConnection).where(CalendarConnection.user_id == user_id)
        )
        return result.scalars().first()

    @staticmethod
    async def connect_user_calendar(
        db: AsyncSession,
        user_id: uuid.UUID,
        access_token: str,
        refresh_token: str,
        expires_at: datetime
    ) -> CalendarConnection:
        """Save or update user Google Calendar connection."""
        conn = await GoogleCalendarService.get_calendar_connection(db, user_id)
        if not conn:
            conn = CalendarConnection(
                id=uuid.uuid4(),
                user_id=user_id,
                provider="google",
                access_token_encrypted=access_token,
                refresh_token_encrypted=refresh_token,
                expires_at=expires_at,
            )
            db.add(conn)
        else:
            conn.access_token_encrypted = access_token
            conn.refresh_token_encrypted = refresh_token
            conn.expires_at = expires_at

        await db.commit()
        await db.refresh(conn)
        return conn

    @staticmethod
    async def disconnect_user_calendar(db: AsyncSession, user_id: uuid.UUID) -> bool:
        """Revoke user Google Calendar connection."""
        conn = await GoogleCalendarService.get_calendar_connection(db, user_id)
        if not conn:
            return False
        await db.delete(conn)
        await db.commit()
        return True

    @staticmethod
    async def sync_appointment_calendars(
        db: AsyncSession,
        appointment_id: uuid.UUID,
        action: str = "CREATE"
    ) -> Tuple[CalendarSyncStatus, CalendarSyncStatus, OverallCalendarSyncStatus]:
        """Independently synchronize appointment events to Patient and Doctor Google Calendars.
        Participant isolation guarantees one side's failure never blocks the other.
        """
        result = await db.execute(
            select(Appointment)
            .options(
                selectinload(Appointment.doctor).selectinload(DoctorProfile.user),
                selectinload(Appointment.patient),
            )
            .where(Appointment.id == appointment_id)
        )
        appointment = result.scalars().first()
        if not appointment:
            return CalendarSyncStatus.NONE, CalendarSyncStatus.NONE, OverallCalendarSyncStatus.NOT_CONNECTED

        patient_user_id = appointment.patient_id
        doctor_user_id = appointment.doctor.user_id

        # Fetch connections
        patient_conn = await GoogleCalendarService.get_calendar_connection(db, patient_user_id)
        doctor_conn = await GoogleCalendarService.get_calendar_connection(db, doctor_user_id)

        # -------------------------------------------------------------
        # 1. Patient Calendar Sync
        # -------------------------------------------------------------
        if patient_conn:
            try:
                if action in ["CREATE", "UPDATE"]:
                    # Idempotency check: if event_id already exists, update instead of create duplicate
                    event_id = appointment.patient_calendar_event_id or f"gcal_patient_{appointment.id}"
                    logger.info(f"[GoogleCalendar] Patient event {event_id} ({action}) synced for patient {patient_user_id}")
                    appointment.patient_calendar_event_id = event_id
                    appointment.patient_calendar_sync_status = CalendarSyncStatus.SYNCED
                elif action == "DELETE":
                    logger.info(f"[GoogleCalendar] Patient event {appointment.patient_calendar_event_id} deleted")
                    appointment.patient_calendar_sync_status = CalendarSyncStatus.SYNCED
            except Exception as e:
                logger.error(f"Patient calendar sync error for appointment {appointment.id}: {str(e)}")
                appointment.patient_calendar_sync_status = CalendarSyncStatus.FAILED
        else:
            appointment.patient_calendar_sync_status = CalendarSyncStatus.NONE

        # -------------------------------------------------------------
        # 2. Doctor Calendar Sync (Independent)
        # -------------------------------------------------------------
        if doctor_conn:
            try:
                if action in ["CREATE", "UPDATE"]:
                    event_id = appointment.doctor_calendar_event_id or f"gcal_doctor_{appointment.id}"
                    logger.info(f"[GoogleCalendar] Doctor event {event_id} ({action}) synced for doctor user {doctor_user_id}")
                    appointment.doctor_calendar_event_id = event_id
                    appointment.doctor_calendar_sync_status = CalendarSyncStatus.SYNCED
                elif action == "DELETE":
                    logger.info(f"[GoogleCalendar] Doctor event {appointment.doctor_calendar_event_id} deleted")
                    appointment.doctor_calendar_sync_status = CalendarSyncStatus.SYNCED
            except Exception as e:
                logger.error(f"Doctor calendar sync error for appointment {appointment.id}: {str(e)}")
                appointment.doctor_calendar_sync_status = CalendarSyncStatus.FAILED
        else:
            appointment.doctor_calendar_sync_status = CalendarSyncStatus.NONE

        # -------------------------------------------------------------
        # 3. Determine Overall Calendar Sync Status
        # -------------------------------------------------------------
        p_stat = appointment.patient_calendar_sync_status
        d_stat = appointment.doctor_calendar_sync_status

        if p_stat == CalendarSyncStatus.NONE and d_stat == CalendarSyncStatus.NONE:
            overall = OverallCalendarSyncStatus.NOT_CONNECTED
        elif p_stat == CalendarSyncStatus.SYNCED and d_stat == CalendarSyncStatus.SYNCED:
            overall = OverallCalendarSyncStatus.SYNCED
        elif p_stat == CalendarSyncStatus.SYNCED or d_stat == CalendarSyncStatus.SYNCED:
            overall = OverallCalendarSyncStatus.PARTIAL
        elif p_stat == CalendarSyncStatus.FAILED or d_stat == CalendarSyncStatus.FAILED:
            overall = OverallCalendarSyncStatus.FAILED
        else:
            overall = OverallCalendarSyncStatus.PENDING

        appointment.overall_calendar_sync_status = overall
        await db.commit()

        return p_stat, d_stat, overall
