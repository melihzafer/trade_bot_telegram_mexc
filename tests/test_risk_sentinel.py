"""pytest test suite for trading.risk_manager.RiskSentinel.

Safety:
- No real exchange/network calls (ccxt is stubbed for import-time safety).
- Kill switch is simulated via mocking Path.exists (no real file required).

Covers Phase 3 scenarios:
- Circuit breaker (5% daily loss) => can_trade() is False
- Whitelist rejection
- Kill switch file rejection
- Risk-based position sizing math
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from unittest.mock import patch


# Ensure project root is importable when running from repo root or tests/.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Provide minimal stubs for optional deps, so importing `trading` doesn't fail
# in lean test environments.

# --- dotenv stub (utils.config imports python-dotenv) ---
if "dotenv" not in sys.modules:
    dotenv_stub = ModuleType("dotenv")

    def load_dotenv(*args: Any, **kwargs: Any) -> None:  # pragma: no cover
        return None

    dotenv_stub.load_dotenv = load_dotenv  # type: ignore[attr-defined]
    sys.modules["dotenv"] = dotenv_stub


# --- rich stub (utils.logger imports rich) ---
if "rich" not in sys.modules:
    rich_stub = ModuleType("rich")
    rich_console = ModuleType("rich.console")
    rich_table = ModuleType("rich.table")

    class Console:  # pragma: no cover
        def log(self, *args: Any, **kwargs: Any) -> None:
            return None

    class Table:  # pragma: no cover
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            return None

    rich_console.Console = Console  # type: ignore[attr-defined]
    rich_table.Table = Table  # type: ignore[attr-defined]

    sys.modules["rich"] = rich_stub
    sys.modules["rich.console"] = rich_console
    sys.modules["rich.table"] = rich_table


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


# --- ccxt stub (trading/__init__.py imports backtester/paper_trader which import ccxt) ---
if "ccxt" not in sys.modules:
    ccxt_stub = ModuleType("ccxt")

    def mexc(*args: Any, **kwargs: Any):  # pragma: no cover
        raise AssertionError("ccxt.mexc should never be called in unit tests")

    ccxt_stub.mexc = mexc  # type: ignore[attr-defined]
    sys.modules["ccxt"] = ccxt_stub


from trading.risk_manager import RiskSentinel


def test_circuit_breaker_trigger(tmp_path: Path) -> None:
    """Simulate losses beyond 5% daily limit; can_trade() must return False."""
    sentinel = RiskSentinel(initial_equity=10000, config_file=tmp_path / "risk_config.json")

    sentinel.update_equity(9400)  # -6%
    assert sentinel.check_circuit_breaker() is True
    assert sentinel.circuit_breaker_active is True
    assert sentinel.can_trade() is False


def test_whitelist_rejection(tmp_path: Path) -> None:
    """Reject symbol not present in whitelist."""
    sentinel = RiskSentinel(initial_equity=10000, config_file=tmp_path / "risk_config.json")

    result = sentinel.validate_signal(
        symbol="SHITCOIN_USDT",
        side="LONG",
        entry=100.0,
        sl=90.0,
        tp=120.0,
    )

    assert result.valid is False
    assert "whitelist" in result.reason.lower()


def test_kill_switch_file(tmp_path: Path) -> None:
    """Mock existence of STOP_TRADING file; validation must fail immediately."""
    stop_file = tmp_path / "STOP_TRADING"

    # Patch Path.exists so ONLY stop_file appears to exist.
    original_exists = Path.exists

    def exists_side_effect(self: Path) -> bool:  # pragma: no cover
        if self == stop_file:
            return True
        return original_exists(self)

    with patch("pathlib.Path.exists", new=exists_side_effect):
        sentinel = RiskSentinel(initial_equity=10000, config_file=tmp_path / "risk_config.json")
        sentinel.kill_switch_file = stop_file

        assert sentinel.can_trade() is False

        result = sentinel.validate_signal(
            symbol="BTCUSDT",
            side="LONG",
            entry=100.0,
            sl=90.0,
            tp=120.0,
        )

        assert result.valid is False
        assert "kill switch" in result.reason.lower()


def test_position_sizing_risk(tmp_path: Path) -> None:
    """$10k equity, 1% risk, entry=100, SL=90 => $100 risk / $10 per unit => 10 qty ($1000 position)."""
    sentinel = RiskSentinel(initial_equity=10000, config_file=tmp_path / "risk_config.json")

    sizing = sentinel.calculate_safe_quantity(
        equity=10000,
        entry_price=100,
        sl_price=90,
        risk_pct=0.01,
    )

    assert sizing["risk_amount"] == pytest.approx(100.0)
    assert sizing["quantity"] == pytest.approx(10.0)
    assert sizing["position_value"] == pytest.approx(1000.0)
