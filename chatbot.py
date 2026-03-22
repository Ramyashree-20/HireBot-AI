"""
chatbot.py
══════════
TalentScoutBot — the conversation engine for TalentScout AI.

Hybrid LLM architecture
────────────────────────
  ⚡ FAST_MODEL  (llama3-8b-8192)
      → generate_response()  — all conversational turns:
        greetings, info acknowledgements, question delivery, fallbacks, closing

  🧠 SMART_MODEL (llama-3.3-70b-versatile)
      → generate_tech_questions()  — one call per interview:
        generates 5 domain-specific questions; result is cached

  The routing is handled transparently by llm_handler.py — this file
  simply calls the two public functions and never touches model names.

Other responsibilities
──────────────────────
  • Stage machine        drives WHAT information to collect next
  • prompt_engine        supplies system prompts / task strings per stage
  • utils                validation + parsing (no LLM needed)
"""

import re
from prompt_engine import PromptEngine
from llm_handler   import generate_response, generate_tech_questions
from utils         import validate_email, validate_phone, parse_tech_stack


# ═══════════════════════════════════════════════════════════════════════════════
# TalentScoutBot
# ═══════════════════════════════════════════════════════════════════════════════

class TalentScoutBot:
    """
    Stage-based conversational hiring assistant powered by Groq (Llama 3).

    Stages (in order)
    ─────────────────
    greeting → collect_name → collect_email → collect_phone →
    collect_experience → collect_position → collect_location →
    collect_tech_stack → technical_questions → closing
    """

    STAGES = [
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

    EXIT_KEYWORDS = {"exit", "quit", "bye", "goodbye", "stop", "end"}

    def __init__(self, data_handler=None):
        self.stage           = self.STAGES[0]
        self.pe              = PromptEngine()
        self.data_handler    = data_handler

        # Candidate profile (populated as interview progresses)
        self.candidate_info: dict = {
            "name":       None,
            "email":      None,
            "phone":      None,
            "experience": None,
            "position":   None,
            "location":   None,
            "tech_stack": None,   # stored as list[str] after parsing
        }

        # Technical Q&A state
        self.tech_questions:          list[str]  = []
        self.current_question_index:  int        = 0
        self.answers:                 list[dict] = []

        # LLM conversation history (role/content pairs sent to Groq)
        # Keeps the model contextually aware across the full conversation.
        self.conversation_history: list[dict] = []

    # ── Public API ────────────────────────────────────────────────────────────

    def initialize_with_form_data(self, candidate_info: dict) -> str:
        """
        Called after the profile form is submitted.

        Skips all info-collection stages, pre-populates the candidate
        profile, generates tech questions via Groq, then returns an
        LLM-crafted opening message that greets the candidate by name
        and presents the first question.

        Parameters
        ----------
        candidate_info : dict with keys name, email, phone, experience,
                         position, location, tech_stack (list[str])

        Returns
        -------
        str  — the opening assistant message for the chat page
        """
        # Populate profile from form
        self.candidate_info.update(candidate_info)

        # Generate questions via Groq
        tech = candidate_info.get("tech_stack") or []
        if isinstance(tech, str):
            tech = [tech]

        self.tech_questions = generate_tech_questions(
            tech_stack = tech,
            position   = candidate_info.get("position") or "",
            experience = candidate_info.get("experience") or "",
        )
        self.current_question_index = 0
        self.stage = "technical_questions"

        # Build opening message: greet + context + first question
        techs_str = ", ".join(tech) if tech else "your tech stack"
        task = (
            f"The candidate has just submitted their profile. Here is a summary:\n"
            f"  Name: {candidate_info.get('name')}\n"
            f"  Applying for: {candidate_info.get('position')}\n"
            f"  Experience: {candidate_info.get('experience')}\n"
            f"  Location: {candidate_info.get('location')}\n"
            f"  Tech stack: {techs_str}\n\n"
            f"Welcome them warmly and by name. Briefly acknowledge their profile "
            f"(1 sentence). Tell them the technical assessment will now begin and "
            f"they should answer each question as clearly as they can. "
            f"Then present this as Question 1 of {len(self.tech_questions)}:\n\n"
            f"\"{self.tech_questions[0]}\""
        )
        system = self.pe.system(
            stage          = self.stage,
            candidate_info = self.candidate_info,
            task           = task,
        )
        reply = generate_response([], system)
        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply

    def get_welcome(self) -> str:
        """
        Generate the opening greeting via the LLM.
        Called once when the Streamlit session is first created.
        """
        system  = self.pe.system(
            stage          = self.stage,
            candidate_info = self.candidate_info,
            task           = self.pe.task_greeting(),
        )
        reply = generate_response([], system)
        # Seed the conversation history with the assistant's opening message
        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply

    def process(self, user_input: str) -> str:
        """
        Main entry point. Routes the user's message to the correct handler
        and returns the LLM-generated reply.
        """
        user_input = user_input.strip()
        if not user_input:
            return self._llm_fallback()

        # Record user turn in conversation history (used for LLM context)
        self.conversation_history.append({"role": "user", "content": user_input})

        # ── Exit detection ─────────────────────────────────────────────────
        if any(kw in user_input.lower().split() for kw in self.EXIT_KEYWORDS):
            self.stage = "closing"
            return self._llm_farewell()

        # ── Help request ───────────────────────────────────────────────────
        if user_input.lower().strip() in {"help", "?", "h"}:
            return self._llm_fallback()

        # ── Route to stage handler ─────────────────────────────────────────
        handler = {
            "greeting":            self._handle_greeting,
            "collect_name":        self._handle_name,
            "collect_email":       self._handle_email,
            "collect_phone":       self._handle_phone,
            "collect_experience":  self._handle_experience,
            "collect_position":    self._handle_position,
            "collect_location":    self._handle_location,
            "collect_tech_stack":  self._handle_tech_stack,
            "technical_questions": self._handle_tech_question,
            "closing":             self._handle_closing,
        }.get(self.stage)

        reply = handler(user_input) if handler else self._llm_fallback()

        # Record assistant turn in conversation history
        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply

    # ── Stage handlers ────────────────────────────────────────────────────────
    # Each handler:
    #   1. Validates / stores the user's input (if this stage collects data)
    #   2. Advances to the next stage
    #   3. Calls the LLM with an appropriate task string
    #   4. Returns the LLM's reply

    def _handle_greeting(self, _: str) -> str:
        self._next_stage()   # → collect_name
        system = self.pe.system(
            stage          = self.stage,
            candidate_info = self.candidate_info,
            task           = self.pe.task_ask_name(),
        )
        return generate_response(self.conversation_history, system)

    def _handle_name(self, user_input: str) -> str:
        name = user_input.strip()
        if len(name) < 2 or not re.search(r"[a-zA-Z]", name):
            return self.pe.invalid_name()   # fast validation — no LLM needed

        self.candidate_info["name"] = name
        self._next_stage()   # → collect_email
        system = self.pe.system(
            stage          = self.stage,
            candidate_info = self.candidate_info,
            task           = self.pe.task_ask_email(name),
        )
        return generate_response(self.conversation_history, system)

    def _handle_email(self, user_input: str) -> str:
        email = user_input.strip().lower()
        if not validate_email(email):
            return self.pe.invalid_email()  # fast validation

        self.candidate_info["email"] = email
        self._next_stage()   # → collect_phone
        system = self.pe.system(
            stage          = self.stage,
            candidate_info = self.candidate_info,
            task           = self.pe.task_ask_phone(),
        )
        return generate_response(self.conversation_history, system)

    def _handle_phone(self, user_input: str) -> str:
        if not validate_phone(user_input.strip()):
            return self.pe.invalid_phone()  # fast validation

        self.candidate_info["phone"] = user_input.strip()
        self._next_stage()   # → collect_experience
        system = self.pe.system(
            stage          = self.stage,
            candidate_info = self.candidate_info,
            task           = self.pe.task_ask_experience(),
        )
        return generate_response(self.conversation_history, system)

    def _handle_experience(self, user_input: str) -> str:
        self.candidate_info["experience"] = user_input.strip()
        self._next_stage()   # → collect_position
        system = self.pe.system(
            stage          = self.stage,
            candidate_info = self.candidate_info,
            task           = self.pe.task_ask_position(),
        )
        return generate_response(self.conversation_history, system)

    def _handle_position(self, user_input: str) -> str:
        if len(user_input.strip()) < 2:
            return self._llm_fallback()

        self.candidate_info["position"] = user_input.strip()
        self._next_stage()   # → collect_location
        system = self.pe.system(
            stage          = self.stage,
            candidate_info = self.candidate_info,
            task           = self.pe.task_ask_location(),
        )
        return generate_response(self.conversation_history, system)

    def _handle_location(self, user_input: str) -> str:
        self.candidate_info["location"] = user_input.strip()
        self._next_stage()   # → collect_tech_stack
        system = self.pe.system(
            stage          = self.stage,
            candidate_info = self.candidate_info,
            task           = self.pe.task_ask_tech_stack(),
        )
        return generate_response(self.conversation_history, system)

    def _handle_tech_stack(self, user_input: str) -> str:
        techs = parse_tech_stack(user_input)
        if not techs:
            return self.pe.invalid_tech_stack()  # fast validation

        self.candidate_info["tech_stack"] = techs

        # ── Generate technical questions via Groq ──────────────────────────
        self.tech_questions = generate_tech_questions(
            tech_stack = techs,
            position   = self.candidate_info.get("position") or "",
            experience = self.candidate_info.get("experience") or "",
        )
        self.current_question_index = 0
        self._next_stage()   # → technical_questions

        system = self.pe.system(
            stage          = self.stage,
            candidate_info = self.candidate_info,
            task           = self.pe.task_start_technical(self.tech_questions[0]),
        )
        return generate_response(self.conversation_history, system)

    def _handle_tech_question(self, user_input: str) -> str:
        # Record answer
        self.answers.append({
            "question": self.tech_questions[self.current_question_index],
            "answer":   user_input.strip(),
        })
        self.current_question_index += 1

        # More questions remaining?
        if self.current_question_index < len(self.tech_questions):
            system = self.pe.system(
                stage          = self.stage,
                candidate_info = self.candidate_info,
                task           = self.pe.task_next_question(
                    question = self.tech_questions[self.current_question_index],
                    current  = self.current_question_index + 1,
                    total    = len(self.tech_questions),
                ),
            )
            return generate_response(self.conversation_history, system)

        # All questions answered → save and close
        self._save_candidate()
        self._next_stage()   # → closing
        return self._llm_closing()

    def _handle_closing(self, _: str) -> str:
        return self._llm_closing()

    # ── LLM convenience wrappers ──────────────────────────────────────────────

    def _llm_fallback(self) -> str:
        system = self.pe.system(
            stage          = self.stage,
            candidate_info = self.candidate_info,
            task           = self.pe.task_fallback(self.stage),
        )
        return generate_response(self.conversation_history, system)

    def _llm_farewell(self) -> str:
        system = self.pe.system(
            stage          = "closing",
            candidate_info = self.candidate_info,
            task           = self.pe.task_farewell(),
        )
        return generate_response(self.conversation_history, system)

    def _llm_closing(self) -> str:
        system = self.pe.system(
            stage          = "closing",
            candidate_info = self.candidate_info,
            task           = self.pe.task_closing(),
        )
        return generate_response(self.conversation_history, system)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _next_stage(self) -> None:
        idx = self.STAGES.index(self.stage)
        if idx + 1 < len(self.STAGES):
            self.stage = self.STAGES[idx + 1]

    def _save_candidate(self) -> None:
        if self.data_handler:
            try:
                self.data_handler.save_candidate(self.candidate_info, self.answers)
            except Exception:
                pass   # storage failure must never crash the interview
