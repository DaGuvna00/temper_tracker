import streamlit as st


def outcome_color(outcome):
    return {"Stayed calm": "🟢", "Struggled": "🟡", "Blew up": "🔴"}.get(outcome, "⚪")


def page_title(title, subtitle):
    st.title(title)
    st.caption(subtitle)


def card(title, body, kind="normal"):
    css = "tt-card"
    if kind == "danger":
        css = "tt-danger"
    elif kind == "success":
        css = "tt-success"
    st.markdown(f"<div class='{css}'><strong>{title}</strong><br><span class='tt-muted'>{body}</span></div>", unsafe_allow_html=True)
