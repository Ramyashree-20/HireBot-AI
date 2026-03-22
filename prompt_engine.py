"""
prompt_engine.py
════════════════
All prompt templates for TalentScout AI.

This module is the single source of truth for:
  • System prompts    — shape the LLM's persona and task at each stage
  • Inline directives — short task strings injected into the system prompt
  • Validation copy   — the few non-LLM messages (fast, deterministic)

Design principles
─────────────────
  Deterministic   structured prompts → consistent, predictable LLM output
  Context-aware   every prompt carries the candidate's collected profile
  Minimal         each prompt does ONE thing; no bloat
  Separated       all prompt text lives here, never in business logic
"""


# ═══════════════════════════════════════════════════════════════════════════════
# BASE PERSONA  (injected into every system prompt)
# ═══════════════════════════════════════════════════════════════════════════════

_PERSONA = (
    "You are TalentScout AI, a professional, warm, and concise AI hiring assistant. "
    "You are conducting a structured initial screening interview on behalf of the hiring team. "
    "Guidelines:\n"
    "- Keep every reply to 2–4 sentences unless the task explicitly requires more.\n"
    "- Never repeat information the candidate already provided.\n"
    "- Use the candidate's first name once you know it.\n"
    "- Never invent or assume candidate details.\n"
    "- If the candidate goes off-topic, gently redirect them to the interview.\n"
    "- Do NOT mention that you are an AI unless directly asked.\n"
)


class PromptEngine:
    """
    Factory for every prompt used by TalentScoutBot.

    Usage
    -----
    pe = PromptEngine()
    system = pe.system(stage="collect_email", candidate_info={...})
    """

    # ── Master system prompt builder ──────────────────────────────────────────

    def system(self, stage: str, candidate_info: dict, task: str) -> str:
        """
        Build the full system prompt for a given conversation turn.

        Parameters
        ----------
        stage          : current bot stage  (e.g. "collect_email")
        candidate_info : dict of collected fields (None values are excluded)
        task           : one-line instruction for what the LLM should do NOW
        """
        profile = self._format_profile(candidate_info)
        return (
            f"{_PERSONA}\n"
            f"── Candidate profile so far ──\n{profile}\n\n"
            f"── Current interview stage ──\n{stage}\n\n"
            f"── Your task for this turn ──\n{task}"
        )

    # ── Stage-specific task strings ───────────────────────────────────────────
    # These are passed as the `task` argument to self.system().

    def task_greeting(self) -> str:
        return (
            "Warmly greet the candidate. Introduce yourself as TalentScout AI. "
            "Briefly explain that this is a quick initial screening (about 10–15 minutes). "
            "Tell them you will ask for some personal details and then a few technical questions. "
            "Invite them to say 'hi' or 'start' when ready."
        )

    def task_ask_name(self) -> str:
        return (
            "The candidate is ready to start. Ask for their full name. "
            "Keep it friendly and brief."
        )

    def task_ask_email(self, name: str) -> str:
        return (
            f"The candidate's name is {name}. "
            "Acknowledge their name warmly (one short sentence), "
            "then ask for their email address."
        )

    def task_ask_phone(self) -> str:
        return (
            "The candidate just provided their email. "
            "Acknowledge briefly, then ask for their phone number. "
            "Remind them to include the country code if they are outside the US."
        )

    def task_ask_experience(self) -> str:
        return (
            "Phone number collected. "
            "Acknowledge, then ask how many years of professional experience they have."
        )

    def task_ask_position(self) -> str:
        return (
            "Experience noted. "
            "Now ask what position or role they are applying for."
        )

    def task_ask_location(self) -> str:
        return (
            "Position noted. "
            "Ask where they are currently located (city and country)."
        )

    def task_ask_tech_stack(self) -> str:
        return (
            "Location noted. You now have all the basic details. "
            "Ask the candidate to list their primary tech stack — "
            "programming languages, frameworks, databases, or any tools they work with. "
            "Give an example like 'Python, Django, PostgreSQL, Docker'."
        )

    def task_start_technical(self, first_question: str) -> str:
        return (
            "All personal details are collected. "
            "Transition to the technical assessment. "
            "Tell the candidate you will now ask a few technical questions based on their stack. "
            "Encourage them to take their time. "
            f"Then present this as Question 1:\n\n\"{first_question}\""
        )

    def task_next_question(self, question: str, current: int, total: int) -> str:
        return (
            f"The candidate just answered a technical question. "
            f"Give a brief, neutral acknowledgement (do NOT evaluate their answer — "
            f"do not say whether it was right or wrong). "
            f"Then present the next question as Question {current} of {total}:\n\n"
            f"\"{question}\""
        )

    def task_closing(self) -> str:
        return (
            "The technical assessment is complete. "
            "Thank the candidate sincerely. "
            "Tell them the hiring team will review their responses and get back to them "
            "within 3–5 business days. "
            "Wish them well and close the conversation warmly."
        )

    def task_farewell(self) -> str:
        return (
            "The candidate wants to end the conversation early. "
            "Thank them for their time. "
            "Let them know they can refresh the page to start a new session. "
            "Say goodbye warmly."
        )

    def task_fallback(self, stage: str) -> str:
        context_hints = {
            "collect_name":       "They need to provide their full name.",
            "collect_email":      "They need to provide a valid email address.",
            "collect_phone":      "They need to provide their phone number.",
            "collect_experience": "They need to state their years of professional experience.",
            "collect_position":   "They need to name the job title they are applying for.",
            "collect_location":   "They need to provide their city and country.",
            "collect_tech_stack": "They need to list their primary technologies.",
            "technical_questions":"They need to answer the technical question that was asked.",
        }
        hint = context_hints.get(stage, "Gently guide them back to the interview.")
        return (
            f"The candidate's response was unclear or off-topic at stage '{stage}'. "
            f"Politely say you didn't quite understand. "
            f"Provide a clear, friendly hint: {hint} "
            f"Ask them to try again."
        )

    # ── Validation messages  (fast, no LLM needed) ────────────────────────────

    @staticmethod
    def invalid_email() -> str:
        return (
            "That doesn't look like a valid email address. 🤔\n\n"
            "Please enter a valid email — for example: `jane@company.com`"
        )

    @staticmethod
    def invalid_phone() -> str:
        return (
            "That doesn't look like a valid phone number. 📱\n\n"
            "Please enter 7–15 digits, with the country code if needed "
            "(e.g., `+1 555 000 1234`)."
        )

    @staticmethod
    def invalid_name() -> str:
        return "Could you please enter your **full name**? (at least 2 characters)"

    @staticmethod
    def invalid_tech_stack() -> str:
        return (
            "I couldn't pick out any technologies from that. "
            "Please list them separated by commas — "
            "for example: *Python, React, PostgreSQL*."
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _format_profile(info: dict) -> str:
        labels = {
            "name":       "Full Name",
            "email":      "Email",
            "phone":      "Phone",
            "experience": "Experience",
            "position":   "Position",
            "location":   "Location",
            "tech_stack": "Tech Stack",
        }
        lines = []
        for key, label in labels.items():
            value = info.get(key)
            if value:
                if isinstance(value, list):
                    value = ", ".join(value)
                lines.append(f"  {label}: {value}")
        return "\n".join(lines) if lines else "  (none collected yet)"
