from datetime import datetime
from bson import ObjectId


def object_id_to_str(obj_id) -> str:
    """Convert ObjectId to string."""
    if isinstance(obj_id, ObjectId):
        return str(obj_id)
    return obj_id


def format_document(document: dict) -> dict:
    """Format MongoDB document for API response."""
    if document and "_id" in document:
        document["id"] = str(document["_id"])
        del document["_id"]
    return document


def get_current_timestamp() -> datetime:
    """Get current UTC timestamp."""
    return datetime.utcnow()
