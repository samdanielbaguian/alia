import secrets
import string
from typing import Optional
from datetime import datetime, timedelta
from urllib.parse import quote
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
import qrcode
import io
import base64

from app.core.config import settings
from app.schemas.share import ProductShareResponse, ProductShareStatsResponse, MerchantShareResponse
from app.schemas.cart import SharedCartResponse, SharedCartItemResponse


class ShareService:
    """Service for sharing operations."""
    
    @staticmethod
    def generate_share_code(length: int = 8) -> str:
        """Generate a unique share code."""
        characters = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    @staticmethod
    def sanitize_text_for_share(text: str, max_length: int = 100) -> str:
        """
        Sanitize text for use in share messages.
        Removes or replaces potentially problematic characters and limits length.
        """
        # Remove or replace problematic characters
        # Keep alphanumerics, spaces, and common safe punctuation
        safe_chars = set(string.ascii_letters + string.digits + ' .,!?-éèêëàâäôöùûüïîçÉÈÊËÀÂÄÔÖÙÛÜÏÎÇ')
        sanitized = ''.join(c if c in safe_chars else ' ' for c in text)
        
        # Collapse multiple spaces
        sanitized = ' '.join(sanitized.split())
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rsplit(' ', 1)[0] + '...'
        
        return sanitized
    
    @staticmethod
    async def create_cart_share(
        user_id: str,
        expires_in_hours: int,
        db: AsyncIOMotorDatabase
    ) -> dict:
        """Create a shareable cart link."""
        # Get user's cart
        cart = await db.carts.find_one({"user_id": user_id})
        
        if not cart or not cart.get("items"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )
        
        # Create cart snapshot with product details
        cart_snapshot = []
        for item in cart["items"]:
            try:
                product = await db.products.find_one({"_id": ObjectId(item["product_id"])})
            except InvalidId:
                continue
            
            if product:
                cart_snapshot.append({
                    "product_id": item["product_id"],
                    "quantity": item["quantity"],
                    "price_at_share": product["price"],
                    "title": product["title"]
                })
        
        if not cart_snapshot:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid products in cart"
            )
        
        # Generate unique share code
        share_code = ShareService.generate_share_code()
        while await db.cart_shares.find_one({"share_code": share_code}):
            share_code = ShareService.generate_share_code()
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours) if expires_in_hours else None
        
        # Create share record
        share_data = {
            "share_code": share_code,
            "cart_snapshot": cart_snapshot,
            "user_id": user_id,
            "expires_at": expires_at,
            "view_count": 0,
            "import_count": 0,
            "created_at": datetime.utcnow()
        }
        
        result = await db.cart_shares.insert_one(share_data)
        share_data["_id"] = result.inserted_id
        
        return share_data
    
    @staticmethod
    async def get_shared_cart(share_code: str, db: AsyncIOMotorDatabase) -> dict:
        """Get a shared cart by code."""
        share = await db.cart_shares.find_one({"share_code": share_code})
        
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared cart not found"
            )
        
        # Check expiration
        is_expired = False
        if share.get("expires_at") and share["expires_at"] < datetime.utcnow():
            is_expired = True
        
        # Increment view count
        await db.cart_shares.update_one(
            {"_id": share["_id"]},
            {"$inc": {"view_count": 1}}
        )
        
        # Get sharer info (anonymized)
        user = await db.users.find_one({"_id": ObjectId(share["user_id"])})
        shared_by = "Anonymous"
        if user:
            email = user.get("email", "")
            shared_by = email.split("@")[0][:3] + "***"
        
        # Build response
        items = []
        total_amount = 0.0
        
        for item in share["cart_snapshot"]:
            subtotal = item["price_at_share"] * item["quantity"]
            total_amount += subtotal
            
            items.append(SharedCartItemResponse(
                product_id=item["product_id"],
                quantity=item["quantity"],
                price=item["price_at_share"],
                title=item["title"],
                subtotal=subtotal
            ))
        
        return SharedCartResponse(
            items=items,
            total_amount=total_amount,
            total_items=len(items),
            shared_by=shared_by,
            expires_at=share.get("expires_at"),
            is_expired=is_expired
        )
    
    @staticmethod
    async def import_shared_cart(
        share_code: str,
        user_id: str,
        db: AsyncIOMotorDatabase
    ) -> dict:
        """Import a shared cart to user's cart."""
        share = await db.cart_shares.find_one({"share_code": share_code})
        
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared cart not found"
            )
        
        # Check expiration
        if share.get("expires_at") and share["expires_at"] < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This shared cart has expired"
            )
        
        # Get or create user's cart
        cart = await db.carts.find_one({"user_id": user_id})
        if not cart:
            cart_data = {
                "user_id": user_id,
                "items": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = await db.carts.insert_one(cart_data)
            cart = cart_data
            cart["_id"] = result.inserted_id
        
        # Add items from shared cart
        for item in share["cart_snapshot"]:
            # Validate product still exists and has stock
            try:
                product = await db.products.find_one({"_id": ObjectId(item["product_id"])})
            except InvalidId:
                continue
            
            if not product or product["stock"] < item["quantity"]:
                continue
            
            # Check if item already in cart
            item_exists = False
            for cart_item in cart["items"]:
                if cart_item["product_id"] == item["product_id"]:
                    cart_item["quantity"] += item["quantity"]
                    item_exists = True
                    break
            
            if not item_exists:
                cart["items"].append({
                    "product_id": item["product_id"],
                    "quantity": item["quantity"],
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
        
        # Increment import count
        await db.cart_shares.update_one(
            {"_id": share["_id"]},
            {"$inc": {"import_count": 1}}
        )
        
        return cart
    
    @staticmethod
    def generate_qr_code(data: str) -> str:
        """Generate a QR code and return as base64 encoded PNG."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
    
    @staticmethod
    async def create_product_share(
        product_id: str,
        user_id: str,
        db: AsyncIOMotorDatabase
    ) -> ProductShareResponse:
        """Create a shareable product link."""
        # Validate product exists
        try:
            product = await db.products.find_one({"_id": ObjectId(product_id)})
        except InvalidId:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID"
            )
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Generate unique share code
        share_code = ShareService.generate_share_code()
        while await db.product_shares.find_one({"share_code": share_code}):
            share_code = ShareService.generate_share_code()
        
        # Create share record
        share_data = {
            "product_id": product_id,
            "share_code": share_code,
            "user_id": user_id,
            "view_count": 0,
            "conversion_count": 0,
            "created_at": datetime.utcnow()
        }
        
        await db.product_shares.insert_one(share_data)
        
        # Generate share links
        share_link = f"{settings.BASE_URL}/products/share/{share_code}"
        
        # WhatsApp message with sanitized and URL encoded text
        sanitized_title = ShareService.sanitize_text_for_share(product['title'], max_length=50)
        whatsapp_text = f"Découvre ce produit sur Alia : {sanitized_title} - {product['price']} FCFA {share_link}"
        whatsapp_link = f"https://wa.me/?text={quote(whatsapp_text)}"
        
        # QR code
        qr_code = ShareService.generate_qr_code(share_link)
        
        return ProductShareResponse(
            share_link=share_link,
            share_code=share_code,
            whatsapp_link=whatsapp_link,
            qr_code=qr_code
        )
    
    @staticmethod
    async def get_shared_product(share_code: str, db: AsyncIOMotorDatabase) -> dict:
        """Get a shared product by code."""
        share = await db.product_shares.find_one({"share_code": share_code})
        
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared product not found"
            )
        
        # Increment view count
        await db.product_shares.update_one(
            {"_id": share["_id"]},
            {"$inc": {"view_count": 1}}
        )
        
        # Get product
        try:
            product = await db.products.find_one({"_id": ObjectId(share["product_id"])})
        except InvalidId:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID"
            )
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Add share info to product
        product["shared_by"] = share["user_id"]
        product["share_code"] = share_code
        
        return product
    
    @staticmethod
    async def get_product_share_stats(
        product_id: str,
        merchant_id: str,
        db: AsyncIOMotorDatabase
    ) -> ProductShareStatsResponse:
        """Get share statistics for a product."""
        # Validate product ownership
        try:
            product = await db.products.find_one({"_id": ObjectId(product_id)})
        except InvalidId:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID"
            )
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        if product["merchant_id"] != merchant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view stats for your own products"
            )
        
        # Get all shares for this product
        shares = await db.product_shares.find({"product_id": product_id}).to_list(length=None)
        
        total_shares = len(shares)
        views_from_shares = sum(share.get("view_count", 0) for share in shares)
        conversions_from_shares = sum(share.get("conversion_count", 0) for share in shares)
        
        conversion_rate = "0.0%"
        if views_from_shares > 0:
            rate = (conversions_from_shares / views_from_shares) * 100
            conversion_rate = f"{rate:.1f}%"
        
        return ProductShareStatsResponse(
            total_shares=total_shares,
            views_from_shares=views_from_shares,
            conversions_from_shares=conversions_from_shares,
            conversion_rate=conversion_rate
        )
    
    @staticmethod
    async def create_merchant_share(
        merchant_id: str,
        user_id: str,
        db: AsyncIOMotorDatabase
    ) -> MerchantShareResponse:
        """Create a shareable merchant shop link."""
        # Validate merchant exists
        merchant = await db.merchants.find_one({"user_id": merchant_id})
        
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Merchant not found"
            )
        
        # Generate unique share code
        share_code = ShareService.generate_share_code()
        while await db.merchant_shares.find_one({"share_code": share_code}):
            share_code = ShareService.generate_share_code()
        
        # Create share record
        share_data = {
            "merchant_id": merchant_id,
            "share_code": share_code,
            "user_id": user_id,
            "view_count": 0,
            "created_at": datetime.utcnow()
        }
        
        await db.merchant_shares.insert_one(share_data)
        
        # Generate share links
        share_link = f"{settings.BASE_URL}/merchants/share/{share_code}"
        
        # WhatsApp message with sanitized and URL encoded text
        shop_name = merchant.get("shop_name", "Shop")
        sanitized_shop_name = ShareService.sanitize_text_for_share(shop_name, max_length=50)
        whatsapp_text = f"Découvre cette boutique sur Alia : {sanitized_shop_name} {share_link}"
        whatsapp_link = f"https://wa.me/?text={quote(whatsapp_text)}"
        
        return MerchantShareResponse(
            share_link=share_link,
            share_code=share_code,
            whatsapp_link=whatsapp_link
        )
    
    @staticmethod
    async def get_shared_merchant(share_code: str, db: AsyncIOMotorDatabase) -> dict:
        """Get a shared merchant by code."""
        share = await db.merchant_shares.find_one({"share_code": share_code})
        
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared merchant not found"
            )
        
        # Increment view count
        await db.merchant_shares.update_one(
            {"_id": share["_id"]},
            {"$inc": {"view_count": 1}}
        )
        
        # Get merchant
        merchant = await db.merchants.find_one({"user_id": share["merchant_id"]})
        
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Merchant not found"
            )
        
        return merchant
