# app/app.py
import sys
from pathlib import Path
import streamlit as st

# ----------------------------
# Path setup (so "src" imports work)
# ----------------------------
ROOT = Path(__file__).resolve().parents[1]  # project root
sys.path.append(str(ROOT))

# ----------------------------
# Imports from project
# ----------------------------
from src.utility import (
    load_env,
    load_personas,
    timestamp,
    save_json,
    append_markdown,
)
from src.simulator import (
    simulate_feedback,
    analyze_feedback,
    simulate_followup,
)

# ----------------------------
# Streamlit config 
# ----------------------------
st.set_page_config(page_title="Persona Feedback Simulator", layout="wide")

# ----------------------------
# Constants / paths
# ----------------------------
PERSONAS_PATH = ROOT / "personas" / "personas.json"
REPORTS_DIR = ROOT / "reports"
CONVERSATIONS_MD = REPORTS_DIR / "conversations.md"

# ----------------------------
# Init
# ----------------------------
load_env()
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

st.title("Persona Feedback Simulator (TinyTroupe-style Prototype)")
st.write("Enter a feature description, choose personas, and generate simulated feedback.")

# ----------------------------
# Load personas (cached)
# ----------------------------
@st.cache_data
def cached_personas(path_str: str):
    # load_personas should return either:
    # 1) list[dict] personas OR
    # 2) dict with key "personas" containing list
    data = load_personas(Path(path_str))

    # Normalize to list[dict]
    if isinstance(data, dict) and "personas" in data:
        return data["personas"]
    if isinstance(data, list):
        return data

    raise ValueError("personas.json format not recognized. Expect list or {'personas': [...]}")

personas_list = cached_personas(str(PERSONAS_PATH))
persona_names = [p.get("name", "Unnamed Persona") for p in personas_list]

def find_persona_by_name(name: str) -> dict:
    for p in personas_list:
        if p.get("name") == name:
            return p
    # fallback (shouldn't happen)
    return personas_list[0]

# ----------------------------
# UI inputs
# ----------------------------
feature_description = st.text_area(
    "Feature Description",
    placeholder="Describe the feature you want feedback on...",
    height=180,
)

mode = st.radio("Mode", ["Single Persona", "Compare Personas"], horizontal=True)

model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o"], index=0)

st.divider()

# ----------------------------
# Session state for follow-up chat
# ----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_feature" not in st.session_state:
    st.session_state.last_feature = ""
if "last_persona" not in st.session_state:
    st.session_state.last_persona = None
if "last_model" not in st.session_state:
    st.session_state.last_model = model


# ============================================================
# Single Persona mode
# ============================================================
if mode == "Single Persona":
    persona_name = st.selectbox("Persona", persona_names)
    selected_persona = find_persona_by_name(persona_name)

    run = st.button("Run Simulation", type="primary")

    if run:
        if not feature_description.strip():
            st.error("Please enter a feature description.")
        else:
            st.session_state.chat_history = []  # reset follow-up history
            st.session_state.last_feature = feature_description.strip()
            st.session_state.last_persona = selected_persona
            st.session_state.last_model = model

            with st.spinner("Generating persona feedback..."):
                feedback_text = simulate_feedback(
                    feature_description=feature_description.strip(),
                    persona=selected_persona,
                    model=model,
                )

            st.subheader("Simulated Feedback")
            st.write(feedback_text)

            # Save outputs
            run_id = timestamp()
            out_json = {
                "run_id": run_id,
                "mode": "single",
                "model": model,
                "feature_description": feature_description.strip(),
                "persona": selected_persona,
                "feedback": feedback_text,
            }
            json_path = REPORTS_DIR / f"sample_run_{run_id}.json"
            save_json(out_json, json_path)

            md_block = (
                f"## Run {run_id}\n\n"
                f"**Mode:** Single Persona\n\n"
                f"**Model:** {model}\n\n"
                f"**Persona:** {selected_persona.get('name','')}\n\n"
                f"**Feature:**\n{feature_description.strip()}\n\n"
                f"**Feedback:**\n{feedback_text}\n\n"
            )
            append_markdown(CONVERSATIONS_MD, md_block)

            st.success(f"Saved: {json_path.name} and updated conversations.md")

            # Initialize follow-up chat with the assistant output
            st.session_state.chat_history.append({"role": "assistant", "content": feedback_text})

    # ----------------------------
    # Follow-up conversation 
    # ----------------------------
    if st.session_state.last_feature and st.session_state.last_persona:
        st.divider()
        st.subheader("Conversation Mode (Follow-up)")

        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

        followup = st.chat_input("Ask a follow-up question...")
        if followup:
            st.session_state.chat_history.append({"role": "user", "content": followup})

            with st.spinner("Simulating persona response..."):
                reply = simulate_followup(
                    feature_description=st.session_state.last_feature,
                    persona=st.session_state.last_persona,
                    chat_history=st.session_state.chat_history,
                    user_question=followup,
                    model=st.session_state.last_model,
                )

            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            st.rerun()

    st.divider()
    st.subheader("Persona Details")
    st.json(selected_persona)


# ============================================================
# Compare Personas mode
# ============================================================
else:
    selected_names = st.multiselect(
        "Select 2–5 personas",
        persona_names,
        default=persona_names[:2],
    )

    run = st.button("Run Simulation", type="primary")

    if run:
        if not feature_description.strip():
            st.error("Please enter a feature description.")
        elif len(selected_names) < 2:
            st.error("Select at least 2 personas.")
        elif len(selected_names) > 5:
            st.error("Select no more than 5 personas.")
        else:
            with st.spinner("Generating feedback for selected personas..."):
                outputs = []
                for name in selected_names:
                    persona_obj = find_persona_by_name(name)
                    fb = simulate_feedback(
                        feature_description=feature_description.strip(),
                        persona=persona_obj,
                        model=model,
                    )
                    outputs.append(
                        {
                            "persona_name": name,
                            "persona": persona_obj,
                            "feedback": fb,
                        }
                    )

            st.subheader("Persona Feedback Results")
            tabs = st.tabs([o["persona_name"] for o in outputs])
            for tab, o in zip(tabs, outputs):
                with tab:
                    st.write(o["feedback"])

            st.subheader("Aggregated Analysis")
            with st.spinner("Analyzing feedback across personas..."):
                analysis = analyze_feedback(
                    feature_description=feature_description.strip(),
                    outputs=outputs,
                    model=model,
                )
            st.write(analysis)

            # Save outputs
            run_id = timestamp()
            out_json = {
                "run_id": run_id,
                "mode": "compare",
                "model": model,
                "feature_description": feature_description.strip(),
                "selected_personas": selected_names,
                "outputs": outputs,
                "analysis": analysis,
            }
            json_path = REPORTS_DIR / f"batch_run_{run_id}.json"
            save_json(out_json, json_path)

            md_block = (
                f"## Batch Run {run_id}\n\n"
                f"**Mode:** Compare Personas\n\n"
                f"**Model:** {model}\n\n"
                f"**Personas:** {', '.join(selected_names)}\n\n"
                f"**Feature:**\n{feature_description.strip()}\n\n"
                f"**Analysis:**\n{analysis}\n\n"
            )
            append_markdown(CONVERSATIONS_MD, md_block)

            st.success(f"Saved: {json_path.name} and updated conversations.md")
