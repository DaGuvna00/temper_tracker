from datetime import date

import streamlit as st

from core.database import save_daily_checkin
from ui.components import page_title


def render_checkin():
    page_title("Daily Check-In", "Track the background factors that make anger easier or harder to control.")
    with st.form("daily_checkin"):
        checkin_date = st.date_input("Date", value=date.today())
        c1, c2, c3 = st.columns(3)
        sleep = c1.slider("Sleep quality", 1, 10, 5)
        stress = c2.slider("Stress level", 1, 10, 5)
        energy = c3.slider("Energy level", 1, 10, 5)
        c4, c5, c6 = st.columns(3)
        hunger = c4.slider("Hunger level", 1, 10, 3)
        caffeine = c5.slider("Caffeine level", 0, 10, 3)
        overwhelm = c6.slider("Overwhelm level", 1, 10, 5)
        notes = st.text_area("Daily notes", placeholder="Anything that might affect patience today?")
        submitted = st.form_submit_button("Save Daily Check-In", use_container_width=True)
    if submitted:
        save_daily_checkin(checkin_date, sleep, stress, energy, hunger, caffeine, overwhelm, notes)
        st.success("Daily check-in saved.")
