import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.core.database import Base, get_session
from app.core.config import Settings


# Override settings for testing
class TestSettings(Settings):
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    DEBUG: bool = True
    SECRET_KEY: str = "test-secret-key-for-testing-only"
    DEMO_MODE: bool = True


test_settings = TestSettings()


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    # Override get_settings dependency
    from app.core.config import get_settings as original_get_settings
    import app.core.config as config_module

    config_module.get_settings = lambda: test_settings

    app = create_app()
    yield app


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(async_engine):
    """Create database session for testing."""
    async_session_maker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(app, session):
    """Create test client with overridden database session."""
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def sample_policy_data():
    return {
        "name": "test-policy",
        "description": "Test policy for egress",
        "action": "allow",
        "destination_host": "api.example.com",
        "destination_port": 443,
        "protocol": "tcp",
        "priority": 10,
        "enabled": True,
    }


@pytest.fixture
def sample_sandbox_data():
    return {
        "name": "test-sandbox",
        "policy_id": None,
        "config": '{"memory": "512m", "cpu": "0.5"}',
    }