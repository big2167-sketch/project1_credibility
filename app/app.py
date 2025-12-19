"""
Deliverable 3: Live application integration (Streamlit).

This app:
- takes multiple URLs
- runs score_source() on each
- shows score + explanation
- includes basic fallback handling and progress UI
"""

import pandas as pd
import streamlit as st
from src.scorer import score_source


st.set_page_config(page_title="CS676 - Project 1 Credibility Scorer", layout="wide")

st.title("Project 1: Credibility Scoring")
st.write("Paste one or more URLs (one per line), then click **Score Sources**.")

urls_text = st.text_area(
    "URLs (one per line)",
    height=200,
    placeholder="https://www.nih.gov\nhttps://www.cdc.gov\nexample.com\nnot a url"
)

col1, col2 = st.columns([1, 2])
with col1:
    run_btn = st.button("Score Sources")

with col2:
    st.caption("Tip: include a mix of .gov/.edu and normal sites to show score differences.")

if run_btn:
    raw_lines = [ln.strip() for ln in urls_text.splitlines() if ln.strip()]
    if not raw_lines:
        st.warning("Please enter at least one URL.")
        st.stop()

    results = []
    progress = st.progress(0)
    status = st.empty()

    for i, u in enumerate(raw_lines, start=1):
        status.write(f"Scoring {i}/{len(raw_lines)}: {u}")
        out = score_source(u)

        # Fallback: if something unexpected happens, protect the UI
        if not isinstance(out, dict) or "score" not in out or "explanation" not in out:
            out = {"score": 0.0, "explanation": "Internal error: output not in expected format."}

        results.append({
            "url": u,
            "score": out["score"],
            "explanation": out["explanation"]
        })
        progress.progress(i / len(raw_lines))

    status.success("Done.")

    df = pd.DataFrame(results).sort_values(by="score", ascending=False)
    st.subheader("Results")
    st.dataframe(df, use_container_width=True)

    st.subheader("Interpretation")
    st.write(
        "- Scores are **heuristic** (draft) and meant to show meaningful distinctions.\n"
        "- Higher scores typically reflect trusted domains (e.g., .gov/.edu), HTTPS, and signals like references/date/author hints."
    )