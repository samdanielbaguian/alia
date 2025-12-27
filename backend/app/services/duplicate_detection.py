from typing import List, Dict, Optional
from app.core.database import get_database


async def detect_duplicate_product(title: str, description: str) -> List[Dict]:
    """
    Detect duplicate products by comparing title and description similarity.
    
    This function searches for local products (is_imported=false) that have similar
    titles or descriptions to help merchants avoid importing products that already
    exist locally.
    
    Args:
        title: Product title to search for
        description: Product description to search for
        
    Returns:
        List of similar products with similarity scores
        
    Algorithm:
        1. Search for products with similar titles (word matching)
        2. Calculate basic similarity score based on common words
        3. Return products sorted by similarity score
        
    TODO: Implement more sophisticated similarity detection using:
        - TF-IDF or word embeddings
        - Machine learning models (e.g., sentence transformers)
        - Fuzzy string matching (e.g., fuzzywuzzy)
    """
    db = get_database()
    
    # Normalize input for comparison
    title_words = set(title.lower().split())
    description_words = set(description.lower().split())
    
    # Find local products (not imported)
    local_products = await db.products.find({"is_imported": False}).to_list(length=100)
    
    similar_products = []
    
    for product in local_products:
        # Calculate similarity score
        product_title_words = set(product["title"].lower().split())
        product_desc_words = set(product.get("description", "").lower().split())
        
        # Count common words in title (weighted more heavily)
        title_common = len(title_words.intersection(product_title_words))
        title_total = len(title_words.union(product_title_words))
        title_similarity = (title_common / title_total * 100) if title_total > 0 else 0
        
        # Count common words in description
        desc_common = len(description_words.intersection(product_desc_words))
        desc_total = len(description_words.union(product_desc_words))
        desc_similarity = (desc_common / desc_total * 100) if desc_total > 0 else 0
        
        # Combined similarity score (title weighted 70%, description 30%)
        similarity_score = (title_similarity * 0.7) + (desc_similarity * 0.3)
        
        # Only include products with similarity > 40%
        if similarity_score > 40:
            similar_products.append({
                "product_id": str(product["_id"]),
                "title": product["title"],
                "description": product.get("description", ""),
                "price": product["price"],
                "merchant_id": product["merchant_id"],
                "similarity_score": round(similarity_score, 2)
            })
    
    # Sort by similarity score (highest first)
    similar_products.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    return similar_products
