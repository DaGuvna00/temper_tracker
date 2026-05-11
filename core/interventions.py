import pandas as pd

from core.constants import DEFAULT_INTERVENTIONS, MANTRAS


TRIGGER_STRATEGY_MAP = {
    "Noise / chaos": ["distance", "attention", "body"],
    "Disrespect": ["repair", "voice", "distance"],
    "Overwhelmed": ["breathing", "body", "distance"],
    "Tired": ["distance", "breathing", "body"],
    "Interrupted": ["voice", "breathing"],
    "Repetition": ["breathing", "attention"],
    "Other": ["distance", "breathing"],
}


def get_strategy_options():
    return ["None"] + [x["name"] for x in DEFAULT_INTERVENTIONS] + ["Other"]


def get_adaptive_interventions(df):
    if df.empty or "strategy" not in df.columns:
        return DEFAULT_INTERVENTIONS
    strategy_logs = df[df["strategy"].notna()].copy()
    if strategy_logs.empty:
        return DEFAULT_INTERVENTIONS
    scores = (
        strategy_logs.assign(success=strategy_logs["outcome"].eq("Stayed calm"))
        .groupby("strategy")
        .agg(uses=("id", "count"), success_rate=("success", "mean"))
        .reset_index()
    )
    score_map = {row["strategy"]: (row["success_rate"], row["uses"]) for _, row in scores.iterrows()}
    return sorted(DEFAULT_INTERVENTIONS, key=lambda x: score_map.get(x["name"], (-1, 0)), reverse=True)


def strategy_by_trigger(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    temp = df[df["strategy"].notna()].copy()
    if temp.empty:
        return pd.DataFrame()
    temp["drop"] = temp["intensity"] - temp["intensity_after"].fillna(temp["intensity"])
    result = (
        temp.assign(success=temp["outcome"].eq("Stayed calm"))
        .groupby(["trigger", "strategy"])
        .agg(uses=("id", "count"), success_rate=("success", "mean"), avg_drop=("drop", "mean"))
        .reset_index()
        .sort_values(["trigger", "success_rate", "avg_drop"], ascending=[True, False, False])
    )
    result["success_rate"] = (result["success_rate"] * 100).round(0).astype(int)
    result["avg_drop"] = result["avg_drop"].round(1)
    return result


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

    temp = real_logs[real_logs["strategy"].notna()].copy()

    if temp.empty:
        return None

    temp["success"] = temp["outcome"].eq("Stayed calm")

    if "intensity_after" in temp.columns:
        temp["drop"] = temp["intensity"] - temp["intensity_after"].fillna(temp["intensity"])
    else:
        temp["drop"] = 0

    stats = (
        temp.groupby("strategy")
        .agg(uses=("id", "count"), success_rate=("success", "mean"), avg_drop=("drop", "mean"))
        .reset_index()
    )

    stats = stats[stats["uses"] >= 3]

    if stats.empty:
        return None

    stats["score"] = stats["success_rate"] * 100 + stats["avg_drop"] * 5 + stats["uses"]
    best = stats.sort_values("score", ascending=False).iloc[0]

    return {
        "strategy": best["strategy"],
        "uses": int(best["uses"]),
        "success_rate": int(round(best["success_rate"] * 100)),
        "avg_drop": round(best["avg_drop"], 1),
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
        trigger_matched = [item for item in interventions if item.get("type") in preferred_types]
    else:
        trigger_matched = interventions

    if not trigger_matched:
        trigger_matched = interventions

    if logs is not None and not logs.empty and trigger:
        history = logs[
            (logs["trigger"] == trigger)
            & (logs["strategy"].notna())
            & (logs["strategy"] != "")
        ].copy()

        if not history.empty:
            history["success"] = history["outcome"].eq("Stayed calm")

            if "intensity_after" in history.columns:
                history["drop"] = history["intensity"] - history["intensity_after"].fillna(history["intensity"])
            else:
                history["drop"] = 0

            stats = (
                history.groupby("strategy")
                .agg(uses=("id", "count"), success_rate=("success", "mean"), avg_drop=("drop", "mean"))
                .reset_index()
            )
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

    return trigger_matched[step % len(trigger_matched)]


def get_emergency_mantra(step):
    return MANTRAS[step % len(MANTRAS)]
