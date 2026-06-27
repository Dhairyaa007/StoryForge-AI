import os
import re
from html import escape

import streamlit as st
from dotenv import load_dotenv
from groq import Groq


MODEL_NAME = "llama-3.3-70b-versatile"
DEFAULT_CHOICES = ["Continue forward", "Explore the area", "Wait and observe"]


THEMES = {
    "Sci-Fi": "futuristic science fiction",
    "Fantasy": "high fantasy",
    "Horror": "atmospheric horror",
    "Mystery": "detective mystery",
    "Comedy": "light adventure comedy",
}


DIFFICULTY_GUIDANCE = {
    "Easy": "Keep danger low and make the next best step fairly clear.",
    "Medium": "Add complications, but keep choices understandable.",
    "Hard": "Create meaningful risk, tradeoffs, and consequences.",
}


load_dotenv()


st.set_page_config(
    page_title="AI StoryForge",
    page_icon="GAME",
    layout="wide",
)


@st.cache_resource
def get_groq_client() -> Groq | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)


def initialize_state() -> None:
    defaults = {
        "story_history": [],
        "current_scene": "",
        "choices": [],
        "started": False,
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_game() -> None:
    for key in ("story_history", "current_scene", "choices", "started"):
        st.session_state.pop(key, None)
    initialize_state()


def build_system_prompt(theme: str, difficulty: str) -> str:
    return f"""
You are an interactive story game engine.

Theme: {THEMES[theme]}
Difficulty: {difficulty}
Difficulty guidance: {DIFFICULTY_GUIDANCE[difficulty]}

Rules:
- Write immersive second-person storytelling.
- Keep each scene between 180 and 260 words.
- Maintain continuity with the story so far.
- Always end with exactly 3 choices.
- Make choices specific, meaningful, and different from each other.
- Do not put choice text inside the story section.

Output format:

STORY:
<story text>

CHOICES:
1. <choice 1>
2. <choice 2>
3. <choice 3>
""".strip()


def generate_scene(prompt: str, theme: str, difficulty: str) -> str:
    client = get_groq_client()
    if client is None:
        raise RuntimeError("Missing GROQ_API_KEY. Add it to your .env file before starting the app.")

    history = "\n".join(st.session_state.story_history[-8:])
    user_content = f"""
Story so far:
{history or "No story yet."}

Next instruction:
{prompt}
""".strip()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": build_system_prompt(theme, difficulty)},
            {"role": "user", "content": user_content},
        ],
        temperature=0.8,
        max_tokens=900,
    )

    return response.choices[0].message.content.strip()


def split_scene_and_choices(text: str) -> tuple[str, list[str]]:
    story_match = re.search(
        r"STORY:\s*(.*?)(?:\n\s*CHOICES:\s*|\Z)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    choices_match = re.search(
        r"CHOICES:\s*(.*)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    story = story_match.group(1).strip() if story_match else text.strip()
    raw_choices = choices_match.group(1).strip() if choices_match else ""

    choices = []
    for line in raw_choices.splitlines():
        cleaned = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line).strip()
        if cleaned:
            choices.append(cleaned)

    if len(choices) != 3:
        choices = DEFAULT_CHOICES

    return story, choices


def render_scene(text: str) -> None:
    story, _ = split_scene_and_choices(text)
    safe_story = escape(story).replace("\n", "<br>")

    st.markdown(
        f"""
        <div class="story-panel">
            {safe_story}
        </div>
        """,
        unsafe_allow_html=True,
    )


initialize_state()

st.markdown(
    """
    <style>
        .story-title {
            text-align: center;
            color: #4f46e5;
            margin-bottom: 0.25rem;
        }

        .story-subtitle {
            text-align: center;
            font-size: 1.1rem;
            color: #4b5563;
            margin-top: 0;
        }

        .story-panel {
            background: #111827;
            border: 1px solid #374151;
            border-radius: 8px;
            color: white;
            font-size: 1rem;
            line-height: 1.65;
            padding: 1.25rem;
        }
    </style>
    <h1 class="story-title">AI StoryForge</h1>
    <p class="story-subtitle">Interactive AI-powered choose-your-own-adventure game</p>
    """,
    unsafe_allow_html=True,
)

st.divider()

with st.sidebar:
    st.title("Game Settings")
    theme = st.selectbox("Story Theme", list(THEMES.keys()))
    difficulty = st.selectbox("Difficulty Level", list(DIFFICULTY_GUIDANCE.keys()), index=1)

    if st.button("Restart Game", use_container_width=True):
        reset_game()
        st.rerun()

if get_groq_client() is None:
    st.error("Missing `GROQ_API_KEY`. Add it to your `.env` file, then restart Streamlit.")
    st.stop()

st.subheader("Start Your Adventure")

start = st.text_area(
    "Enter your story idea",
    placeholder="Example: A hacker wakes up inside a broken simulation...",
    disabled=st.session_state.started,
)

if st.button("Start Adventure", disabled=st.session_state.started):
    if not start.strip():
        st.warning("Please enter a story idea first.")
    else:
        with st.spinner("Generating your world..."):
            try:
                scene = generate_scene(start.strip(), theme, difficulty)
            except Exception as exc:
                st.error(f"Could not generate the scene: {exc}")
            else:
                st.session_state.started = True
                st.session_state.current_scene = scene
                st.session_state.choices = split_scene_and_choices(scene)[1]
                st.session_state.story_history = [f"Opening premise: {start.strip()}", scene]
                st.rerun()

if st.session_state.current_scene:
    st.divider()
    render_scene(st.session_state.current_scene)
    st.divider()

    st.subheader("What do you do next?")
    choice = st.radio(
        "Choose your action:",
        st.session_state.choices,
        key=f"choice_{len(st.session_state.story_history)}",
    )

    col1, col2 = st.columns(2)

    with col1:
        continue_clicked = st.button("Continue Story", type="primary", use_container_width=True)

    with col2:
        reset_clicked = st.button("Reset Story", use_container_width=True)

    if continue_clicked:
        prompt = f"""
The player chose: {choice}

Continue from that decision. Show the immediate consequence, advance the story,
and end with exactly 3 new choices.
""".strip()

        with st.spinner("The story evolves..."):
            try:
                next_scene = generate_scene(prompt, theme, difficulty)
            except Exception as exc:
                st.error(f"Could not continue the story: {exc}")
            else:
                st.session_state.story_history.extend(
                    [f"Player choice: {choice}", next_scene]
                )
                st.session_state.current_scene = next_scene
                st.session_state.choices = split_scene_and_choices(next_scene)[1]
                st.rerun()

    if reset_clicked:
        reset_game()
        st.rerun()
