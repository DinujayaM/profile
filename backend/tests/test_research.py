"""Tests for research / video ideas endpoints."""
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
async def auth_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post("/api/v1/auth/register", json={
            "email": "admin@test.com", "username": "admin", "password": "Admin123"
        })
        resp = await ac.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "Admin123"})
        token = resp.json()["access_token"]
        ac.headers = {"Authorization": f"Bearer {token}"}
        yield ac


@pytest.mark.asyncio
async def test_generate_ideas(auth_client):
    resp = await auth_client.post("/api/v1/research/generate-ideas", json={"count": 2})
    assert resp.status_code == 200
    ideas = resp.json()
    assert len(ideas) >= 1  # Mock may return fewer


@pytest.mark.asyncio
async def test_list_ideas(auth_client):
    await auth_client.post("/api/v1/research/generate-ideas", json={"count": 3})
    resp = await auth_client.get("/api/v1/research/ideas")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_approve_idea(auth_client):
    gen_resp = await auth_client.post("/api/v1/research/generate-ideas", json={"count": 1})
    idea_id = gen_resp.json()[0]["id"]

    resp = await auth_client.post(f"/api/v1/research/ideas/{idea_id}/approve")
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"
