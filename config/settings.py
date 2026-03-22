import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM provider: "openai" or "anthropic"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")

    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Model config
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1024"))

    # App config
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


settings = Settings()
