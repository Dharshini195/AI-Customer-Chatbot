# ui.py
import streamlit as st
import requests
import random

API_URL = "http://localhost:8000"

# ── Page config ──────────────────────────────────────────
st.set_page_config(
    page_title="AI Customer Support",
    page_icon="🤖",
    layout="wide"
)

# ── Session state bootstrap ───────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = random.randint(1000, 9999)

if "messages" not in st.session_state:
    st.session_state.messages = []   # [{role, content}]

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Controls")
    st.info(f"**Session ID:** `{st.session_state.session_id}`")

    if st.button("🗑️ Clear Conversation"):
        requests.delete(f"{API_URL}/history/{st.session_state.session_id}")
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # Show full history from backend
    if st.button("📋 Show Full History"):
        res = requests.get(f"{API_URL}/history/{st.session_state.session_id}")
        if res.ok:
            st.json(res.json())

    st.divider()
    st.caption("Built with FastAPI + Streamlit")

# ── Main chat area ────────────────────────────────────────
st.title("🤖 AI Customer Support Agent")
st.caption("Ask about orders, policies, or raise a support ticket.")

# Render existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
       

# Chat input
if user_input := st.chat_input("Type your message..."):

    # Show user message immediately
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    with st.chat_message("user"):
        st.write(user_input)

    # Call your FastAPI backend
    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking..."):
            try:
                res = requests.post(
                    f"{API_URL}/chat",
                    json={
                        "session_id": st.session_state.session_id,
                        "query": user_input
                    },
                    timeout=30
                )

                if res.ok:
                    data = res.json()
                    reply = data["response"]
                else:
                    reply = f"⚠️ Error {res.status_code}: {res.text}"

            except requests.exceptions.ConnectionError:
                reply = "❌ Cannot reach the backend. Is FastAPI running?"

        st.write(reply)
        

    # Save assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })