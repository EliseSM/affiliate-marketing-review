from app.config import Settings
from app.evaluation.llm_judge.provider_interface import LLMProvider


def get_provider(settings: Settings) -> LLMProvider:
    """Config-driven provider selection. Adding a new vendor means adding an
    LLMProvider implementation and a branch here -- no other code changes."""
    if settings.LLM_PROVIDER == "openai":
        from app.evaluation.llm_judge.openai_provider import OpenAIProvider

        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.LLM_MODEL,
            timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER!r}")
