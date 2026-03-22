from utils.constants import FALLBACK_RESPONSES, CONVERSATION_STAGES


class FallbackHandler:
    def handle(self, user_input: str, current_stage: str) -> str:
        lowered = user_input.lower().strip()

        if any(word in lowered for word in ["help", "what", "how", "?"]):
            return self._context_help(current_stage)

        if any(word in lowered for word in ["bye", "exit", "quit", "stop"]):
            return FALLBACK_RESPONSES["exit"]

        return FALLBACK_RESPONSES["default"]

    def _context_help(self, stage: str) -> str:
        stage_hints = {
            "collect_name":    "Please enter your full name (e.g., Jane Doe).",
            "collect_email":   "Please enter a valid email address (e.g., jane@example.com).",
            "collect_phone":   "Please enter your phone number with country code (e.g., +1 555 000 1234).",
            "collect_experience": "Enter the number of years you have worked professionally (e.g., 3).",
            "collect_position":   "Enter the job title you are applying for (e.g., Backend Engineer).",
            "collect_location":   "Enter your current city and country (e.g., New York, USA).",
            "collect_tech_stack": "List the technologies you work with separated by commas.",
            "technical_questions": "Answer the question as clearly and concisely as you can.",
        }
        return stage_hints.get(stage, FALLBACK_RESPONSES["default"])
