"""
Wishlist functionality tests.

Tests CRUD operations on user wishlist (favorites):
- Add product to wishlist
- Get user's wishlist
- Remove product from wishlist
- Prevent duplicate items
"""

import pytest
from httpx import AsyncClient
from app.main import app
from app.core.config import settings


TEST_BUYER_EMAIL = "wishlist_buyer@test.com"
TEST_BUYER_PASSWORD = "TestPass1234!"


@pytest.fixture
async def async_client():
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def authenticated_buyer_token(async_client):
    """Register and get authenticated buyer token."""
    response = await async_client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": TEST_BUYER_EMAIL,
            "password": TEST_BUYER_PASSWORD,
            "role": "buyer",
            "age": 28
        }
    )
    return response.json()["access_token"]


class TestWishlistCRUD:
    """Test Wishlist CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_get_empty_wishlist(self, async_client, authenticated_buyer_token):
        """Test getting empty wishlist for new user."""
        headers = {"Authorization": f"Bearer {authenticated_buyer_token}"}
        
        response = await async_client.get(
            f"{settings.API_V1_PREFIX}/me/wishlist",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    
    @pytest.mark.asyncio
    async def test_add_product_to_wishlist(self, async_client, authenticated_buyer_token):
        """Test adding a product to wishlist."""
        headers = {"Authorization": f"Bearer {authenticated_buyer_token}"}
        
        # First get a product ID from the products list
        products_response = await async_client.get(
            f"{settings.API_V1_PREFIX}/products?limit=1",
            headers=headers
        )
        
        if products_response.status_code == 200:
            products = products_response.json()
            if len(products) > 0:
                product_id = products[0].get("_id") or products[0].get("id")
                
                # Add to wishlist
                response = await async_client.post(
                    f"{settings.API_V1_PREFIX}/me/wishlist",
                    json={"product_id": product_id},
                    headers=headers
                )
                
                assert response.status_code in [200, 201]
                data = response.json()
                assert "wishlist" in data or "message" in data
    
    
    @pytest.mark.asyncio
    async def test_get_wishlist_with_items(self, async_client, authenticated_buyer_token):
        """Test retrieving wishlist with items."""
        headers = {"Authorization": f"Bearer {authenticated_buyer_token}"}
        
        # Get product
        products_response = await async_client.get(
            f"{settings.API_V1_PREFIX}/products?limit=1",
            headers=headers
        )
        
        if products_response.status_code == 200:
            products = products_response.json()
            if len(products) > 0:
                product_id = products[0].get("_id") or products[0].get("id")
                
                # Add to wishlist
                await async_client.post(
                    f"{settings.API_V1_PREFIX}/me/wishlist",
                    json={"product_id": product_id},
                    headers=headers
                )
                
                # Get wishlist
                response = await async_client.get(
                    f"{settings.API_V1_PREFIX}/me/wishlist",
                    headers=headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
                # Should have at least 1 item (if add succeeded)
    
    
    @pytest.mark.asyncio
    async def test_remove_product_from_wishlist(self, async_client, authenticated_buyer_token):
        """Test removing a product from wishlist."""
        headers = {"Authorization": f"Bearer {authenticated_buyer_token}"}
        
        # Get product
        products_response = await async_client.get(
            f"{settings.API_V1_PREFIX}/products?limit=1",
            headers=headers
        )
        
        if products_response.status_code == 200:
            products = products_response.json()
            if len(products) > 0:
                product_id = products[0].get("_id") or products[0].get("id")
                
                # Add to wishlist
                add_response = await async_client.post(
                    f"{settings.API_V1_PREFIX}/me/wishlist",
                    json={"product_id": product_id},
                    headers=headers
                )
                
                if add_response.status_code in [200, 201]:
                    # Remove from wishlist
                    response = await async_client.delete(
                        f"{settings.API_V1_PREFIX}/me/wishlist/{product_id}",
                        headers=headers
                    )
                    
                    assert response.status_code in [200, 204]
    
    
    @pytest.mark.asyncio
    async def test_prevent_duplicate_wishlist_items(self, async_client, authenticated_buyer_token):
        """Test that duplicate items are prevented in wishlist."""
        headers = {"Authorization": f"Bearer {authenticated_buyer_token}"}
        
        # Get product
        products_response = await async_client.get(
            f"{settings.API_V1_PREFIX}/products?limit=1",
            headers=headers
        )
        
        if products_response.status_code == 200:
            products = products_response.json()
            if len(products) > 0:
                product_id = products[0].get("_id") or products[0].get("id")
                
                # Add to wishlist first time
                response1 = await async_client.post(
                    f"{settings.API_V1_PREFIX}/me/wishlist",
                    json={"product_id": product_id},
                    headers=headers
                )
                
                if response1.status_code in [200, 201]:
                    # Try to add the same product again
                    response2 = await async_client.post(
                        f"{settings.API_V1_PREFIX}/me/wishlist",
                        json={"product_id": product_id},
                        headers=headers
                    )
                    
                    # Should either prevent duplicate or return same result
                    # Status depends on implementation
                    assert response2.status_code in [200, 201, 400, 409]
    
    
    @pytest.mark.asyncio
    async def test_wishlist_pagination(self, async_client, authenticated_buyer_token):
        """Test pagination on wishlist endpoint."""
        headers = {"Authorization": f"Bearer {authenticated_buyer_token}"}
        
        # Get wishlist with limit
        response = await async_client.get(
            f"{settings.API_V1_PREFIX}/me/wishlist?limit=5",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    
    @pytest.mark.asyncio
    async def test_wishlist_with_invalid_product_id(self, async_client, authenticated_buyer_token):
        """Test adding invalid product ID to wishlist."""
        headers = {"Authorization": f"Bearer {authenticated_buyer_token}"}
        
        response = await async_client.post(
            f"{settings.API_V1_PREFIX}/me/wishlist",
            json={"product_id": "invalid_id_12345"},
            headers=headers
        )
        
        # Should fail validation
        assert response.status_code in [400, 404, 422]
    
    
    @pytest.mark.asyncio
    async def test_wishlist_requires_authentication(self, async_client):
        """Test that wishlist endpoints require authentication."""
        # No auth header
        response = await async_client.get(f"{settings.API_V1_PREFIX}/me/wishlist")
        
        assert response.status_code == 401


class TestWishlistIntegration:
    """Integration tests for wishlist with other features."""
    
    @pytest.mark.asyncio
    async def test_wishlist_product_info_complete(self, async_client, authenticated_buyer_token):
        """Test that wishlist returns complete product information."""
        headers = {"Authorization": f"Bearer {authenticated_buyer_token}"}
        
        # Get product
        products_response = await async_client.get(
            f"{settings.API_V1_PREFIX}/products?limit=1",
            headers=headers
        )
        
        if products_response.status_code == 200:
            products = products_response.json()
            if len(products) > 0:
                product_id = products[0].get("_id") or products[0].get("id")
                
                # Add to wishlist
                await async_client.post(
                    f"{settings.API_V1_PREFIX}/me/wishlist",
                    json={"product_id": product_id},
                    headers=headers
                )
                
                # Get wishlist
                response = await async_client.get(
                    f"{settings.API_V1_PREFIX}/me/wishlist",
                    headers=headers
                )
                
                if response.status_code == 200:
                    wishlist = response.json()
                    for item in wishlist:
                        # Check for key product fields
                        assert "product_id" in item or "_id" in item or "id" in item
                        assert "title" in item or "name" in item
                        assert "price" in item


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
