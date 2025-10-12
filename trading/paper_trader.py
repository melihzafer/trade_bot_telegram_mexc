"""
Paper Trader - simulates live trading with virtual positions.
Uses ccxt public API for live pricing, no real orders placed.
"""
import asyncio
import ccxt
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid

from utils.config import (
    DATA_DIR,
    ACCOUNT_EQUITY_USDT,
    RISK_PER_TRADE_PCT,
    LEVERAGE,
    MAX_CONCURRENT_POSITIONS,
)
from utils.logger import info, warn, error, success
from trading.models import Order

PARSED_PATH = DATA_DIR / "signals_parsed.csv"


class PaperExchange:
    """Wrapper around ccxt for fetching live market data."""

    def __init__(self):
        self.exchange = ccxt.mexc()

    def last_price(self, symbol: str) -> float:
        """
        Get latest price for a symbol.

        Args:
            symbol: Trading pair (e.g., BTCUSDT)

        Returns:
            Latest price as float
        """
        try:
            ccxt_symbol = symbol.replace("USDT", "/USDT")
            ticker = self.exchange.fetch_ticker(ccxt_symbol)
            return float(ticker.get("last") or ticker.get("close", 0))
        except Exception as e:
            error(f"Error fetching price for {symbol}: {e}")
            return 0.0


