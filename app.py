import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

# -----------------------------
# App Config
# -----------------------------
st.set_page_config(page_title="Temper Tracker", page_icon="🧠", layout="wide")

APP_DIR = Path(__file__).parent if "__file__" in globals() else Path.cwd()
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "temper_tracker.db"

TRIGGER_OPTIONS = ["Repetition", "Noise / chaos", "Disrespect", "Tired", "Overwhelmed", "Interrupted", "Other"]
OUTCOME_OPTIONS = ["Stayed calm", "Struggled", "Blew up"]
REPAIR_OPTIONS = ["Not needed", "Yes", "No", "Planned"]

MANTRAS = [
    "Nothing needs to be solved right now.",
    "Pause first. Fix later.",
    "I control my next move.",
    "Distance beats discipline.",
    "This will pass. Words don’t.",
    "Lower the damage.",
    "I can be angry and still be careful.",
    "Stop talking. Start breathing.",
    "My job is to calm the room, not win the moment.",
    "I can repair later. Right now, I prevent damage.",
]

DEFAULT_INTERVENTIONS = [
    {"type": "distance", "name": "Step Away Reset", "instructions": ["Stop talking if you can.", "Physically move away from the trigger if everyone is safe.", "Put both feet on the floor.", "Take 3 slow breaths before doing anything else."]},
    {"type": "breathing", "name": "Box Breathing", "instructions": ["Breathe in for 4 seconds.", "Hold for 4 seconds.", "Breathe out for 4 seconds.", "Hold for 4 seconds.", "Repeat 3 times."]},
    {"type": "breathing", "name": "Physiological Sigh", "instructions": ["Take a deep inhale through your nose.", "Before exhaling, take one small extra inhale.", "Slowly exhale all the way out.", "Repeat 3 to 5 times."]},
    {"type": "body", "name": "Unclench Reset", "instructions": ["Unclench your jaw.", "Drop your shoulders.", "Open your hands.", "Relax your tongue from the roof of your mouth.", "Take one slow breath."]},
    {"type": "cold", "name": "Cold Water Reset", "instructions": ["Go to the sink if possible.", "Splash cold water on your face or run cold water over your wrists.", "Focus only on the cold sensation for 20 to 30 seconds.", "Do not restart the conversation yet."]},
    {"type": "attention", "name": "5-4-3 Grounding", "instructions": ["Name 5 things you can see.", "Name 4 things you can feel.", "Name 3 things you can hear.", "Name 2 things you can smell.", "Name 1 thing you can do next that lowers the damage."]},
    {"type": "attention", "name": "Counting Interrupt", "instructions": ["Count backwards from 50 by 3s.", "If you mess up, start again.", "Keep your mouth closed while counting.", "Let the wave pass before responding."]},
    {"type": "repair", "name": "Repair Preview", "instructions": ["Imagine having to apologize for what you say next.", "Ask: will this make repair harder?", "Choose the smallest next action that avoids damage."]},
    {"type": "voice", "name": "Lower Your Voice Drill", "instructions": ["Before saying anything, lower your voice on purpose.", "Speak slower than normal.", "Use one sentence only: ‘I need a minute.’", "Do not lecture while heated."]},
]

# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1150px;
    }

    /* Metric cards - dark theme friendly */
    div[data-testid="stMetric"] {
        background: #161b22;
        border: 1px solid #30363d;
        padding: 14px 16px;
        border-radius: 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.25);
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] div {
        color: #f0f6fc !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 800;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #7ee787 !important;
    }

    /* Custom cards */
    .tt-card {
        background: #161b22;
        color: #f0f6fc;
        border: 1px solid #30363d;
        border-radius: 18px;
        padding: 18px 20px;
        margin: 10px 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.25);
    }
    .tt-danger {
        background: #2d1719;
        color: #f0f6fc;
        border: 1px solid #7d2a32;
        border-radius: 18px;
        padding: 18px 20px;
        margin: 10px 0;
    }
    .tt-success {
        background: #14281d;
        color: #f0f6fc;
        border: 1px solid #2f7d4f;
        border-radius: 18px;
        padding: 18px 20px;
        margin: 10px 0;
    }
    .tt-card strong,
    .tt-danger strong,
    .tt-success strong {
        color: #ffffff !important;
        font-size: 1.02rem;
    }
    .tt-muted {
        color: #c9d1d9 !important;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    .tt-emergency-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        color: #ffffff;
    }
    .tt-big-text {
        font-size: 1.25rem;
        line-height: 1.55;
        color: #f0f6fc;
    }
    .tt-mantra {
        background: #101820;
        color: #ffffff;
        border: 1px solid #3b82f6;
        border-radius: 18px;
        padding: 18px 20px;
        margin: 16px 0;
        font-size: 1.2rem;
        line-height: 1.45;
    }

    /* Info boxes can be too bright in dark mode, soften them slightly */
    div[data-testid="stAlert"] {
        border-radius: 14px;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .tt-emergency-title {
            font-size: 1.65rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Database
# -----------------------------
def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'Manual log',
                trigger TEXT NOT NULL,
                intensity INTEGER NOT NULL,
                intensity_after INTEGER,
                outcome TEXT NOT NULL,
                strategy TEXT,
                repaired TEXT DEFAULT 'Not needed',
                notes TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checkin_date TEXT NOT NULL UNIQUE,
                sleep_quality INTEGER,
                stress_level INTEGER,
                energy_level INTEGER,
                hunger_level INTEGER,
                caffeine_level INTEGER,
                overwhelm_level INTEGER,
                notes TEXT
            )
            """
        )

        existing_cols = [row[1] for row in conn.execute("PRAGMA table_info(logs)").fetchall()]
        migrations = {
            "source": "ALTER TABLE logs ADD COLUMN source TEXT NOT NULL DEFAULT 'Manual log'",
            "strategy": "ALTER TABLE logs ADD COLUMN strategy TEXT",
            "intensity_after": "ALTER TABLE logs ADD COLUMN intensity_after INTEGER",
            "repaired": "ALTER TABLE logs ADD COLUMN repaired TEXT DEFAULT 'Not needed'",
        }
        for col, sql in migrations.items():
            if col not in existing_cols:
                conn.execute(sql)
        conn.commit()


def add_log(trigger, intensity, outcome, notes="", source="Manual log", strategy=None, intensity_after=None, repaired="Not needed"):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO logs (timestamp, source, trigger, intensity, intensity_after, outcome, strategy, repaired, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (datetime.now().isoformat(timespec="seconds"), source, trigger, intensity, intensity_after, outcome, strategy, repaired, notes),
        )
        conn.commit()


def update_log(log_id, trigger, intensity, intensity_after, outcome, strategy, repaired, notes):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE logs
            SET trigger=?, intensity=?, intensity_after=?, outcome=?, strategy=?, repaired=?, notes=?
            WHERE id=?
            """,
            (trigger, intensity, intensity_after, outcome, strategy, repaired, notes, log_id),
        )
        conn.commit()


