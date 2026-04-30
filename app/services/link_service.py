import secrets
import uuid
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.models.documents import TrackingLinkDocument

_MAX_RETRIES = 5


async def create_link(db: AsyncIOMotorDatabase, original_url: str) -> TrackingLinkDocument:
    for _ in range(_MAX_RETRIES):
        link = TrackingLinkDocument(
            link_id=str(uuid.uuid4()),
            short_code=_generate_short_code(),
            original_url=original_url,
            created_at=datetime.utcnow(),
        )
        try:
            await db.tracking_links.insert_one(link.model_dump())
            return link
        except DuplicateKeyError:
            continue
    raise RuntimeError("Failed to generate a unique short code after multiple attempts")


async def get_link_by_short_code(
    db: AsyncIOMotorDatabase, short_code: str
) -> TrackingLinkDocument | None:
    doc = await db.tracking_links.find_one({"short_code": short_code})
    if not doc:
        return None
    return TrackingLinkDocument(**doc)


async def get_link_by_id(
    db: AsyncIOMotorDatabase, link_id: str
) -> TrackingLinkDocument | None:
    doc = await db.tracking_links.find_one({"link_id": link_id})
    if not doc:
        return None
    return TrackingLinkDocument(**doc)


def _generate_short_code() -> str:
    # token_urlsafe(6) produces 8 base64url characters
    return secrets.token_urlsafe(6)
