import re
from typing import Dict, Any, List, Optional
from backend.app.satellite.stac_client import stac_client


class SatelliteImageRetrievalService:
    """Interprets user's natural language requests to search live remote sensing products via STAC."""

    def parse_and_search(self, nl_query: str) -> Dict[str, Any]:
        """
        Parses location, date, sensor from NL string (e.g. 'Mumbai Sentinel-2', 'Find Sentinel-2 images of Hyderabad'):
        Executes live STAC search and returns real satellite imagery without hardcoded fallbacks.
        """
        query_lower = nl_query.lower()

        # Detect satellite preference
        satellite = None
        if "sentinel-2" in query_lower or "sentinel 2" in query_lower:
            satellite = "Sentinel-2"
        elif "sentinel-1" in query_lower or "sar" in query_lower or "radar" in query_lower:
            satellite = "Sentinel-1"
        elif "landsat" in query_lower:
            satellite = "Landsat"

        # Detect dates (months, years)
        date_pattern = r"\b(201[5-9]|202[0-6])\b"
        year_match = re.search(date_pattern, query_lower)
        date_str = f"{year_match.group(1)}-01-01T00:00:00Z/{year_match.group(1)}-12-31T23:59:59Z" if year_match else None

        # Search live STAC
        search_result = stac_client.search_live_imagery(
            query_text=nl_query,
            satellite=satellite,
            date_range=date_str
        )

        return search_result


retrieval_service = SatelliteImageRetrievalService()

