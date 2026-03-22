from chatbot.prompts import PromptTemplates
from chatbot.question_generator import QuestionGenerator
from chatbot.fallback import FallbackHandler
from utils.validators import validate_email, validate_phone
from utils.constants import CONVERSATION_STAGES
from models.llm_handler import LLMHandler


class ConversationManager:
    def __init__(self):
        self.llm = LLMHandler()
        self.question_gen = QuestionGenerator(self.llm)
        self.fallback = FallbackHandler()
        self.stage = CONVERSATION_STAGES[0]
        self.candidate_info = {}
        self.tech_questions = []
        self.current_question_index = 0
        self.chat_history = []

    def get_welcome_message(self):
        return PromptTemplates.welcome_message()

    def process_message(self, user_input: str) -> str:
        self.chat_history.append({"role": "user", "content": user_input})

        response = self._route_stage(user_input)

        self.chat_history.append({"role": "assistant", "content": response})
        return response

    def _route_stage(self, user_input: str) -> str:
        stage_handlers = {
            "greeting":        self._handle_greeting,
            "collect_name":    self._handle_name,
            "collect_email":   self._handle_email,
            "collect_phone":   self._handle_phone,
            "collect_experience": self._handle_experience,
            "collect_position":   self._handle_position,
            "collect_location":   self._handle_location,
            "collect_tech_stack": self._handle_tech_stack,
            "technical_questions": self._handle_tech_questions,
            "closing":         self._handle_closing,
        }
        handler = stage_handlers.get(self.stage, self._handle_fallback)
        return handler(user_input)

    def _next_stage(self):
        current_index = CONVERSATION_STAGES.index(self.stage)
        if current_index + 1 < len(CONVERSATION_STAGES):
            self.stage = CONVERSATION_STAGES[current_index + 1]

    def _handle_greeting(self, user_input: str) -> str:
        self._next_stage()
        return PromptTemplates.ask_name()

    def _handle_name(self, user_input: str) -> str:
        self.candidate_info["name"] = user_input.strip()
        self._next_stage()
        return PromptTemplates.ask_email(self.candidate_info["name"])

    def _handle_email(self, user_input: str) -> str:
        if not validate_email(user_input.strip()):
            return PromptTemplates.invalid_email()
        self.candidate_info["email"] = user_input.strip()
        self._next_stage()
        return PromptTemplates.ask_phone()

    def _handle_phone(self, user_input: str) -> str:
        if not validate_phone(user_input.strip()):
            return PromptTemplates.invalid_phone()
        self.candidate_info["phone"] = user_input.strip()
        self._next_stage()
        return PromptTemplates.ask_experience()

    def _handle_experience(self, user_input: str) -> str:
        self.candidate_info["experience"] = user_input.strip()
        self._next_stage()
        return PromptTemplates.ask_position()

    def _handle_position(self, user_input: str) -> str:
        self.candidate_info["position"] = user_input.strip()
        self._next_stage()
        return PromptTemplates.ask_location()

    def _handle_location(self, user_input: str) -> str:
        self.candidate_info["location"] = user_input.strip()
        self._next_stage()
        return PromptTemplates.ask_tech_stack()

    def _handle_tech_stack(self, user_input: str) -> str:
        self.candidate_info["tech_stack"] = user_input.strip()
        self.tech_questions = self.question_gen.generate(
            tech_stack=self.candidate_info["tech_stack"],
            position=self.candidate_info.get("position", ""),
            experience=self.candidate_info.get("experience", ""),
        )
        self._next_stage()
        return PromptTemplates.start_technical_round(self.tech_questions[0])

    def _handle_tech_questions(self, user_input: str) -> str:
        self.candidate_info.setdefault("answers", []).append({
            "question": self.tech_questions[self.current_question_index],
            "answer": user_input.strip(),
        })
        self.current_question_index += 1

        if self.current_question_index < len(self.tech_questions):
            return PromptTemplates.next_question(
                self.tech_questions[self.current_question_index],
                self.current_question_index + 1,
                len(self.tech_questions),
            )

        self._next_stage()
        return self._handle_closing(user_input)

    def _handle_closing(self, user_input: str) -> str:
        return PromptTemplates.closing_message(self.candidate_info.get("name", ""))

    def _handle_fallback(self, user_input: str) -> str:
        return self.fallback.handle(user_input, self.stage)
