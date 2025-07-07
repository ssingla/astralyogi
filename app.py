import streamlit as st
from openai import OpenAI
from astro_engine import get_astrology_profile
import os
import datetime

st.set_page_config(page_title="AstralYogi Chatbot", layout="centered")
st.title("🔱 AstralYogi — Your Vedic Astrology Chatbot")
st.markdown("Talk to a wise astrologer who decodes your chart in real time.")

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
            max_value=datetime.date.today(),
            value=datetime.date(1990, 1, 1)
        )

        col1, col2 = st.columns(2)
        with col1:
            hour = st.selectbox("Hour", list(range(0, 24)))
        with col2:
            minute = st.selectbox("Minute", list(range(0, 60)))

        cities = ["Bathinda", "Delhi", "Mumbai", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune", "Ahmedabad", "Jaipur"]
        city = st.selectbox("Place of Birth", cities)

        submitted = st.form_submit_button("Start Chat")

        if submitted and all([name, dob, city]):
            tob = f"{hour:02d}:{minute:02d}"
            st.session_state.astro_data = get_astrology_profile(
                name=str(name),
                dob=str(dob),
                tob=tob,
                city=city,
                tz_offset=5.5,
                adjust_dst=False
            )
            if "error" in st.session_state.astro_data:
                st.error("Error: " + st.session_state.astro_data["error"])
            else:
                st.session_state.profile_collected = True
                st.success("✅ Profile saved! You can now chat with AstralYogi.")
                st.stop()
else:
    for msg in st.session_state.messages:
        role = "🧘 AstralYogi" if msg["role"] == "assistant" else "🧍 You"
        with st.chat_message(msg["role"]):
            st.markdown(f"**{role}:** {msg['content']}")

    if user_input := st.chat_input("Ask about your life, karma, or planets..."):
        st.session_state.messages.append({"role": "user", "content": user_input})

        data = st.session_state.astro_data

        summary = (
            f"User Details:\n"
            f"- Name: {data['name']}\n"
            f"- Date of Birth: {data['dob']}\n"
            f"- Time of Birth: {data['tob']}\n"
            f"- City: {data['city']}\n\n"
            f"Key Chart Insights:\n"
            f"- Ascendant: {data['ascendant']['sign']} at {data['ascendant']['degree']}\n"
            f"- Moon: in {data['planets']['Moon']['sign']}, Nakshatra: {data['planets']['Moon']['nakshatra']} Pada {data['planets']['Moon']['pada']}\n"
            f"- Current Mahadasha: {data['current_dasha']['mahadasha']} ({data['current_dasha']['start']} to {data['current_dasha']['end']})\n"
        )

        prompt = f"""
You are AstralYogi — a compassionate, wise Vedic astrologer.

Here is the user's astrological summary:
{summary}

They asked: "{user_input}"

Now give an insightful, mystical, karmically-aware response based on their Moon placement, Mahadasha, and chart.
Respond with spiritual clarity and uplifting Vedic guidance.
"""

        with st.expander("🔍 GPT Prompt Preview"):
            st.code(prompt)

        with st.expander("🪐 Astro Data from Engine"):
            st.json(data)

        messages = [{"role": "system", "content": prompt}]
        messages += st.session_state.messages

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            reply = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(f"**🧘 AstralYogi:** {reply}")
            with st.expander("🧾 Raw GPT Response"):
                st.code(reply)
        except Exception as e:
            st.error("Failed to generate response: " + str(e))