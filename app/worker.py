import logging
from datetime import datetime

from arq.connections import RedisSettings
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

logger = logging.getLogger(__name__)


async def process_click(ctx: dict, click_data: dict) -> None:
    if isinstance(click_data.get("clicked_at"), str):
        click_data["clicked_at"] = datetime.fromisoformat(click_data["clicked_at"])
    await ctx["db"].click_events.insert_one(click_data)
    logger.debug("Stored click for link_id=%s", click_data.get("link_id"))


async def startup(ctx: dict) -> None:
    ctx["mongo_client"] = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    ctx["db"] = ctx["mongo_client"][settings.mongodb_db]
    logger.info("Worker connected to MongoDB")


async def shutdown(ctx: dict) -> None:
    ctx["mongo_client"].close()
    logger.info("Worker disconnected from MongoDB")


class WorkerSettings:
    functions = [process_click]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 50
    job_timeout = 30
