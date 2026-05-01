from datetime import date

import pandas as pd
import streamlit as st

from core.analytics import build_pattern_insights, calculate_risk_score
from core.state import reset_emergency_session
from ui.components import card, page_title


def render_home(real_logs, checkins):
    page_title("Temper Tracker", "Your anger-control dashboard. Simple, honest, useful.")

    # The emergency action must be first on mobile. No scrolling. No sidebar hunting.
    st.markdown(
        """
        <div class='tt-danger'>
            <div class='tt-big-text'>
                <strong>Need help right now?</strong><br>
                Start Emergency Mode before anything gets worse.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🚨 START EMERGENCY RESET", use_container_width=True):
        reset_emergency_session(start=True)
        st.session_state.current_page = "Emergency"
        st.rerun()

    a, b = st.columns(2)
    with a:
        if st.button("📝 Quick Log", use_container_width=True):
            st.session_state.current_page = "Log"
            st.rerun()
    with b:
        if st.button("✅ Daily Check-In", use_container_width=True):
            st.session_state.current_page = "Daily Check-In"
            st.rerun()

    st.divider()

    today = date.today()
    today_logs = real_logs[real_logs["date"] == today] if not real_logs.empty else pd.DataFrame()
    today_checkin = checkins[checkins["checkin_date"] == today] if not checkins.empty else pd.DataFrame()
    risk_score, risk_label, risk_reasons = calculate_risk_score(today_checkin, real_logs)

    st.subheader("Today")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Triggers Today", 0 if today_logs.empty else len(today_logs))
    c2.metric("Blow-Ups Today", 0 if today_logs.empty else int((today_logs["outcome"] == "Blew up").sum()))
    c3.metric("Avg Intensity", "—" if today_logs.empty else round(today_logs["intensity"].mean(), 1))
    c4.metric("Risk", risk_label, delta=f"{risk_score}/100")

    if len(real_logs) < 20:
        card("Early data warning", f"Only {len(real_logs)} real log(s) so far. Treat risk and pattern results as early clues, not hard truth.")

    if risk_reasons:
        card("Today’s risk factors", ", ".join(risk_reasons) + ".", "danger" if risk_label == "High" else "normal")
    else:
        card("Today’s risk factors", "No major risk flags based on current data.", "success")

    st.divider()
    st.subheader("This Week Snapshot")
    if real_logs.empty:
        st.info("No real logs yet.")
    else:
        last_7 = real_logs[real_logs["timestamp"] >= pd.Timestamp.now() - pd.Timedelta(days=7)]
        if not last_7.empty:
            a, b, c = st.columns(3)
            a.metric("Most Common Trigger", last_7["trigger"].mode().iloc[0])
            b.metric("Blow-Ups This Week", int((last_7["outcome"] == "Blew up").sum()))
            c.metric("Avg Intensity", round(last_7["intensity"].mean(), 1))
            for insight in build_pattern_insights(last_7):
                card("Early clue", insight)
