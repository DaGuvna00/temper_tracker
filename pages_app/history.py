import pandas as pd
import streamlit as st

from core.constants import DEFAULT_INTERVENTIONS, OUTCOME_OPTIONS, REPAIR_OPTIONS, TRIGGER_OPTIONS
from core.database import delete_log, update_log
from ui.components import outcome_color, page_title


def render_history(logs, real_logs):
    page_title("History", "Review, edit, or delete logs.")
    if logs.empty:
        st.info("No logs yet.")
    else:
        show_test_logs = st.checkbox("Show old/test 'Triggered button' logs", value=False)
        history_df = logs.copy() if show_test_logs else real_logs.copy()
        if history_df.empty:
            st.info("No logs to show.")
        else:
            display_df = history_df.copy()
            display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %I:%M %p")
            display_df["result"] = display_df["outcome"].apply(lambda x: f"{outcome_color(x)} {x}")
            st.dataframe(display_df[["id", "timestamp", "source", "trigger", "intensity", "intensity_after", "result", "strategy", "repaired", "notes"]], use_container_width=True, hide_index=True)
            st.divider()
            st.subheader("Edit or Delete a Log")
            selected_id = st.selectbox("Choose log ID", history_df["id"].tolist())
            row = history_df[history_df["id"] == selected_id].iloc[0]
            with st.form("edit_log_form"):
                trigger = st.selectbox("Trigger", TRIGGER_OPTIONS, index=TRIGGER_OPTIONS.index(row["trigger"]) if row["trigger"] in TRIGGER_OPTIONS else 0)
                c1, c2 = st.columns(2)
                intensity = c1.slider("Intensity before", 1, 10, int(row["intensity"]))
                after_val = int(row["intensity_after"]) if pd.notna(row["intensity_after"]) else int(row["intensity"])
                intensity_after = c2.slider("Intensity after", 1, 10, after_val)
                outcome = st.selectbox("Outcome", OUTCOME_OPTIONS, index=OUTCOME_OPTIONS.index(row["outcome"]) if row["outcome"] in OUTCOME_OPTIONS else 0)
                strategy_options = ["None"] + [x["name"] for x in DEFAULT_INTERVENTIONS] + ["Other"]
                strategy_value = row["strategy"] if pd.notna(row["strategy"]) else "None"
                strategy = st.selectbox("Strategy", strategy_options, index=strategy_options.index(strategy_value) if strategy_value in strategy_options else 0)
                repaired = st.selectbox("Repair/apology?", REPAIR_OPTIONS, index=REPAIR_OPTIONS.index(row["repaired"]) if row["repaired"] in REPAIR_OPTIONS else 0)
                notes = st.text_area("Notes", value="" if pd.isna(row["notes"]) else row["notes"])
                save = st.form_submit_button("Save Changes", use_container_width=True)
            if save:
                update_log(selected_id, trigger, intensity, intensity_after, outcome, None if strategy == "None" else strategy, repaired, notes)
                st.success("Log updated.")
                st.rerun()
            confirm_delete = st.checkbox(f"Confirm delete log {selected_id}")
            if st.button("Delete Selected Log", disabled=not confirm_delete, use_container_width=True):
                delete_log(selected_id)
                st.success("Log deleted.")
                st.rerun()
            st.download_button("Download CSV", data=display_df.to_csv(index=False), file_name="temper_tracker_logs.csv", mime="text/csv")
