from pathlib import Path


APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "temper_tracker.db"

TRIGGER_OPTIONS = ["Repetition", "Noise / chaos", "Disrespect", "Tired", "Overwhelmed", "Interrupted", "Other"]
OUTCOME_OPTIONS = ["Stayed calm", "Struggled", "Blew up"]
REPAIR_OPTIONS = ["Not needed", "Yes", "No", "Planned"]

PAGES = ["Home", "Emergency", "Daily Check-In", "Log", "Insights", "Weekly Review", "History", "Settings"]

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
