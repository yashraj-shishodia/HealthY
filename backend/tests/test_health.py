import pytest


@pytest.mark.asyncio
async def test_health_check_endpoint(async_client):
    """Test root and /api/health endpoints return 200 OK."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data

    api_response = await async_client.get("/api/health")
    assert api_response.status_code == 200
    assert api_response.json()["status"] == "healthy"
