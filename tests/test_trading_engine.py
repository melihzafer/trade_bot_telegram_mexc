"""pytest test suite for trading.trading_engine.TradingEngine (CCXT live execution).

Safety:
- No real CCXT network calls (ccxt.mexc is always mocked).
- No real file I/O (Portfolio and queue loading are mocked).
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# Ensure project root is importable when running from repo root or tests/.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Provide minimal stubs for optional deps, so imports don't fail in lean test envs.

# --- pandas stub (trading/__init__.py imports backtester which imports pandas) ---
if "pandas" not in sys.modules:
    pandas_stub = ModuleType("pandas")

    class _DataFrame:  # pragma: no cover
        pass

    class _Series:  # pragma: no cover
        pass

    pandas_stub.DataFrame = _DataFrame  # type: ignore[attr-defined]
    pandas_stub.Series = _Series  # type: ignore[attr-defined]

    sys.modules["pandas"] = pandas_stub


# --- pytz stub (utils.timeutils imports pytz) ---
if "pytz" not in sys.modules:
    pytz_stub = ModuleType("pytz")

    class UnknownTimeZoneError(Exception):
        pass

    class _TZ:  # pragma: no cover
        def localize(self, dt):
            return dt

    def timezone(_name: str):
        return _TZ()

    pytz_stub.UnknownTimeZoneError = UnknownTimeZoneError  # type: ignore[attr-defined]
    pytz_stub.timezone = timezone  # type: ignore[attr-defined]
    pytz_stub.UTC = _TZ()  # type: ignore[attr-defined]

    sys.modules["pytz"] = pytz_stub


# --- dotenv stub (utils.config imports python-dotenv) ---
if "dotenv" not in sys.modules:
    dotenv_stub = ModuleType("dotenv")

    def load_dotenv(*args: Any, **kwargs: Any) -> None:  # pragma: no cover
        return None

    dotenv_stub.load_dotenv = load_dotenv  # type: ignore[attr-defined]
    sys.modules["dotenv"] = dotenv_stub


# --- ccxt.async_support stub ---
# NOTE: trading.trading_engine imports `ccxt.async_support as ccxt`.
if "ccxt.async_support" not in sys.modules:
    ccxt_pkg = ModuleType("ccxt")
    ccxt_async = ModuleType("ccxt.async_support")

    class InsufficientFunds(Exception):
        pass

    class InvalidOrder(Exception):
        pass

    class NetworkError(Exception):
        pass

    class ExchangeError(Exception):
        pass

    def mexc(*args: Any, **kwargs: Any):  # pragma: no cover
        raise AssertionError("ccxt.mexc should be patched in tests")

    ccxt_async.InsufficientFunds = InsufficientFunds  # type: ignore[attr-defined]
    ccxt_async.InvalidOrder = InvalidOrder  # type: ignore[attr-defined]
    ccxt_async.NetworkError = NetworkError  # type: ignore[attr-defined]
    ccxt_async.ExchangeError = ExchangeError  # type: ignore[attr-defined]
    ccxt_async.mexc = mexc  # type: ignore[attr-defined]

    ccxt_pkg.async_support = ccxt_async  # type: ignore[attr-defined]

    sys.modules["ccxt"] = ccxt_pkg
    sys.modules["ccxt.async_support"] = ccxt_async


class FakePortfolio:
    """In-memory portfolio stub to avoid disk writes during tests."""

    def __init__(self, initial_balance: float, portfolio_file: Path):
        self.initial_balance = initial_balance
        self.portfolio_file = portfolio_file

    def get_equity(self) -> float:
        return 10000.0

    def has_position(self, symbol: str) -> bool:
        return False

    def get_open_position_count(self) -> int:
        return 0

    def open_position(self, **kwargs: Any) -> bool:
        return True


@pytest.fixture()
def logger_mock() -> MagicMock:
    mock = MagicMock()
    mock.info = MagicMock()
    mock.warn = MagicMock()
    mock.error = MagicMock()
    mock.success = MagicMock()
    mock.debug = MagicMock()
    return mock


def _make_exchange_mock(last_price: float = 50000.0) -> MagicMock:
    exchange = MagicMock()
    exchange.fetch_ticker = AsyncMock(return_value={"last": last_price})
    exchange.set_leverage = AsyncMock(return_value=None)
    exchange.create_order = AsyncMock(return_value={"id": "order-1", "price": last_price, "fee": {"cost": 0.0}})
    return exchange


def _make_engine_live(
    *,
    monkeypatch: pytest.MonkeyPatch,
    logger_mock: MagicMock,
    exchange_mock: MagicMock,
    require_confirmation: bool = False,
    dry_run_first: bool = False,
):
    # LiveConfig defaults are safety-first; disable in tests to allow order placement.
    monkeypatch.setattr("trading.trading_engine.LiveConfig.REQUIRE_CONFIRMATION", require_confirmation, raising=False)
    monkeypatch.setattr("trading.trading_engine.LiveConfig.DRY_RUN_FIRST", dry_run_first, raising=False)
    monkeypatch.setattr("trading.trading_engine.LiveConfig.ENABLE_EMERGENCY_STOP", False, raising=False)

    # Provide API keys for exchange init.
    monkeypatch.setenv("MEXC_API_KEY", "live-key")
    monkeypatch.setenv("MEXC_API_SECRET", "live-secret")

    with patch("trading.trading_engine.logger", logger_mock), patch(
        "trading.trading_engine.Portfolio", FakePortfolio
    ), patch(
        "trading.trading_engine.TradingEngine._load_signal_queue", lambda self: None
    ), patch(
        "trading.trading_engine.TradingEngine._check_emergency_stop", lambda self: None
    ), patch(
        "trading.trading_engine.BinanceClient", None
    ), patch(
        "trading.trading_engine.ccxt.mexc", return_value=exchange_mock
    ):
        from trading.trading_engine import TradingEngine

        engine = TradingEngine(mode="live")
        engine._log_trade = MagicMock()  # prevent file writes
        return engine


def test_initialization_live(monkeypatch: pytest.MonkeyPatch, logger_mock: MagicMock) -> None:
    """Verify exchange is set up with correct API keys in LIVE mode."""
    exchange_mock = _make_exchange_mock()

    monkeypatch.setenv("MEXC_API_KEY", "k")
    monkeypatch.setenv("MEXC_API_SECRET", "s")

    with patch("trading.trading_engine.logger", logger_mock), patch(
        "trading.trading_engine.Portfolio", FakePortfolio
    ), patch(
        "trading.trading_engine.TradingEngine._load_signal_queue", lambda self: None
    ), patch(
        "trading.trading_engine.TradingEngine._check_emergency_stop", lambda self: None
    ), patch(
        "trading.trading_engine.BinanceClient", None
    ), patch(
        "trading.trading_engine.LiveConfig.ENABLE_EMERGENCY_STOP", False
    ), patch(
        "trading.trading_engine.ccxt.mexc", return_value=exchange_mock
    ) as mexc_ctor:
        from trading.trading_engine import TradingEngine

        engine = TradingEngine(mode="live")
        assert engine.exchange is exchange_mock

        mexc_ctor.assert_called_once()
        cfg = mexc_ctor.call_args.args[0]
        assert cfg["apiKey"] == "k"
        assert cfg["secret"] == "s"


def test_execute_signal_long(monkeypatch: pytest.MonkeyPatch, logger_mock: MagicMock) -> None:
    """Mock a LONG signal; verify create_order called with side='buy' and correct amount."""
    exchange_mock = _make_exchange_mock(last_price=50000.0)
    engine = _make_engine_live(monkeypatch=monkeypatch, logger_mock=logger_mock, exchange_mock=exchange_mock)

    from trading.trading_engine import Signal

    signal = Signal(symbol="BTC/USDT", side="LONG", entry=None, leverage=1)

    ok = asyncio.run(engine.execute_signal_live(signal))
    assert ok is True

    exchange_mock.create_order.assert_awaited_once()
    kwargs: Dict[str, Any] = exchange_mock.create_order.call_args.kwargs
    assert kwargs["symbol"] == "BTC/USDT"
    assert kwargs["type"] == "market"
    assert kwargs["side"] == "buy"

    # Expected: equity(10000) * max_pos_pct(0.10) / price(50000) = 0.02
    assert kwargs["amount"] == pytest.approx(0.02, rel=1e-6)


def test_execute_signal_short(monkeypatch: pytest.MonkeyPatch, logger_mock: MagicMock) -> None:
    """Mock a SHORT signal; verify create_order called with side='sell'."""
    exchange_mock = _make_exchange_mock(last_price=50000.0)
    engine = _make_engine_live(monkeypatch=monkeypatch, logger_mock=logger_mock, exchange_mock=exchange_mock)

    from trading.trading_engine import Signal

    signal = Signal(symbol="BTC/USDT", side="SHORT", entry=None, leverage=1)

    ok = asyncio.run(engine.execute_signal_live(signal))
    assert ok is True

    kwargs: Dict[str, Any] = exchange_mock.create_order.call_args.kwargs
    assert kwargs["side"] == "sell"


def test_leverage_setting(monkeypatch: pytest.MonkeyPatch, logger_mock: MagicMock) -> None:
    """Verify set_leverage is called before placing an order."""
    exchange_mock = _make_exchange_mock(last_price=50000.0)
    engine = _make_engine_live(monkeypatch=monkeypatch, logger_mock=logger_mock, exchange_mock=exchange_mock)

    from trading.trading_engine import Signal

    called = {"set_leverage": False}

    def _set_leverage(symbol: str, leverage: int) -> bool:
        called["set_leverage"] = True
        return True

    def _create_order(**kwargs: Any) -> Dict[str, Any]:
        assert called["set_leverage"] is True, "set_leverage must be called before create_order"
        return {"id": "order-2", "price": 50000.0, "fee": {"cost": 0.0}}

    engine.set_leverage = AsyncMock(side_effect=_set_leverage)
    exchange_mock.create_order = AsyncMock(side_effect=_create_order)

    signal = Signal(symbol="BTC/USDT", side="LONG", entry=None, leverage=10)

    ok = asyncio.run(engine.execute_signal_live(signal))
    assert ok is True

    engine.set_leverage.assert_awaited_once_with("BTC/USDT", 10)
    exchange_mock.create_order.assert_awaited_once()


def test_insufficient_funds(monkeypatch: pytest.MonkeyPatch, logger_mock: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
    """Mock ccxt.InsufficientFunds and ensure graceful handling (logs error, returns False)."""
    import logging

    caplog.set_level(logging.ERROR)

    exchange_mock = _make_exchange_mock(last_price=50000.0)
    engine = _make_engine_live(monkeypatch=monkeypatch, logger_mock=logger_mock, exchange_mock=exchange_mock)

    from trading.trading_engine import Signal, ccxt

    exchange_mock.create_order = AsyncMock(side_effect=ccxt.InsufficientFunds("no money"))

    signal = Signal(symbol="BTC/USDT", side="LONG", entry=None, leverage=1)

    ok = asyncio.run(engine.execute_signal_live(signal))
    assert ok is False
    assert any("Insufficient funds" in rec.getMessage() for rec in caplog.records)
