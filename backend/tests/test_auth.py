"""Integration tests for authentication endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import engine, Base


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_register_and_login(client):
    # Register
    resp = await client.post("/api/v1/auth/register", json={
        "email": "admin@test.com",
        "username": "testadmin",
        "password": "TestPass123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "admin@test.com"
    assert data["role"] == "superadmin"  # First user gets superadmin

    # Login
    resp = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "TestPass123",
    })
    assert resp.status_code == 200
    tokens = resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # Me
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@test.com"


@pytest.mark.asyncio
async def test_invalid_login(client):
    resp = await client.post("/api/v1/auth/login", json={"email": "nobody@test.com", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_weak_password_rejected(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "user@test.com",
        "username": "user1",
        "password": "weak",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
