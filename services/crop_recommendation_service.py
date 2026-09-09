"""Simple, explainable crop ranking built on the local knowledge base."""

from typing import Any

import pandas as pd


class CropRecommendationService:
    """Rank dataset rows and expose missing information for follow-up questions."""

    REQUIRED_FIELDS = {
        "location": "location (state or district)",
        "season": "season",
        "soil_type": "soil type",
        "water_availability": "water availability",
        "previous_crop": "previous crop",
    }

    def __init__(self, knowledge_service):
        self.knowledge_service = knowledge_service

    def missing_fields(self, details: dict[str, Any]) -> list[str]:
        return [label for key, label in self.REQUIRED_FIELDS.items() if not str(details.get(key, "")).strip()]

    @staticmethod
    def invalid_fields(details: dict[str, Any]) -> list[str]:
        """Flag values that should be verified before they affect ranking."""
        soil_ph = details.get("soil_ph", "")
        if soil_ph in ("", None):
            return []
        try:
            value = float(soil_ph)
        except (TypeError, ValueError):
            return ["soil pH must be a number"]
        if value < 3.5 or value > 10.0:
            return [f"soil pH {value:g} is unusual; retest the soil before choosing a crop"]
        return []

    @staticmethod
    def _text_match(value: Any, query: Any) -> bool:
        return str(query).lower() in str(value).lower()

    def recommend(self, details: dict[str, Any], weather: dict[str, Any] | None = None, market: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return ranked crops plus transparent reasons and limitations."""
        missing = self.missing_fields(details)
        invalid = self.invalid_fields(details)
        rows = self.knowledge_service.data.copy()
        if missing:
            return {"missing": missing, "invalid": invalid, "recommendations": [], "message": "More farmer details are needed before ranking crops."}

        scores = []
        for _, row in rows.iterrows():
            score = 0
            reasons = []
            for field, row_column, label in [
                ("season", "season", "season"),
                ("soil_type", "soil_type", "soil"),
                ("location", "state", "location"),
                ("water_availability", "water_requirement", "water"),
            ]:
                value = details.get(field, "")
                if self._text_match(row[row_column], value) or str(value).lower() in str(row[row_column]).lower():
                    score += 2
                    reasons.append(f"matches {label}")
            previous = str(details.get("previous_crop", "")).lower()
            crop_name = str(row.get("crop_name", "")).lower()
            if previous and previous in crop_name:
                score -= 5
                reasons.append("is the same as the previous crop; rotation needs local review")
            elif previous and previous in str(row.get("previous_crop", "")).lower():
                score += 1
                reasons.append("supports the stated crop rotation")
            if weather and weather.get("available"):
                score += 1
                reasons.append("weather data was available for review")
            if market and market.get("available"):
                score += 1
                reasons.append("market data was available for review")
            scores.append({
                "crop": row["crop_name"],
                "score": score,
                "reasons": reasons or ["is included as a broad fallback option"],
                "details": row.to_dict(),
            })
        scores.sort(key=lambda item: item["score"], reverse=True)
        return {
            "missing": [],
            "invalid": invalid,
            "recommendations": scores[:3],
            "message": "These are dataset-based suggestions, not guaranteed outcomes. Verify unusual soil readings before planting.",
        }
