from types import SimpleNamespace

import pytest

from app.services.providers.factory import get_provider
from app.services.providers.mock import MockImageProvider
from app.services.providers.openai import OpenAIImageEditProvider, _build_provider_url, _extract_error_message


def test_openai_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.providers.factory.get_settings",
        lambda: SimpleNamespace(openai_api_key=None, openai_base_url="https://api.example.test"),
    )

    with pytest.raises(RuntimeError, match="OpenAI API key is not configured"):
        get_provider("gpt-image-2")


def test_openai_provider_requires_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.providers.factory.get_settings",
        lambda: SimpleNamespace(openai_api_key="test-key", openai_base_url=None),
    )

    with pytest.raises(RuntimeError, match="OpenAI base URL is not configured"):
        get_provider("gpt-image-2")


def test_openai_provider_is_real_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.providers.factory.get_settings",
        lambda: SimpleNamespace(openai_api_key="test-key", openai_base_url="https://api.example.test"),
    )

    assert isinstance(get_provider("gpt-image-2"), OpenAIImageEditProvider)


def test_non_openai_provider_still_uses_mock() -> None:
    assert isinstance(get_provider("gemini-banana"), MockImageProvider)


def test_openai_provider_url_adds_v1_path() -> None:
    assert (
        _build_provider_url("https://www.llmgateway.cn", "/images/edits")
        == "https://www.llmgateway.cn/v1/images/edits"
    )


def test_openai_provider_url_does_not_duplicate_v1_path() -> None:
    assert (
        _build_provider_url("https://www.llmgateway.cn/v1", "/images/edits")
        == "https://www.llmgateway.cn/v1/images/edits"
    )


def test_openai_provider_error_message_is_extracted() -> None:
    assert (
        _extract_error_message('{"error":{"message":"Invalid or expired authentication token"}}')
        == "Invalid or expired authentication token"
    )
