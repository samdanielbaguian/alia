import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure the backend package is importable when running this script directly
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config.payment_config import PAYMENT_CONFIG
from app.core.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

PROVIDER_GATEWAY_KEY = {
    "orange_money": "orange_gateway_fee_percent",
    "mtn_money": "mtn_gateway_fee_percent",
    "moov_money": "moov_gateway_fee_percent"
}


def get_platform_fee_percent_from_settings(settings_doc: Optional[Dict[str, Any]]) -> float:
    if settings_doc and settings_doc.get("platform_fee_percentage") is not None:
        try:
            return float(settings_doc.get("platform_fee_percentage"))
        except (TypeError, ValueError):
            pass
    return PAYMENT_CONFIG["fees"]["platform_commission_percent"]


def calculate_fees(amount: float, fee_percent: float, gateway_fee_percent: float = 0.0) -> Dict[str, float]:
    platform_fee = round(amount * (fee_percent / 100), 2)
    payment_gateway_fee = round(amount * (gateway_fee_percent / 100), 2)
    merchant_payout = round(amount - platform_fee - payment_gateway_fee, 2)
    return {
        "platform_fee": platform_fee,
        "payment_gateway_fee": payment_gateway_fee,
        "merchant_payout": merchant_payout
    }


def get_gateway_fee_percent(provider: Optional[str]) -> float:
    if not provider:
        return 0.0
    provider = str(provider).lower()
    config_key = PROVIDER_GATEWAY_KEY.get(provider)
    if config_key:
        return PAYMENT_CONFIG["fees"].get(config_key, 0.0)
    return 0.0


async def connect_db() -> AsyncIOMotorDatabase:
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    return client[settings.MONGODB_DB_NAME]


async def migrate_payments(db: AsyncIOMotorDatabase, dry_run: bool = True) -> int:
    settings_doc = await db.settings.find_one({})
    fee_percent = get_platform_fee_percent_from_settings(settings_doc)

    query = {
        "$or": [
            {"platform_fee": {"$exists": False}},
            {"platform_fee": None},
            {"payment_gateway_fee": {"$exists": False}},
            {"payment_gateway_fee": None},
            {"merchant_payout": {"$exists": False}},
            {"merchant_payout": None}
        ]
    }

    cursor = db.payments.find(query)
    count = 0
    updated = 0

    async for payment in cursor:
        count += 1
        amount = float(payment.get("amount", 0.0) or 0.0)
        provider = payment.get("provider")
        gateway_fee_percent = get_gateway_fee_percent(provider)

        fees = calculate_fees(amount, fee_percent, gateway_fee_percent)
        update_fields = {}

        if payment.get("platform_fee") is None:
            update_fields["platform_fee"] = fees["platform_fee"]
        if payment.get("payment_gateway_fee") is None:
            update_fields["payment_gateway_fee"] = fees["payment_gateway_fee"]
        if payment.get("merchant_payout") is None:
            update_fields["merchant_payout"] = fees["merchant_payout"]

        if update_fields:
            update_fields["updated_at"] = datetime.utcnow()
            if dry_run:
                logger.info(f"DRY RUN payment {payment.get('payment_id')} missing fields -> {update_fields}")
            else:
                await db.payments.update_one(
                    {"_id": payment["_id"]},
                    {"$set": update_fields}
                )
                logger.info(f"Updated payment {payment.get('payment_id')} with missing fee fields")
            updated += 1

    logger.info(
        "Migrated payments: %s documents inspected, %s updated",
        count,
        updated
    )
    return updated


async def migrate_orders(db: AsyncIOMotorDatabase, dry_run: bool = True) -> int:
    settings_doc = await db.settings.find_one({})
    fee_percent = get_platform_fee_percent_from_settings(settings_doc)

    query = {
        "$or": [
            {"platform_fee": {"$exists": False}},
            {"platform_fee": None},
            {"payment_gateway_fee": {"$exists": False}},
            {"payment_gateway_fee": None},
            {"merchant_payout": {"$exists": False}},
            {"merchant_payout": None}
        ]
    }

    cursor = db.orders.find(query)
    count = 0
    updated = 0

    async for order in cursor:
        count += 1
        order_id = str(order.get("_id"))
        platform_fee = order.get("platform_fee")
        payment_gateway_fee = order.get("payment_gateway_fee")
        merchant_payout = order.get("merchant_payout")

        if platform_fee is not None and payment_gateway_fee is not None and merchant_payout is not None:
            continue

        # Try to copy values from an associated payment if available
        payment = await db.payments.find_one({"order_id": order_id}, sort=[("created_at", -1)])
        if payment and payment.get("platform_fee") is not None:
            platform_fee = platform_fee if platform_fee is not None else payment.get("platform_fee")
            payment_gateway_fee = payment_gateway_fee if payment_gateway_fee is not None else payment.get("payment_gateway_fee")
            merchant_payout = merchant_payout if merchant_payout is not None else payment.get("merchant_payout")

        # If still missing values, compute from order total
        if platform_fee is None or payment_gateway_fee is None or merchant_payout is None:
            total_amount = float(order.get("total_amount", 0.0) or 0.0)
            gateway_fee_percent = 0.0
            if payment:
                gateway_fee_percent = get_gateway_fee_percent(payment.get("provider"))
            fees = calculate_fees(total_amount, fee_percent, gateway_fee_percent)
            platform_fee = platform_fee if platform_fee is not None else fees["platform_fee"]
            payment_gateway_fee = payment_gateway_fee if payment_gateway_fee is not None else fees["payment_gateway_fee"]
            merchant_payout = merchant_payout if merchant_payout is not None else fees["merchant_payout"]

        update_fields = {}
        if order.get("platform_fee") is None:
            update_fields["platform_fee"] = platform_fee
        if order.get("payment_gateway_fee") is None:
            update_fields["payment_gateway_fee"] = payment_gateway_fee
        if order.get("merchant_payout") is None:
            update_fields["merchant_payout"] = merchant_payout

        if update_fields:
            update_fields["updated_at"] = datetime.utcnow()
            if dry_run:
                logger.info(f"DRY RUN order {order_id} missing fields -> {update_fields}")
            else:
                await db.orders.update_one(
                    {"_id": order["_id"]},
                    {"$set": update_fields}
                )
                logger.info(f"Updated order {order_id} with missing fee fields")
            updated += 1

    logger.info(
        "Migrated orders: %s documents inspected, %s updated",
        count,
        updated
    )
    return updated


async def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate existing orders and payments to include fee breakdown fields.")
    parser.add_argument("--run", action="store_true", help="Apply changes instead of dry-run")
    args = parser.parse_args()

    db = await connect_db()
    logger.info("Connected to MongoDB: %s", settings.MONGODB_DB_NAME)

    if args.run:
        logger.info("Running migration in APPLY mode")
    else:
        logger.info("Running migration in DRY-RUN mode")

    payments_updated = await migrate_payments(db, dry_run=not args.run)
    orders_updated = await migrate_orders(db, dry_run=not args.run)

    logger.info("Migration complete. payments updated=%s, orders updated=%s", payments_updated, orders_updated)
    if not args.run:
        logger.info("To apply changes, run: python scripts/migrate_fees.py --run")


if __name__ == "__main__":
    asyncio.run(main())