class PaperTrader:
    """
    Virtual trading engine.
    Manages paper positions, calculates PnL, enforces risk limits.
    """

    def __init__(self):
        self.cash = ACCOUNT_EQUITY_USDT
        self.initial_cash = ACCOUNT_EQUITY_USDT
        self.positions: List[Dict[str, Any]] = []
        self.exchange = PaperExchange()
        self.closed_trades: List[Order] = []

    def calculate_position_size(self, entry_price: float, sl_price: Optional[float] = None) -> float:
        """
        Calculate position size based on risk management rules.

        Args:
            entry_price: Entry price for the trade
            sl_price: Stop loss price (optional)

        Returns:
            Position size in base asset units
        """
        risk_usdt = self.cash * (RISK_PER_TRADE_PCT / 100.0)

        if sl_price and sl_price != entry_price:
            # Calculate size based on risk and stop distance
            risk_distance = abs(entry_price - sl_price)
            nominal = risk_usdt / risk_distance
        else:
            # Default: 1% of entry as risk distance
            nominal = risk_usdt / (entry_price * 0.01)

        # Apply leverage
        base_qty = (nominal * LEVERAGE) / entry_price

        return round(base_qty, 6)

    def open_position(self, signal: Dict[str, Any]):
        """
        Open a new paper position from a signal.

        Args:
            signal: Parsed signal dict with symbol, side, entry, tp, sl
        """
        if len(self.positions) >= MAX_CONCURRENT_POSITIONS:
            warn(f"⚠️  Max concurrent positions ({MAX_CONCURRENT_POSITIONS}) reached. Skipping signal.")
            return

        symbol = signal["symbol"]
        side = signal["side"]
        entry = signal.get("entry")

        # Get live price if no entry specified
        if not entry:
            entry = self.exchange.last_price(symbol)
            if entry == 0:
                error(f"Failed to get price for {symbol}")
                return

        # Calculate position size
        qty = self.calculate_position_size(entry, signal.get("sl"))

        # Create position
        position = {
            "id": str(uuid.uuid4())[:8],
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "entry": entry,
            "tp": signal.get("tp"),
            "sl": signal.get("sl"),
            "opened_at": datetime.utcnow(),
            "pnl": 0.0,
        }

        self.positions.append(position)
        info(f"📈 OPEN {side} {symbol} | Qty: {qty:.6f} @ ${entry:.2f} | TP: {signal.get('tp')} | SL: {signal.get('sl')}")

    def update_positions(self):
        """
        Update all open positions with current prices and check TP/SL.
        Closes positions if TP or SL is hit.
        """
        closed_positions = []

        for pos in self.positions:
            symbol = pos["symbol"]
            side = pos["side"]
            entry = pos["entry"]
            qty = pos["qty"]
            tp = pos.get("tp")
            sl = pos.get("sl")

            # Get current price
            current_price = self.exchange.last_price(symbol)
            if current_price == 0:
                continue

            # Calculate unrealized PnL
            if side == "BUY":
                pnl = (current_price - entry) * qty
            else:  # SELL
                pnl = (entry - current_price) * qty

            pos["pnl"] = pnl

            # Check TP/SL
            should_close = False
            close_reason = ""

            if side == "BUY":
                if tp and current_price >= tp:
                    should_close = True
                    close_reason = "TP HIT"
                elif sl and current_price <= sl:
                    should_close = True
                    close_reason = "SL HIT"
            else:  # SELL
                if tp and current_price <= tp:
                    should_close = True
                    close_reason = "TP HIT"
                elif sl and current_price >= sl:
                    should_close = True
                    close_reason = "SL HIT"

            if should_close:
                self.close_position(pos, current_price, close_reason)
                closed_positions.append(pos)

        # Remove closed positions
        for pos in closed_positions:
            self.positions.remove(pos)

    def close_position(self, pos: Dict[str, Any], close_price: float, reason: str):
        """
        Close a position and record PnL.

        Args:
            pos: Position dict
            close_price: Closing price
            reason: Reason for closing (TP HIT, SL HIT, etc.)
        """
        symbol = pos["symbol"]
        side = pos["side"]
        entry = pos["entry"]
        qty = pos["qty"]

        # Calculate realized PnL
        if side == "BUY":
            pnl = (close_price - entry) * qty
        else:
            pnl = (entry - close_price) * qty

        # Update cash
        self.cash += pnl

        # Create closed order record
        order = Order(
            id=pos["id"],
            signal_id=symbol,
            symbol=symbol,
            side=side,
            qty=qty,
            entry_price=entry,
            sl=pos.get("sl"),
            tp=pos.get("tp"),
            opened_at=pos["opened_at"],
            closed_at=datetime.utcnow(),
            status="CLOSED",
            pnl_usdt=pnl,
        )

        self.closed_trades.append(order)

        # Log closure
        pnl_pct = (pnl / (entry * qty)) * 100
        pnl_color = "green" if pnl > 0 else "red"
        success(
            f"💰 CLOSE {side} {symbol} | {reason} @ ${close_price:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)"
        )

    def print_status(self):
        """Print current account status."""
        total_pnl = self.cash - self.initial_cash
        pnl_pct = (total_pnl / self.initial_cash) * 100

        info(f"\n{'='*60}")
        info(f"💼 Paper Trading Account Status")
        info(f"{'='*60}")
        info(f"💰 Current Cash: ${self.cash:.2f}")
        info(f"📊 Total PnL: ${total_pnl:+.2f} ({pnl_pct:+.2f}%)")
        info(f"📈 Open Positions: {len(self.positions)}")
        info(f"✅ Closed Trades: {len(self.closed_trades)}")

        if self.closed_trades:
            wins = sum(1 for t in self.closed_trades if t.pnl_usdt > 0)
            losses = sum(1 for t in self.closed_trades if t.pnl_usdt < 0)
            win_rate = (wins / len(self.closed_trades)) * 100 if self.closed_trades else 0
            info(f"🎯 Win Rate: {win_rate:.2f}% ({wins}W / {losses}L)")

        info(f"{'='*60}\n")


async def run_paper():
    """
    Main paper trading loop.
    Loads parsed signals and simulates trading with position management.
    """
    import pandas as pd

    if not PARSED_PATH.exists():
        warn(f"Parsed signals file not found: {PARSED_PATH}")
        return

    trader = PaperTrader()
    df = pd.read_csv(PARSED_PATH)

    info(f"🚀 Starting paper trader with {len(df)} signals")

    # Open initial positions (for demo purposes)
    for idx, row in df.head(5).iterrows():  # Test with first 5 signals
        signal = row.to_dict()
        trader.open_position(signal)
        await asyncio.sleep(0.5)

    # Monitor positions
    info("🔄 Monitoring positions...")
    for _ in range(60):  # Monitor for 60 cycles (~2 minutes)
        trader.update_positions()
        trader.print_status()
        await asyncio.sleep(2)

    info("✅ Paper trading session complete")


if __name__ == "__main__":
    asyncio.run(run_paper())
