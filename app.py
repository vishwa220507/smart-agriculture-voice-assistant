"""Streamlit interface for the multilingual smart agriculture assistant."""

from datetime import datetime

import streamlit as st

from config import (
    APP_TITLE,
    GEMINI_API_KEY,
    GEMINI_LIVE_MODEL,
    GEMINI_TEXT_MODEL,
    KNOWLEDGE_FILE,
    MARKET_API_KEY,
    MARKET_API_URL,
    SUPPORTED_LANGUAGES,
    WEATHER_API_KEY,
    WEATHER_API_URL,
)
from prompts import build_user_prompt
from services.crop_recommendation_service import CropRecommendationService
from services.gemini_live_service import GeminiLiveService
from services.knowledge_service import KnowledgeService
from services.market_service import MarketService
from services.weather_service import WeatherService


st.set_page_config(page_title=APP_TITLE, page_icon="🌾", layout="wide")


@st.cache_resource
def get_services():
    knowledge = KnowledgeService(KNOWLEDGE_FILE)
    return {
        "knowledge": knowledge,
        "recommendation": CropRecommendationService(knowledge),
        "weather": WeatherService(WEATHER_API_KEY, WEATHER_API_URL),
        "market": MarketService(MARKET_API_KEY, MARKET_API_URL),
        "gemini": GeminiLiveService(GEMINI_API_KEY, GEMINI_TEXT_MODEL, GEMINI_LIVE_MODEL),
    }


def initialize_state():
    if "conversation" not in st.session_state:
        st.session_state.conversation = []
    if "last_recommendations" not in st.session_state:
        st.session_state.last_recommendations = None
    if "voice_question" not in st.session_state:
        st.session_state.voice_question = ""
    if "voice_transcript" not in st.session_state:
        st.session_state.voice_transcript = ""


initialize_state()
st.title(APP_TITLE)
st.caption("Ask in your language. Start with the text fallback, then add Gemini credentials for AI responses.")

try:
    services = get_services()
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()

with st.sidebar:
    st.header("Assistant settings")
    language_label = st.selectbox("Response language", list(SUPPORTED_LANGUAGES))
    language = SUPPORTED_LANGUAGES[language_label]
    if GEMINI_API_KEY:
        st.success("Gemini API key loaded")
    else:
        st.warning("GEMINI_API_KEY is missing. Dataset mode is available; AI generation is disabled.")
    st.info("Sample crop rows are illustrative. Confirm all decisions with a local agricultural officer.")

st.subheader("Farmer details")
with st.form("farmer_details"):
    first_row = st.columns(3)
    with first_row[0]:
        location = st.text_input("Location (state or district)", placeholder="Example: Telangana")
    with first_row[1]:
        season = st.selectbox("Current season", ["", "Kharif", "Rabi", "Summer", "Multi-season"])
    with first_row[2]:
        soil_type = st.text_input("Soil type", placeholder="Example: black soil")
    second_row = st.columns(3)
    with second_row[0]:
        soil_ph = st.number_input("Soil pH (optional)", min_value=0.0, max_value=14.0, value=0.0, step=0.1)
    with second_row[1]:
        water_availability = st.selectbox("Water availability", ["", "Low", "Medium", "High"])
    with second_row[2]:
        land_area = st.number_input("Land area (acres, optional)", min_value=0.0, value=0.0, step=0.1)
    third_row = st.columns(3)
    with third_row[0]:
        previous_crop = st.text_input("Previous crop")
    with third_row[1]:
        weather_text = st.text_input("Known weather (optional)", placeholder="Example: warm, recent rain")
    with third_row[2]:
        market_interest = st.text_input("Market demand or price (optional)")
    question = st.text_area(
        "Ask the assistant",
        value=st.session_state.voice_question,
        placeholder="What crop should I grow this season?",
        height=100,
    )
    submit = st.form_submit_button("Ask Assistant", type="primary")

st.subheader("Voice input")
st.write("Record a question, transcribe it with Gemini, then review it in the question box before submitting.")
audio_value = st.audio_input("Record a question") if hasattr(st, "audio_input") else None
if audio_value:
    st.audio(audio_value)
    if st.button("Transcribe recorded question"):
        with st.spinner("Transcribing the recorded question..."):
            transcript = services["gemini"].transcribe_audio(
                audio_value.getvalue(),
                getattr(audio_value, "type", "audio/wav"),
                language,
            )
            st.session_state.voice_transcript = transcript
            st.session_state.voice_question = transcript
        st.rerun()

