import pandas as pd
import streamlit as st

from core.analytics import build_pattern_insights, strategy_by_trigger, top_danger_patterns
from ui.components import card, page_title


def get_confidence_label(log_count):
    if log_count < 10:
        return "Too early to tell"
    elif log_count < 30:
        return "Possible pattern"
    return "Stronger pattern"


def extract_warning_signs(real_logs):
    if real_logs.empty or "notes" not in real_logs.columns:
        return {}

    counts = {}

    for note in real_logs["notes"].dropna():
        marker = "Early warning signs:"

        if marker not in note:
            continue

        signs_text = note.split(marker, 1)[1].split("\n", 1)[0]

        signs = [
            s.strip()
            for s in signs_text.split(",")
            if s.strip()
        ]

        for sign in signs:
            if sign.lower() == "not answered":
                continue

            counts[sign] = counts.get(sign, 0) + 1

    return dict(
        sorted(
            counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )
    )


def render_insights(real_logs):
    page_title("Insights", "Useful clues, not fake certainty.")

    if real_logs.empty:
        st.info("No real data yet. Log a few real moments first.")
        return

    log_count = len(real_logs)
    confidence = get_confidence_label(log_count)

    card(
        "Pattern confidence",
        f"{confidence}. Based on {log_count} real log(s). Treat this as guidance, not a diagnosis.",
        "danger" if log_count < 10 else "normal",
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Real Logs", log_count)
    c2.metric("Avg Before", round(real_logs["intensity"].mean(), 1))
    c3.metric("Blow-Ups", int((real_logs["outcome"] == "Blew up").sum()))

    if real_logs["intensity_after"].notna().any():
        drops = real_logs.dropna(subset=["intensity_after"]).copy()

        c4.metric(
            "Avg Drop",
            round((drops["intensity"] - drops["intensity_after"]).mean(), 1),
        )
    else:
        c4.metric("Avg Drop", "—")

    st.divider()

    # -----------------------------
    # Main clues
    # -----------------------------
    st.subheader("Main Clues")

    for insight in build_pattern_insights(real_logs):
        card("Clue", insight)

    # -----------------------------
    # Early warning signs
    # -----------------------------
    st.subheader("Early Warning Signs")

    warning_signs = extract_warning_signs(real_logs)

    if not warning_signs:
        st.info("No early warning signs logged yet.")
    else:
        top_signs = list(warning_signs.items())[:5]

        top_text = "\n".join(
            [
                f"{i + 1}. {sign} ({count}x)"
                for i, (sign, count) in enumerate(top_signs)
            ]
        )

        card(
            "Most common early signs",
            top_text,
            "normal",
        )

        warning_df = pd.DataFrame(
            list(warning_signs.items()),
            columns=["Warning sign", "Count"],
        ).set_index("Warning sign")

        st.bar_chart(warning_df)

    st.divider()

    # -----------------------------
    # Danger patterns
    # -----------------------------
    st.subheader("Possible Danger Patterns")

    danger = top_danger_patterns(real_logs)

    if danger.empty:
        st.info("Not enough pattern data yet.")
    else:
        for _, row in danger.iterrows():
            label = "Possible pattern" if log_count < 30 else "Stronger pattern"

            card(
                f"{label}: {row['trigger']} · {row['intensity_band']}",
                f"{row['logs']} log(s), {row['blowup_rate']}% blow-up rate, average intensity {row['avg_intensity']}/10.",
                "danger" if row["blowup_rate"] >= 50 and row["logs"] >= 3 else "normal",
            )

    st.divider()

    # -----------------------------
    # Charts
    # -----------------------------
    with st.expander("Charts"):
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Triggers by Count")

            st.bar_chart(
                real_logs["trigger"]
                .value_counts()
                .sort_values(ascending=True)
            )

        with c2:
            st.subheader("Outcomes")

            st.bar_chart(
                real_logs["outcome"]
                .value_counts()
                .sort_values(ascending=True)
            )

    # -----------------------------
    # Detailed tables
    # -----------------------------
    with st.expander("Detailed Tables"):
        st.subheader("Trigger Risk Table")

        risk = (
            real_logs.assign(
                blowup=real_logs["outcome"].eq("Blew up")
            )
            .groupby("trigger")
            .agg(
                logs=("id", "count"),
                avg_intensity=("intensity", "mean"),
                blowup_rate=("blowup", "mean"),
            )
            .sort_values(
                ["blowup_rate", "avg_intensity"],
                ascending=False,
            )
        )

        risk["avg_intensity"] = risk["avg_intensity"].round(1)

        risk["blowup_rate"] = (
            risk["blowup_rate"] * 100
        ).round(0).astype(int)

        st.dataframe(risk, use_container_width=True)

        st.subheader("Strategy Effectiveness by Trigger")

        sbt = strategy_by_trigger(real_logs)

        if sbt.empty:
            st.info("No strategy-by-trigger data yet.")
        else:
            st.dataframe(
                sbt,
                use_container_width=True,
                hide_index=True,
            )

    # -----------------------------
    # Repair tracking
    # -----------------------------
    with st.expander("Repair Tracking"):
        st.bar_chart(
            real_logs["repaired"]
            .fillna("Not tracked")
            .value_counts()
            .sort_values(ascending=True)
        )