import pytest

from normkompass_mcp.config import DEFAULT_API_URL, ENV_API_URL, api_url


def test_default_address(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_API_URL, raising=False)
    assert api_url() == DEFAULT_API_URL


def test_custom_address_without_trailing_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_API_URL, "http://example.test:4000/")
    assert api_url() == "http://example.test:4000"


def test_blank_value_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_API_URL, "   ")
    assert api_url() == DEFAULT_API_URL
