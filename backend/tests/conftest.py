import pytest
import pytest_asyncio
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.main import app

# Shared In-Memory SQLite Engine for Async Testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 10},
    poolclass=StaticPool,
    echo=False
)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def prepare_database():
    """Build fresh database tables for each test function."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function", autouse=True)
def mock_worker_tasks():
    """Mock Celery task .delay dispatch to prevent background task workers from opening detached SQLite connections."""
    with patch("app.services.booking_service.generate_pre_visit_summary_task.delay"), \
         patch("app.services.booking_service.send_booking_email_task.delay"), \
         patch("app.services.booking_service.sync_google_calendar_task.delay"), \
         patch("app.services.booking_service.send_cancellation_email_task.delay"), \
         patch("app.services.leave_service.send_cancellation_email_task.delay"), \
         patch("app.services.leave_service.sync_google_calendar_task.delay"):
        yield


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Provides a fresh dedicated transactional database session for direct unit tests."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def async_client():
    """Provides an AsyncClient where each HTTP request opens and closes its own AsyncSession."""
    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()
