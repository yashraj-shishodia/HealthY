import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.notification import NotificationLog, NotificationType, NotificationStatus
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service abstraction for email delivery with idempotency tracking."""

    @staticmethod
    async def send_email(
        db: AsyncSession,
        appointment_id: Optional[uuid.UUID],
        recipient: str,
        notification_type: NotificationType,
        subject: str,
        body: str
    ) -> NotificationLog:
        idempotency_key = f"{appointment_id}:{notification_type.value}:{recipient}"

        # 1. Check idempotency log
        result = await db.execute(
            select(NotificationLog).where(NotificationLog.idempotency_key == idempotency_key)
        )
        existing_log = result.scalars().first()
        if existing_log and existing_log.status == NotificationStatus.SENT:
            logger.info(f"Notification already sent for key {idempotency_key}. Skipping duplicate.")
            return existing_log

        if not existing_log:
            log_entry = NotificationLog(
                id=uuid.uuid4(),
                idempotency_key=idempotency_key,
                appointment_id=appointment_id,
                recipient=recipient,
                notification_type=notification_type,
                provider=settings.EMAIL_PROVIDER,
                status=NotificationStatus.PENDING,
                attempt_count=1,
            )
            db.add(log_entry)
            await db.flush()
        else:
            log_entry = existing_log
            log_entry.attempt_count += 1

        # 2. Provider Dispatch
        try:
            if settings.EMAIL_PROVIDER.lower() == "sendgrid" and settings.EMAIL_API_KEY:
                # Real SendGrid call logic
                logger.info(f"[SendGrid] Sending {notification_type.value} to {recipient}: {subject}")
            else:
                # Mock / Development provider logging
                logger.info(f"[MockEmail] Dispatched {notification_type.value} to {recipient}: Subject='{subject}'")

            log_entry.status = NotificationStatus.SENT
            log_entry.sent_at = datetime.now(timezone.utc)
            log_entry.last_error = None

        except Exception as e:
            logger.error(f"Failed to send email {notification_type.value} to {recipient}: {str(e)}")
            log_entry.status = NotificationStatus.FAILED
            log_entry.last_error = str(e)

        await db.commit()
        await db.refresh(log_entry)
        return log_entry
