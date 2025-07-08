import streamlit as st
from openai import OpenAI
from astro_engine import get_astrology_profile
import os
import datetime
import json

st.set_page_config(page_title="AstralYogi Chatbot", layout="centered")
st.title("🔱 AstralYogi — Your Vedic Astrology Chatbot")
st.markdown("Speak your heart. Receive gentle karmic guidance, not jargon.")

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
        dob = st.date_input("Date of Birth", min_value=datetime.date(1900, 1, 1), value=datetime.date(1990, 1, 1))
        col1, col2 = st.columns(2)
        with col1:
            hour = st.selectbox("Hour", list(range(0, 24)))
        with col2:
            minute = st.selectbox("Minute", list(range(0, 60)))
        cities = ["Bathinda", "Delhi", "Mumbai", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune"]
        city = st.selectbox("Place of Birth", cities)

        if st.form_submit_button("Start Chat"):
            tob = f"{hour:02d}:{minute:02d}"
            st.session_state.astro_data = get_astrology_profile(str(name), str(dob), tob, city)
            if "error" in st.session_state.astro_data:
                st.error("Error: " + st.session_state.astro_data["error"])
            else:
                st.session_state.profile_collected = True
                st.success("✅ Chart calculated. You may now chat.")
                st.stop()

else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Ask anything..."):
        st.session_state.messages.append({"role": "user", "content": user_input})

        data = st.session_state.astro_data

        # Convert complete astro_data into GPT-aware summary
        full_context = f"""
You are AstralYogi — a wise Vedic guide. You interpret deep astrological insights but express them gently in human, spiritual, emotionally uplifting terms. Avoid technical words unless the user asks.

Below is the user's full astrological chart data — DO NOT repeat it unless it's relevant to the question.

{json.dumps(data, indent=2)}

User's question: {user_input}

Answer like a spiritual mentor who knows this chart by heart and guides with compassion and cosmic clarity.
"""

        messages = [{"role": "system", "content": full_context}]

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages + st.session_state.messages
            )
            reply = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)
            with st.expander("📦 GPT Full Input"):
                st.code(full_context)
        except Exception as e:
            st.error("Chatbot failed: " + str(e))