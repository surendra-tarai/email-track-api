import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, IndexModel
from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


async def connect_db() -> None:
    global _client
    _client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    await _client.admin.command("ping")
    logger.info("Connected to MongoDB")
    await _create_indexes()


async def close_db() -> None:
    if _client:
        _client.close()
        logger.info("Disconnected from MongoDB")


def get_db() -> AsyncIOMotorDatabase:
    return _client[settings.mongodb_db]


async def _create_indexes() -> None:
    db = get_db()

    await db.tracking_links.create_indexes([
        IndexModel([("link_id", ASCENDING)], unique=True),
        IndexModel([("short_code", ASCENDING)], unique=True),
        IndexModel([("created_at", ASCENDING)]),
    ])

    await db.click_events.create_indexes([
        IndexModel([("link_id", ASCENDING)]),
        IndexModel([("clicked_at", ASCENDING)]),
        IndexModel([("utm_source", ASCENDING)]),
        IndexModel([("link_id", ASCENDING), ("ip", ASCENDING), ("user_agent", ASCENDING)]),
    ])

    logger.info("MongoDB indexes ensured")
