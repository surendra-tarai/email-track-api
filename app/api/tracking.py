import logging
from typing import Optional

from arq import ArqRedis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse, Response
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_db
from app.models.documents import ClickEventDocument
from app.services import link_service

# Smallest possible 1x1 transparent GIF (43 bytes)
TRANSPARENT_PIXEL = (
    b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
    b"\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00"
    b"\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02"
    b"\x44\x01\x00\x3b"
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tracking"])


def db_dep(request: Request) -> AsyncIOMotorDatabase:
    return get_db()


def redis_dep(request: Request) -> ArqRedis:
    return request.app.state.redis


@router.get("/t/{short_code}", status_code=status.HTTP_302_FOUND)
async def redirect_and_track(
    short_code: str,
    request: Request,
    utm_source: Optional[str] = None,
    utm_medium: Optional[str] = None,
    utm_campaign: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(db_dep),
    redis: ArqRedis = Depends(redis_dep),
) -> RedirectResponse:
    link = await link_service.get_link_by_short_code(db, short_code)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    client_ip = _get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    click = ClickEventDocument(
        link_id=link.link_id,
        ip=client_ip,
        user_agent=user_agent,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
    )

    await redis.enqueue_job("process_click", click.model_dump(mode="json"))

    return RedirectResponse(url=link.original_url, status_code=status.HTTP_302_FOUND)


@router.get("/pixel/{short_code}")
async def pixel_track(
    short_code: str,
    request: Request,
    utm_source: Optional[str] = None,
    utm_medium: Optional[str] = None,
    utm_campaign: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(db_dep),
    redis: ArqRedis = Depends(redis_dep),
) -> Response:
    link = await link_service.get_link_by_short_code(db, short_code)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    click = ClickEventDocument(
        link_id=link.link_id,
        ip=_get_client_ip(request),
        user_agent=request.headers.get("user-agent", ""),
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
    )

    await redis.enqueue_job("process_click", click.model_dump(mode="json"))

    return Response(content=TRANSPARENT_PIXEL, media_type="image/gif")


def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"
