import pytest
from app.models.user import UserRole


@pytest.mark.asyncio
async def test_patient_registration_and_login(async_client):
    """Test registering a patient user and authenticating with JWT token."""
    # 1. Register Patient
    reg_payload = {
        "email": "patient.test@example.com",
        "password": "SecretPassword123!",
        "full_name": "John Patient",
        "role": "PATIENT"
    }
    response = await async_client.post("/api/auth/register", json=reg_payload)
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == "patient.test@example.com"
    assert user_data["role"] == "PATIENT"
    assert "password_hash" not in user_data

    # 2. Login Patient
    login_payload = {
        "email": "patient.test@example.com",
        "password": "SecretPassword123!"
    }
    login_resp = await async_client.post("/api/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    token = token_data["access_token"]

    # 3. Fetch /me endpoint with Bearer Token
    me_resp = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "patient.test@example.com"


@pytest.mark.asyncio
async def test_unauthenticated_access_returns_401(async_client):
    """Test protected endpoints return HTTP 401 when unauthenticated."""
    response = await async_client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_email_registration_fails(async_client):
    """Test registering duplicate emails returns HTTP 400."""
    reg_payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "Original User",
        "role": "PATIENT"
    }
    resp1 = await async_client.post("/api/auth/register", json=reg_payload)
    assert resp1.status_code == 201

    resp2 = await async_client.post("/api/auth/register", json=reg_payload)
    assert resp2.status_code == 400
    assert resp2.json()["error"]["code"] == "EMAIL_EXISTS"
