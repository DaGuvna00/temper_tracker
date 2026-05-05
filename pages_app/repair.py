import pandas as pd
import streamlit as st

from core.database import update_log
from ui.components import card, page_title


def render_repair(real_logs):
    page_title("Repair Mode", "Fix the moment, don’t replay it.")

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

    last = blowups.sort_values("timestamp", ascending=False).iloc[0]

    card(
        "Last blow-up",
        f"{last['trigger']} · intensity {last['intensity']}/10 · repair status: {last.get('repaired', 'Not tracked')}",
        "danger",
    )

    st.markdown("### What do I need to own?")
    ownership = st.text_area(
        "No excuses. Just your part.",
        placeholder="Example: I raised my voice. I scared them. I kept arguing instead of stepping away.",
    )

    st.markdown("### Simple repair script")
    st.markdown(
        """
        > “I’m sorry I raised my voice. That wasn’t okay.  
        > I was frustrated, but that’s my responsibility to handle better.  
        > I love you, and I’m working on it.”
        """
    )

    st.markdown("### When will I repair?")
    when = st.radio("Choose one", ["Now", "Later today", "Not sure"], horizontal=True)

    intensity_after = None if pd.isna(last["intensity_after"]) else int(last["intensity_after"])
    notes = "" if pd.isna(last["notes"]) else last["notes"]
    strategy = None if pd.isna(last["strategy"]) else last["strategy"]

    if ownership:
        notes = f"{notes}\n\nRepair ownership: {ownership}".strip()

    if when:
        notes = f"{notes}\nRepair timing: {when}".strip()

    if st.button("Mark Repair Planned", use_container_width=True):
        update_log(
            int(last["id"]),
            last["trigger"],
            int(last["intensity"]),
            intensity_after,
            last["outcome"],
            strategy,
            "Planned",
            notes,
        )
        st.success("Repair marked as planned.")
        st.rerun()

    if st.button("Mark Repair Done", use_container_width=True):
        update_log(
            int(last["id"]),
            last["trigger"],
            int(last["intensity"]),
            intensity_after,
            last["outcome"],
            strategy,
            "Yes",
            notes,
        )
        st.success("Repair marked as done.")
        st.rerun()