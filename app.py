import streamlit as st


st.set_page_config(page_title="Temper Tracker", page_icon="🧠", layout="wide")

from core.analytics import clean_logs, get_adaptive_interventions
from core.auth import USE_SUPABASE, current_user_id, logout, require_login
from core.constants import PAGES
from core.database import init_db, load_checkins, load_logs
from core.state import init_session_state, reset_emergency_session
from pages_app.checkin import render_checkin
from pages_app.emergency import render_emergency
from pages_app.history import render_history
from pages_app.home import render_home
from pages_app.insights import render_insights
from pages_app.log import render_log
from pages_app.settings import render_settings
from pages_app.weekly_review import render_weekly_review
from ui.styles import apply_styles
from pages_app.repair import render_repair


apply_styles()
init_session_state()
init_db()
require_login()

logs = load_logs()
real_logs = clean_logs(logs)
checkins = load_checkins()
adaptive_interventions = get_adaptive_interventions(real_logs)

st.sidebar.title("🧠 Temper Tracker")
st.sidebar.caption("Track it. Catch it. Control it.")

if USE_SUPABASE and current_user_id():
    st.sidebar.caption(f"Signed in as {st.session_state.sb_user.get('email')}")
    if st.sidebar.button("Log out", use_container_width=True):
        logout()
        st.rerun()

# Mobile-friendly escape hatch: put Emergency above the sidebar navigation.
# On phones, the user should not have to hunt through the menu when heated.
if st.sidebar.button("🚨 Emergency Reset", use_container_width=True):
    reset_emergency_session(start=True)
    st.session_state.current_page = "Emergency"
    st.rerun()

if "current_page" not in st.session_state or st.session_state.current_page not in PAGES:
    st.session_state.current_page = "Home"

page = st.sidebar.radio(
    "Go to",
    PAGES,
    index=PAGES.index(st.session_state.current_page),
)
st.session_state.current_page = page

if page == "Home":
    render_home(real_logs, checkins)
elif page == "Emergency":
    render_emergency(adaptive_interventions)
elif page == "Daily Check-In":
    render_checkin()
elif page == "Log":
    render_log()
elif page == "Insights":
    render_insights(real_logs)
elif page == "Weekly Review":
    render_weekly_review(real_logs)
elif page == "History":
    render_history(logs, real_logs)
elif page == "Settings":
    render_settings()
elif page == "Repair":
    render_repair(real_logs)
