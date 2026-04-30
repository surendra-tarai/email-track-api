from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field

IST = ZoneInfo("Asia/Kolkata")


class TrackingLinkDocument(BaseModel):
    link_id: str
    short_code: str
    original_url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ClickEventDocument(BaseModel):
    link_id: str
    clicked_at: datetime = Field(default_factory=lambda: datetime.now(tz=IST))
    ip: str
    user_agent: str
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
