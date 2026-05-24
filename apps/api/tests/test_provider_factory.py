import pytest

from app.core.config import Settings
from app.core.errors import AppError
from app.llm.factory import ProviderFactory


def test_factory_returns_mock_provider() -> None:
    factory = ProviderFactory(Settings(llm_provider="mock"))

    provider = factory.get()

    assert provider.name == "mock"
    assert factory.default_model_for(provider.name) == "mock/local-chat"


def test_openrouter_requires_api_key() -> None:
    factory = ProviderFactory(Settings(llm_provider="openrouter", openrouter_api_key=""))

    with pytest.raises(AppError) as error:
        factory.get()

    assert error.value.code == "provider_not_configured"


def test_groq_requires_api_key() -> None:
    factory = ProviderFactory(Settings(llm_provider="groq", groq_api_key=""))

    with pytest.raises(AppError) as error:
        factory.get()

    assert error.value.code == "provider_not_configured"
