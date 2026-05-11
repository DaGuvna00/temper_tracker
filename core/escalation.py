import pandas as pd


EARLY_WARNING_SIGNS = [
    "Jaw clenched",
    "Shoulders tight",
    "Voice got sharper",
    "Talking faster",
    "Repeating myself",
    "Wanted to argue/win",
    "Couldn't let it go",
    "Felt rushed",
    "Heat in chest/face",
    "Needed space",
    "Felt overstimulated",
    "Wanted control",
]

INTERVENTION_TIMING_OPTIONS = [
    "Before 5/10",
    "At 5/10",
    "At 7/10",
    "After escalation",
]

RECOVERY_TIME_OPTIONS = [
    "Under 5 minutes",
    "5-15 minutes",
    "15-30 minutes",
    "30-60 minutes",
    "More than 1 hour",
]

WHAT_MADE_IT_WORSE_OPTIONS = [
    "Kept talking",
    "Stayed in the room",
    "Raised my voice",
    "Tried to win the argument",
    "Ignored body signals",
    "Too much noise/stimulation",
    "Other",
]


def extract_warning_signs(real_logs):
    if real_logs.empty or "notes" not in real_logs.columns:
        return {}

    counts = {}

    for note in real_logs["notes"].dropna():
        marker = "Early warning signs:"

        if marker not in note:
            continue

        signs_text = note.split(marker, 1)[1].split("\n", 1)[0]
        signs = [s.strip() for s in signs_text.split(",") if s.strip()]

        for sign in signs:
            if sign.lower() == "not answered":
                continue

            counts[sign] = counts.get(sign, 0) + 1

    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


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


def get_intervention_timing_options():
    return INTERVENTION_TIMING_OPTIONS


def get_recovery_time_options():
    return RECOVERY_TIME_OPTIONS


def get_what_made_it_worse_options():
    return WHAT_MADE_IT_WORSE_OPTIONS
