from typing import Dict, List
from pydantic import BaseModel


class LinkStatsResponse(BaseModel):
    link_id: str
    total_clicks: int
    unique_clicks: int
    by_source: Dict[str, int]
    by_campaign: Dict[str, int]


class BulkStatsRequest(BaseModel):
    link_ids: List[str]


class BulkStatsResponse(BaseModel):
    results: List[LinkStatsResponse]
