import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_redirect_with_utm(client: AsyncClient):
    mock_link = MagicMock()
    mock_link.link_id = "test-uuid"
    mock_link.original_url = "https://example.com/landing"

    with patch(
        "app.api.tracking.link_service.get_link_by_short_code", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_link
        response = await client.get(
            "/t/abc12345?utm_source=whatsapp&utm_campaign=promo",
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/landing"


@pytest.mark.asyncio
async def test_redirect_not_found(client: AsyncClient):
    with patch(
        "app.api.tracking.link_service.get_link_by_short_code", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = None
        response = await client.get("/t/badcode", follow_redirects=False)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_redirect_enqueues_click(client: AsyncClient):
    mock_link = MagicMock()
    mock_link.link_id = "test-uuid"
    mock_link.original_url = "https://example.com"

    with patch(
        "app.api.tracking.link_service.get_link_by_short_code", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = mock_link
        response = await client.get(
            "/t/abc12345?utm_source=email",
            follow_redirects=False,
        )

    assert response.status_code == 302
    client.app.state.redis.enqueue_job.assert_called_once()
    call_args = client.app.state.redis.enqueue_job.call_args
    assert call_args[0][0] == "process_click"
    click_data = call_args[0][1]
    assert click_data["utm_source"] == "email"
    assert click_data["link_id"] == "test-uuid"
