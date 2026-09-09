"""Optional weather lookup with a safe offline fallback."""

from typing import Any

import requests


class WeatherService:
    def __init__(self, api_key: str, api_url: str, timeout: int = 8):
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout

    def get_weather(self, location: str) -> dict[str, Any]:
        if not self.api_key:
            return {"available": False, "message": "Weather API key is not configured."}
        try:
            response = requests.get(
                self.api_url,
                params={"q": location, "appid": self.api_key, "units": "metric"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            return {
                "available": True,
                "temperature_c": payload.get("main", {}).get("temp"),
                "description": payload.get("weather", [{}])[0].get("description", ""),
                "raw": payload,
            }
        except (requests.RequestException, ValueError, IndexError, KeyError) as exc:
            return {"available": False, "message": f"Weather data is unavailable: {exc}"}
