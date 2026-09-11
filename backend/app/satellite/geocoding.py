import re
import logging
from typing import Optional, List, Tuple
import httpx

logger = logging.getLogger("satquery.geocoding")

# Built-in high-precision bounding boxes [min_lon, min_lat, max_lon, max_lat] for instant lookup
KNOWN_LOCATIONS = {
    "mumbai": [72.775, 18.890, 72.998, 19.270],
    "hyderabad": [78.237, 17.200, 78.618, 17.580],
    "delhi": [76.840, 28.400, 77.350, 28.880],
    "bengaluru": [77.460, 12.830, 77.750, 13.140],
    "bangalore": [77.460, 12.830, 77.750, 13.140],
    "chennai": [80.120, 12.900, 80.330, 13.230],
    "kolkata": [88.240, 22.450, 88.450, 22.680],
    "pune": [73.730, 18.430, 74.010, 18.630],
    "ahmedabad": [72.480, 22.920, 72.690, 23.120],
    "jaipur": [75.700, 26.800, 75.920, 27.020],
    "london": [-0.350, 51.380, 0.150, 51.670],
    "paris": [2.224, 48.815, 2.469, 48.902],
    "new york": [-74.259, 40.477, -73.700, 40.917],
    "tokyo": [139.560, 35.530, 139.910, 35.820],
    "cairo": [31.120, 29.920, 31.450, 30.180],
    "dubai": [55.100, 24.950, 55.450, 25.320],
    "singapore": [103.600, 1.200, 104.050, 1.480],
    "berlin": [13.088, 52.338, 13.761, 52.675],
    "rotterdam": [4.350, 51.850, 4.600, 51.980],
    "san francisco": [-122.520, 37.700, -122.350, 37.830]
}


def geocode_location(query: str) -> Tuple[Optional[List[float]], Optional[str]]:
    """
    Geocode location name to [min_lon, min_lat, max_lon, max_lat].
    Checks fast city dictionary first, then OpenStreetMap Nominatim API.
    """
    clean_query = query.lower()
    # Strip common sensor terms
    for term in ["sentinel-2", "sentinel-1", "sentinel 2", "sentinel 1", "sentinel", "landsat", "sar", "images", "image", "satellite"]:
        clean_query = clean_query.replace(term, " ")
    clean_query = clean_query.strip()

    # 1. Fast match in known locations
    for city, bbox in KNOWN_LOCATIONS.items():
        if city in clean_query:
            logger.info(f"Geocoded '{city}' via known bounding box: {bbox}")
            return bbox, city.title()

    if not clean_query or len(clean_query) < 3:
        return None, None

    # 2. Live Nominatim Geocoding
    try:
        url = f"https://nominatim.openstreetmap.org/search"
        params = {"q": clean_query, "format": "json", "limit": 1}
        headers = {"User-Agent": "SatQueryAI-RemoteSensing/1.0 (contact: satquery@example.com)"}
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                results = resp.json()
                if results and len(results) > 0:
                    item = results[0]
                    # Nominatim returns [south, north, west, east]
                    south, north, west, east = [float(c) for c in item["boundingbox"]]
                    bbox = [west, south, east, north]
                    name = item.get("display_name", clean_query).split(",")[0]
                    logger.info(f"Geocoded '{clean_query}' via Nominatim: {bbox}")
                    return bbox, name
    except Exception as e:
        logger.warning(f"Nominatim geocoding failed for '{clean_query}': {e}")

    return None, None
