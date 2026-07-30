# app/services/rating_service.py
async def update_merchant_rating(merchant_id: str, db):
    pipeline = [
        {"$match": {"merchant_id": merchant_id}},
        {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}}
    ]
    result = await db.reviews.aggregate(pipeline).to_list(1)
    avg = result[0]["avg_rating"] if result else 50.0
    avg = round(avg, 1)
    await db.merchants.update_one(
        {"_id": ObjectId(merchant_id)},
        {"$set": {"rating": avg * 20}}  # 1-5 → 0-100
    )