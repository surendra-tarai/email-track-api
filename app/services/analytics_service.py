from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.analytics import LinkStatsResponse


async def get_link_stats(db: AsyncIOMotorDatabase, link_id: str) -> LinkStatsResponse:
    pipeline = [
        {"$match": {"link_id": link_id}},
        {
            "$facet": {
                "total": [{"$count": "count"}],
                "unique": [
                    {"$group": {"_id": {"ip": "$ip", "ua": "$user_agent"}}},
                    {"$count": "count"},
                ],
                "by_source": [
                    {"$match": {"utm_source": {"$ne": None}}},
                    {"$group": {"_id": "$utm_source", "count": {"$sum": 1}}},
                ],
                "by_campaign": [
                    {"$match": {"utm_campaign": {"$ne": None}}},
                    {"$group": {"_id": "$utm_campaign", "count": {"$sum": 1}}},
                ],
            }
        },
    ]

    cursor = db.click_events.aggregate(pipeline)
    results = await cursor.to_list(length=1)

    if not results:
        return _empty_stats(link_id)

    data = results[0]
    total = data["total"][0]["count"] if data["total"] else 0
    unique = data["unique"][0]["count"] if data["unique"] else 0
    by_source = {item["_id"]: item["count"] for item in data["by_source"]}
    by_campaign = {item["_id"]: item["count"] for item in data["by_campaign"]}

    return LinkStatsResponse(
        link_id=link_id,
        total_clicks=total,
        unique_clicks=unique,
        by_source=by_source,
        by_campaign=by_campaign,
    )


async def get_bulk_stats(
    db: AsyncIOMotorDatabase, link_ids: list[str]
) -> list[LinkStatsResponse]:
    pipeline = [
        {"$match": {"link_id": {"$in": link_ids}}},
        {
            "$facet": {
                "totals": [{"$group": {"_id": "$link_id", "count": {"$sum": 1}}}],
                "unique": [
                    {
                        "$group": {
                            "_id": {"link_id": "$link_id", "ip": "$ip", "ua": "$user_agent"}
                        }
                    },
                    {"$group": {"_id": "$_id.link_id", "count": {"$sum": 1}}},
                ],
                "by_source": [
                    {"$match": {"utm_source": {"$ne": None}}},
                    {
                        "$group": {
                            "_id": {"link_id": "$link_id", "source": "$utm_source"},
                            "count": {"$sum": 1},
                        }
                    },
                ],
                "by_campaign": [
                    {"$match": {"utm_campaign": {"$ne": None}}},
                    {
                        "$group": {
                            "_id": {"link_id": "$link_id", "campaign": "$utm_campaign"},
                            "count": {"$sum": 1},
                        }
                    },
                ],
            }
        },
    ]

    cursor = db.click_events.aggregate(pipeline)
    results = await cursor.to_list(length=1)

    if not results:
        return [_empty_stats(lid) for lid in link_ids]

    data = results[0]

    totals = {item["_id"]: item["count"] for item in data["totals"]}
    unique = {item["_id"]: item["count"] for item in data["unique"]}

    sources: dict[str, dict[str, int]] = {}
    for item in data["by_source"]:
        lid = item["_id"]["link_id"]
        src = item["_id"]["source"]
        sources.setdefault(lid, {})[src] = item["count"]

    campaigns: dict[str, dict[str, int]] = {}
    for item in data["by_campaign"]:
        lid = item["_id"]["link_id"]
        cmp = item["_id"]["campaign"]
        campaigns.setdefault(lid, {})[cmp] = item["count"]

    return [
        LinkStatsResponse(
            link_id=lid,
            total_clicks=totals.get(lid, 0),
            unique_clicks=unique.get(lid, 0),
            by_source=sources.get(lid, {}),
            by_campaign=campaigns.get(lid, {}),
        )
        for lid in link_ids
    ]


def _empty_stats(link_id: str) -> LinkStatsResponse:
    return LinkStatsResponse(
        link_id=link_id,
        total_clicks=0,
        unique_clicks=0,
        by_source={},
        by_campaign={},
    )
