from datetime import date, timedelta

import pandas as pd
import streamlit as st

from core.analytics import strategy_by_trigger, top_danger_patterns
from core.database import (
    load_weekly_experiment,
    save_weekly_experiment,
    update_weekly_experiment,
)
from ui.components import card, page_title


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


def build_weekly_narrative(this_week):
    if this_week.empty:
        return "No logs this week yet. The review becomes useful once a few real moments are logged."

    blowups = int((this_week["outcome"] == "Blew up").sum())
    stayed_calm = int((this_week["outcome"] == "Stayed calm").sum())
    avg_intensity = round(this_week["intensity"].mean(), 1)

    top_trigger = this_week["trigger"].mode().iloc[0] if not this_week.empty else None

    narrative = (
        f"This week, the most common trigger was {top_trigger}. "
        f"You logged {stayed_calm} calm outcome(s) and {blowups} blow-up(s). "
        f"Average intensity was {avg_intensity}/10."
    )

    if blowups > stayed_calm:
        narrative += " The main opportunity is catching escalation earlier, before it becomes hard to recover."
    elif stayed_calm > blowups:
        narrative += " There were more calm outcomes than blow-ups, which is a real sign of progress."
    else:
        narrative += " This looks like a mixed week. The goal is not perfection — it is earlier interruption and faster repair."

    return narrative


def build_next_focus(this_week):
    if this_week.empty:
        return "Log consistently next week so the pattern gets clearer.", "normal"

    danger = top_danger_patterns(this_week)

    if not danger.empty:
        top_row = danger.iloc[0]
        trigger = top_row["trigger"]
        intensity_band = str(top_row["intensity_band"])

        if "High" in intensity_band:
            return (
                f"When {trigger} starts building, intervene before it reaches 7/10. "
                f"Do not wait until you are already flooded.",
                "danger",
            )

        return (
            f"Watch {trigger} earlier in the moment. Use Emergency Mode before it turns into a high-intensity situation.",
            "normal",
        )

    return "Keep logging consistently so the pattern gets clearer.", "normal"


def build_behavior_experiment(this_week):
    if this_week.empty:
        return "Log a few real moments this week so the app can suggest a useful experiment."

    avg_intensity = round(this_week["intensity"].mean(), 1)
    blowups = this_week[this_week["outcome"] == "Blew up"]

    if not blowups.empty:
        trigger = blowups["trigger"].mode().iloc[0]

        return (
            f"When {trigger} starts building, step away at 5/10 instead of waiting until it hits 7/10."
        )

    if avg_intensity >= 6:
        return "Use Emergency Mode earlier this week, even when you think you can still handle it."

    top_trigger = this_week["trigger"].mode().iloc[0]

    return f"Keep noticing what helps you stay calm during {top_trigger}."


