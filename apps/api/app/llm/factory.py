from app.core.config import Settings
from app.core.errors import AppError
from app.llm.base import LLMProvider
from app.llm.groq_provider import GroqProvider
from app.llm.mock_provider import MockProvider
from app.llm.openrouter_provider import OpenRouterProvider


class ProviderFactory:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._mock = MockProvider()

    def default_provider_name(self) -> str:
        return self.settings.llm_provider

    def default_model_for(self, provider: str) -> str:
        if provider == "openrouter":
            return self.settings.openrouter_model
        if provider == "groq":
            return self.settings.groq_model
        return "mock/local-chat"

    def get(self, provider: str | None = None) -> LLMProvider:
        selected = provider or self.settings.llm_provider
        if selected == "mock":
            return self._mock
        if selected == "openrouter":
            if not self.settings.openrouter_api_key:
                raise AppError(
                    "OPENROUTER_API_KEY is required for the openrouter provider",
                    status_code=500,
                    code="provider_not_configured",
                )
            return OpenRouterProvider(
                api_key=self.settings.openrouter_api_key,
                base_url=self.settings.openrouter_base_url,
                timeout_seconds=self.settings.request_timeout_seconds,
            )
        if selected == "groq":
            if not self.settings.groq_api_key:
                raise AppError(
                    "GROQ_API_KEY is required for the groq provider",
                    status_code=500,
                    code="provider_not_configured",
                )
            return GroqProvider(
                api_key=self.settings.groq_api_key,
                base_url=self.settings.groq_base_url,
                timeout_seconds=self.settings.request_timeout_seconds,
            )
        raise AppError("Unsupported provider", status_code=400, code="unsupported_provider")