if st.session_state.voice_transcript:
    st.success("Voice question transcribed")
    st.write(f"**Your voice question:** {st.session_state.voice_transcript}")

farmer_details = {
    "location": location,
    "season": season,
    "soil_type": soil_type,
    "soil_ph": soil_ph or "",
    "water_availability": water_availability,
    "land_area": land_area or "",
    "previous_crop": previous_crop,
    "weather": weather_text,
    "market": market_interest,
}

if submit:
    if not question.strip():
        st.warning("Please enter a question first.")
    else:
        with st.spinner("The assistant is preparing a grounded response..."):
            weather = services["weather"].get_weather(location) if location else {"available": False, "message": "Location is missing."}
            market = services["market"].get_prices("", location) if location else {"available": False, "message": "Location is missing."}
            recommendation = services["recommendation"].recommend(farmer_details, weather, market)
            rows = services["knowledge"].search({"season": season, "soil_type": soil_type, "state": location})
            context = services["knowledge"].format_context(rows)
            ranked_crops = "\n".join(
                f"{index}. {item['crop']}: " + "; ".join(item["reasons"])
                for index, item in enumerate(recommendation.get("recommendations", []), start=1)
            )
            prompt = build_user_prompt(question, language, farmer_details, context, ranked_crops)
            answer = services["gemini"].generate_text(prompt) if GEMINI_API_KEY else (
                "I can use the local illustrative crop dataset, but Gemini is not configured. "
                "Please review the Crop recommendations below and verify them locally."
            )
            if recommendation.get("recommendations") and question.strip():
                first_crop = recommendation["recommendations"][0]["crop"]
                if not answer.lower().startswith("recommended crop:"):
                    answer = f"Recommended crop: {first_crop}\n\n{answer}"
            st.session_state.conversation.append({
                "time": datetime.now().strftime("%H:%M"),
                "question": question,
                "answer": answer,
                "language": language,
            })
            st.session_state.last_recommendations = recommendation

st.subheader("Assistant response")
if st.session_state.conversation:
    latest = st.session_state.conversation[-1]
    st.markdown(f"**{latest['language']} | {latest['time']}**")
    st.write(latest["answer"])
else:
    st.info("Your response will appear here after you ask a question.")

st.subheader("Crop recommendations")
recommendation = st.session_state.last_recommendations
if recommendation:
    if recommendation["missing"]:
        st.warning("Please provide: " + ", ".join(recommendation["missing"]))
    elif recommendation.get("invalid"):
        st.warning("Please verify: " + "; ".join(recommendation["invalid"]))
        st.info("A soil pH reading near 0.6 is unusual and should be retested before choosing a crop.")
    else:
        if recommendation.get("invalid"):
            st.warning("Please verify: " + "; ".join(recommendation["invalid"]))
        st.caption(recommendation["message"])
        for item in recommendation["recommendations"]:
            details = item["details"]
            with st.expander(f"{item['crop']} | match score {item['score']}"):
                st.write("Why: " + "; ".join(item["reasons"]))
                st.write(f"Season: {details.get('season', '')} | Soil: {details.get('soil_type', '')} | Water: {details.get('water_requirement', '')}")
                st.write(f"Fertilizer guidance: {details.get('fertilizer_guidance', '')}")
                st.write(f"Pests and diseases: {details.get('common_pests', '')}; {details.get('common_diseases', '')}")
                st.caption(f"Source: {details.get('source', '')} | Last verified: {details.get('last_verified_date', '')}")
else:
    st.info("Complete the farmer details and ask for a crop recommendation to see ranked options.")

with st.expander("Conversation history"):
    if not st.session_state.conversation:
        st.write("No questions asked in this session yet.")
    for item in reversed(st.session_state.conversation):
        st.markdown(f"**Farmer ({item['language']}, {item['time']})**: {item['question']}")
        st.markdown(f"**Assistant**: {item['answer']}")

st.warning("Safety: Always follow the product label and local agricultural department advice. Do not mix chemicals or apply fertilizer or pesticide without a soil/crop-specific recommendation. Never treat this sample dataset as a guaranteed or real-time prescription.")
