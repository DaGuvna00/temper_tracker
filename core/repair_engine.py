import pandas as pd


OWNERSHIP_OPTIONS = [
    "Raised my voice",
    "Kept arguing instead of stepping away",
    "Was too harsh",
    "Reacted instead of pausing",
    "Blamed instead of owning my part",
    "Scared or overwhelmed someone",
    "Something else",
]


REPAIR_TARGET_OPTIONS = ["Child", "Partner", "General"]
REPAIR_TIMING_OPTIONS = ["Now", "Later today", "Not sure"]
REPAIR_QUEUE_STATUSES = ["Not needed", "No", "Planned"]


REPAIR_SCRIPTS = {
    "Child": {
        "Raised my voice": """I'm sorry I raised my voice. That wasn't okay.
You didn't deserve to be spoken to that way.
I was frustrated, but it's my job to handle that better.
I love you, and I'm working on it.""",
        "Kept arguing instead of stepping away": """I'm sorry I kept arguing instead of taking a break.
I should have stepped away before things got worse.
I'm going to work on pausing sooner next time.
I love you.""",
        "Was too harsh": """I'm sorry I was too harsh.
I could have handled that with more patience.
You’re allowed to make mistakes, and I’m working on handling mine better too.""",
        "Reacted instead of pausing": """I’m sorry I reacted too fast.
I should have paused before responding.
Next time I’m going to slow down before I speak.""",
        "Blamed instead of owning my part": """I'm sorry I blamed you instead of owning my part.
I'm the adult, and I need to handle my feelings better.
I'm going to keep working on that.""",
        "Scared or overwhelmed someone": """I'm sorry I scared or overwhelmed you.
That wasn't okay.
You should feel safe with me, even when I’m frustrated.
I love you, and I'm working on handling anger better.""",
        "Something else": """I'm sorry for how I handled that.
That wasn't okay.
I'm going to keep working on doing better.""",
    },
    "Partner": {
        "Raised my voice": """I’m sorry I raised my voice.
That wasn't fair to you.
I was overwhelmed, but that doesn't excuse how I spoke.
I'm going to work on taking space before I get to that point.""",
        "Kept arguing instead of stepping away": """I'm sorry I kept arguing when I should have stepped away.
I let it keep building instead of pausing.
Next time I’m going to take space sooner.""",
        "Was too harsh": """I'm sorry I was too harsh.
I could have said what I felt without cutting you down.
I'm going to work on being clearer without being hurtful.""",
        "Reacted instead of pausing": """I'm sorry I reacted instead of pausing.
I let the emotion drive my response.
Next time I’ll slow down before I answer.""",
        "Blamed instead of owning my part": """I'm sorry I blamed instead of owning my part.
I can see where I contributed to that moment.
I'm going to take responsibility for my side.""",
        "Scared or overwhelmed someone": """I'm sorry I overwhelmed you.
That's not the kind of partner I want to be.
I'm going to work on lowering the intensity sooner.""",
        "Something else": """I'm sorry for my part in that.
I didn't handle it the way I want to.
I'm taking responsibility, and I'm working on doing better.""",
    },
    "General": {
        "Raised my voice": """I’m sorry I raised my voice.
That wasn't okay.
I was frustrated, but I’m responsible for how I respond.""",
        "Kept arguing instead of stepping away": """I’m sorry I kept pushing instead of stepping away.
I should have paused before things got worse.
I’ll work on taking space sooner.""",
        "Was too harsh": """I’m sorry I was too harsh.
I could have handled that better.
I’ll work on being more patient next time.""",
        "Reacted instead of pausing": """I’m sorry I reacted too quickly.
I should have paused first.
I’m working on slowing down before I respond.""",
        "Blamed instead of owning my part": """I’m sorry I blamed instead of owning my part.
I’m responsible for my reaction.
I’ll do better at owning my side.""",
        "Scared or overwhelmed someone": """I’m sorry I overwhelmed you.
That wasn’t okay.
I’ll work on lowering the intensity sooner.""",
        "Something else": """I’m sorry for how I handled that.
That wasn’t okay.
I’m going to work on doing better.""",
    },
}


def safe_value(value, fallback=""):
    return fallback if pd.isna(value) else value


def get_blowups(real_logs):
    if real_logs.empty:
        return real_logs.copy()
    return real_logs[real_logs["outcome"] == "Blew up"].copy()


def get_unrepaired_blowups(blowups):
    if blowups.empty:
        return blowups.copy()
    return blowups[
        blowups["repaired"].fillna("Not needed").isin(REPAIR_QUEUE_STATUSES)
    ].copy()


def get_repair_count(real_logs):
    return len(get_unrepaired_blowups(get_blowups(real_logs)))


def choose_repair_pool(blowups):
    unrepaired = get_unrepaired_blowups(blowups)
    if not unrepaired.empty:
        return unrepaired, True
    return blowups, False


def build_repair_options(repair_pool):
    options = []
    option_map = {}

    for _, row in repair_pool.iterrows():
        repaired_status = safe_value(row.get("repaired"), "Not tracked")
        label = (
            f"{row['timestamp'].strftime('%Y-%m-%d %I:%M %p')} · "
            f"{row['trigger']} · {row['intensity']}/10 · "
            f"repair: {repaired_status}"
        )
        options.append(label)
        option_map[label] = row

    return options, option_map


def get_repair_script(repair_target, ownership_choice):
    return REPAIR_SCRIPTS[repair_target].get(
        ownership_choice,
        REPAIR_SCRIPTS[repair_target]["Something else"],
    )


def build_repair_notes(existing_notes, ownership_final, repair_target, when):
    updated_notes = existing_notes

    if ownership_final:
        updated_notes = f"{updated_notes}\n\nRepair ownership: {ownership_final}".strip()

    updated_notes = f"{updated_notes}\nRepair target: {repair_target}".strip()
    updated_notes = f"{updated_notes}\nRepair timing: {when}".strip()
    return updated_notes


def prepare_log_values(row, repaired_status, notes):
    intensity_after = None if pd.isna(row["intensity_after"]) else int(row["intensity_after"])
    strategy = None if pd.isna(row["strategy"]) else row["strategy"]

    return {
        "log_id": int(row["id"]),
        "trigger": row["trigger"],
        "intensity": int(row["intensity"]),
        "intensity_after": intensity_after,
        "outcome": row["outcome"],
        "strategy": strategy,
        "repaired": repaired_status,
        "notes": notes,
    }


def should_route_to_repair(outcome, repaired):
    return outcome == "Blew up" and repaired in ["Yes", "Planned", "No"]


def default_repair_status_for_outcome(outcome):
    return "Planned" if outcome == "Blew up" else "Not needed"
