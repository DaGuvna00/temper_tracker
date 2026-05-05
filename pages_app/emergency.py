import streamlit as st

from core.analytics import get_emergency_intervention, get_emergency_mantra
from core.constants import REPAIR_OPTIONS, TRIGGER_OPTIONS
from core.database import add_log
from core.state import reset_emergency_session, reset_trigger_flow

def render_emergency(adaptive_interventions):
    st.markdown("<div class='tt-emergency-title'>🚨 Emergency Mode</div>", unsafe_allow_html=True)
    st.caption("Calm first. Think later.")

    if not st.session_state.trigger_mode and not st.session_state.get("trigger_outcome"):
        st.markdown(
            """
            <div class='tt-danger'>
                <div class='tt-big-text'>
                    <strong>First move:</strong><br>
                    Stop talking. Create space. Lower the damage.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🚨 Start Reset", use_container_width=True):
            reset_emergency_session(start=True)
            st.rerun()

    if st.session_state.trigger_mode and not st.session_state.get("trigger_outcome"):
        step = st.session_state.trigger_step
        intervention = get_emergency_intervention(step, adaptive_interventions)
        mantra = get_emergency_mantra(step)

        st.session_state.trigger_intervention = intervention["name"]
        st.session_state.trigger_mantra = mantra

        st.caption(f"Strategy {step + 1}")

        st.markdown(
            f"""
            <div class='tt-mantra'>
                🧠 <strong>Repeat:</strong><br>{mantra}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("## Right now")
        st.markdown(
            """
            <div class='tt-card'>
                <div class='tt-big-text'>
                    Stop talking.<br>
                    Take 3 slow breaths.<br>
                    Step away if you can.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Next move")
        primary_action = intervention["instructions"][0]

        st.markdown(
            f"""
            <div class='tt-card'>
                <div class='tt-big-text'>
                    {primary_action}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander(f"More ways to handle this ({intervention['name']})"):
            for item in intervention["instructions"]:
                st.markdown(f"- {item}")

        st.divider()

        if st.button("✅ I’m calmer", use_container_width=True):
            st.session_state.trigger_outcome = "Stayed calm"
            st.rerun()

        if st.button("➡️ Not yet — try another", use_container_width=True):
            st.session_state.trigger_step += 1
            st.rerun()

        if st.button("🔴 It escalated", use_container_width=True):
            st.session_state.trigger_outcome = "Blew up"
            st.rerun()

        st.divider()

        if st.button("Cancel Emergency Mode", use_container_width=True):
            reset_trigger_flow()
            st.rerun()

    if st.session_state.get("trigger_outcome"):
        st.markdown("## Quick Emergency Log")
        st.caption("Tiny log only. No essay needed.")

        outcome = st.session_state.trigger_outcome
        strategy_used = st.session_state.get("trigger_intervention")
        mantra_used = st.session_state.get("trigger_mantra")

        if outcome == "Blew up":
            st.markdown(
                """
                <div class='tt-danger'>
                    <div class='tt-big-text'>
                        Log it, then repair if needed. Data, not shame.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.form("emergency_log_form"):
            trigger = st.selectbox("What triggered it?", TRIGGER_OPTIONS)

            intensity_before = st.slider("Intensity before", 1, 10, 6)

            default_after = 4 if outcome == "Stayed calm" else 8
            intensity_after = st.slider("Intensity now", 1, 10, default_after)

            repaired = st.selectbox("Repair/apology needed?", REPAIR_OPTIONS)

            helped = st.radio(
                "Did Emergency Mode help in the moment?",
                ["Yes", "Kind of", "No"],
                horizontal=True,
            )

            notes = st.text_area(
                "Optional note",
                placeholder="What helped? What made it harder?",
            )

            submitted = st.form_submit_button("Save Emergency Log", use_container_width=True)

        if submitted:
            note_parts = []

            if mantra_used:
                note_parts.append(f"Mantra: {mantra_used}")

            if helped:
                note_parts.append(f"Emergency feedback: {helped}")

            if notes:
                note_parts.append(notes)

            full_notes = "\n\n".join(note_parts)

            add_log(
                trigger,
                intensity_before,
                outcome,
                full_notes,
                "Emergency mode",
                strategy_used,
                intensity_after,
                repaired,
            )

            if outcome == "Blew up" and repaired in ["Yes", "Planned", "No"]:
                reset_trigger_flow()
                st.session_state.current_page = "Repair"
                st.rerun()

            reset_trigger_flow()
            st.success("Logged.")
            st.rerun()

        st.divider()

        st.markdown("### Need it faster?")

        if st.button("⚡ Quick save and move on", use_container_width=True):
            note_parts = []

            if mantra_used:
                note_parts.append(f"Mantra: {mantra_used}")

            note_parts.append("Emergency feedback: Not answered")
            note_parts.append("Quick-saved from Emergency Mode.")

            add_log(
                "Other",
                6,
                outcome,
                "\n\n".join(note_parts),
                "Emergency mode",
                strategy_used,
                4 if outcome == "Stayed calm" else 8,
                "Planned" if outcome == "Blew up" else "Not needed",
            )

            if outcome == "Blew up":
                reset_trigger_flow()
                st.session_state.current_page = "Repair"
                st.rerun()

            reset_trigger_flow()
            st.rerun()

        if st.button("Skip logging and close Emergency Mode", use_container_width=True):
            reset_trigger_flow()
            st.rerun()