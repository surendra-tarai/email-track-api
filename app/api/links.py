from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_db
from app.schemas.analytics import BulkStatsRequest, BulkStatsResponse, LinkStatsResponse
from app.schemas.link import CreateLinkRequest, CreateLinkResponse
from app.services import analytics_service, link_service
from app.config import settings

router = APIRouter(prefix="/links", tags=["links"])


def db_dep(request: Request) -> AsyncIOMotorDatabase:
    return get_db()


@router.post("", response_model=CreateLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(
    body: CreateLinkRequest,
    db: AsyncIOMotorDatabase = Depends(db_dep),
) -> CreateLinkResponse:
    link = await link_service.create_link(db, body.original_url)
    return CreateLinkResponse(
        link_id=link.link_id,
        tracking_url=f"{settings.base_url}/t/{link.short_code}",
        tracking_pixel=f"{settings.base_url}/pixel/{link.short_code}"
    )


@router.post("/stats", response_model=BulkStatsResponse)
async def bulk_stats(
    body: BulkStatsRequest,
    db: AsyncIOMotorDatabase = Depends(db_dep),
) -> BulkStatsResponse:
    if not body.link_ids:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="link_ids cannot be empty")
    results = await analytics_service.get_bulk_stats(db, body.link_ids)
    return BulkStatsResponse(results=results)


@router.get("/{link_id}/stats", response_model=LinkStatsResponse)
async def link_stats(
    link_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dep),
) -> LinkStatsResponse:
    link = await link_service.get_link_by_id(db, link_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return await analytics_service.get_link_stats(db, link_id)
