from datetime import date, timedelta

import streamlit as st

from core.analytics import build_pattern_insights, strategy_by_trigger, top_danger_patterns
from ui.components import card, page_title


def render_weekly_review(real_logs):
    page_title("Weekly Review", "A quick review so the data turns into behaviour change.")
    if real_logs.empty:
        st.info("No logs yet. Weekly review will become useful after a few days of real use.")
    else:
        end_date = st.date_input("Week ending", value=date.today())
        start_date = end_date - timedelta(days=6)
        prev_start = start_date - timedelta(days=7)
        prev_end = start_date - timedelta(days=1)
        this_week = real_logs[(real_logs["date"] >= start_date) & (real_logs["date"] <= end_date)]
        prev_week = real_logs[(real_logs["date"] >= prev_start) & (real_logs["date"] <= prev_end)]
        st.caption(f"Current review window: {start_date} to {end_date}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Logs", len(this_week), delta=len(this_week) - len(prev_week))
        c2.metric("Blow-Ups", int((this_week["outcome"] == "Blew up").sum()), delta=int((this_week["outcome"] == "Blew up").sum()) - int((prev_week["outcome"] == "Blew up").sum()))
        c3.metric("Stayed Calm", int((this_week["outcome"] == "Stayed calm").sum()), delta=int((this_week["outcome"] == "Stayed calm").sum()) - int((prev_week["outcome"] == "Stayed calm").sum()))
        c4.metric("Avg Intensity", "—" if this_week.empty else round(this_week["intensity"].mean(), 1))
        if this_week.empty:
            st.info("No logs in this review window.")
        else:
            for insight in build_pattern_insights(this_week):
                card("This week says", insight)
            danger = top_danger_patterns(this_week)
            if not danger.empty:
                top_row = danger.iloc[0]
                card("Focus for next week", f"Main focus: {top_row['trigger']} during {top_row['intensity_band']} intensity. Intervene before it reaches 7/10.", "danger")
            else:
                card("Focus for next week", "Keep logging consistently so the pattern gets clearer.")
            sbt = strategy_by_trigger(this_week)
            if not sbt.empty:
                best = sbt.sort_values(["success_rate", "avg_drop"], ascending=False).iloc[0]
                card("Best strategy this week", f"{best['strategy']} for {best['trigger']} ({best['success_rate']}% success, avg drop {best['avg_drop']}).", "success")
            st.text_area("Reflection", placeholder="What did I learn? What do I want to try next week?", height=160)
