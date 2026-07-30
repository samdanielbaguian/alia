# app/models/review.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class Review(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    order_id: str                     # Commande associée
    merchant_id: str                  # Marchand noté
    user_id: str                      # Client qui note
    rating: int = Field(..., ge=1, le=5)  # Note 1-5
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)