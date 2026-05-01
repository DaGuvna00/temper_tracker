import sqlite3
from datetime import datetime

import pandas as pd

from core.auth import USE_SUPABASE, current_user_id, get_supabase_client
from core.constants import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Initialize local SQLite only. Supabase tables are created with SQL in Supabase."""
    if USE_SUPABASE:
        return

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
    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "trigger": trigger,
        "intensity": int(intensity),
        "intensity_after": None if intensity_after is None else int(intensity_after),
        "outcome": outcome,
        "strategy": strategy,
        "repaired": repaired,
        "notes": notes,
    }

    if USE_SUPABASE:
        payload["user_id"] = current_user_id()
        get_supabase_client().table("logs").insert(payload).execute()
        return

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO logs (timestamp, source, trigger, intensity, intensity_after, outcome, strategy, repaired, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (payload["timestamp"], source, trigger, payload["intensity"], payload["intensity_after"], outcome, strategy, repaired, notes),
        )
        conn.commit()


def update_log(log_id, trigger, intensity, intensity_after, outcome, strategy, repaired, notes):
    payload = {
        "trigger": trigger,
        "intensity": int(intensity),
        "intensity_after": None if intensity_after is None else int(intensity_after),
        "outcome": outcome,
        "strategy": strategy,
        "repaired": repaired,
        "notes": notes,
    }

    if USE_SUPABASE:
        get_supabase_client().table("logs").update(payload).eq("id", int(log_id)).eq("user_id", current_user_id()).execute()
        return

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE logs
            SET trigger=?, intensity=?, intensity_after=?, outcome=?, strategy=?, repaired=?, notes=?
            WHERE id=?
            """,
            (trigger, int(intensity), payload["intensity_after"], outcome, strategy, repaired, notes, int(log_id)),
        )
        conn.commit()


def delete_log(log_id):
    if USE_SUPABASE:
        get_supabase_client().table("logs").delete().eq("id", int(log_id)).eq("user_id", current_user_id()).execute()
        return

    with get_connection() as conn:
        conn.execute("DELETE FROM logs WHERE id=?", (int(log_id),))
        conn.commit()


def save_daily_checkin(checkin_date, sleep_quality, stress_level, energy_level, hunger_level, caffeine_level, overwhelm_level, notes):
    payload = {
        "checkin_date": str(checkin_date),
        "sleep_quality": int(sleep_quality),
        "stress_level": int(stress_level),
        "energy_level": int(energy_level),
        "hunger_level": int(hunger_level),
        "caffeine_level": int(caffeine_level),
        "overwhelm_level": int(overwhelm_level),
        "notes": notes,
    }

    if USE_SUPABASE:
        payload["user_id"] = current_user_id()
        get_supabase_client().table("daily_checkins").upsert(payload, on_conflict="user_id,checkin_date").execute()
        return

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
            (str(checkin_date), int(sleep_quality), int(stress_level), int(energy_level), int(hunger_level), int(caffeine_level), int(overwhelm_level), notes),
        )
        conn.commit()


def load_logs():
    if USE_SUPABASE:
        response = get_supabase_client().table("logs").select("*").eq("user_id", current_user_id()).order("timestamp", desc=True).execute()
        df = pd.DataFrame(response.data or [])
    else:
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
    if USE_SUPABASE:
        response = get_supabase_client().table("daily_checkins").select("*").eq("user_id", current_user_id()).order("checkin_date", desc=True).execute()
        df = pd.DataFrame(response.data or [])
    else:
        with get_connection() as conn:
            df = pd.read_sql_query("SELECT * FROM daily_checkins ORDER BY checkin_date DESC", conn)

    if df.empty:
        return df

    df["checkin_date"] = pd.to_datetime(df["checkin_date"]).dt.date
    return df


def delete_old_triggered_button_logs():
    if USE_SUPABASE:
        get_supabase_client().table("logs").delete().eq("trigger", "Triggered button").eq("user_id", current_user_id()).execute()
        return

    with get_connection() as conn:
        conn.execute("DELETE FROM logs WHERE trigger = 'Triggered button'")
        conn.commit()


def delete_all_logs():
    if USE_SUPABASE:
        get_supabase_client().table("logs").delete().eq("user_id", current_user_id()).execute()
        get_supabase_client().table("daily_checkins").delete().eq("user_id", current_user_id()).execute()
        return

    with get_connection() as conn:
        conn.execute("DELETE FROM logs")
        conn.execute("DELETE FROM daily_checkins")
        conn.commit()
