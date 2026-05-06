from datetime import datetime

import pandas as pd

from core.constants import DEFAULT_INTERVENTIONS, MANTRAS


def clean_logs(df):
    if df.empty:
        return df
    return df[df["trigger"] != "Triggered button"].copy()


def get_adaptive_interventions(df):
    if df.empty or "strategy" not in df.columns:
        return DEFAULT_INTERVENTIONS
    strategy_logs = df[df["strategy"].notna()].copy()
    if strategy_logs.empty:
        return DEFAULT_INTERVENTIONS
    scores = strategy_logs.assign(success=strategy_logs["outcome"].eq("Stayed calm")).groupby("strategy").agg(uses=("id", "count"), success_rate=("success", "mean")).reset_index()
    score_map = {row["strategy"]: (row["success_rate"], row["uses"]) for _, row in scores.iterrows()}
    return sorted(DEFAULT_INTERVENTIONS, key=lambda x: score_map.get(x["name"], (-1, 0)), reverse=True)


TRIGGER_STRATEGY_MAP = {
    "Noise / chaos": ["distance", "attention", "body"],
    "Disrespect": ["repair", "voice", "distance"],
    "Overwhelmed": ["breathing", "body", "distance"],
    "Tired": ["distance", "breathing", "body"],
    "Interrupted": ["voice", "breathing"],
    "Repetition": ["breathing", "attention"],
    "Other": ["distance", "breathing"],
}


def get_emergency_intervention(step, interventions, trigger=None, logs=None):
    """
    Emergency Mode selector.

    Priority:
    1. Match strategies to the current trigger.
    2. If enough personal history exists, rank strategies by success.
    3. Fall back to trigger-aware rotation.
    """

    if not interventions:
        return {
            "type": "breathing",
            "name": "Pause",
            "instructions": ["Take one slow breath."],
        }

    preferred_types = TRIGGER_STRATEGY_MAP.get(trigger, []) if trigger else []

    if preferred_types:
        trigger_matched = [
            item for item in interventions
            if item.get("type") in preferred_types
        ]
    else:
        trigger_matched = interventions

    if not trigger_matched:
        trigger_matched = interventions

    # -----------------------------
    # Personal learning layer
    # -----------------------------
    if logs is not None and not logs.empty and trigger:
        history = logs[
            (logs["trigger"] == trigger)
            & (logs["strategy"].notna())
            & (logs["strategy"] != "")
        ].copy()

        if not history.empty:
            history["success"] = history["outcome"].eq("Stayed calm")

            if "intensity_after" in history.columns:
                history["drop"] = (
                    history["intensity"]
                    - history["intensity_after"].fillna(history["intensity"])
                )
            else:
                history["drop"] = 0

            stats = (
                history.groupby("strategy")
                .agg(
                    uses=("id", "count"),
                    success_rate=("success", "mean"),
                    avg_drop=("drop", "mean"),
                )
                .reset_index()
            )

            # Don't trust one lucky success.
            stats = stats[stats["uses"] >= 3]

            if not stats.empty:
                stat_map = {
                    row["strategy"]: {
                        "uses": row["uses"],
                        "success_rate": row["success_rate"],
                        "avg_drop": row["avg_drop"],
                    }
                    for _, row in stats.iterrows()
                }

                ranked = []

                for item in trigger_matched:
                    name = item["name"]

                    if name in stat_map:
                        score = (
                            stat_map[name]["success_rate"] * 100
                            + stat_map[name]["avg_drop"] * 5
                            + min(stat_map[name]["uses"], 10)
                        )
                    else:
                        score = -1

                    ranked.append((score, item))

                ranked = sorted(ranked, key=lambda x: x[0], reverse=True)

                learned = [item for score, item in ranked if score >= 0]
                unlearned = [item for score, item in ranked if score < 0]

                ordered = learned + unlearned

                return ordered[step % len(ordered)]

    # -----------------------------
    # Trigger-aware fallback
    # -----------------------------
    return trigger_matched[step % len(trigger_matched)]
  

def get_emergency_mantra(step):
    return MANTRAS[step % len(MANTRAS)]


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

