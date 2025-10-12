"""
Trading engine module.

Components:
- models: Pydantic data models (Signal, Order, Candle, BacktestResult)
- backtester: Historical signal testing
- paper_trader: Live paper trading simulation
- risk_manager: Position and risk limit enforcement
"""

from .models import Signal, Order, Candle, BacktestResult
from .backtester import run_backtest
from .paper_trader import PaperTrader
from .risk_manager import RiskManager

__all__ = [
    # Models
    "Signal",
    "Order",
    "Candle",
    "BacktestResult",
    # Functions
    "run_backtest",
    # Classes
    "PaperTrader",
    "RiskManager",
]
