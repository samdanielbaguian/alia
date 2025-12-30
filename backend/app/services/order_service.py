"""
Order service for managing order business logic and status transitions.
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId


class OrderService:
    """Service class for order management business logic."""
    
    # Valid status transitions
    STATUS_TRANSITIONS = {
        "pending": ["confirmed", "cancelled"],
        "confirmed": ["shipped", "cancelled"],
        "shipped": ["delivered"],
        "delivered": [],  # Final state
        "cancelled": []   # Final state
    }
    
    @staticmethod
    async def get_merchant_by_user_id(user_id: str, db: AsyncIOMotorDatabase) -> Optional[dict]:
        """Get merchant profile by user_id."""
        merchant = await db.merchants.find_one({"user_id": user_id})
        return merchant
    
    @staticmethod
    async def verify_order_access(order: dict, user_id: str, user_role: str, db: AsyncIOMotorDatabase) -> bool:
        """
        Verify user has permission to access/modify this order.
        - Customers can only access their own orders
        - Merchants can only access orders they received
        - Admins can access all orders (if role exists)
        """
        # Admin has full access (if role exists in the future)
        if user_role == "admin":
            return True
        
        # Customer can access their own orders
        if user_role == "buyer" and order["user_id"] == user_id:
            return True
        
        # Merchant can access orders they received
        if user_role == "merchant":
            merchant = await OrderService.get_merchant_by_user_id(user_id, db)
            if merchant and order["merchant_id"] == merchant["user_id"]:
                return True
        
        return False
    
    @staticmethod
    def validate_status_transition(current_status: str, new_status: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if status transition is allowed.
        Returns (is_valid, error_message)
        """
        if current_status not in OrderService.STATUS_TRANSITIONS:
            return False, f"Invalid current status: {current_status}"
        
        valid_next_statuses = OrderService.STATUS_TRANSITIONS[current_status]
        
        if new_status not in valid_next_statuses:
            if not valid_next_statuses:
                return False, f"Order is in final state '{current_status}' and cannot be modified"
            return False, f"Cannot transition from '{current_status}' to '{new_status}'. Valid transitions: {', '.join(valid_next_statuses)}"
        
        return True, None
    
    @staticmethod
    async def can_user_change_status(
        order: dict,
        new_status: str,
        user_id: str,
        user_role: str,
        db: AsyncIOMotorDatabase
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if user has permission to change order to new status.
        Returns (can_change, error_message)
        """
        current_status = order["status"]
        
        # Check if transition is valid
        is_valid, error_msg = OrderService.validate_status_transition(current_status, new_status)
        if not is_valid:
            return False, error_msg
        
        # Check role-based permissions
        if new_status in ["confirmed", "shipped", "delivered"]:
            # Only merchant can confirm, ship, or deliver
            if user_role != "merchant":
                return False, "Only merchants can confirm, ship, or deliver orders"
            
            merchant = await OrderService.get_merchant_by_user_id(user_id, db)
            if not merchant or order["merchant_id"] != merchant["user_id"]:
                return False, "You can only modify orders for your own shop"
        
        elif new_status == "cancelled":
            # Customer can cancel if pending
            if user_role == "buyer":
                if current_status != "pending":
                    return False, "Customers can only cancel pending orders"
                if order["user_id"] != user_id:
                    return False, "You can only cancel your own orders"
            
            # Merchant can cancel if pending or confirmed
            elif user_role == "merchant":
                if current_status not in ["pending", "confirmed"]:
                    return False, "Merchants can only cancel pending or confirmed orders"
                merchant = await OrderService.get_merchant_by_user_id(user_id, db)
                if not merchant or order["merchant_id"] != merchant["user_id"]:
                    return False, "You can only cancel orders for your own shop"
            
            else:
                return False, "Invalid role for cancellation"
        
        return True, None
    
    @staticmethod
    async def update_order_status(
        order_id: str,
        new_status: str,
        user_id: str,
        user_role: str,
        db: AsyncIOMotorDatabase,
        note: Optional[str] = None,
        tracking_number: Optional[str] = None,
        cancelled_by: Optional[str] = None,
        cancellation_reason: Optional[str] = None
    ) -> dict:
        """
        Update order status with validation and side effects.
        """
        # Get order
        try:
            order = await db.orders.find_one({"_id": ObjectId(order_id)})
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid order ID"
            )
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        current_status = order["status"]
        
        # Verify user has permission to change status
        can_change, error_msg = await OrderService.can_user_change_status(
            order, new_status, user_id, user_role, db
        )
        
        if not can_change:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )
        
        # Validate tracking number for shipped status
        if new_status == "shipped" and not tracking_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tracking number is required when shipping an order"
            )
        
        # Prepare update data
        update_data = {
            "status": new_status,
            "updated_at": datetime.utcnow()
        }
        
        # Add status history entry
        history_entry = {
            "status": new_status,
            "changed_at": datetime.utcnow(),
            "changed_by": user_id,
            "note": note
        }
        
        # Update timestamps based on status
        if new_status == "shipped":
            update_data["shipped_at"] = datetime.utcnow()
            update_data["tracking_number"] = tracking_number
        elif new_status == "delivered":
            update_data["delivered_at"] = datetime.utcnow()
        elif new_status == "cancelled":
            update_data["cancelled_by"] = cancelled_by
            if cancellation_reason:
                update_data["cancellation_reason"] = cancellation_reason
        
        # Update order in database
        await db.orders.update_one(
            {"_id": ObjectId(order_id)},
            {
                "$set": update_data,
                "$push": {"status_history": history_entry}
            }
        )
        
        # Handle side effects
        if new_status == "cancelled":
            # Restore product stock
            await OrderService.restore_product_stock(order, db)
            
            # TODO: Initiate refund if payment was completed
            # TODO: Send notification to both parties
        
        # TODO: Send notification to customer on status change
        
        # Get updated order
        updated_order = await db.orders.find_one({"_id": ObjectId(order_id)})
        
        return {
            "message": f"Order status updated to {new_status}",
            "order_id": order_id,
            "old_status": current_status,
            "new_status": new_status,
            "updated_at": update_data["updated_at"]
        }
    
    @staticmethod
    async def restore_product_stock(order: dict, db: AsyncIOMotorDatabase):
        """Restore product stock when order is cancelled."""
        for product in order["products"]:
            try:
                await db.products.update_one(
                    {"_id": ObjectId(product["product_id"])},
                    {"$inc": {"stock": product["quantity"]}}
                )
            except Exception as e:
                # Log error but don't fail the cancellation
                print(f"Error restoring stock for product {product['product_id']}: {e}")
    
    @staticmethod
    def get_valid_next_statuses(current_status: str, user_role: str) -> List[str]:
        """Get list of valid next statuses based on current status and role."""
        if current_status not in OrderService.STATUS_TRANSITIONS:
            return []
        
        valid_statuses = OrderService.STATUS_TRANSITIONS[current_status]
        
        # Filter based on role
        if user_role == "buyer":
            # Customers can only cancel pending orders
            if current_status == "pending" and "cancelled" in valid_statuses:
                return ["cancelled"]
            return []
        
        elif user_role == "merchant":
            # Merchants can perform all transitions except customer-only cancellations
            return valid_statuses
        
        return []
    
    @staticmethod
    async def can_cancel_order(order_id: str, user_id: str, user_role: str, db: AsyncIOMotorDatabase) -> Tuple[bool, Optional[str]]:
        """Check if user can cancel this order."""
        try:
            order = await db.orders.find_one({"_id": ObjectId(order_id)})
        except Exception:
            return False, "Invalid order ID"
        
        if not order:
            return False, "Order not found"
        
        current_status = order["status"]
        
        # Cannot cancel if already delivered or cancelled
        if current_status in ["delivered", "cancelled"]:
            return False, f"Cannot cancel order in '{current_status}' status"
        
        # Cannot cancel if shipped
        if current_status == "shipped":
            return False, "Cannot cancel order that has already been shipped"
        
        # Check user permissions
        if user_role == "buyer":
            if current_status != "pending":
                return False, "Customers can only cancel pending orders"
            if order["user_id"] != user_id:
                return False, "You can only cancel your own orders"
        
        elif user_role == "merchant":
            if current_status not in ["pending", "confirmed"]:
                return False, "Merchants can only cancel pending or confirmed orders"
            merchant = await OrderService.get_merchant_by_user_id(user_id, db)
            if not merchant or order["merchant_id"] != merchant["user_id"]:
                return False, "You can only cancel orders for your own shop"
        
        else:
            return False, "Invalid role"
        
        return True, None
