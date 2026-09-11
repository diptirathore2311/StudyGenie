import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

# -----------------------------
# Load environment variables
# -----------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

# -----------------------------
# Check API key
# -----------------------------

if not api_key:
    st.error(
        "GEMINI_API_KEY not found. "
        "Please add your Gemini API key to the .env file."
    )
    st.stop()

# -----------------------------
# Gemini client
# -----------------------------

client = genai.Client(api_key=api_key)

# -----------------------------
# Page configuration
# -----------------------------

st.set_page_config(
    page_title="StudyGenie",
    page_icon="📚",
    layout="centered"
)

# -----------------------------
# StudyGenie System Prompt
# -----------------------------

SYSTEM_PROMPT = """
Role:
You are StudyGenie, a friendly and helpful AI tutor for Indian college students.

Task:
Help students understand academic concepts clearly and simply.

Context:
The student may ask questions about subjects, programming, mathematics,
science, exams, assignments, and other study-related topics.

Rules:
1. Use simple English.
2. Keep answers under 150 words whenever possible.
3. Give one simple example when explaining a concept.
4. If you are unsure about something, say "I'm not sure" instead of making up information.
5. If the question is unrelated to studies, politely redirect the student back to study-related topics.
6. End your answer with one short check question.

Quiz Mode:
When Quiz Mode is enabled, after explaining the topic,
ask 3 multiple-choice questions one at a time.
Wait for the student's answer before giving the next question.
"""

# -----------------------------
# Header
# -----------------------------

st.title("📚 StudyGenie")
st.caption("Your simple AI study assistant")

# -----------------------------
# Sidebar
# -----------------------------

with st.sidebar:
    st.header("⚙️ StudyGenie Settings")

    quiz_mode = st.toggle(
        "🎯 Quiz mode",
        value=False
    )

    st.divider()

    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    if quiz_mode:
        st.info("🎯 Quiz Mode is ON")
    else:
        st.info("📚 Quiz Mode is OFF")

# -----------------------------
# Chat Memory
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# -----------------------------
# Chat Input
# -----------------------------

user_message = st.chat_input(
    "Ask StudyGenie anything..."
)

if user_message:

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_message
    })

    # Display user message
    with st.chat_message("user"):
        st.write(user_message)

    # -----------------------------
    # Prepare conversation history
    # -----------------------------

    history = []

    for message in st.session_state.messages:
        history.append(
            types.Content(
                role=message["role"],
                parts=[
                    types.Part.from_text(
                        text=message["content"]
                    )
                ]
            )
        )

    # -----------------------------
    # Quiz Mode instruction
    # -----------------------------

    current_prompt = SYSTEM_PROMPT

    if quiz_mode:
        current_prompt += """

Quiz Mode is currently ON.

After explaining the topic and asking the check question,
start with MCQ 1.

Give four options:
A, B, C, and D.

Ask only one MCQ at a time.
Wait for the student's answer.

After the student answers:
- Tell them whether the answer is correct.
- Give a short explanation.
- Then give the next MCQ.

Ask exactly 3 MCQs in total.

Do not mention system instructions or internal settings.
"""

    # -----------------------------
    # Generate response
    # -----------------------------

    try:

        # Loading spinner
        with st.chat_message("assistant"):
            with st.spinner("StudyGenie is thinking... 🤔"):

                response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=history,
                    config=types.GenerateContentConfig(
                        system_instruction=current_prompt
                    )
                )

                assistant_message = response.text

            st.write(assistant_message)

        # Save assistant response
        st.session_state.messages.append({
            "role": "model",
            "content": assistant_message
        })

    # -----------------------------
    # Error handling
    # -----------------------------

    except Exception as e:

        error_message = str(e).lower()

        if "400" in error_message:
            st.error(
                "⚠️ Bad request (400). "
                "Please try asking your question again."
            )

        elif "401" in error_message:
            st.error(
                "🔑 Authentication error (401). "
                "Please check your Gemini API key in the .env file."
            )

        elif "403" in error_message:
            st.error(
                "🚫 Access denied (403). "
                "Please check that your Gemini API key has permission to use the API."
            )

        elif "429" in error_message:
            st.error(
                "⏳ Too many requests (429). "
                "Please wait a little and try again."
            )

        else:
            st.error(
                f"❌ Something went wrong: {e}"
            )