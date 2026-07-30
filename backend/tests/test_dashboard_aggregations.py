import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.core.database import get_database
from app.core.security import create_access_token
from datetime import datetime


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
async def test_merchant_and_admin_fee_aggregations(async_client, db):
    """Insert payments for a merchant and verify merchant/admin endpoints aggregate fees."""
    # create merchant user directly
    merchant_doc = {"email": "agg_merchant@tests.local", "password_hash": "x", "role": "merchant"}
    mres = await db.users.insert_one(merchant_doc)
    merchant_user_id = str(mres.inserted_id)

    # create merchant profile
    await db.merchants.insert_one({"user_id": merchant_user_id, "shop_name": "Agg Shop", "created_at": datetime.utcnow()})

    # create merchant token
    merch_token = create_access_token({"sub": merchant_user_id, "email": merchant_doc["email"]}, role="merchant")

    # create admin user and token
    admin_doc = {"email": "agg_admin@tests.local", "password_hash": "x", "role": "admin"}
    ares = await db.users.insert_one(admin_doc)
    admin_user_id = str(ares.inserted_id)
    admin_token = create_access_token({"sub": admin_user_id, "email": admin_doc["email"]}, role="admin")

    # insert payments for merchant (completed)
    now = datetime.utcnow()
    payments = [
        {"payment_id": "p1", "order_id": "o1", "merchant_id": merchant_user_id, "amount": 1000.0, "platform_fee": 25.0, "payment_gateway_fee": 5.0, "merchant_payout": 970.0, "status": "completed", "initiated_at": now},
        {"payment_id": "p2", "order_id": "o2", "merchant_id": merchant_user_id, "amount": 2000.0, "platform_fee": 50.0, "payment_gateway_fee": 10.0, "merchant_payout": 1940.0, "status": "completed", "initiated_at": now}
    ]
    await db.payments.insert_many(payments)

    # call merchant dashboard overview
    resp = await async_client.get("/api/merchants/me/dashboard-overview", headers={"Authorization": f"Bearer {merch_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert float(data.get("total_platform_fees", 0)) == pytest.approx(25.0 + 50.0)
    assert float(data.get("merchant_net_payout", 0)) == pytest.approx(970.0 + 1940.0)

    # call admin stats
    resp2 = await async_client.get("/api/admin/orders/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp2.status_code == 200
    d2 = resp2.json()
    assert float(d2.get("total_platform_fees", 0)) == pytest.approx(75.0)
    assert float(d2.get("total_gateway_fees", 0)) == pytest.approx(15.0)
    assert float(d2.get("total_merchant_payout", 0)) == pytest.approx(970.0 + 1940.0)

    # cleanup
    await db.payments.delete_many({"merchant_id": merchant_user_id})
    await db.merchants.delete_many({"user_id": merchant_user_id})
    await db.users.delete_one({"_id": mres.inserted_id})
    await db.users.delete_one({"_id": ares.inserted_id})