def delete_log(log_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM logs WHERE id=?", (log_id,))
        conn.commit()


def save_daily_checkin(checkin_date, sleep_quality, stress_level, energy_level, hunger_level, caffeine_level, overwhelm_level, notes):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO daily_checkins (checkin_date, sleep_quality, stress_level, energy_level, hunger_level, caffeine_level, overwhelm_level, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(checkin_date) DO UPDATE SET
                sleep_quality=excluded.sleep_quality,
                stress_level=excluded.stress_level,
                energy_level=excluded.energy_level,
                hunger_level=excluded.hunger_level,
                caffeine_level=excluded.caffeine_level,
                overwhelm_level=excluded.overwhelm_level,
                notes=excluded.notes
            """,
            (str(checkin_date), sleep_quality, stress_level, energy_level, hunger_level, caffeine_level, overwhelm_level, notes),
        )
        conn.commit()


def load_logs():
    with get_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM logs ORDER BY timestamp DESC", conn)
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["week_start"] = df["timestamp"].dt.to_period("W-MON").apply(lambda r: r.start_time.date())
    return df


def load_checkins():
    with get_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM daily_checkins ORDER BY checkin_date DESC", conn)
    if df.empty:
        return df
    df["checkin_date"] = pd.to_datetime(df["checkin_date"]).dt.date
    return df


def delete_old_triggered_button_logs():
    with get_connection() as conn:
        conn.execute("DELETE FROM logs WHERE trigger = 'Triggered button'")
        conn.commit()


def delete_all_logs():
    with get_connection() as conn:
        conn.execute("DELETE FROM logs")
        conn.execute("DELETE FROM daily_checkins")
        conn.commit()


init_db()

# -----------------------------
# Helpers
# -----------------------------
def clean_logs(df):
    if df.empty:
        return df
    return df[df["trigger"] != "Triggered button"].copy()


def outcome_color(outcome):
    return {"Stayed calm": "🟢", "Struggled": "🟡", "Blew up": "🔴"}.get(outcome, "⚪")


def page_title(title, subtitle):
    st.title(title)
    st.caption(subtitle)


def card(title, body, kind="normal"):
    css = "tt-card"
    if kind == "danger":
        css = "tt-danger"
    elif kind == "success":
        css = "tt-success"
    st.markdown(f"<div class='{css}'><strong>{title}</strong><br><span class='tt-muted'>{body}</span></div>", unsafe_allow_html=True)


def get_adaptive_interventions(df):
    if df.empty or "strategy" not in df.columns:
        return DEFAULT_INTERVENTIONS
    strategy_logs = df[df["strategy"].notna()].copy()
    if strategy_logs.empty:
        return DEFAULT_INTERVENTIONS
    scores = strategy_logs.assign(success=strategy_logs["outcome"].eq("Stayed calm")).groupby("strategy").agg(uses=("id", "count"), success_rate=("success", "mean")).reset_index()
    score_map = {row["strategy"]: (row["success_rate"], row["uses"]) for _, row in scores.iterrows()}
    return sorted(DEFAULT_INTERVENTIONS, key=lambda x: score_map.get(x["name"], (-1, 0)), reverse=True)


def get_emergency_intervention(step, interventions):
    """Rotate through intervention types so Emergency Mode feels intentional, not random."""
    rotation = ["distance", "breathing", "body", "cold", "attention", "repair", "voice"]
    target_type = rotation[step % len(rotation)]
    matching = [item for item in interventions if item.get("type") == target_type]
    if matching:
        index = step // len(rotation)
        return matching[index % len(matching)]
    return interventions[step % len(interventions)]


def get_emergency_mantra(step):
    return MANTRAS[step % len(MANTRAS)]


def reset_emergency_session(start=False):
    st.session_state.trigger_mode = start
    st.session_state.trigger_step = 0
    st.session_state.trigger_outcome = None
    st.session_state.trigger_intervention = None
    st.session_state.trigger_mantra = None
    st.session_state.trigger_context_saved = False
    st.session_state.trigger_context = {}


def build_pattern_insights(df):
    if df.empty:
        return ["No pattern data yet. Add a few real logs first."]
    insights = []
    summary = df.assign(blowup=df["outcome"].eq("Blew up"), high=df["intensity"].ge(7)).groupby("trigger").agg(logs=("id", "count"), avg_intensity=("intensity", "mean"), blowup_rate=("blowup", "mean"), high_rate=("high", "mean")).sort_values(["blowup_rate", "avg_intensity"], ascending=False)
    if not summary.empty:
        top = summary.index[0]
        row = summary.iloc[0]
        insights.append(f"Highest-risk trigger: {top}. Blow-up rate: {row['blowup_rate'] * 100:.0f}%. Average intensity: {row['avg_intensity']:.1f}/10.")
    if "intensity_after" in df.columns and df["intensity_after"].notna().any():
        improved = df[df["intensity_after"].notna()].copy()
        improved["drop"] = improved["intensity"] - improved["intensity_after"]
        avg_drop = improved["drop"].mean()
        insights.append(f"Average intensity change after using a strategy: {avg_drop:.1f} points.")
    blowups = df[df["outcome"] == "Blew up"]
    if not blowups.empty:
        hour = blowups["hour"].mode().iloc[0]
        insights.append(f"Most common blow-up hour so far: around {datetime.strptime(str(hour), '%H').strftime('%I %p').lstrip('0')}.")
    if len(df) < 10:
        insights.append("Data warning: fewer than 10 real logs. These are clues, not final truth.")
    return insights


def calculate_risk_score(today_checkin: pd.DataFrame, recent_logs: pd.DataFrame) -> tuple[int, str, list[str]]:
    """Simple risk score for the day.

    This should be useful, not dramatic. It is intentionally conservative so a few
    test logs do not instantly scream 100/100 forever.
    """
    score = 10
    reasons = []

    if not today_checkin.empty:
        row = today_checkin.iloc[0]
        stress = int(row.get("stress_level") or 5)
        overwhelm = int(row.get("overwhelm_level") or 5)
        sleep = int(row.get("sleep_quality") or 5)
        hunger = int(row.get("hunger_level") or 3)
        energy = int(row.get("energy_level") or 5)

        score += max(0, stress - 5) * 4
        score += max(0, overwhelm - 5) * 4
        score += max(0, 6 - sleep) * 4
        score += max(0, hunger - 5) * 3
        score += max(0, 5 - energy) * 2

        if stress >= 7:
            reasons.append("stress is high")
        if overwhelm >= 7:
            reasons.append("overwhelm is high")
        if sleep <= 4:
            reasons.append("sleep quality is low")
        if hunger >= 7:
            reasons.append("hunger is high")
    else:
        score += 5
        reasons.append("daily check-in missing")

    if not recent_logs.empty:
        last_3 = recent_logs[recent_logs["timestamp"] >= pd.Timestamp.now() - pd.Timedelta(days=3)]
        recent_blowups = int((last_3["outcome"] == "Blew up").sum())
        recent_high = int((last_3["intensity"] >= 7).sum())

        score += min(recent_blowups * 5, 20)
        score += min(recent_high * 2, 10)

        if recent_blowups:
            reasons.append(f"{recent_blowups} blow-up(s) in the last 3 days")
        if recent_high >= 2:
            reasons.append("multiple high-intensity moments recently")

    score = max(0, min(100, int(score)))
    label = "High" if score >= 65 else "Medium" if score >= 35 else "Low"
    return score, label, reasons


def top_danger_patterns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    temp = df.copy()
    temp["intensity_band"] = pd.cut(temp["intensity"], bins=[0, 3, 6, 10], labels=["Low 1-3", "Medium 4-6", "High 7-10"])
    patterns = temp.assign(blowup=temp["outcome"].eq("Blew up")).groupby(["trigger", "intensity_band"], observed=True).agg(logs=("id", "count"), blowup_rate=("blowup", "mean"), avg_intensity=("intensity", "mean")).reset_index()
    patterns = patterns[patterns["logs"] >= 1].sort_values(["blowup_rate", "avg_intensity", "logs"], ascending=False)
    if patterns.empty:
        return patterns
    patterns["blowup_rate"] = (patterns["blowup_rate"] * 100).round(0).astype(int)
    patterns["avg_intensity"] = patterns["avg_intensity"].round(1)
    return patterns.head(5)


def strategy_by_trigger(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    temp = df[df["strategy"].notna()].copy()
    if temp.empty:
        return pd.DataFrame()
    temp["drop"] = temp["intensity"] - temp["intensity_after"].fillna(temp["intensity"])
    result = temp.assign(success=temp["outcome"].eq("Stayed calm")).groupby(["trigger", "strategy"]).agg(uses=("id", "count"), success_rate=("success", "mean"), avg_drop=("drop", "mean")).reset_index().sort_values(["trigger", "success_rate", "avg_drop"], ascending=[True, False, False])
    result["success_rate"] = (result["success_rate"] * 100).round(0).astype(int)
    result["avg_drop"] = result["avg_drop"].round(1)
    return result


def reset_trigger_flow():
    reset_emergency_session(start=False)


for key, default in {
    "trigger_mode": False,
    "trigger_step": 0,
    "trigger_context_saved": False,
    "trigger_context": {},
    "trigger_outcome": None,
    "trigger_intervention": None,
    "trigger_mantra": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

logs = load_logs()
real_logs = clean_logs(logs)
checkins = load_checkins()
adaptive_interventions = get_adaptive_interventions(real_logs)

st.sidebar.title("🧠 Temper Tracker")
st.sidebar.caption("Track it. Catch it. Control it.")
PAGES = ["Home", "Emergency", "Daily Check-In", "Log", "Insights", "Weekly Review", "History", "Settings"]
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"
page = st.sidebar.radio(
    "Go to",
    PAGES,
    index=PAGES.index(st.session_state.current_page),
    key="nav_page",
)
st.session_state.current_page = page

# -----------------------------
# Home
# -----------------------------
if page == "Home":
    page_title("Temper Tracker", "Your anger-control dashboard. Simple, honest, useful.")
    today = date.today()
    today_logs = real_logs[real_logs["date"] == today] if not real_logs.empty else pd.DataFrame()
    today_checkin = checkins[checkins["checkin_date"] == today] if not checkins.empty else pd.DataFrame()
    risk_score, risk_label, risk_reasons = calculate_risk_score(today_checkin, real_logs)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Triggers Today", 0 if today_logs.empty else len(today_logs))
    c2.metric("Blow-Ups Today", 0 if today_logs.empty else int((today_logs["outcome"] == "Blew up").sum()))
    c3.metric("Avg Intensity", "—" if today_logs.empty else round(today_logs["intensity"].mean(), 1))
    c4.metric("Risk", risk_label, delta=f"{risk_score}/100")

    if len(real_logs) < 20:
        card("Early data warning", f"Only {len(real_logs)} real log(s) so far. Treat risk and pattern results as early clues, not hard truth.")

    if risk_reasons:
        card("Today’s risk factors", ", ".join(risk_reasons) + ".", "danger" if risk_label == "High" else "normal")
    else:
        card("Today’s risk factors", "No major risk flags based on current data.", "success")

    st.markdown("### Fast Actions")
    a, b, c = st.columns(3)
    with a:
        if st.button("🚨 Start Emergency Mode", use_container_width=True):
            reset_emergency_session(start=True)
            st.session_state.current_page = "Emergency"
            st.rerun()
    with b:
        if st.button("📝 Quick Log", use_container_width=True):
            st.session_state.current_page = "Log"
            st.rerun()
    with c:
        if st.button("✅ Daily Check-In", use_container_width=True):
            st.session_state.current_page = "Daily Check-In"
            st.rerun()

    if st.session_state.trigger_mode:
        st.info("Emergency Mode is active. Go to the Emergency page or continue below.")
        page = "Emergency"

    st.divider()
    st.subheader("This Week Snapshot")
    if real_logs.empty:
        st.info("No real logs yet.")
    else:
        last_7 = real_logs[real_logs["timestamp"] >= pd.Timestamp.now() - pd.Timedelta(days=7)]
        if not last_7.empty:
            a, b, c = st.columns(3)
            a.metric("Most Common Trigger", last_7["trigger"].mode().iloc[0])
            b.metric("Blow-Ups This Week", int((last_7["outcome"] == "Blew up").sum()))
            c.metric("Avg Intensity", round(last_7["intensity"].mean(), 1))
            for insight in build_pattern_insights(last_7):
                card("Early clue", insight)

# -----------------------------
# Emergency
# -----------------------------
if page == "Emergency":
    st.markdown("<div class='tt-emergency-title'>🚨 Emergency Mode</div>", unsafe_allow_html=True)
    st.caption("For the heat of the moment. Do less. Slow the reaction first. Solve later.")

    if not st.session_state.trigger_mode and not st.session_state.get("trigger_outcome"):
        st.markdown(
            "<div class='tt-danger'><div class='tt-big-text'>"
            "<strong>First move:</strong> stop talking if you can. Create space. Lower the damage."
            "</div></div>",
            unsafe_allow_html=True,
        )

        if st.button("Start Emergency Reset", use_container_width=True):
            reset_emergency_session(start=True)
            st.rerun()

    if st.session_state.trigger_mode and not st.session_state.get("trigger_outcome"):
        step = st.session_state.trigger_step
        intervention = get_emergency_intervention(step, adaptive_interventions)
        mantra = get_emergency_mantra(step)

        st.session_state.trigger_intervention = intervention["name"]
        st.session_state.trigger_mantra = mantra

        st.caption(f"Strategy {step + 1}")
        st.markdown("### Right now, do this:")
        st.markdown(f"## {intervention['name']}")

        for item in intervention["instructions"]:
            st.markdown(f"- {item}")

        st.markdown(
            f"""
            <div class='tt-mantra'>
                🧠 <strong>Repeat:</strong> {mantra}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()
        c1, c2 = st.columns(2)

        with c1:
            if st.button("✅ I’m calmer", use_container_width=True):
                st.session_state.trigger_outcome = "Stayed calm"
                st.rerun()

        with c2:
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

        with st.form("emergency_log_form"):
            trigger = st.selectbox("What triggered it?", TRIGGER_OPTIONS)
            c1, c2 = st.columns(2)
            intensity_before = c1.slider("Intensity before", 1, 10, 6)

            default_after = 4 if st.session_state.trigger_outcome == "Stayed calm" else 8
            intensity_after = c2.slider("Intensity now", 1, 10, default_after)

            repaired = st.selectbox("Repair/apology needed?", REPAIR_OPTIONS)
            notes = st.text_area("Optional note", placeholder="What helped? What made it harder?")

            submitted = st.form_submit_button("Save Emergency Log", use_container_width=True)

        if submitted:
            strategy_used = st.session_state.get("trigger_intervention")
            mantra_used = st.session_state.get("trigger_mantra")
            full_notes = notes

            if mantra_used:
                full_notes = f"Mantra: {mantra_used}" + (f"\n\n{notes}" if notes else "")

            add_log(
                trigger,
                intensity_before,
                st.session_state.trigger_outcome,
                full_notes,
                "Emergency mode",
                strategy_used,
                intensity_after,
                repaired,
            )

            if st.session_state.trigger_outcome == "Stayed calm":
                st.success("Logged as a win.")
            else:
                st.error("Logged. Data, not shame.")

            reset_trigger_flow()
            st.rerun()

        if st.button("Skip logging and close Emergency Mode", use_container_width=True):
            reset_trigger_flow()
            st.rerun()

# -----------------------------
# Daily Check-In
# -----------------------------
elif page == "Daily Check-In":
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

# -----------------------------
# Log
# -----------------------------
elif page == "Log":
    page_title("Quick Log", "Log what happened in under 15 seconds.")
    with st.form("anger_log_form", clear_on_submit=True):
        trigger = st.selectbox("What triggered it?", TRIGGER_OPTIONS)
        c1, c2 = st.columns(2)
        intensity = c1.slider("Intensity before", 1, 10, 5)
        intensity_after = c2.slider("Intensity after", 1, 10, 5)
        outcome = st.radio("Outcome", OUTCOME_OPTIONS, horizontal=True)
        strategy = st.selectbox("What did you try?", ["None"] + [x["name"] for x in DEFAULT_INTERVENTIONS] + ["Other"])
        repaired = st.selectbox("Repair/apology?", REPAIR_OPTIONS)
        notes = st.text_area("Optional notes", placeholder="What happened? What did you notice?")
        submitted = st.form_submit_button("Save Log", use_container_width=True)
    if submitted:
        add_log(trigger, intensity, outcome, notes, "Manual log", None if strategy == "None" else strategy, intensity_after, repaired)
        st.success("Saved. Data beats guessing.")

# -----------------------------
# Insights
# -----------------------------
elif page == "Insights":
    page_title("Insights", "Patterns beat guesses.")
    if real_logs.empty:
        st.info("No real data yet.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Real Logs", len(real_logs))
        c2.metric("Avg Before", round(real_logs["intensity"].mean(), 1))
        c3.metric("Blow-Ups", int((real_logs["outcome"] == "Blew up").sum()))
        if real_logs["intensity_after"].notna().any():
            drops = real_logs.dropna(subset=["intensity_after"]).copy()
            c4.metric("Avg Drop", round((drops["intensity"] - drops["intensity_after"]).mean(), 1))
        else:
            c4.metric("Avg Drop", "—")

        st.subheader("Pattern Cards")
        for insight in build_pattern_insights(real_logs):
            card("Insight", insight)

        st.subheader("Top Danger Patterns")
        danger = top_danger_patterns(real_logs)
        if danger.empty:
            st.info("Not enough pattern data yet.")
        else:
            for _, row in danger.iterrows():
                card(
                    f"{row['trigger']} · {row['intensity_band']}",
                    f"{row['logs']} log(s), {row['blowup_rate']}% blow-up rate, average intensity {row['avg_intensity']}/10.",
                    "danger" if row["blowup_rate"] >= 50 else "normal",
                )

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Triggers by Count")
            st.bar_chart(real_logs["trigger"].value_counts().sort_values(ascending=True))
        with c2:
            st.subheader("Outcomes")
            st.bar_chart(real_logs["outcome"].value_counts().sort_values(ascending=True))

        with st.expander("Detailed Tables"):
            st.subheader("Trigger Risk Table")
            risk = real_logs.assign(blowup=real_logs["outcome"].eq("Blew up")).groupby("trigger").agg(logs=("id", "count"), avg_intensity=("intensity", "mean"), blowup_rate=("blowup", "mean")).sort_values(["blowup_rate", "avg_intensity"], ascending=False)
            risk["avg_intensity"] = risk["avg_intensity"].round(1)
            risk["blowup_rate"] = (risk["blowup_rate"] * 100).round(0).astype(int)
            st.dataframe(risk, use_container_width=True)

            st.subheader("Strategy Effectiveness by Trigger")
            sbt = strategy_by_trigger(real_logs)
            if sbt.empty:
                st.info("No strategy-by-trigger data yet.")
            else:
                st.dataframe(sbt, use_container_width=True, hide_index=True)

        st.subheader("Repair Tracking")
        st.bar_chart(real_logs["repaired"].fillna("Not tracked").value_counts().sort_values(ascending=True))

# -----------------------------
# Weekly Review
# -----------------------------
elif page == "Weekly Review":
    page_title("Weekly Review", "A quick review so the data turns into behaviour change.")
    if real_logs.empty:
        st.info("No logs yet. Weekly review will become useful after a few days of real use.")
    else:
        end_date = st.date_input("Week ending", value=date.today())
        start_date = end_date - timedelta(days=6)
        prev_start = start_date - timedelta(days=7)
        prev_end = start_date - timedelta(days=1)
        this_week = real_logs[(real_logs["date"] >= start_date) & (real_logs["date"] <= end_date)]
        prev_week = real_logs[(real_logs["date"] >= prev_start) & (real_logs["date"] <= prev_end)]
        st.caption(f"Current review window: {start_date} to {end_date}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Logs", len(this_week), delta=len(this_week) - len(prev_week))
        c2.metric("Blow-Ups", int((this_week["outcome"] == "Blew up").sum()), delta=int((this_week["outcome"] == "Blew up").sum()) - int((prev_week["outcome"] == "Blew up").sum()))
        c3.metric("Stayed Calm", int((this_week["outcome"] == "Stayed calm").sum()), delta=int((this_week["outcome"] == "Stayed calm").sum()) - int((prev_week["outcome"] == "Stayed calm").sum()))
        c4.metric("Avg Intensity", "—" if this_week.empty else round(this_week["intensity"].mean(), 1))
        if this_week.empty:
            st.info("No logs in this review window.")
        else:
            for insight in build_pattern_insights(this_week):
                card("This week says", insight)
            danger = top_danger_patterns(this_week)
            if not danger.empty:
                top_row = danger.iloc[0]
                card("Focus for next week", f"Main focus: {top_row['trigger']} during {top_row['intensity_band']} intensity. Intervene before it reaches 7/10.", "danger")
            else:
                card("Focus for next week", "Keep logging consistently so the pattern gets clearer.")
            sbt = strategy_by_trigger(this_week)
            if not sbt.empty:
                best = sbt.sort_values(["success_rate", "avg_drop"], ascending=False).iloc[0]
                card("Best strategy this week", f"{best['strategy']} for {best['trigger']} ({best['success_rate']}% success, avg drop {best['avg_drop']}).", "success")
            st.text_area("Reflection", placeholder="What did I learn? What do I want to try next week?", height=160)

# -----------------------------
# History
# -----------------------------
elif page == "History":
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

# -----------------------------
# Settings
# -----------------------------
elif page == "Settings":
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
    st.subheader("Database Location")
    st.code(str(DB_PATH))
