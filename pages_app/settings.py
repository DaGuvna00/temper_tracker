import streamlit as st

from core.auth import USE_SUPABASE
from core.constants import DB_PATH
from core.database import delete_all_logs, delete_old_triggered_button_logs
from ui.components import page_title


def render_settings():
    page_title("Settings", "Clean test data and manage your local app.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Remove old 'Triggered button' test logs", use_container_width=True):
            delete_old_triggered_button_logs()
            st.success("Old test logs removed.")
            st.rerun()
    with c2:
        confirm = st.checkbox("I understand this deletes all logs and check-ins")
        if st.button("Delete ALL data", use_container_width=True, disabled=not confirm):
            delete_all_logs()
            st.success("All data deleted.")
            st.rerun()
    st.divider()
    st.subheader("Database")
    if USE_SUPABASE:
        st.code("Supabase connected. Data is stored online per signed-in user.")
    else:
        st.code(str(DB_PATH))
