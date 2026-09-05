from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api.deps import get_db, get_current_user
from app.services.rating_service import update_merchant_rating
from bson import ObjectId
from datetime import datetime

router = APIRouter()


class ReviewRequest(BaseModel):
    rating: int
    comment: str = None


@router.post("/{order_id}")
async def create_review(
    order_id: str,
    request: ReviewRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Vérifier que la commande appartient à l'utilisateur et est livrée
    order = await db.orders.find_one({"_id": ObjectId(order_id), "user_id": current_user["_id"]})
    if not order or order["status"] != "delivered":
        raise HTTPException(400, "Seules les commandes livrées peuvent être notées")
    
    # Empêcher les doublons
    existing = await db.reviews.find_one({"order_id": order_id})
    if existing:
        raise HTTPException(400, "Avis déjà laissé pour cette commande")
    
    review = {
        "order_id": order_id,
        "merchant_id": order["merchant_id"],
        "user_id": current_user["_id"],
        "rating": request.rating,
        "comment": request.comment,
        "created_at": datetime.utcnow()
    }
    await db.reviews.insert_one(review)
    
    # Mettre à jour la note du marchand (moyenne)
    await update_merchant_rating(order["merchant_id"], db)
    
    return {"message": "Avis ajouté"}


@router.get("/order/{order_id}")
async def get_order_reviews(
    order_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    reviews = await db.reviews.find({"order_id": order_id}).to_list(100)
    for review in reviews:
        review["_id"] = str(review["_id"])
        if review.get("created_at"):
            review["created_at"] = review["created_at"].isoformat()
    return reviews


@router.get("/merchant/{merchant_id}")
async def get_merchant_reviews(merchant_id: str, db=Depends(get_db)):
    reviews = await db.reviews.find({"merchant_id": merchant_id}).to_list(100)
    return {"reviews": reviews, "count": len(reviews)}