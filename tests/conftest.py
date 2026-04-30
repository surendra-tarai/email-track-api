import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.database import get_db


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def mock_db():
    db = MagicMock()
    db.tracking_links = MagicMock()
    db.click_events = MagicMock()
    return db


@pytest_asyncio.fixture
async def mock_redis():
    redis = AsyncMock()
    redis.enqueue_job = AsyncMock(return_value=None)
    return redis


@pytest_asyncio.fixture
async def client(mock_db, mock_redis):
    app.state.redis = mock_redis

    original_get_db = get_db

    import app.database as db_module
    db_module._client = MagicMock()
    db_module._client.__getitem__ = MagicMock(return_value=mock_db)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
