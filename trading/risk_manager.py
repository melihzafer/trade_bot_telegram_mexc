"""
Risk Manager - enforces risk limits and position sizing rules.
Prevents excessive losses and ensures safe trading practices.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta

from utils.config import (
    ACCOUNT_EQUITY_USDT,
    DAILY_MAX_LOSS_PCT,
    MAX_CONCURRENT_POSITIONS,
    RISK_PER_TRADE_PCT,
    LEVERAGE,
)
from utils.logger import warn, error


class RiskManager:
    """
    Manages trading risk and enforces limits.
    """

    def __init__(self, initial_equity: float = ACCOUNT_EQUITY_USDT):
        self.initial_equity = initial_equity
        self.equity_start_of_day = initial_equity
        self.current_equity = initial_equity
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.utcnow().date()

    def reset_daily_counters(self):
        """Reset daily tracking counters at the start of a new day."""
        today = datetime.utcnow().date()
        if today > self.last_reset_date:
            self.equity_start_of_day = self.current_equity
            self.daily_pnl = 0.0
            self.last_reset_date = today

    def update_equity(self, new_equity: float):
        """
        Update current equity and calculate daily PnL.

        Args:
            new_equity: Updated account equity
        """
        self.reset_daily_counters()
        self.current_equity = new_equity
        self.daily_pnl = new_equity - self.equity_start_of_day

    def check_daily_loss_limit(self) -> bool:
        """
        Check if daily loss limit has been breached.

        Returns:
            True if trading should stop, False otherwise
        """
        self.reset_daily_counters()
        max_daily_loss = self.equity_start_of_day * (DAILY_MAX_LOSS_PCT / 100.0)

        if self.daily_pnl <= -max_daily_loss:
            error(
                f"🛑 DAILY LOSS LIMIT REACHED: ${self.daily_pnl:.2f} "
                f"(Max: -${max_daily_loss:.2f})"
            )
            return True

        return False

    def check_position_limit(self, current_positions: int) -> bool:
        """
        Check if maximum concurrent positions limit is reached.

        Args:
            current_positions: Number of currently open positions

        Returns:
            True if limit reached, False otherwise
        """
        if current_positions >= MAX_CONCURRENT_POSITIONS:
            warn(
                f"⚠️  Position limit reached: {current_positions}/{MAX_CONCURRENT_POSITIONS}"
            )
            return True
        return False

    def calculate_position_size(
        self,
        entry_price: float,
        sl_price: float = None,
        risk_pct: float = None,
    ) -> float:
        """
        Calculate position size based on risk parameters.

        Args:
            entry_price: Entry price for the position
            sl_price: Stop loss price (optional)
            risk_pct: Risk percentage override (uses config default if None)

        Returns:
            Position size in base asset units
        """
        risk_pct = risk_pct or RISK_PER_TRADE_PCT
        risk_amount = self.current_equity * (risk_pct / 100.0)

        if sl_price and sl_price != entry_price:
            # Risk-based position sizing
            risk_per_unit = abs(entry_price - sl_price)
            position_size = risk_amount / risk_per_unit
        else:
            # Default: use 1% of entry as risk distance
            risk_per_unit = entry_price * 0.01
            position_size = risk_amount / risk_per_unit

        # Apply leverage
        position_size_with_leverage = (position_size * LEVERAGE) / entry_price

        return round(position_size_with_leverage, 6)

    def validate_order(
        self,
        symbol: str,
        side: str,
        entry: float,
        sl: float = None,
        tp: float = None,
    ) -> Dict[str, Any]:
        """
        Validate an order against risk rules.

        Args:
            symbol: Trading pair
            side: BUY or SELL
            entry: Entry price
            sl: Stop loss price
            tp: Take profit price

        Returns:
            Dict with 'valid' bool and 'reason' string
        """
        # Check daily loss limit
        if self.check_daily_loss_limit():
            return {"valid": False, "reason": "Daily loss limit reached"}

        # Validate price sanity
        if entry <= 0:
            return {"valid": False, "reason": "Invalid entry price"}

        if sl and sl <= 0:
            return {"valid": False, "reason": "Invalid stop loss price"}

        if tp and tp <= 0:
            return {"valid": False, "reason": "Invalid take profit price"}

        # Validate TP/SL relationship
        if side == "BUY":
            if sl and sl >= entry:
                return {"valid": False, "reason": "Stop loss must be below entry for BUY"}
            if tp and tp <= entry:
                return {"valid": False, "reason": "Take profit must be above entry for BUY"}
        elif side == "SELL":
            if sl and sl <= entry:
                return {"valid": False, "reason": "Stop loss must be above entry for SELL"}
            if tp and tp >= entry:
                return {"valid": False, "reason": "Take profit must be below entry for SELL"}

        # All checks passed
        return {"valid": True, "reason": "Order validated"}

    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Get current risk metrics for monitoring.

        Returns:
            Dict with risk statistics
        """
        self.reset_daily_counters()

        max_daily_loss = self.equity_start_of_day * (DAILY_MAX_LOSS_PCT / 100.0)
        remaining_daily_risk = max_daily_loss + self.daily_pnl

        return {
            "current_equity": self.current_equity,
            "daily_pnl": self.daily_pnl,
            "daily_pnl_pct": (self.daily_pnl / self.equity_start_of_day) * 100,
            "max_daily_loss": max_daily_loss,
            "remaining_daily_risk": remaining_daily_risk,
            "risk_per_trade_pct": RISK_PER_TRADE_PCT,
            "max_positions": MAX_CONCURRENT_POSITIONS,
            "leverage": LEVERAGE,
        }


if __name__ == "__main__":
    # Test risk manager
    rm = RiskManager(initial_equity=1000)

    print("Initial metrics:", rm.get_risk_metrics())

    # Simulate loss
    rm.update_equity(950)
    print("After -$50 loss:", rm.get_risk_metrics())

    # Check daily limit
    rm.update_equity(900)
    if rm.check_daily_loss_limit():
        print("Daily loss limit would trigger at $900")
