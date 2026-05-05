import pandas as pd
import streamlit as st

from core.database import update_log
from ui.components import card, page_title


REPAIR_SCRIPTS = {
    "Child": """“I’m sorry I raised my voice. That wasn’t okay.
I was frustrated, but it’s my job to handle that better.
I love you, and I’m working on it.”""",
    "Partner": """“I’m sorry for how I handled that. I got overwhelmed and reacted badly.
That’s not an excuse. I’m going to take space sooner next time instead of letting it build.”""",
    "General": """“I’m sorry for my part in that. I didn’t handle it the way I want to.
I’m taking responsibility, and I’m working on doing better next time.”""",
}


def _safe_value(value, fallback=""):
    return fallback if pd.isna(value) else value


def _prepare_log_values(row, repaired_status, notes):
    intensity_after = None if pd.isna(row["intensity_after"]) else int(row["intensity_after"])
    strategy = None if pd.isna(row["strategy"]) else row["strategy"]

    return {
        "log_id": int(row["id"]),
        "trigger": row["trigger"],
        "intensity": int(row["intensity"]),
        "intensity_after": intensity_after,
        "outcome": row["outcome"],
        "strategy": strategy,
        "repaired": repaired_status,
        "notes": notes,
    }


def render_repair(real_logs):
    page_title("Repair Mode", "Repair fast. Shame slow.")

    if real_logs.empty:
        st.info("No logs yet. Repair Mode becomes useful after a blow-up is logged.")
        return

    blowups = real_logs[real_logs["outcome"] == "Blew up"].copy()

    if blowups.empty:
        card(
            "No repair needed right now",
            "No blow-ups found in your logs. That’s a good thing.",
            "success",
        )
        return

    unrepaired = blowups[
        blowups["repaired"].fillna("Not needed").isin(["Not needed", "No", "Planned"])
    ].copy()

    if not unrepaired.empty:
        card(
            "Repair queue",
            f"You have {len(unrepaired)} blow-up(s) that may still need repair.",
            "danger",
        )
        repair_pool = unrepaired
    else:
        card(
            "Repair queue clear",
            "No unrepaired blow-ups found. You can still review older moments below.",
            "success",
        )
        repair_pool = blowups

    repair_pool = repair_pool.sort_values("timestamp", ascending=False)

    options = []
    option_map = {}

    for _, row in repair_pool.iterrows():
        label = (
            f"{row['timestamp'].strftime('%Y-%m-%d %I:%M %p')} · "
            f"{row['trigger']} · {row['intensity']}/10 · "
            f"repair: {row.get('repaired', 'Not tracked')}"
        )
        options.append(label)
        option_map[label] = row

    selected_label = st.selectbox("Choose a blow-up to repair", options)
    selected = option_map[selected_label]

    card(
        "Selected moment",
        f"{selected['trigger']} · intensity {selected['intensity']}/10 · repair status: {selected.get('repaired', 'Not tracked')}",
        "danger",
    )

    existing_notes = _safe_value(selected["notes"])

    with st.expander("View original notes"):
        st.write(existing_notes if existing_notes else "No notes saved.")

    st.markdown("### Who needs the repair?")
    repair_target = st.radio(
        "Choose one",
        ["Child", "Partner", "General"],
        horizontal=True,
    )

    st.markdown("### What do I need to own?")
    ownership = st.text_area(
        "No excuses. Just your part.",
        placeholder="Example: I raised my voice. I scared them. I kept arguing instead of stepping away.",
    )

    st.markdown("### Suggested repair script")
    st.markdown(f"> {REPAIR_SCRIPTS[repair_target].replace(chr(10), chr(10) + '> ')}")

    st.markdown("### When will I repair?")
    when = st.radio("Choose one", ["Now", "Later today", "Not sure"], horizontal=True)

    updated_notes = existing_notes

    if ownership:
        updated_notes = f"{updated_notes}\n\nRepair ownership: {ownership}".strip()

    updated_notes = f"{updated_notes}\nRepair target: {repair_target}".strip()
    updated_notes = f"{updated_notes}\nRepair timing: {when}".strip()

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Mark Repair Planned", use_container_width=True):
            values = _prepare_log_values(selected, "Planned", updated_notes)
            update_log(**values)
            st.success("Repair marked as planned.")
            st.rerun()

    with c2:
        if st.button("Mark Repair Done", use_container_width=True):
            values = _prepare_log_values(selected, "Yes", updated_notes)
            update_log(**values)
            st.success("Repair marked as done.")
            st.rerun()