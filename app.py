import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv

# -----------------------------
# LOAD ENV
# -----------------------------
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="AI StoryForge",
    page_icon="🎮",
    layout="wide"
)

# -----------------------------
# UI HEADER
# -----------------------------
st.markdown(
    """
    <h1 style='text-align: center; color: #6C63FF;'>🎮 AI StoryForge</h1>
    <p style='text-align: center; font-size:18px;'>
    Interactive AI-powered choose-your-own-adventure game
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()

# -----------------------------
# SIDEBAR SETTINGS
# -----------------------------
st.sidebar.title("⚙️ Game Settings")

theme = st.sidebar.selectbox(
    "Story Theme",
    ["Sci-Fi 🚀", "Fantasy 🏰", "Horror 👻", "Mystery 🕵️", "Comedy 😂"]
)

difficulty = st.sidebar.selectbox(
    "Difficulty Level",
    ["Easy", "Medium", "Hard"]
)


if st.sidebar.button("🔄 Restart Game"):
    st.session_state.clear()
    st.rerun()

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "story_history" not in st.session_state:
    st.session_state.story_history = ""

if "current_scene" not in st.session_state:
    st.session_state.current_scene = ""

if "choices" not in st.session_state:
    st.session_state.choices = []

# -----------------------------
# AI FUNCTION
# -----------------------------
def generate_scene(prompt, history=""):
    system_prompt = f"""
You are an interactive story game engine.

Theme: {theme}
Difficulty: {difficulty}

Rules:
- Create immersive storytelling
- Keep scene medium length
- Always end with EXACTLY 3 choices
- Choices must be meaningful and different
- Keep tone consistent with theme

OUTPUT FORMAT:

STORY:
<story text>

CHOICES:
1. <choice 1>
2. <choice 2>
3. <choice 3>
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": history + "\n\n" + prompt}
        ]
    )

    return response.choices[0].message.content

# -----------------------------
# EXTRACT CHOICES
# -----------------------------
def extract_choices(text):
    try:
        if "CHOICES:" not in text:
            return ["Continue", "Explore", "Wait"]

        choices_part = text.split("CHOICES:")[1]
        lines = choices_part.strip().split("\n")

        choices = []
        for line in lines:
            if line.strip():
                choice = line.split(".", 1)[-1].strip()
                if choice:
                    choices.append(choice)

        return choices[:3] if len(choices) >= 3 else choices

    except:
        return ["Continue", "Explore", "Wait"]

# -----------------------------
# START STORY INPUT
# -----------------------------
formatted_scene = st.session_state.current_scene.replace("\n", "<br>")
st.subheader("🧠 Start Your Adventure")

start = st.text_area(
    "Enter your story idea",
    placeholder="e.g. A hacker wakes up inside a broken simulation..."
)

start_btn = st.button("🚀 Start Adventure")

# -----------------------------
# START GAME
# -----------------------------
if start_btn:
    if start.strip() == "":
        st.warning("Please enter a story idea first.")
    else:
        with st.spinner("Generating your world..."):
            scene = generate_scene(start)
            st.session_state.current_scene = scene
            st.session_state.story_history = start
            st.session_state.choices = extract_choices(scene)

# -----------------------------
# DISPLAY STORY
# -----------------------------
if st.session_state.current_scene:

    st.divider()

    st.markdown(
        f"""
        <div style="
            background-color:#111827;
            padding:20px;
            border-radius:12px;
            color:white;
            font-size:16px;
            line-height:1.6;
        ">
        {formatted_scene}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # -----------------------------
    # CHOICES UI
    # -----------------------------
    st.subheader("🎯 What do you do next?")

    choice = st.radio(
        "Choose your action:",
        st.session_state.choices
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        next_btn = st.button("➡️ Continue Story")

    with col2:
        restart_btn = st.button("🔄 Reset Story")

    # -----------------------------
    # CONTINUE STORY
    # -----------------------------
    if next_btn:
        with st.spinner("The story evolves..."):

            new_prompt = f"""
User chose: {choice}

Continue the story based on this decision.
Make it feel like a continuous interactive narrative.
"""

            next_scene = generate_scene(new_prompt, st.session_state.story_history)

            st.session_state.story_history += "\n" + choice
            st.session_state.current_scene = next_scene
            st.session_state.choices = extract_choices(next_scene)

            st.rerun()

    # -----------------------------
    # RESET
    # -----------------------------
    if restart_btn:
        st.session_state.clear()
        st.rerun()

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:gray;'>Built with Streamlit + Groq AI</p>",
    unsafe_allow_html=True
)
