import streamlit as st
from openai import OpenAI
import os
import datetime

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Page setup
st.set_page_config(page_title="AstralYogi Chat", layout="centered")
st.title("🪐 AstralYogi")
st.caption("Chat with your personal Vedic astrology guide")

# Initialize session state for user profile and chat history
if "profile_submitted" not in st.session_state:
    st.session_state.profile_submitted = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Step 1: Collect user birth details
if not st.session_state.profile_submitted:
    with st.form("birth_form"):
        name = st.text_input("Your Name")
        dob = st.date_input("Date of Birth", min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today())

        col1, col2 = st.columns(2)
        with col1:
            hour = st.selectbox("Hour (0–23)", list(range(0, 24)))
        with col2:
            minute = st.selectbox("Minute", list(range(0, 60)))
        tob = f"{hour:02d}:{minute:02d}"

        cities = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Jaipur", "Pune", "Ahmedabad", "Varanasi"]
        place = st.selectbox("Place of Birth (City)", options=cities)

        submitted = st.form_submit_button("Start Chatting")

        if submitted:
            st.session_state.profile = {
                "name": name,
                "dob": str(dob),
                "tob": tob,
                "place": place
            }
            st.session_state.profile_submitted = True
            st.rerun()

# Step 2: Chat interface
if st.session_state.profile_submitted:
    st.markdown(f"🧘 Welcome, **{st.session_state.profile['name']}** — your cosmic chat is open.")

    for msg in st.session_state.chat_history:
        role, content = msg
        if role == "user":
            st.chat_message("user").markdown(content)
        else:
            st.chat_message("assistant").markdown(content)

    user_input = st.chat_input("Ask AstralYogi anything about your life, karma, or future...")

    if user_input:
        st.chat_message("user").markdown(user_input)
        st.session_state.chat_history.append(("user", user_input))

        # Prepare prompt
        profile = st.session_state.profile
        full_prompt = f"""You are AstralYogi — a wise, intuitive Vedic astrologer.
Use the user's birth profile below to respond to their message with insight, dasha logic, and Vedic remedies.

Birth Details:
Name: {profile['name']}
Date of Birth: {profile['dob']}
Time of Birth: {profile['tob']}
Place of Birth: {profile['place']}

User Message:
{user_input}

Respond now with deep wisdom.
""" 

        with st.spinner("Consulting the stars..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are AstralYogi, a Vedic astrology expert."},
                        {"role": "user", "content": full_prompt}
                    ]
                )
                reply = response.choices[0].message.content
                st.chat_message("assistant").markdown(reply)
                st.session_state.chat_history.append(("assistant", reply))
            except Exception as e:
                st.error(f"❌ OpenAI Error: {e}")