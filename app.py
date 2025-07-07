import streamlit as st
import os
from openai import OpenAI
import datetime



# App config
st.set_page_config(page_title="AstralYogi", layout="centered")
st.title("🪐 AstralYogi")
st.caption("Ask your cosmic guide. Decode your karma.")

# Input form
with st.form("astro_form"):
    name = st.text_input("Your Name")
    dob = st.date_input("Date of Birth", min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today())
    tob = st.time_input("Time of Birth", value=datetime.time(12, 0))
    location = st.text_input("Place of Birth (City)")
    question = st.text_area("What would you like to ask the cosmos?", height=150)
    submitted = st.form_submit_button("Ask AstralYogi")

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if submitted:
    with st.spinner("Calculating cosmic frequencies..."):
        prompt = f"""You are AstralYogi — a wise, kind, and deeply intuitive Vedic astrologer.
Use the user's birth information and question to give a response rooted in:
1. Vedic astrology (nakshatras, dashas, planetary influences)
2. Karma and life purpose
3. A gentle, encouraging tone
4. One insight or remedy they can reflect on

User:
Name: {name}
Date of Birth: {dob}
Time of Birth: {tob}
Location: {location}
Question: {question}

Respond now with cosmic insight.
""" 

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are AstralYogi, a Vedic astrologer and karmic guide."},
                    {"role": "user", "content": prompt}
                ]
            )
            st.markdown("---")
            st.markdown(response.choices[0].message.content)

        except Exception as e:
            st.error(f"❌ OpenAI Error: {e}")
