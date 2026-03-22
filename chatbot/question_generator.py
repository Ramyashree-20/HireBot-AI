from chatbot.prompts import PromptTemplates


class QuestionGenerator:
    def __init__(self, llm_handler):
        self.llm = llm_handler

    def generate(self, tech_stack: str, position: str, experience: str) -> list[str]:
        prompt = PromptTemplates.tech_question_generation_prompt(
            tech_stack=tech_stack,
            position=position,
            experience=experience,
        )
        raw_response = self.llm.generate(prompt)
        return self._parse_questions(raw_response)

    def _parse_questions(self, raw: str) -> list[str]:
        questions = []
        for line in raw.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            # Strip leading numbering like "1." or "1)"
            if line[0].isdigit():
                dot_idx = line.find(".")
                paren_idx = line.find(")")
                split_at = min(
                    dot_idx if dot_idx != -1 else len(line),
                    paren_idx if paren_idx != -1 else len(line),
                )
                line = line[split_at + 1:].strip()
            if line:
                questions.append(line)
        return questions or ["Tell me about your experience with your primary tech stack."]
