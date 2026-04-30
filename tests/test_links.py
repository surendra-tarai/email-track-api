import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_link(client: AsyncClient):
    mock_link = MagicMock()
    mock_link.link_id = "test-uuid-1234"
    mock_link.short_code = "abc12345"

    with patch("app.api.links.link_service.create_link", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_link
        response = await client.post("/links", json={"original_url": "https://example.com"})

    assert response.status_code == 201
    data = response.json()
    assert data["link_id"] == "test-uuid-1234"
    assert "abc12345" in data["tracking_url"]


@pytest.mark.asyncio
async def test_create_link_invalid_url(client: AsyncClient):
    response = await client.post("/links", json={"original_url": "not-a-url"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_link_stats_not_found(client: AsyncClient):
    with patch("app.api.links.link_service.get_link_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        response = await client.get("/links/nonexistent-id/stats")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_link_stats_found(client: AsyncClient):
    mock_link = MagicMock()
    mock_link.link_id = "test-uuid-1234"

    mock_stats = MagicMock()
    mock_stats.model_dump = lambda: {
        "link_id": "test-uuid-1234",
        "total_clicks": 50,
        "unique_clicks": 30,
        "by_source": {"whatsapp": 25, "email": 25},
        "by_campaign": {"promo": 50},
    }

    with (
        patch("app.api.links.link_service.get_link_by_id", new_callable=AsyncMock) as mock_get,
        patch("app.api.links.analytics_service.get_link_stats", new_callable=AsyncMock) as mock_stats_fn,
    ):
        mock_get.return_value = mock_link
        mock_stats_fn.return_value = MagicMock(
            link_id="test-uuid-1234",
            total_clicks=50,
            unique_clicks=30,
            by_source={"whatsapp": 25, "email": 25},
            by_campaign={"promo": 50},
        )
        response = await client.get("/links/test-uuid-1234/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["total_clicks"] == 50
    assert data["unique_clicks"] == 30


@pytest.mark.asyncio
async def test_bulk_stats(client: AsyncClient):
    with patch("app.api.links.analytics_service.get_bulk_stats", new_callable=AsyncMock) as mock_bulk:
        mock_bulk.return_value = [
            MagicMock(
                link_id="id1",
                total_clicks=10,
                unique_clicks=8,
                by_source={"email": 10},
                by_campaign={},
            )
        ]
        response = await client.post("/links/stats", json={"link_ids": ["id1"]})

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
