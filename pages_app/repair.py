import pandas as pd
import streamlit as st

from core.database import update_log
from ui.components import card, page_title


OWNERSHIP_OPTIONS = [
    "Raised my voice",
    "Kept arguing instead of stepping away",
    "Was too harsh",
    "Reacted instead of pausing",
    "Blamed instead of owning my part",
    "Scared or overwhelmed someone",
    "Something else",
]


REPAIR_SCRIPTS = {
    "Child": {
        "Raised my voice": """I’m sorry I raised my voice. That wasn’t okay.
You didn’t deserve to be spoken to that way.
I was frustrated, but it’s my job to handle that better.
I love you, and I’m working on it.""",
        "Kept arguing instead of stepping away": """I’m sorry I kept arguing instead of taking a break.
I should have stepped away before things got worse.
I’m going to work on pausing sooner next time.
I love you.""",
        "Was too harsh": """I’m sorry I was too harsh.
I could have handled that with more patience.
You’re allowed to make mistakes, and I’m working on handling mine better too.""",
        "Reacted instead of pausing": """I’m sorry I reacted too fast.
I should have paused before responding.
Next time I’m going to slow down before I speak.""",
        "Blamed instead of owning my part": """I’m sorry I blamed you instead of owning my part.
I’m the adult, and I need to handle my feelings better.
I’m going to keep working on that.""",
        "Scared or overwhelmed someone": """I’m sorry I scared or overwhelmed you.
That wasn’t okay.
You should feel safe with me, even when I’m frustrated.
I love you, and I’m working on handling anger better.""",
        "Something else": """I’m sorry for how I handled that.
That wasn’t okay.
I’m going to keep working on doing better.""",
    },
    "Partner": {
        "Raised my voice": """I’m sorry I raised my voice.
That wasn’t fair to you.
I was overwhelmed, but that doesn’t excuse how I spoke.
I’m going to work on taking space before I get to that point.""",
        "Kept arguing instead of stepping away": """I’m sorry I kept arguing when I should have stepped away.
I let it keep building instead of pausing.
Next time I’m going to take space sooner.""",
        "Was too harsh": """I’m sorry I was too harsh.
I could have said what I felt without cutting you down.
I’m going to work on being clearer without being hurtful.""",
        "Reacted instead of pausing": """I’m sorry I reacted instead of pausing.
I let the emotion drive my response.
Next time I’ll slow down before I answer.""",
        "Blamed instead of owning my part": """I’m sorry I blamed instead of owning my part.
I can see where I contributed to that moment.
I’m going to take responsibility for my side.""",
        "Scared or overwhelmed someone": """I’m sorry I overwhelmed you.
That’s not the kind of partner I want to be.
I’m going to work on lowering the intensity sooner.""",
        "Something else": """I’m sorry for my part in that.
I didn’t handle it the way I want to.
I’m taking responsibility, and I’m working on doing better.""",
    },
    "General": {
        "Raised my voice": """I’m sorry I raised my voice.
That wasn’t okay.
I was frustrated, but I’m responsible for how I respond.""",
        "Kept arguing instead of stepping away": """I’m sorry I kept pushing instead of stepping away.
I should have paused before things got worse.
I’ll work on taking space sooner.""",
        "Was too harsh": """I’m sorry I was too harsh.
I could have handled that better.
I’ll work on being more patient next time.""",
        "Reacted instead of pausing": """I’m sorry I reacted too quickly.
I should have paused first.
I’m working on slowing down before I respond.""",
        "Blamed instead of owning my part": """I’m sorry I blamed instead of owning my part.
I’m responsible for my reaction.
I’ll do better at owning my side.""",
        "Scared or overwhelmed someone": """I’m sorry I overwhelmed you.
That wasn’t okay.
I’ll work on lowering the intensity sooner.""",
        "Something else": """I’m sorry for how I handled that.
That wasn’t okay.
I’m going to work on doing better.""",
    },
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

    st.markdown(
        """
        <div class='tt-card'>
            <div class='tt-big-text'>
                This is not about beating yourself up. Own it, repair it, move forward.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
        repaired_status = _safe_value(row.get("repaired"), "Not tracked")
        label = (
            f"{row['timestamp'].strftime('%Y-%m-%d %I:%M %p')} · "
            f"{row['trigger']} · {row['intensity']}/10 · "
            f"repair: {repaired_status}"
        )
        options.append(label)
        option_map[label] = row

    selected_label = st.selectbox("Choose a moment", options)
    selected = option_map[selected_label]

    card(
        "Selected moment",
        f"{selected['trigger']} · intensity {selected['intensity']}/10 · repair status: {_safe_value(selected.get('repaired'), 'Not tracked')}",
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
    ownership_choice = st.radio(
        "Pick the closest one",
        OWNERSHIP_OPTIONS,
    )

    ownership_extra = ""
    if ownership_choice == "Something else":
        ownership_extra = st.text_area(
            "Write your part",
            placeholder="Example: I kept pushing when I should have stepped away.",
        )

    ownership_final = ownership_extra if ownership_choice == "Something else" else ownership_choice

    script = REPAIR_SCRIPTS[repair_target].get(
        ownership_choice,
        REPAIR_SCRIPTS[repair_target]["Something else"],
    )

    st.markdown("### Suggested repair script")
    st.code(script, language=None)

    st.markdown("### When will I repair?")
    when = st.radio(
        "Choose one",
        ["Now", "Later today", "Not sure"],
        horizontal=True,
    )

    updated_notes = existing_notes

    if ownership_final:
        updated_notes = f"{updated_notes}\n\nRepair ownership: {ownership_final}".strip()

    updated_notes = f"{updated_notes}\nRepair target: {repair_target}".strip()
    updated_notes = f"{updated_notes}\nRepair timing: {when}".strip()

    st.divider()

    if st.button("✅ Mark Repair Done", use_container_width=True):
        values = _prepare_log_values(selected, "Yes", updated_notes)
        update_log(**values)
        st.success("Repair marked as done.")
        st.rerun()

    if st.button("🕒 Mark Repair Planned", use_container_width=True):
        values = _prepare_log_values(selected, "Planned", updated_notes)
        update_log(**values)
        st.success("Repair marked as planned.")
        st.rerun()

    if st.button("Not needed for this one", use_container_width=True):
        values = _prepare_log_values(selected, "Not needed", updated_notes)
        update_log(**values)
        st.success("Marked as not needed.")
        st.rerun()