import streamlit as st

from core.analytics import build_pattern_insights, strategy_by_trigger, top_danger_patterns
from ui.components import card, page_title


def render_insights(real_logs):
    page_title("Insights", "Patterns beat guesses.")
    if real_logs.empty:
        st.info("No real data yet.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Real Logs", len(real_logs))
        c2.metric("Avg Before", round(real_logs["intensity"].mean(), 1))
        c3.metric("Blow-Ups", int((real_logs["outcome"] == "Blew up").sum()))
        if real_logs["intensity_after"].notna().any():
            drops = real_logs.dropna(subset=["intensity_after"]).copy()
            c4.metric("Avg Drop", round((drops["intensity"] - drops["intensity_after"]).mean(), 1))
        else:
            c4.metric("Avg Drop", "—")

        st.subheader("Pattern Cards")
        for insight in build_pattern_insights(real_logs):
            card("Insight", insight)

        st.subheader("Top Danger Patterns")
        danger = top_danger_patterns(real_logs)
        if danger.empty:
            st.info("Not enough pattern data yet.")
        else:
            for _, row in danger.iterrows():
                card(
                    f"{row['trigger']} · {row['intensity_band']}",
                    f"{row['logs']} log(s), {row['blowup_rate']}% blow-up rate, average intensity {row['avg_intensity']}/10.",
                    "danger" if row["blowup_rate"] >= 50 else "normal",
                )

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Triggers by Count")
            st.bar_chart(real_logs["trigger"].value_counts().sort_values(ascending=True))
        with c2:
            st.subheader("Outcomes")
            st.bar_chart(real_logs["outcome"].value_counts().sort_values(ascending=True))

        with st.expander("Detailed Tables"):
            st.subheader("Trigger Risk Table")
            risk = real_logs.assign(blowup=real_logs["outcome"].eq("Blew up")).groupby("trigger").agg(logs=("id", "count"), avg_intensity=("intensity", "mean"), blowup_rate=("blowup", "mean")).sort_values(["blowup_rate", "avg_intensity"], ascending=False)
            risk["avg_intensity"] = risk["avg_intensity"].round(1)
            risk["blowup_rate"] = (risk["blowup_rate"] * 100).round(0).astype(int)
            st.dataframe(risk, use_container_width=True)

            st.subheader("Strategy Effectiveness by Trigger")
            sbt = strategy_by_trigger(real_logs)
            if sbt.empty:
                st.info("No strategy-by-trigger data yet.")
            else:
                st.dataframe(sbt, use_container_width=True, hide_index=True)

        st.subheader("Repair Tracking")
        st.bar_chart(real_logs["repaired"].fillna("Not tracked").value_counts().sort_values(ascending=True))
