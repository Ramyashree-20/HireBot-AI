class PromptTemplates:

    @staticmethod
    def welcome_message() -> str:
        return (
            "👋 Hello! I'm **TalentScout**, your AI hiring assistant.\n\n"
            "I'll guide you through a quick screening process for our open positions. "
            "This should take about 10–15 minutes.\n\n"
            "When you're ready, just say **hi** or **start** to begin!"
        )

    @staticmethod
    def ask_name() -> str:
        return "Great, let's get started! 🎉\n\nWhat's your **full name**?"

    @staticmethod
    def ask_email(name: str) -> str:
        return f"Nice to meet you, **{name}**! 😊\n\nWhat's your **email address**?"

    @staticmethod
    def invalid_email() -> str:
        return "That doesn't look like a valid email address. Please try again (e.g., name@example.com)."

    @staticmethod
    def ask_phone() -> str:
        return "Got it! What's your **phone number**? (Include country code if outside the US)"

    @staticmethod
    def invalid_phone() -> str:
        return "That doesn't look like a valid phone number. Please enter digits only (10–15 digits)."

    @staticmethod
    def ask_experience() -> str:
        return "How many **years of professional experience** do you have?"

    @staticmethod
    def ask_position() -> str:
        return "What **position** are you applying for?"

    @staticmethod
    def ask_location() -> str:
        return "Where are you currently located? (City, Country)"

    @staticmethod
    def ask_tech_stack() -> str:
        return (
            "Awesome! Now, please list your **primary tech stack** — "
            "programming languages, frameworks, databases, tools, etc.\n\n"
            "*(e.g., Python, Django, PostgreSQL, Docker, AWS)*"
        )

    @staticmethod
    def start_technical_round(first_question: str) -> str:
        return (
            "Perfect! Let's move on to the **technical assessment**. 🧠\n\n"
            "I'll ask you a few questions based on your tech stack. Take your time!\n\n"
            f"**Question 1:** {first_question}"
        )

    @staticmethod
    def next_question(question: str, current: int, total: int) -> str:
        return f"**Question {current} of {total}:** {question}"

    @staticmethod
    def closing_message(name: str) -> str:
        return (
            f"Thank you, **{name}**! 🙏\n\n"
            "You've completed the initial screening. Our team will review your responses "
            "and reach out within **3–5 business days**.\n\n"
            "Best of luck! Feel free to close this window."
        )

    @staticmethod
    def system_prompt(candidate_info: dict) -> str:
        return (
            "You are TalentScout, a professional AI hiring assistant. "
            "You are conducting an initial screening interview. "
            "Be friendly, professional, and concise. "
            f"Candidate info so far: {candidate_info}"
        )

    @staticmethod
    def tech_question_generation_prompt(tech_stack: str, position: str, experience: str) -> str:
        return (
            f"Generate 5 technical interview questions for a candidate applying for the role of '{position}' "
            f"with {experience} years of experience. Their tech stack includes: {tech_stack}.\n\n"
            "Requirements:\n"
            "- Questions should be practical and role-relevant\n"
            "- Vary difficulty from beginner to intermediate\n"
            "- Return ONLY a numbered list of questions, no extra text"
        )