def render_weekly_review(real_logs):
    page_title("Weekly Review", "Turn the week into one clear next move.")

    if real_logs.empty:
        st.info("No logs yet. Weekly review will become useful after a few days of real use.")
        return

    end_date = st.date_input("Week ending", value=date.today())
    start_date = end_date - timedelta(days=6)

    prev_start = start_date - timedelta(days=7)
    prev_end = start_date - timedelta(days=1)

    this_week = real_logs[
        (real_logs["date"] >= start_date)
        & (real_logs["date"] <= end_date)
    ]

    prev_week = real_logs[
        (real_logs["date"] >= prev_start)
        & (real_logs["date"] <= prev_end)
    ]

    st.caption(f"Current review window: {start_date} to {end_date}")

    if this_week.empty:
        st.info("No logs in this review window.")
        return

    logs_count = len(this_week)
    prev_logs_count = len(prev_week)

    blowups = int((this_week["outcome"] == "Blew up").sum())
    prev_blowups = int((prev_week["outcome"] == "Blew up").sum())

    stayed_calm = int((this_week["outcome"] == "Stayed calm").sum())
    prev_stayed_calm = int((prev_week["outcome"] == "Stayed calm").sum())

    avg_intensity = round(this_week["intensity"].mean(), 1)

    if not prev_week.empty:
        prev_avg_intensity = round(prev_week["intensity"].mean(), 1)
        intensity_delta = round(avg_intensity - prev_avg_intensity, 1)
    else:
        intensity_delta = None

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Logs",
        logs_count,
        delta=logs_count - prev_logs_count,
    )

    c2.metric(
        "Blow-Ups",
        blowups,
        delta=blowups - prev_blowups,
    )

    c3.metric(
        "Stayed Calm",
        stayed_calm,
        delta=stayed_calm - prev_stayed_calm,
    )

    c4.metric(
        "Avg Intensity",
        avg_intensity,
        delta=intensity_delta if intensity_delta is not None else None,
    )

    st.divider()

    repairs_done = int((this_week["repaired"].fillna("") == "Yes").sum())
    emergency_uses = int((this_week["source"] == "Emergency mode").sum())

    win_parts = []

    if stayed_calm:
        win_parts.append(f"{stayed_calm} calm outcome(s)")

    if repairs_done:
        win_parts.append(f"{repairs_done} repair(s) completed")

    if emergency_uses:
        win_parts.append(f"{emergency_uses} Emergency Mode use(s)")

    if not win_parts:
        win_text = "No obvious wins logged yet, but showing up and tracking honestly still counts."
    else:
        win_text = ", ".join(win_parts) + "."

    card("Wins this week", win_text, "success")

    card(
        "This week’s pattern",
        build_weekly_narrative(this_week),
        "normal",
    )

    warning_signs = extract_warning_signs(this_week)

    if warning_signs:
        top_signs = list(warning_signs.items())[:3]

        warning_text = "\n".join(
            [
                f"{i + 1}. {sign} ({count}x)"
                for i, (sign, count) in enumerate(top_signs)
            ]
        )

        card(
            "Early warning signs this week",
            warning_text,
            "normal",
        )
    else:
        card(
            "Early warning signs this week",
            "No warning signs logged yet. After Emergency Mode, choose any signs you noticed before things escalated.",
            "normal",
        )

    sbt = strategy_by_trigger(this_week)

    if not sbt.empty:
        best = sbt.sort_values(
            ["success_rate", "avg_drop"],
            ascending=False,
        ).iloc[0]

        confidence = "appears promising" if int(best["uses"]) < 3 else "worked best"

        card(
            "Best strategy this week",
            f"{best['strategy']} for {best['trigger']} {confidence} ({best['uses']} use(s), {best['success_rate']}% calm outcome rate, avg drop {best['avg_drop']}).",
            "success" if int(best["uses"]) >= 3 else "normal",
        )
    else:
        card(
            "Best strategy this week",
            "Not enough strategy data yet.",
            "normal",
        )

    focus_text, focus_kind = build_next_focus(this_week)

    card(
        "Focus for next week",
        focus_text,
        focus_kind,
    )

    st.divider()

    # -----------------------------
    # Weekly Behavior Experiment
    # -----------------------------
    st.subheader("Behavior Experiment")

    suggested_experiment = build_behavior_experiment(this_week)
    saved_experiment = load_weekly_experiment(start_date, end_date)

    if saved_experiment:
        card(
            "Current experiment",
            saved_experiment["experiment_text"],
            "success" if saved_experiment.get("status") in ["Worked", "Tried"] else "normal",
        )

        status_options = ["Planned", "Tried", "Worked", "Didn’t work"]
        current_status = saved_experiment.get("status", "Planned")

        status = st.selectbox(
            "Experiment status",
            status_options,
            index=status_options.index(current_status) if current_status in status_options else 0,
        )

        reflection = st.text_area(
            "Experiment reflection",
            value=saved_experiment.get("reflection") or "",
            placeholder="Did you try it? What happened?",
            height=120,
        )

        if st.button("Save Experiment Update", use_container_width=True):
            update_weekly_experiment(
                saved_experiment["id"],
                status=status,
                reflection=reflection,
            )
            st.success("Experiment updated.")
            st.rerun()

    else:
        card(
            "Suggested experiment",
            suggested_experiment,
            "normal",
        )

        if st.button("Accept this experiment", use_container_width=True):
            save_weekly_experiment(
                start_date,
                end_date,
                suggested_experiment,
                status="Planned",
                reflection="",
            )
            st.success("Experiment saved.")
            st.rerun()

    st.divider()

    st.text_area(
        "Reflection",
        placeholder="What did I learn? What do I want to try next week?",
        height=160,
    )

    with st.expander("Raw weekly details"):
        danger = top_danger_patterns(this_week)

        if danger.empty:
            st.info("Not enough danger pattern data yet.")
        else:
            st.dataframe(danger, use_container_width=True, hide_index=True)

        if not sbt.empty:
            st.dataframe(sbt, use_container_width=True, hide_index=True)