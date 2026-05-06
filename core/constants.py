from pathlib import Path


APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "temper_tracker.db"

TRIGGER_OPTIONS = ["Repetition", "Noise / chaos", "Disrespect", "Tired", "Overwhelmed", "Interrupted", "Other"]
OUTCOME_OPTIONS = ["Stayed calm", "Struggled", "Blew up"]
REPAIR_OPTIONS = ["Not needed", "Yes", "No", "Planned"]

PAGES = ["Home", "Emergency", "Daily Check-In", "Log", "Insights", "Weekly Review", "History", "Repair", "Settings"]

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
    {
        "type": "distance",
        "name": "Step Away Reset",
        "instructions": [
            "Leave the room for 2 minutes if everyone is safe.",
            "Do not continue the argument from another room.",
            "Return only when your voice can stay calm.",
        ],
    },
    {
        "type": "breathing",
        "name": "Box Breathing",
        "instructions": [
            "Do 3 rounds of box breathing: in 4, hold 4, out 4, hold 4.",
            "Keep your mouth closed unless you need to say: ‘I need a minute.’",
            "Restart the conversation only after your body slows down.",
        ],
    },
    {
        "type": "breathing",
        "name": "Physiological Sigh",
        "instructions": [
            "Take one deep inhale, add a short second inhale, then long slow exhale.",
            "Repeat 3 to 5 times.",
            "Let your shoulders drop on each exhale.",
        ],
    },
    {
        "type": "body",
        "name": "Unclench Reset",
        "instructions": [
            "Open your hands and unclench your jaw right now.",
            "Drop your shoulders.",
            "Relax your tongue from the roof of your mouth.",
            "Take one slow breath before speaking.",
        ],
    },
    {
        "type": "cold",
        "name": "Cold Water Reset",
        "instructions": [
            "Go splash cold water on your face or wrists.",
            "Focus only on the cold feeling for 20 seconds.",
            "Do not restart the conversation while your voice still feels sharp.",
        ],
    },
    {
        "type": "attention",
        "name": "5-4-3 Grounding",
        "instructions": [
            "Name 5 things you can see before you say anything else.",
            "Name 4 things you can feel.",
            "Name 3 things you can hear.",
            "Choose the next action that lowers the damage.",
        ],
    },
    {
        "type": "attention",
        "name": "Counting Interrupt",
        "instructions": [
            "Count backward from 50 by 3s before responding.",
            "If you mess up, start again.",
            "Keep your mouth closed while counting.",
        ],
    },
    {
        "type": "voice",
        "name": "Lower Your Voice Drill",
        "instructions": [
            "Say only this: ‘I need a minute.’",
            "Lower your voice before saying anything else.",
            "Speak slower than normal.",
            "Do not lecture while heated.",
        ],
    },
    {
        "type": "repair",
        "name": "Future Repair Check",
        "instructions": [
            "Imagine apologizing for the next sentence before you say it.",
            "Ask: will this make repair harder?",
            "Choose the smallest action that prevents damage.",
        ],
    },
]