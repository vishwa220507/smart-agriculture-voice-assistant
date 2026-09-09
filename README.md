# AI-Powered Multilingual Voice Assistant for Smart Agriculture

A beginner-friendly Streamlit prototype for farmers to ask agricultural questions in English, Telugu, Hindi, or Tamil. It uses a local CSV knowledge base for retrieval and can call the Google Gemini SDK for grounded text responses. Weather and market integrations are optional and fail safely when unavailable.

## Sharing securely with your team

This project is safe to share only after rotating any API key that was pasted into chat, source control, screenshots, or logs. The repository ignores `.env`, virtual environments, caches, and Streamlit secrets. Never commit a real API key.

To create a team copy:

```powershell
git clone <your-repository-url>
cd smart_agriculture
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Each teammate must put their own rotated API key in their private `.env` file. Use a private GitHub repository while the data and integrations are still prototypes. For a deployed website, put the API key in the hosting provider's secret manager and never expose it to browser-side code.

## What works in the first version

- Text questions with a selected response language.
- Conversation history stored for the current Streamlit session.
- Crop ranking using location, season, soil, water, previous crop, and optional weather/market availability.
- CSV retrieval with source and last verified date shown in the UI.
- Fertilizer, irrigation, pest, and disease context from the dataset.
- Missing required farmer details are reported before ranking.
- `st.audio_input` microphone capture with one-clip Gemini transcription and a text fallback.
- Safe offline behavior when Gemini, weather, or market keys are missing.

The included rows are explicitly illustrative. Replace them with reviewed agriculture department or university data before production use.

## Installation

Windows PowerShell:

```powershell
cd c:\Users\SMILEY\Desktop\smart_agriculture
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If `py` is unavailable, install Python 3.11 or newer from python.org, enable PATH during setup, and repeat the commands. The application is intended for Python 3.10+.

## API key setup

1. Copy `.env.example` to `.env`.
2. Set `GEMINI_API_KEY` using a key from Google AI Studio.
3. Keep `GEMINI_TEXT_MODEL=gemini-3.6-flash` for normal text requests. Native-audio preview models only support the Live WebSocket API.
4. Optionally set a weather API key and a market API key for providers matching the configured URLs.
5. Never commit `.env` or place real keys in Python files. If a key is exposed, revoke it immediately and create a replacement.

Without `GEMINI_API_KEY`, the app still runs in local dataset mode and explains that AI generation is disabled. Without weather or market keys, those services return a non-fatal unavailable message.

## Run

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

Open the local URL printed by Streamlit. Fill in the farmer details, choose a language, enter a question, and select **Ask Assistant**.

## Test

A basic syntax check is:

```powershell
python -m compileall app.py config.py prompts.py services
```

Then run the app without any API keys to verify the offline path. Test that missing location, season, soil type, water availability, or previous crop causes a follow-up message. Add a Gemini key and repeat to verify model responses. Disconnect or use invalid weather/market credentials to confirm that the app remains usable.

## File guide

- `app.py`: Streamlit layout, forms, session history, loading state, and safety notice.
- `config.py`: Environment variables, paths, model name, and supported languages.
- `prompts.py`: Grounding and language behavior instructions for Gemini.
- `crop_knowledge.csv`: Initial retrieval dataset.
- `data/sample_crop_data.csv`: Copy of the illustrative starter data.
- `services/knowledge_service.py`: CSV loading, filtering, and prompt context formatting.
- `services/crop_recommendation_service.py`: Explainable crop ranking and missing-field checks.
- `services/weather_service.py`: Optional weather HTTP integration with fallback handling.
- `services/market_service.py`: Optional market HTTP integration with fallback handling.
- `services/gemini_live_service.py`: Current `google-genai` text call and asynchronous Live API connection hook.

## Gemini Live and microphone support

The Live API connection is created with `client.aio.live.connect(...)`, which is the current asynchronous SDK pattern. The interface now transcribes one recorded clip through the normal Gemini content endpoint. A production real-time microphone feature still needs a browser audio bridge that sends PCM chunks to the Live session and plays returned audio chunks. Streamlit's built-in recorder does not itself provide bidirectional low-latency streaming.

## Safety and data quality

This prototype does not guarantee yield, profit, or prices. It does not provide pesticide dosages. Product labels, crop-specific soil tests, weather observations, and local agriculture officers must be consulted before action. Every dataset row carries a source and verification date; the sample source is intentionally marked illustrative.

## Future improvements

- Add a dedicated WebRTC or Streamlit component for true bidirectional Gemini Live audio.
- Add disease-image detection with a reviewed plant pathology model.
- Add offline speech recognition and local-language speech synthesis.
- Store farmer profiles only with consent and appropriate privacy controls.
- Improve Telugu speech recognition and pronunciation through field testing.
- Replace illustrative rows with reviewed, region-specific datasets and live market provider schemas.
