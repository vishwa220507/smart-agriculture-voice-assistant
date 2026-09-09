"""CSV-backed retrieval for grounded agricultural context."""

from pathlib import Path
from typing import Any

import pandas as pd


class KnowledgeService:
    """Load and retrieve rows from the local crop knowledge base."""

    def __init__(self, csv_path: Path):
        self.csv_path = Path(csv_path)
        self.data = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        try:
            data = pd.read_csv(self.csv_path).fillna("")
            required = {"crop_name", "season", "soil_type", "source", "last_verified_date"}
            missing = required.difference(data.columns)
            if missing:
                raise ValueError(f"Knowledge file is missing columns: {', '.join(sorted(missing))}")
            return data
        except (OSError, ValueError, pd.errors.ParserError) as exc:
            raise RuntimeError(f"Could not load crop knowledge data: {exc}") from exc

    @staticmethod
    def _matches(value: str, query: str) -> bool:
        return not query or query.lower() in str(value).lower()

    def search(self, filters: dict[str, Any], limit: int = 5) -> pd.DataFrame:
        """Return rows matching the strongest available farmer details."""
        result = self.data.copy()
        for column, query in filters.items():
            if column not in result.columns or not query:
                continue
            result = result[result[column].apply(lambda value: self._matches(value, str(query)))]
        if result.empty:
            result = self.data.copy()
        return result.head(limit)

    def format_context(self, rows: pd.DataFrame) -> str:
        """Format retrieved rows for a model prompt without hiding provenance."""
        if rows.empty:
            return "No matching crop knowledge was found."
        fields = [
            "crop_name", "season", "state", "soil_type", "soil_ph",
            "water_requirement", "sowing_period", "crop_duration",
            "fertilizer_guidance", "common_pests", "common_diseases",
            "market_information", "source", "last_verified_date",
        ]
        available = [field for field in fields if field in rows.columns]
        return "\n\n".join(
            "; ".join(f"{field}: {row[field]}" for field in available)
            for _, row in rows.iterrows()
        )
