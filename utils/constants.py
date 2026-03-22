APP_TITLE = "TalentScout AI"
APP_DESCRIPTION = "AI-powered hiring assistant for initial candidate screening"

CONVERSATION_STAGES = [
    "greeting",
    "collect_name",
    "collect_email",
    "collect_phone",
    "collect_experience",
    "collect_position",
    "collect_location",
    "collect_tech_stack",
    "technical_questions",
    "closing",
]

FALLBACK_RESPONSES = {
    "default": (
        "I'm not sure I understood that. Could you please rephrase? "
        "Type **help** if you need guidance on what to enter."
    ),
    "exit": (
        "Thank you for your time! If you'd like to restart, "
        "please refresh the page. Goodbye! 👋"
    ),
}

MAX_TECH_QUESTIONS = 5
DATA_FILE_PATH = "data/sample_candidates.json"
