import streamlit as st
import datetime
from openai import OpenAI
from astro_engine import get_astrology_profile
import os
import json

st.set_page_config(page_title="AstralYogi — Your Vedic Guide", layout="centered")

def reset_session():
    for key in ["messages", "astro_data", "profile_collected"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

st.title("🔱 AstralYogi — Your Cosmic Companion")
st.markdown("**Your cosmic mirror. Get modern-day guidance using ancient Vedic wisdom.**")

if st.button("❌ Close Chat", type="primary"):
    reset_session()

api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "astro_data" not in st.session_state:
    st.session_state.astro_data = None
if "profile_collected" not in st.session_state:
    st.session_state.profile_collected = False

if not st.session_state.profile_collected:
    with st.form("birth_form"):
        name = st.text_input("Your Name")
        dob = st.date_input(
            "Date of Birth",
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date(2100, 1, 1),
            value=datetime.date(1990, 1, 1)
        )

        col1, col2 = st.columns(2)
        with col1:
            hour = st.selectbox("Hour", list(range(0, 24)))
        with col2:
            minute = st.selectbox("Minute", list(range(0, 60)))

        tob = f"{hour:02d}:{minute:02d}"

        cities = [
            "Bathinda", "Chandigarh", "Delhi", "Mumbai", "Bangalore", "Hyderabad",
            "Chennai", "Kolkata", "Pune", "Ahmedabad", "Jaipur"
        ]
        city = st.selectbox("Place of Birth", cities)

        if st.form_submit_button("🔍 Generate My Chart"):
            st.session_state.astro_data = get_astrology_profile(
                name=name,
                date_of_birth=str(dob),
                time_of_birth=tob,
                city=city,
                tz_offset=5.5,
                adjust_dst=False
            )
            if "error" in st.session_state.astro_data:
                st.error("Error: " + st.session_state.astro_data["error"])
            else:
                st.session_state.profile_collected = True
                st.success("🪐 Chart ready. Ask AstralYogi anything.")
                st.rerun()

else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask me anything about your purpose, relationships, career, business, finance, or growth…")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        data = st.session_state.astro_data
        system_prompt = f"""
You are AstralYogi — a compassionate Vedic astrologer and guide.
You have access to the user's complete chart. Use this internally but only reveal technical details if directly asked.
Always speak in a wise, emotionally supportive, and spiritual tone. Keep responses human and intuitive.

Here is the user's astrology data:
{json.dumps(data, indent=2)}

Their question is: {user_input}

Answer using deep understanding but plain language.
"""

        messages = [{"role": "system", "content": system_prompt}]

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages + st.session_state.messages
            )
            reply = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": reply})

            with st.chat_message("assistant"):
                st.markdown(reply)

        except Exception as e:
            st.error("Chatbot error: " + str(e))