from config.settings import settings


class LLMHandler:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self._client = self._init_client()

    def _init_client(self):
        if self.provider == "openai":
            from openai import OpenAI
            return OpenAI(api_key=settings.OPENAI_API_KEY)
        elif self.provider == "anthropic":
            import anthropic
            return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def generate(self, prompt: str, system: str = "") -> str:
        if self.provider == "openai":
            return self._call_openai(prompt, system)
        elif self.provider == "anthropic":
            return self._call_anthropic(prompt, system)

    def _call_openai(self, prompt: str, system: str) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=messages,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()

    def _call_anthropic(self, prompt: str, system: str) -> str:
        kwargs = {
            "model": settings.MODEL_NAME,
            "max_tokens": settings.MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        response = self._client.messages.create(**kwargs)
        return response.content[0].text.strip()
