import streamlit as st
import requests
import json

API_KEY = "YOUR_GEMINI_API_KEY"   # <-- paste your key here
MODEL = "gemini-1.5-flash"

st.set_page_config(page_title="Gemini Free API", layout="wide")
st.title("🎓 School of AI — Gemini (Free REST API)")

prompt = st.text_area("Enter your question or topic:")

if st.button("Ask Gemini"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}

    with st.spinner("Gemini is thinking..."):
        res = requests.post(url, headers=headers, data=json.dumps(data))
        if res.status_code == 200:
            out = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            st.success("### 🌈 Gemini says:")
            st.write(out)
        else:
            st.error(f"Error {res.status_code}: {res.text}")
