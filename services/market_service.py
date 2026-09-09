"""Optional market lookup with a safe offline fallback."""

from typing import Any

import requests


class MarketService:
    def __init__(self, api_key: str, api_url: str, timeout: int = 8):
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout

    def get_prices(self, crop: str, location: str) -> dict[str, Any]:
        if not self.api_key:
            return {"available": False, "message": "Market API key is not configured."}
        try:
            response = requests.get(
                self.api_url,
                params={"crop": crop, "location": location, "api_key": self.api_key},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return {"available": True, "data": response.json()}
        except (requests.RequestException, ValueError) as exc:
            return {"available": False, "message": f"Market data is unavailable: {exc}"}
