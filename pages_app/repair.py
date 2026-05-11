import streamlit as st

from core.database import update_log
from core.repair_engine import (
    OWNERSHIP_OPTIONS,
    REPAIR_TARGET_OPTIONS,
    REPAIR_TIMING_OPTIONS,
    build_repair_notes,
    build_repair_options,
    choose_repair_pool,
    get_blowups,
    get_repair_script,
    prepare_log_values,
    safe_value,
)
from ui.components import card, page_title


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

    blowups = get_blowups(real_logs)

    if blowups.empty:
        card(
            "No repair needed right now",
            "No blow-ups found in your logs. That's a good thing.",
            "success",
        )
        return

    repair_pool, has_unrepaired = choose_repair_pool(blowups)

    if has_unrepaired:
        card(
            "Repair queue",
            f"You have {len(repair_pool)} blow-up(s) that may still need repair.",
            "danger",
        )
    else:
        card(
            "Repair queue clear",
            "No unrepaired blow-ups found. You can still review older moments below.",
            "success",
        )

    repair_pool = repair_pool.sort_values("timestamp", ascending=False)

    options, option_map = build_repair_options(repair_pool)

    selected_label = st.selectbox("Choose a moment", options)
    selected = option_map[selected_label]

    card(
        "Selected moment",
        f"{selected['trigger']} · intensity {selected['intensity']}/10 · repair status: {safe_value(selected.get('repaired'), 'Not tracked')}",
        "danger",
    )

    existing_notes = safe_value(selected["notes"])

    with st.expander("View original notes"):
        st.write(existing_notes if existing_notes else "No notes saved.")

    st.markdown("### Who needs the repair?")
    repair_target = st.radio(
        "Choose one",
        REPAIR_TARGET_OPTIONS,
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

    script = get_repair_script(repair_target, ownership_choice)

    st.markdown("### Suggested repair script")
    st.code(script, language=None)

    st.markdown("### When will I repair?")
    when = st.radio(
        "Choose one",
        REPAIR_TIMING_OPTIONS,
        horizontal=True,
    )

    updated_notes = build_repair_notes(existing_notes, ownership_final, repair_target, when)

    st.divider()

    if st.button("Mark Repair Done", use_container_width=True):
        values = prepare_log_values(selected, "Yes", updated_notes)
        update_log(**values)
        st.success("Repair marked as done.")
        st.rerun()

    if st.button("📅 Mark Repair Planned", use_container_width=True):
        values = prepare_log_values(selected, "Planned", updated_notes)
        update_log(**values)
        st.success("Repair marked as planned.")
        st.rerun()

    if st.button("Not needed for this one", use_container_width=True):
        values = prepare_log_values(selected, "Not needed", updated_notes)
        update_log(**values)
        st.success("Marked as not needed.")
        st.rerun()
