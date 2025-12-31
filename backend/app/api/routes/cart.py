from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.api.deps import get_db, get_current_user
from app.schemas.cart import (
    AddToCartRequest,
    UpdateCartItemRequest,
    CartResponse,
    CreateShareRequest,
    ShareResponse,
    SharedCartResponse
)
from app.services.cart_service import CartService
from app.services.share_service import ShareService

router = APIRouter()


@router.post("/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    request: AddToCartRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Add a product to the cart.
    
    Validates:
    - Product exists
    - Sufficient stock available
    
    If product already in cart, increases quantity.
    """
    user_id = str(current_user["_id"])
    
    await CartService.add_item(
        user_id=user_id,
        product_id=request.product_id,
        quantity=request.quantity,
        db=db
    )
    
    return await CartService.get_cart_with_details(user_id, db)


@router.get("", response_model=CartResponse)
async def get_cart(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get the current user's cart with full product details.
    
    Returns:
    - All cart items with current prices and stock
    - Price change warnings
    - Stock availability warnings
    - Total amount and item count
    """
    user_id = str(current_user["_id"])
    return await CartService.get_cart_with_details(user_id, db)


@router.put("/items/{item_id}", response_model=CartResponse)
async def update_cart_item(
    item_id: str,
    request: UpdateCartItemRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Update the quantity of an item in the cart.
    
    Validates stock availability before updating.
    """
    user_id = str(current_user["_id"])
    
    return await CartService.update_item_quantity(
        user_id=user_id,
        item_id=item_id,
        quantity=request.quantity,
        db=db
    )


@router.delete("/items/{item_id}", response_model=CartResponse)
async def remove_from_cart(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Remove an item from the cart.
    """
    user_id = str(current_user["_id"])
    return await CartService.remove_item(user_id, item_id, db)


@router.delete("", response_model=CartResponse)
async def clear_cart(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Clear all items from the cart.
    """
    user_id = str(current_user["_id"])
    return await CartService.clear_cart(user_id, db)


@router.post("/share", response_model=ShareResponse)
async def share_cart(
    request: CreateShareRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Generate a shareable link for the current cart.
    
    Creates a snapshot of the cart that can be shared with others.
    The link can have an expiration time (default 24 hours).
    """
    user_id = str(current_user["_id"])
    
    share = await ShareService.create_cart_share(
        user_id=user_id,
        expires_in_hours=request.expires_in_hours,
        db=db
    )
    
    share_link = f"{settings.BASE_URL}/cart/share/{share['share_code']}"
    
    return ShareResponse(
        share_link=share_link,
        share_code=share["share_code"],
        expires_at=share.get("expires_at")
    )


@router.get("/share/{share_code}", response_model=SharedCartResponse)
async def view_shared_cart(
    share_code: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    View a shared cart (public endpoint).
    
    No authentication required.
    Increments view count.
    """
    return await ShareService.get_shared_cart(share_code, db)


@router.post("/import/{share_code}", response_model=CartResponse)
async def import_shared_cart(
    share_code: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Import a shared cart into the current user's cart.
    
    Validates:
    - Share link hasn't expired
    - Products still exist and have stock
    
    Merges items into existing cart.
    """
    user_id = str(current_user["_id"])
    
    await ShareService.import_shared_cart(
        share_code=share_code,
        user_id=user_id,
        db=db
    )
    
    return await CartService.get_cart_with_details(user_id, db)
