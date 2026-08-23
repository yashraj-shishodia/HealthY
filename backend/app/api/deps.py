import uuid
from typing import Callable, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.services.auth_service import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency to extract and validate the authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": {"code": "UNAUTHENTICATED", "message": "Could not validate credentials."}},
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception
    
    user_id_str: str = payload.get("sub")
    if not user_id_str:
        raise credentials_exception
    
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception
    
    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise credentials_exception
    
    return user


def require_roles(allowed_roles: List[UserRole]) -> Callable:
    """Dependency generator enforcing server-side Role-Based Access Control (RBAC)."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "FORBIDDEN", "message": "Forbidden. Insufficient role permissions."}},
            )
        return current_user
    return role_checker


# Shortcuts for single role dependencies
require_patient = require_roles([UserRole.PATIENT])
require_doctor = require_roles([UserRole.DOCTOR])
require_admin = require_roles([UserRole.ADMIN])
require_patient_or_doctor = require_roles([UserRole.PATIENT, UserRole.DOCTOR])
