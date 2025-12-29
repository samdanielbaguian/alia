from typing import List, Optional, Dict
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from fastapi import HTTPException, status

from app.models.cart import CartItem
from app.schemas.cart import CartItemResponse


class CartService:
    """Service for cart operations."""
    
    @staticmethod
    async def get_or_create_cart(user_id: str, db: AsyncIOMotorDatabase) -> dict:
        """Get or create a cart for a user."""
        cart = await db.carts.find_one({"user_id": user_id})
        
        if not cart:
            # Create new cart
            cart_data = {
                "user_id": user_id,
                "items": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = await db.carts.insert_one(cart_data)
            cart_data["_id"] = result.inserted_id
            return cart_data
        
        return cart
    
    @staticmethod
    async def add_item(
        user_id: str,
        product_id: str,
        quantity: int,
        db: AsyncIOMotorDatabase
    ) -> dict:
        """Add an item to the cart."""
        # Validate product exists
        try:
            product = await db.products.find_one({"_id": ObjectId(product_id)})
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID"
            )
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Check stock
        if product["stock"] < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock. Available: {product['stock']}"
            )
        
        # Get or create cart
        cart = await CartService.get_or_create_cart(user_id, db)
        
        # Check if product already in cart
        item_exists = False
        for item in cart["items"]:
            if item["product_id"] == product_id:
                # Update quantity
                new_quantity = item["quantity"] + quantity
                if product["stock"] < new_quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient stock. Available: {product['stock']}, in cart: {item['quantity']}"
                    )
                item["quantity"] = new_quantity
                item_exists = True
                break
        
        if not item_exists:
            # Add new item
            cart["items"].append({
                "product_id": product_id,
                "quantity": quantity,
                "price_at_add": product["price"],
                "added_at": datetime.utcnow()
            })
        
        # Update cart
        cart["updated_at"] = datetime.utcnow()
        await db.carts.update_one(
            {"_id": cart["_id"]},
            {"$set": {
                "items": cart["items"],
                "updated_at": cart["updated_at"]
            }}
        )
        
        return cart
    
    @staticmethod
    async def get_cart_with_details(user_id: str, db: AsyncIOMotorDatabase) -> Dict:
        """Get cart with full product details."""
        cart = await CartService.get_or_create_cart(user_id, db)
        
        items_response = []
        total_amount = 0.0
        
        for item in cart["items"]:
            # Get current product details
            try:
                product = await db.products.find_one({"_id": ObjectId(item["product_id"])})
            except Exception:
                continue
            
            if not product:
                continue
            
            current_price = product["price"]
            price_at_add = item["price_at_add"]
            subtotal = current_price * item["quantity"]
            total_amount += subtotal
            
            items_response.append(CartItemResponse(
                product_id=item["product_id"],
                quantity=item["quantity"],
                price_at_add=price_at_add,
                current_price=current_price,
                title=product["title"],
                image=product.get("images", [None])[0] if product.get("images") else None,
                stock=product["stock"],
                subtotal=subtotal,
                price_changed=abs(current_price - price_at_add) > 0.01,
                stock_warning=product["stock"] < item["quantity"]
            ))
        
        return {
            "items": items_response,
            "total_amount": total_amount,
            "total_items": len(items_response)
        }
    
    @staticmethod
    async def update_item_quantity(
        user_id: str,
        item_id: str,
        quantity: int,
        db: AsyncIOMotorDatabase
    ) -> dict:
        """Update item quantity in cart."""
        cart = await CartService.get_or_create_cart(user_id, db)
        
        # Find item in cart
        item_found = False
        for item in cart["items"]:
            if item["product_id"] == item_id:
                # Validate stock
                try:
                    product = await db.products.find_one({"_id": ObjectId(item_id)})
                except Exception:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid product ID"
                    )
                
                if not product:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Product not found"
                    )
                
                if product["stock"] < quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient stock. Available: {product['stock']}"
                    )
                
                item["quantity"] = quantity
                item_found = True
                break
        
        if not item_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found in cart"
            )
        
        # Update cart
        cart["updated_at"] = datetime.utcnow()
        await db.carts.update_one(
            {"_id": cart["_id"]},
            {"$set": {
                "items": cart["items"],
                "updated_at": cart["updated_at"]
            }}
        )
        
        return await CartService.get_cart_with_details(user_id, db)
    
    @staticmethod
    async def remove_item(
        user_id: str,
        item_id: str,
        db: AsyncIOMotorDatabase
    ) -> dict:
        """Remove item from cart."""
        cart = await CartService.get_or_create_cart(user_id, db)
        
        # Remove item
        original_length = len(cart["items"])
        cart["items"] = [item for item in cart["items"] if item["product_id"] != item_id]
        
        if len(cart["items"]) == original_length:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found in cart"
            )
        
        # Update cart
        cart["updated_at"] = datetime.utcnow()
        await db.carts.update_one(
            {"_id": cart["_id"]},
            {"$set": {
                "items": cart["items"],
                "updated_at": cart["updated_at"]
            }}
        )
        
        return await CartService.get_cart_with_details(user_id, db)
    
    @staticmethod
    async def clear_cart(user_id: str, db: AsyncIOMotorDatabase) -> dict:
        """Clear all items from cart."""
        cart = await CartService.get_or_create_cart(user_id, db)
        
        cart["items"] = []
        cart["updated_at"] = datetime.utcnow()
        
        await db.carts.update_one(
            {"_id": cart["_id"]},
            {"$set": {
                "items": [],
                "updated_at": cart["updated_at"]
            }}
        )
        
        return {
            "items": [],
            "total_amount": 0.0,
            "total_items": 0
        }
    
    @staticmethod
    async def validate_cart_for_order(user_id: str, db: AsyncIOMotorDatabase) -> List[dict]:
        """Validate cart items are available for order."""
        cart = await CartService.get_or_create_cart(user_id, db)
        
        if not cart["items"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )
        
        order_products = []
        merchant_id = None
        
        for item in cart["items"]:
            # Get current product
            try:
                product = await db.products.find_one({"_id": ObjectId(item["product_id"])})
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid product ID: {item['product_id']}"
                )
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product not found: {item['product_id']}"
                )
            
            # Check stock
            if product["stock"] < item["quantity"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for {product['title']}. Available: {product['stock']}"
                )
            
            # Verify all products from same merchant
            if merchant_id is None:
                merchant_id = product["merchant_id"]
            elif merchant_id != product["merchant_id"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="All products must be from the same merchant"
                )
            
            order_products.append({
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "price": product["price"],
                "title": product["title"],
                "merchant_id": merchant_id
            })
        
        return order_products
