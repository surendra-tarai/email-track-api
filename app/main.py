import logging
from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import links, tracking
from app.config import settings
from app.database import close_db, connect_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    app.state.redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    logger.info("Application startup complete")
    yield
    await app.state.redis.close()
    await close_db()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="UTM Link Tracker API",
    description="Track link clicks across channels using UTM parameters",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(links.router)
app.include_router(tracking.router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}
