"""Gemini Live and text response integration.

The Live API is optional in this first version. Text mode remains usable without a key.
"""

from typing import Any

from google import genai
from google.genai import types

from prompts import LIVE_CONFIG, SYSTEM_PROMPT


class GeminiLiveService:
    def __init__(self, api_key: str, text_model: str, live_model: str):
        self.api_key = api_key
        self.text_model = text_model
        self.live_model = live_model
        self.client = genai.Client(api_key=api_key) if api_key else None

    def generate_text(self, prompt: str) -> str:
        if not self.client:
            return "Gemini is not configured. I can still show dataset-based crop results. Please verify advice with a local agricultural officer."
        try:
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            return response.text or "I could not generate a response. Please try again."
        except Exception as exc:
            message = str(exc).lower()
            if "401" in message or "403" in message or "api key" in message or "unauthenticated" in message:
                return "Gemini rejected the API key. Create a new Gemini API key, check that it is enabled, and update GEMINI_API_KEY in .env."
            if "400" in message or "invalid_argument" in message or "only supports real-time" in message:
                return f"Gemini rejected the request configuration. Check GEMINI_TEXT_MODEL (currently '{self.text_model}')."
            return "The Gemini service is temporarily unavailable. Please try again later."

    def transcribe_audio(self, audio_bytes: bytes, mime_type: str, language: str) -> str:
        """Transcribe one recorded audio clip using the normal Gemini endpoint."""
        if not self.client:
            return "Gemini is not configured. Add GEMINI_API_KEY to .env before using voice transcription."
        try:
            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type or "audio/wav")
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=[
                    audio_part,
                    f"Transcribe this farmer's recording accurately. The spoken language is likely {language}. Return only the transcription, with no explanation.",
                ],
            )
            return response.text.strip() if response.text else "I could not understand the recording. Please try again."
        except Exception as exc:
            message = str(exc).lower()
            if "401" in message or "403" in message or "api key" in message or "unauthenticated" in message:
                return "Gemini rejected the API key. Create a new key and update GEMINI_API_KEY in .env."
            return f"Audio transcription failed: {exc}"

    async def live_session(self):
        """Create a current SDK Live API session for future audio streaming."""
        if not self.client:
            raise RuntimeError("GEMINI_API_KEY is missing. Add it to .env to enable Live voice mode.")
        return self.client.aio.live.connect(model=self.live_model, config=types.LiveConnectConfig(**LIVE_CONFIG))

    @staticmethod
    def audio_note() -> str:
        return "Live microphone streaming requires a browser audio bridge. The text fallback is active in this version."
