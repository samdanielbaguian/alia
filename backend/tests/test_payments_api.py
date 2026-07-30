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
async def test_initiate_payment_returns_fee_breakdown(async_client, db):
    """Create merchant/product/buyer, create order and call payments initiate.
    Verify response contains platform_fee/payment_gateway_fee/merchant_payout.
    """
    # insert settings to control platform fee
    await db.settings.update_one({}, {"$set": {"platform_fee_percentage": 4.0}}, upsert=True)

    # register merchant
    merch_reg = await async_client.post("/api/auth/register", json={
        "email": "pm_merchant@tests.local",
        "password": "TestPass1234!",
        "role": "merchant",
        "shop_name": "PM Test Shop"
    })
    assert merch_reg.status_code == 201
    merch_token = merch_reg.json()["access_token"]

    # create product as merchant
    prod_resp = await async_client.post("/api/products", json={
        "title": "PM Test Product",
        "description": "t",
        "price": 10000.0,
        "category": "test",
        "stock": 5
    }, headers={"Authorization": f"Bearer {merch_token}"})
    assert prod_resp.status_code in (200, 201)
    prod = prod_resp.json()
    prod_id = prod.get("id") or prod.get("_id") or prod.get("product_id")
    if not prod_id:
        # fallback: try to find product created by merchant
        p = await db.products.find_one({"merchant_id": str(prod_resp.json().get("merchant_id") or '')})
        prod_id = str(p["_id"]) if p else None

    # register buyer
    buyer_reg = await async_client.post("/api/auth/register", json={
        "email": "pm_buyer@tests.local",
        "password": "TestPass1234!",
        "role": "buyer",
    })
    assert buyer_reg.status_code == 201
    buyer_token = buyer_reg.json()["access_token"]

    # create order as buyer
    order_resp = await async_client.post("/api/orders", json={
        "products": [{"product_id": prod_id, "quantity": 1}],
        "payment_method": "orange_money"
    }, headers={"Authorization": f"Bearer {buyer_token}"})
    assert order_resp.status_code == 201
    order = order_resp.json()
    order_id = order.get("id") or order.get("_id")

    # initiate payment
    pay_resp = await async_client.post("/api/payments/initiate", json={
        "order_id": order_id,
        "phone_number": "+2250707123456"
    }, headers={"Authorization": f"Bearer {buyer_token}"})

    assert pay_resp.status_code == 201
    pay = pay_resp.json()
    assert "platform_fee" in pay
    assert "merchant_payout" in pay
    assert "payment_gateway_fee" in pay

    # compute expected platform fee = total_amount * 4%
    total = float(pay.get("amount", order.get("total_amount", 10000)))
    expected_platform = round(total * (4.0 / 100.0), 2)
    assert float(pay["platform_fee"]) == pytest.approx(expected_platform)

    # cleanup
    await db.settings.delete_many({})
    # leave created users/products/orders for other tests
