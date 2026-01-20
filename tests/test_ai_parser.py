"""pytest test suite for parsers.ai_parser.AIParser.

All OpenAI/OpenRouter calls are fully mocked (no network).
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace, ModuleType
from typing import Any

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# Ensure project root is importable when running from repo root or tests/.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _make_openai_chat_response(content: str) -> Any:
    """Create a minimal object matching OpenAI SDK response shape used by AIParser."""
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=content,
                )
            )
        ]
    )


def _get_openai_api_connection_error() -> type[BaseException]:
    """Best-effort retrieval of openai.APIConnectionError across SDK versions."""
    try:
        import openai  # type: ignore

        return getattr(openai, "APIConnectionError", RuntimeError)
    except Exception:
        return RuntimeError


@pytest.fixture(autouse=True)
def openai_module_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide a minimal `openai` module so `from openai import AsyncOpenAI` works.

    This keeps the suite runnable even if `openai` isn't installed in the test environment.
    """

    class APIConnectionError(Exception):
        pass

    class AsyncOpenAI:  # pragma: no cover
        def __init__(self, *args: Any, **kwargs: Any):
            raise AssertionError("AsyncOpenAI should be patched in tests")

    stub = ModuleType("openai")
    stub.AsyncOpenAI = AsyncOpenAI  # type: ignore[attr-defined]
    stub.APIConnectionError = APIConnectionError  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "openai", stub)


@pytest.fixture()
def logger_mock() -> MagicMock:
    """Mock logger used by parsers.ai_parser."""
    mock = MagicMock()
    # AIParser uses: info/debug/error/warn/success
    mock.info = MagicMock()
    mock.debug = MagicMock()
    mock.error = MagicMock()
    mock.warn = MagicMock()
    mock.success = MagicMock()
    return mock


@pytest.fixture()
def env_with_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "deepseek/deepseek-r1")


def test_missing_api_key(monkeypatch: pytest.MonkeyPatch, logger_mock: MagicMock) -> None:
    """Class should fail fast and log when API key is missing."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with patch("parsers.ai_parser.logger", logger_mock), patch("parsers.ai_parser.AsyncOpenAI") as mock_async_openai:
        from parsers.ai_parser import AIParser

        with pytest.raises(ValueError, match="OPENROUTER_API_KEY must be set"):
            AIParser()

        logger_mock.error.assert_called()
        mock_async_openai.assert_not_called()


def test_parse_signal_valid(env_with_api_key: None, logger_mock: MagicMock) -> None:
    """Verify correct extraction/normalization of core fields."""
    ai_json = json.dumps(
        {
            "symbol": "BTCUSDT",
            "side": "LONG",
            "entry": [42000.5, "41500"],
            "tp": ["43000", 44000.0, 45000],
            "sl": "40000",
            "leverage": "20",
            "confidence": 0.95,
        }
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_make_openai_chat_response(ai_json))

    with patch("parsers.ai_parser.logger", logger_mock), patch("parsers.ai_parser.AsyncOpenAI", return_value=mock_client) as mock_async_openai:
        from parsers.ai_parser import AIParser

        parser = AIParser()
        result = asyncio.run(parser.parse_signal("BTC/USDT LONG Entry: 42000.5"))

        assert result["symbol"] == "BTCUSDT"
        assert result["side"] == "LONG"
        assert result["entry"] == [42000.5, 41500.0]
        assert result["tp"] == [43000.0, 44000.0, 45000.0]
        assert result["sl"] == 40000.0
        assert result["leverage"] == 20
        assert 0.0 <= result["confidence"] <= 1.0

        mock_async_openai.assert_called_once()
        mock_client.chat.completions.create.assert_awaited_once()


def test_parse_signal_garbage_text(env_with_api_key: None, logger_mock: MagicMock) -> None:
    """Ensure the parser handles non-signal input gracefully."""
    ai_json = "{\"signal\": false}"

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_make_openai_chat_response(ai_json))

    with patch("parsers.ai_parser.logger", logger_mock), patch("parsers.ai_parser.AsyncOpenAI", return_value=mock_client):
        from parsers.ai_parser import AIParser

        parser = AIParser()
        result = asyncio.run(parser.parse_signal("Hello world"))

        # Spec allows None or graceful handling; current implementation returns {"signal": False}.
        assert result is None or result.get("signal") is False


def test_parse_signal_malformed_json(env_with_api_key: None, logger_mock: MagicMock) -> None:
    """AI returns broken JSON; parser must catch JSONDecodeError and not crash."""
    broken = '{"symbol": "BTCUSDT", "side": "LONG"'  # missing closing brace

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_make_openai_chat_response(broken))

    with patch("parsers.ai_parser.logger", logger_mock), patch("parsers.ai_parser.AsyncOpenAI", return_value=mock_client):
        from parsers.ai_parser import AIParser

        parser = AIParser()
        result = asyncio.run(parser.parse_signal("BTCUSDT LONG"))

        assert result.get("signal") is False
        assert "JSON decode error" in str(result.get("error", ""))
        logger_mock.error.assert_called()


def test_parse_signal_markdown_stripping(env_with_api_key: None, logger_mock: MagicMock) -> None:
    """AI may wrap JSON in markdown code fences; parser should sanitize before json.loads."""
    fenced = """```json
{\"symbol\": \"ETHUSDT\", \"side\": \"SHORT\", \"entry\": [3000], \"tp\": [2900, 2800], \"sl\": 3100, \"leverage\": 10, \"confidence\": 0.9}
```"""

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_make_openai_chat_response(fenced))

    with patch("parsers.ai_parser.logger", logger_mock), patch("parsers.ai_parser.AsyncOpenAI", return_value=mock_client):
        from parsers.ai_parser import AIParser

        parser = AIParser()
        result = asyncio.run(parser.parse_signal("ETHUSDT SHORT"))

        assert result["symbol"] == "ETHUSDT"
        assert result["side"] == "SHORT"
        assert result["entry"] == [3000.0]
        assert result["tp"] == [2900.0, 2800.0]
        assert result["sl"] == 3100.0
        assert result["leverage"] == 10


def test_api_connection_error(env_with_api_key: None, logger_mock: MagicMock) -> None:
    """Simulate openai.APIConnectionError; parser should log and return None/False signal."""
    APIConnectionError = _get_openai_api_connection_error()

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=APIConnectionError("connection failed"))

    with patch("parsers.ai_parser.logger", logger_mock), patch("parsers.ai_parser.AsyncOpenAI", return_value=mock_client):
        from parsers.ai_parser import AIParser

        parser = AIParser()
        result = asyncio.run(parser.parse_signal("BTCUSDT LONG"))

        assert result is None or result.get("signal") is False
        logger_mock.error.assert_called()
