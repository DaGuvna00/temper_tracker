from datetime import date

import pandas as pd
import streamlit as st

from core.analytics import build_pattern_insights, calculate_risk_score
from core.state import reset_emergency_session
from ui.components import card, page_title


def render_home(real_logs, checkins):
    page_title("Temper Tracker", "Calm first. Log second. Learn over time.")

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

    c1, c2 = st.columns(2)
    c1.metric("Risk", risk_label, delta=f"{risk_score}/100")
    c2.metric("Blow-Ups Today", 0 if today_logs.empty else int((today_logs["outcome"] == "Blew up").sum()))

    if risk_label == "High":
        focus = "Lower exposure today. Step away earlier than feels necessary."
        focus_kind = "danger"
    elif risk_label == "Medium":
        focus = "Catch the early signs. Don’t let it climb to 7/10."
        focus_kind = "normal"
    else:
        focus = "Maintain control. Notice what is working."
        focus_kind = "success"

    card("Today’s focus", focus, focus_kind)

    if risk_reasons:
        card(
            "Main risk factor",
            ", ".join(risk_reasons) + ".",
            "danger" if risk_label == "High" else "normal",
        )
    else:
        card("Main risk factor", "No major risk flags based on current data.", "success")

    # -----------------------------
    # Repair Queue
    # -----------------------------
    if not real_logs.empty:
        blowups = real_logs[real_logs["outcome"] == "Blew up"].copy()

        if not blowups.empty:
            needs_repair = blowups[
                blowups["repaired"]
                .fillna("Not needed")
                .isin(["Not needed", "No", "Planned"])
            ]

            repair_count = len(needs_repair)

            if repair_count > 0:
                card(
                    "Repair queue",
                    f"{repair_count} moment(s) may still need repair. Repair builds trust faster than perfection.",
                    "danger",
                )

                if st.button("🛠️ Go to Repair Mode", use_container_width=True):
                    st.session_state.current_page = "Repair"
                    st.rerun()
            else:
                card(
                    "Repair queue",
                    "All logged blow-ups are marked repaired. That’s progress.",
                    "success",
                )

    if len(real_logs) < 20:
        card(
            "Early data warning",
            f"Only {len(real_logs)} real log(s) so far. Treat patterns as clues, not truth.",
        )

    st.divider()

    st.subheader("Last Moment")

    if real_logs.empty:
        card("No logs yet", "Use Quick Log after a moment happens. Small data beats memory.")
    else:
        last = real_logs.sort_values("timestamp", ascending=False).iloc[0]

        trigger = last["trigger"]
        outcome = last["outcome"]
        intensity = last["intensity"]

        if outcome == "Blew up":
            card(
                "Repair may matter",
                f"Last logged moment: {trigger}, intensity {intensity}/10. Don’t spiral — repair beats shame.",
                "danger",
            )

            if st.button("🛠️ Start Repair Mode", use_container_width=True):
                st.session_state.current_page = "Repair"
                st.session_state.repair_log_id = int(last["id"])
                st.rerun()

        elif outcome == "Stayed calm":
            card(
                "Recent win",
                f"You stayed calm during {trigger} at {intensity}/10. That counts.",
                "success",
            )
        else:
            card(
                "Recent struggle",
                f"You struggled with {trigger} at {intensity}/10. Good data. Watch that pattern.",
                "normal",
            )

    st.divider()

    with st.expander("Weekly snapshot"):
        if real_logs.empty:
            st.info("No real logs yet.")
        else:
            last_7 = real_logs[real_logs["timestamp"] >= pd.Timestamp.now() - pd.Timedelta(days=7)]
            if last_7.empty:
                st.info("No logs in the last 7 days.")
            else:
                a, b, c = st.columns(3)
                a.metric("Most Common Trigger", last_7["trigger"].mode().iloc[0])
                b.metric("Blow-Ups", int((last_7["outcome"] == "Blew up").sum()))
                c.metric("Avg Intensity", round(last_7["intensity"].mean(), 1))

                for insight in build_pattern_insights(last_7):
                    card("Early clue", insight)