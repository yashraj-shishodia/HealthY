import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User, UserRole
from app.core.security import get_password_hash, verify_password
from app.schemas.auth import RegisterRequest


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Retrieve a user record by email address."""
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    """Retrieve a user record by primary key UUID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def create_user(db: AsyncSession, req: RegisterRequest) -> User:
    """Create a new user with hashed password."""
    user = User(
        id=uuid.uuid4(),
        email=req.email.lower(),
        password_hash=get_password_hash(req.password),
        full_name=req.full_name,
        role=req.role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Verify email and password credentials."""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user
