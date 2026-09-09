"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

APP_TITLE = "AI-Powered Multilingual Voice Assistant for Smart Agriculture"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-3.6-flash").strip()
GEMINI_LIVE_MODEL = os.getenv(
    "GEMINI_LIVE_MODEL",
    os.getenv("GEMINI_MODEL", "gemini-2.5-flash-native-audio-preview-09-2025"),
).strip()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "").strip()
WEATHER_API_URL = os.getenv("WEATHER_API_URL", "https://api.openweathermap.org/data/2.5/weather")
MARKET_API_KEY = os.getenv("MARKET_API_KEY", "").strip()
MARKET_API_URL = os.getenv("MARKET_API_URL", "https://api.example.com/market-prices")
KNOWLEDGE_FILE = BASE_DIR / "crop_knowledge.csv"
SAMPLE_DATA_FILE = BASE_DIR / "data" / "sample_crop_data.csv"
SUPPORTED_LANGUAGES = {
    "English": "English",
    "తెలుగు (Telugu)": "Telugu",
    "हिन्दी (Hindi)": "Hindi",
    "தமிழ் (Tamil)": "Tamil",
}
