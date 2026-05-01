import streamlit as st

from core.constants import DEFAULT_INTERVENTIONS, OUTCOME_OPTIONS, REPAIR_OPTIONS, TRIGGER_OPTIONS
from core.database import add_log
from ui.components import page_title


def render_log():
    page_title("Quick Log", "Log what happened in under 15 seconds.")
    with st.form("anger_log_form", clear_on_submit=True):
        trigger = st.selectbox("What triggered it?", TRIGGER_OPTIONS)
        c1, c2 = st.columns(2)
        intensity = c1.slider("Intensity before", 1, 10, 5)
        intensity_after = c2.slider("Intensity after", 1, 10, 5)
        outcome = st.radio("Outcome", OUTCOME_OPTIONS, horizontal=True)
        strategy = st.selectbox("What did you try?", ["None"] + [x["name"] for x in DEFAULT_INTERVENTIONS] + ["Other"])
        repaired = st.selectbox("Repair/apology?", REPAIR_OPTIONS)
        notes = st.text_area("Optional notes", placeholder="What happened? What did you notice?")
        submitted = st.form_submit_button("Save Log", use_container_width=True)
    if submitted:
        add_log(trigger, intensity, outcome, notes, "Manual log", None if strategy == "None" else strategy, intensity_after, repaired)
        st.success("Saved. Data beats guessing.")
