EXPERIMENT_STATUS_OPTIONS = ["Planned", "Tried", "Worked", "Didn't work"]
SUCCESSFUL_EXPERIMENT_STATUSES = ["Worked", "Tried"]


def build_behavior_experiment(this_week):
    if this_week.empty:
        return "Log a few real moments this week so the app can suggest a useful experiment."

    avg_intensity = round(this_week["intensity"].mean(), 1)
    blowups = this_week[this_week["outcome"] == "Blew up"]

    if not blowups.empty:
        trigger = blowups["trigger"].mode().iloc[0]
        return f"When {trigger} starts building, step away at 5/10 instead of waiting until it hits 7/10."

    if avg_intensity >= 6:
        return "Use Emergency Mode earlier this week, even when you think you can still handle it."

    top_trigger = this_week["trigger"].mode().iloc[0]
    return f"Keep noticing what helps you stay calm during {top_trigger}."


def experiment_card_kind(status):
    return "success" if status in SUCCESSFUL_EXPERIMENT_STATUSES else "normal"
