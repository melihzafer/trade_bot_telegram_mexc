"""
Paper Portfolio Manager
Manages virtual trading portfolio with positions and balance tracking
"""
import math
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import (
    PAPER_INITIAL_BALANCE,
    PAPER_POSITION_SIZE_PCT,
    DEFAULT_LEVERAGE,
    MAX_LOSS_PCT,
    MAX_PROFIT_PCT,
    TP1_RATIO,
    TP2_RATIO,
    TP3_RATIO
)


class PaperPortfolio:
    """Virtual portfolio for paper trading."""
    
    def __init__(self, initial_balance=None):
        """Initialize portfolio with starting balance."""
        self.balance = initial_balance or PAPER_INITIAL_BALANCE
        self.initial_balance = self.balance
        self.open_positions = {}  # {position_id: position_dict}
        self.closed_trades = []
        self.total_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
    
    def get_available_balance(self):
        """Get balance not allocated to open positions."""
        allocated = sum(
            pos['entry_price'] * pos['quantity'] / pos['leverage']
            for pos in self.open_positions.values()
        )
        return self.balance - allocated
    
    def calculate_position_size(self, signal):
        """
        Calculate position size based on percentage of portfolio.
        
        Args:
            signal: Parsed signal object with entry, sl, leverage
            
        Returns:
            float: Position quantity in base currency
        """
        # Amount to risk (% of portfolio)
        risk_amount = self.balance * (PAPER_POSITION_SIZE_PCT / 1000)
        
        # Entry price
        entry = signal.entry_min
        if not entry or math.isnan(entry):
            return 0
        
        # Calculate stop loss
        sl = self.calculate_stop_loss(signal)
        
        # Risk per unit
        risk_per_unit = abs(entry - sl)
        if risk_per_unit == 0:
            return 0
        
        # Leverage
        leverage = signal.leverage_x or DEFAULT_LEVERAGE
        if leverage is None or math.isnan(leverage) or leverage <= 0:
            leverage = DEFAULT_LEVERAGE
        
        # Position size = (risk_amount / risk_per_unit) / entry_price
        quantity = risk_amount / risk_per_unit
        
        return quantity
    
    def calculate_stop_loss(self, signal):
        """
        Calculate stop loss price.
        If signal has SL, use it. Otherwise calculate -30% max loss based on leverage.
        
        Args:
            signal: Parsed signal object
            
        Returns:
            float: Stop loss price
        """
        # If signal has SL, use it
        if signal.sl and not math.isnan(signal.sl):
            return signal.sl
        
        # Calculate based on leverage
        leverage = signal.leverage_x or DEFAULT_LEVERAGE
        if leverage is None or math.isnan(leverage) or leverage <= 0:
            leverage = DEFAULT_LEVERAGE
        
        entry = signal.entry_min
        
        # Max loss % / leverage = max price move %
        # Example: 30% loss / 15x leverage = 2% price move
        max_price_move_pct = MAX_LOSS_PCT / leverage
        
        if signal.side.upper() == 'LONG':
            # For LONG: SL below entry
            sl = entry * (1 - max_price_move_pct / 100)
        else:  # SHORT
            # For SHORT: SL above entry
            sl = entry * (1 + max_price_move_pct / 100)
        
        return sl
    
    def calculate_take_profits(self, signal):
        """
        Calculate take profit levels.
        If signal has TPs, use them. Otherwise calculate based on R multiples (1R, 2R, 3R).
        
        Args:
            signal: Parsed signal object
            
        Returns:
            list: Take profit price levels [TP1, TP2, TP3]
        """
        # If signal has TPs, use them
        if signal.tps and len(signal.tps) > 0:
            # Filter out NaN values
            valid_tps = [tp for tp in signal.tps if not math.isnan(tp)]
            if valid_tps:
                return valid_tps
        
        # Calculate based on R multiples
        entry = signal.entry_min
        sl = self.calculate_stop_loss(signal)
        
        # R = risk (distance from entry to SL)
        risk = abs(entry - sl)
        
        if signal.side.upper() == 'LONG':
            tp1 = entry + risk * TP1_RATIO
            tp2 = entry + risk * TP2_RATIO
            tp3 = entry + risk * TP3_RATIO
        else:  # SHORT
            tp1 = entry - risk * TP1_RATIO
            tp2 = entry - risk * TP2_RATIO
            tp3 = entry - risk * TP3_RATIO
        
        return [tp1, tp2, tp3]
    
    def calculate_pnl(self, position, current_price):
        """
        Calculate current PnL for a position.
        
        Args:
            position: Position dict
            current_price: Current market price
            
        Returns:
            tuple: (pnl_pct, pnl_usd)
        """
        entry = position['entry_price']
        quantity = position['quantity']
        leverage = position['leverage']
        side = position['side']
        
        # Price change %
        if side.upper() == 'LONG':
            price_change_pct = ((current_price - entry) / entry) * 100
        else:  # SHORT
            price_change_pct = ((entry - current_price) / entry) * 100
        
        # PnL % (with leverage)
        pnl_pct = price_change_pct * leverage
        
        # PnL USD (based on margin, not notional)
        margin = entry * quantity / leverage
        pnl_usd = margin * (pnl_pct / 100)
        
        return pnl_pct, pnl_usd
    
    def get_stats(self):
        """Get portfolio statistics."""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.balance,
            'total_pnl': self.total_pnl,
            'total_pnl_pct': (self.total_pnl / self.initial_balance * 100),
            'open_positions': len(self.open_positions),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'available_balance': self.get_available_balance()
        }
