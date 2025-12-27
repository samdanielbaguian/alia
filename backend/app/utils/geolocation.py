import math
from typing import Dict


def calculate_distance(location1: Dict[str, float], location2: Dict[str, float]) -> float:
    """
    Calculate the distance between two geographic points using the Haversine formula.
    
    Args:
        location1: Dictionary with 'lat' and 'lng' keys (in degrees)
        location2: Dictionary with 'lat' and 'lng' keys (in degrees)
        
    Returns:
        Distance in kilometers
        
    The Haversine formula calculates the great-circle distance between two points
    on a sphere given their longitudes and latitudes.
    """
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert latitude and longitude from degrees to radians
    lat1 = math.radians(location1["lat"])
    lon1 = math.radians(location1["lng"])
    lat2 = math.radians(location2["lat"])
    lon2 = math.radians(location2["lng"])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    
    return distance
