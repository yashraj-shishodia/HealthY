import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.calendar_service import GoogleCalendarService

router = APIRouter(prefix="/api/calendar", tags=["Google Calendar Integration"])


@router.get("/connect")
async def connect_calendar(current_user: User = Depends(get_current_user)):
    """Generate Google OAuth 2.0 authorization consent URL for user."""
    auth_url = GoogleCalendarService.get_oauth_authorization_url(current_user.id)
    return {"auth_url": auth_url}


@router.get("/callback")
async def calendar_oauth_callback(
    code: str = Query(..., description="Google OAuth authorization code"),
    state: str = Query(..., description="State containing user ID"),
    db: AsyncSession = Depends(get_db)
):
    """Callback endpoint handling Google OAuth code exchange."""
    try:
        user_id = uuid.UUID(state)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_STATE", "message": "Invalid state parameter."}},
        )

    # Mock token exchange for demonstration / testing environment
    access_token = f"mock_access_token_{code[:10]}"
    refresh_token = f"mock_refresh_token_{code[:10]}"
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    conn = await GoogleCalendarService.connect_user_calendar(
        db=db,
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
    )
    return {"status": "success", "message": "Google Calendar connected successfully.", "provider": conn.provider}


@router.get("/status")
async def get_calendar_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check whether current user has connected their Google Calendar."""
    conn = await GoogleCalendarService.get_calendar_connection(db, current_user.id)
    return {
        "is_connected": conn is not None,
        "provider": conn.provider if conn else None,
        "expires_at": conn.expires_at.isoformat() if conn and conn.expires_at else None,
    }


@router.delete("/disconnect")
async def disconnect_calendar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect Google Calendar for current user."""
    success = await GoogleCalendarService.disconnect_user_calendar(db, current_user.id)
    return {"status": "success", "disconnected": success}
