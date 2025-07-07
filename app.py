import streamlit as st
import openai
from astro_engine import get_astrology_profile
import os

st.set_page_config(page_title="AstralYogi Chatbot", layout="centered")

st.title("🔱 AstralYogi — Your Vedic Astrology Chatbot")
st.markdown("Talk to a wise astrologer who decodes your chart in real time.")

# Set up OpenAI API Key
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
else:
    openai.api_key = os.getenv("OPENAI_API_KEY")

# Session state setup
if "messages" not in st.session_state:
    st.session_state.messages = []
if "astro_data" not in st.session_state:
    st.session_state.astro_data = None
if "profile_collected" not in st.session_state:
    st.session_state.profile_collected = False

# Collect user birth details first
if not st.session_state.profile_collected:
    with st.form("birth_form"):
        name = st.text_input("Your Name")
        dob = st.date_input("Date of Birth")
        tob = st.text_input("Time of Birth (HH:MM, 24hr)")
        city = st.text_input("Place of Birth (City)")
        submitted = st.form_submit_button("Start Chat")

        if submitted and all([name, dob, tob, city]):
            st.session_state.astro_data = get_astrology_profile(
                name=str(name),
                dob=str(dob),
                tob=str(tob),
                city=str(city),
                tz_offset=5.5,
                adjust_dst=False
            )
            if "error" in st.session_state.astro_data:
                st.error("Error: " + st.session_state.astro_data["error"])
            else:
                st.session_state.profile_collected = True
                st.success("✅ Profile saved! You can now chat with AstralYogi.")
                st.experimental_rerun()

else:
    # Display previous messages
    for msg in st.session_state.messages:
        role = "🧘 AstralYogi" if msg["role"] == "assistant" else "🧍 You"
        with st.chat_message(msg["role"]):
            st.markdown(f"**{role}:** {msg['content']}")

    # User input
    if user_input := st.chat_input("Ask about your life, karma, or planets..."):
        st.session_state.messages.append({"role": "user", "content": user_input})

        system_prompt = f'''
You are AstralYogi — a compassionate, wise Vedic astrologer and karmic guide.
Here is the user's birth chart:
{st.session_state.astro_data}

Engage in a conversation. Respond with spiritual depth, clarity, and kindness.
Focus on Moon nakshatra, Mahadasha, houses, and karmic patterns when relevant.
Avoid repeating the entire chart unless asked. Build on prior answers.
'''

        messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            reply = response["choices"][0]["message"]["content"]
            st.session_state.messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(f"**🧘 AstralYogi:** {reply}")
        except Exception as e:
            st.error("Failed to generate response: " + str(e))