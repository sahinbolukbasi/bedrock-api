"""
Automated tests for Prometheus Metrics Scrape Security.
Validates Bearer token authentication on the /metrics endpoint.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_metrics_endpoint_rejects_unauthorized():
    """Verifies that accessing /metrics without Bearer token returns 401 Unauthorized."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/metrics")
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_metrics_endpoint_rejects_invalid_token():
    """Verifies that accessing /metrics with invalid Bearer token returns 401 Unauthorized."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/metrics", headers={"Authorization": "Bearer wrong-token-123"})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_metrics_endpoint_accepts_valid_bearer_token():
    """Verifies that accessing /metrics with valid secret Bearer token returns Prometheus metrics."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/metrics", headers={"Authorization": f"Bearer {settings.METRICS_SCRAPE_TOKEN}"})
        assert resp.status_code == 200
        assert "gateway_requests_total" in resp.text or "python_gc_objects_collected_total" in resp.text
