import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.core.database import get_database
from app.core.security import create_access_token


@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def db():
    return get_database()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_get_default_settings(async_client):
    """GET /api/settings should return defaults when DB empty"""
    resp = await async_client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "platform_fee_percentage" in data
    assert float(data["platform_fee_percentage"]) == pytest.approx(2.5)


@pytest.mark.asyncio
async def test_put_settings_requires_admin(async_client, db):
    """PUT /api/settings should be allowed for admin users and update DB"""
    # create an admin user directly in the DB
    admin_doc = {
        "email": "admin_tests@alia.test",
        "password_hash": "x",
        "role": "admin",
    }
    result = await db.users.insert_one(admin_doc)
    admin_id = str(result.inserted_id)

    # create token for admin
    token = create_access_token({"sub": admin_id, "email": admin_doc["email"]}, role="admin")

    # update settings
    payload = {"platform_fee_percentage": 3.0, "maintenance_mode": False}
    headers = {"Authorization": f"Bearer {token}"}
    resp = await async_client.put("/api/settings", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["platform_fee_percentage"]) == pytest.approx(3.0)

    # cleanup
    await db.settings.delete_many({})
    await db.users.delete_one({"_id": result.inserted_id})
