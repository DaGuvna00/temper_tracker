import streamlit as st


def reset_emergency_session(start=False):
    st.session_state.trigger_mode = start
    st.session_state.trigger_step = 0
    st.session_state.trigger_outcome = None
    st.session_state.trigger_intervention = None
    st.session_state.trigger_mantra = None
    st.session_state.trigger_context_saved = False
    st.session_state.trigger_context = {}


def reset_trigger_flow():
    reset_emergency_session(start=False)


def init_session_state():
    for key, default in {
        "trigger_mode": False,
        "trigger_step": 0,
        "trigger_context_saved": False,
        "trigger_context": {},
        "trigger_outcome": None,
        "trigger_intervention": None,
        "trigger_mantra": None,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default
