import re
import logging
from typing import List, Dict, Any, Optional
import httpx

from backend.app.satellite.geocoding import geocode_location

logger = logging.getLogger("satquery.stac")

# Live Public STAC API Endpoints
EARTH_SEARCH_API = "https://earth-search.aws.element84.com/v1/search"
PLANETARY_COMPUTER_API = "https://planetarycomputer.microsoft.com/api/stac/v1/search"


class LiveSTACClient:
    """
    Live Satellite STAC API Client for real-time location-based retrieval.
    Queries Earth Search (AWS Sentinel-2 / Sentinel-1 / Landsat) and Planetary Computer.
    """

    def __init__(self):
        self.endpoint = EARTH_SEARCH_API

    def search_live_imagery(
        self,
        query_text: str,
        bbox: Optional[List[float]] = None,
        date_range: Optional[str] = None,
        satellite: Optional[str] = None,
        max_cloud_cover: float = 30.0,
        limit: int = 8
    ) -> Dict[str, Any]:
        """
        Execute real-time STAC search using location geocoding and filters.
        Returns authentic retrieved satellite scenes with metadata and asset links.
        """
        location_name = None

        # 1. Geocode location if bbox is not explicitly provided
        if not bbox and query_text:
            bbox, location_name = geocode_location(query_text)

        # 2. Determine target satellite collection
        q_lower = (query_text or "").lower()
        sat_lower = (satellite or "").lower()

        if "sentinel-1" in q_lower or "sar" in q_lower or "radar" in sat_lower or "sentinel-1" in sat_lower:
            collections = ["sentinel-1-grd"]
            sensor_type = "Sentinel-1 SAR"
        elif "landsat" in q_lower or "landsat" in sat_lower:
            collections = ["landsat-c2-l2"]
            sensor_type = "Landsat-9"
        else:
            collections = ["sentinel-2-l2a", "sentinel-2-c1-l2a"]
            sensor_type = "Sentinel-2 MSI"

        # 3. Determine datetime filter
        datetime_filter = None
        if date_range:
            datetime_filter = date_range
        else:
            # Check for year or month in query
            year_match = re.search(r"\b(201[5-9]|202[0-6])\b", query_text)
            if year_match:
                year = year_match.group(1)
                datetime_filter = f"{year}-01-01T00:00:00Z/{year}-12-31T23:59:59Z"
            else:
                # Default to recent multi-year span for high recall
                datetime_filter = "2023-01-01T00:00:00Z/.."

        # If location could not be geocoded and no bbox provided, return clear empty result immediately
        if not bbox:
            return {
                "status": "empty",
                "source": "Earth Search STAC API (element84.com)",
                "query": query_text,
                "geocoded_location": None,
                "bbox": None,
                "sensor": sensor_type,
                "count": 0,
                "results": [],
                "message": f"Could not determine geographical coordinates for '{query_text}'. Please enter a recognized city or region name (e.g. 'Mumbai', 'Hyderabad', 'London', 'Tokyo')."
            }

        # Build STAC Search Request
        payload = {
            "collections": collections,
            "bbox": bbox,
            "limit": limit
        }

        if datetime_filter:
            payload["datetime"] = datetime_filter

        # Cloud cover filter for optical sensors
        if "sentinel-1" not in collections[0]:
            payload["query"] = {
                "eo:cloud_cover": {"lte": max_cloud_cover}
            }

        logger.info(f"Submitting Live STAC query to {self.endpoint} with payload: {payload}")

        items = []
        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(self.endpoint, json=payload)
                if resp.status_code == 200:
                    features = resp.json().get("features", [])
                    items = self._format_stac_features(features, location_name or query_text)
                else:
                    logger.warning(f"Earth Search returned {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.error(f"Live STAC query failed on Earth Search: {e}")

        # If primary endpoint returned 0 and we had cloud filter, try without strict cloud filter
        if not items and payload.get("query"):
            try:
                payload.pop("query", None)
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(self.endpoint, json=payload)
                    if resp.status_code == 200:
                        features = resp.json().get("features", [])
                        items = self._format_stac_features(features, location_name or query_text)
            except Exception as e:
                logger.error(f"Fallback STAC query failed: {e}")

        # Construct clear feedback message
        if items:
            message = f"Found {len(items)} real-time {sensor_type} acquisitions for {location_name or query_text} via Earth Search STAC."
        else:
            if not bbox:
                message = f"Could not determine geographical coordinates for '{query_text}'. Please enter a recognized city or region name (e.g. 'Mumbai', 'Hyderabad', 'Cairo')."
            else:
                message = f"No live satellite imagery found for '{query_text}' matching sensor {sensor_type} and cloud cover <= {max_cloud_cover}%. Try increasing the cloud threshold or changing the date range."

        return {
            "status": "success" if len(items) > 0 else "empty",
            "source": "Earth Search STAC API (element84.com)",
            "query": query_text,
            "geocoded_location": location_name,
            "bbox": bbox,
            "sensor": sensor_type,
            "count": len(items),
            "results": items,
            "message": message
        }

    def _format_stac_features(self, features: List[Dict[str, Any]], location_label: str) -> List[Dict[str, Any]]:
        formatted = []
        for feat in features:
            props = feat.get("properties", {})
            assets = feat.get("assets", {})

            # Extract real image/preview URL from STAC assets
            preview_url = None
            if "rendered_preview" in assets:
                preview_url = assets["rendered_preview"].get("href")
            elif "thumbnail" in assets:
                preview_url = assets["thumbnail"].get("href")
            elif "visual" in assets:
                preview_url = assets["visual"].get("href")
            elif "overview" in assets:
                preview_url = assets["overview"].get("href")

            # Extract cloud coverage
            cloud_cov = props.get("eo:cloud_cover")
            if cloud_cov is not None:
                cloud_cov = round(float(cloud_cov), 2)

            platform = props.get("platform", "Sentinel-2")
            instruments = props.get("instruments", ["MSI"])
            instrument_str = ", ".join(instruments) if isinstance(instruments, list) else str(instruments)
            dt_raw = props.get("datetime", "Unknown")
            dt_str = dt_raw[:10] if len(dt_raw) >= 10 else dt_raw

            formatted.append({
                "id": feat.get("id"),
                "title": f"{platform.upper()} {instrument_str} - {location_label}",
                "satellite": platform.upper(),
                "sensor": instrument_str,
                "date": dt_str,
                "datetime": dt_raw,
                "location": location_label,
                "cloud_coverage": cloud_cov,
                "resolution": "10m" if "sentinel-2" in platform.lower() else "10m-20m",
                "thumbnail_url": preview_url,
                "bbox": feat.get("bbox"),
                "stac_item_url": feat.get("links", [{}])[0].get("href", "")
            })

        return formatted


stac_client = LiveSTACClient()