def detect_escalation_state(today_logs: pd.DataFrame, today_checkin: pd.DataFrame):
    """
    Detect whether today is stable, rising, or high-risk.

    This is intentionally simple and transparent.
    It should coach the user, not scare them.
    """

    if today_logs.empty:
        return {
            "state": "Stable",
            "kind": "success",
            "message": "No escalation pattern detected yet today.",
            "reasons": [],
        }

    reasons = []
    score = 0

    blowups_today = int((today_logs["outcome"] == "Blew up").sum())
    high_intensity_today = int((today_logs["intensity"] >= 7).sum())
    emergency_sessions = int((today_logs["source"] == "Emergency mode").sum())
    avg_intensity = float(today_logs["intensity"].mean())

    if blowups_today >= 2:
        score += 4
        reasons.append(f"{blowups_today} blow-ups today")
    elif blowups_today == 1:
        score += 2
        reasons.append("1 blow-up today")

    if high_intensity_today >= 3:
        score += 3
        reasons.append(f"{high_intensity_today} high-intensity moments today")
    elif high_intensity_today >= 1:
        score += 1
        reasons.append(f"{high_intensity_today} high-intensity moment(s) today")

    if emergency_sessions >= 3:
        score += 3
        reasons.append(f"{emergency_sessions} emergency sessions today")
    elif emergency_sessions >= 1:
        score += 1
        reasons.append(f"{emergency_sessions} emergency session(s) today")

    if avg_intensity >= 7:
        score += 2
        reasons.append(f"average intensity is {avg_intensity:.1f}/10")

    if not today_checkin.empty:
        row = today_checkin.iloc[0]

        stress = int(row.get("stress_level") or 5)
        overwhelm = int(row.get("overwhelm_level") or 5)
        sleep = int(row.get("sleep_quality") or 5)

        if stress >= 8:
            score += 1
            reasons.append("stress check-in is very high")

        if overwhelm >= 8:
            score += 1
            reasons.append("overwhelm check-in is very high")

        if sleep <= 3:
            score += 1
            reasons.append("sleep check-in is very low")

    if score >= 6:
        return {
            "state": "High Risk",
            "kind": "danger",
            "message": "Today is trending high-risk. Lower demands, reduce stimulation, and step away earlier than usual.",
            "reasons": reasons,
        }

    if score >= 3:
        return {
            "state": "Rising",
            "kind": "normal",
            "message": "Escalation may be building today. Catch the next moment early.",
            "reasons": reasons,
        }

    return {
        "state": "Stable",
        "kind": "success",
        "message": "No strong escalation pattern detected today.",
        "reasons": reasons,
    }

def get_best_strategy_suggestion(real_logs):
    """
    Return the user's strongest-performing strategy overall.

    Conservative:
    - Requires at least 3 uses
    - Rewards success rate first
    - Uses intensity drop as secondary factor
    """

    if real_logs.empty or "strategy" not in real_logs.columns:
        return None

    temp = real_logs[
        real_logs["strategy"].notna()
    ].copy()

    if temp.empty:
        return None

    temp["success"] = temp["outcome"].eq("Stayed calm")

    if "intensity_after" in temp.columns:
        temp["drop"] = (
            temp["intensity"]
            - temp["intensity_after"].fillna(temp["intensity"])
        )
    else:
        temp["drop"] = 0

    stats = (
        temp.groupby("strategy")
        .agg(
            uses=("id", "count"),
            success_rate=("success", "mean"),
            avg_drop=("drop", "mean"),
        )
        .reset_index()
    )

    stats = stats[stats["uses"] >= 3]

    if stats.empty:
        return None

    stats["score"] = (
        stats["success_rate"] * 100
        + stats["avg_drop"] * 5
        + stats["uses"]
    )

    best = stats.sort_values("score", ascending=False).iloc[0]

    return {
        "strategy": best["strategy"],
        "uses": int(best["uses"]),
        "success_rate": int(round(best["success_rate"] * 100)),
        "avg_drop": round(best["avg_drop"], 1),
    }