"""
💼 Portfolio Manager
Tracks balance, positions, and performance across all trading modes.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, asdict
from utils.logger import info, warn, error, success


@dataclass
class Position:
    """Open trading position."""
    symbol: str
    side: Literal["LONG", "SHORT"]
    entry_price: float
    quantity: float
    entry_time: str
    tp: Optional[float] = None
    sl: Optional[float] = None
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def update_pnl(self, current_price: float):
        """Update unrealized PnL."""
        self.current_price = current_price
        
        if self.side == "LONG":
            pnl = (current_price - self.entry_price) * self.quantity
            pnl_pct = ((current_price / self.entry_price) - 1) * 100
        else:  # SHORT
            pnl = (self.entry_price - current_price) * self.quantity
            pnl_pct = ((self.entry_price / current_price) - 1) * 100
        
        self.unrealized_pnl = pnl
        self.unrealized_pnl_pct = pnl_pct


@dataclass
class Trade:
    """Closed trade record."""
    symbol: str
    side: Literal["LONG", "SHORT"]
    entry_price: float
    exit_price: float
    quantity: float
    entry_time: str
    exit_time: str
    exit_reason: Literal["TP", "SL", "MANUAL"]
    pnl: float
    pnl_pct: float
    fees: float
    net_pnl: float
    
    def to_dict(self) -> dict:
        return asdict(self)


class Portfolio:
    """Portfolio manager for paper/live trading."""
    
    def __init__(self, initial_balance: float, portfolio_file: Path):
        self.initial_balance = initial_balance
        self.portfolio_file = portfolio_file
        
        # Portfolio state
        self.balance: float = initial_balance
        self.positions: Dict[str, Position] = {}
        self.closed_trades: List[Trade] = []
        
        # Performance metrics
        self.total_pnl: float = 0.0
        self.total_fees: float = 0.0
        self.win_count: int = 0
        self.loss_count: int = 0
        
        # Load existing portfolio
        self.load()
    
    def load(self):
        """Load portfolio from disk."""
        if not self.portfolio_file.exists():
            info("📂 No existing portfolio found, starting fresh")
            return
        
        try:
            with open(self.portfolio_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.balance = data.get('balance', self.initial_balance)
            self.total_pnl = data.get('total_pnl', 0.0)
            self.total_fees = data.get('total_fees', 0.0)
            self.win_count = data.get('win_count', 0)
            self.loss_count = data.get('loss_count', 0)
            
            # Load positions
            for pos_data in data.get('positions', []):
                pos = Position(**pos_data)
                self.positions[pos.symbol] = pos
            
            # Load closed trades
            for trade_data in data.get('closed_trades', []):
                self.closed_trades.append(Trade(**trade_data))
            
            info(f"✅ Loaded portfolio: ${self.balance:,.2f} balance, {len(self.positions)} open positions")
        
        except Exception as e:
            error(f"❌ Failed to load portfolio: {e}")
    
    def save(self):
        """Save portfolio to disk."""
        try:
            data = {
                'balance': self.balance,
                'initial_balance': self.initial_balance,
                'total_pnl': self.total_pnl,
                'total_fees': self.total_fees,
                'win_count': self.win_count,
                'loss_count': self.loss_count,
                'positions': [pos.to_dict() for pos in self.positions.values()],
                'closed_trades': [trade.to_dict() for trade in self.closed_trades[-100:]],  # Last 100
                'last_updated': datetime.now().isoformat()
            }
            
            self.portfolio_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.portfolio_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            error(f"❌ Failed to save portfolio: {e}")
    
    def open_position(self, symbol: str, side: str, entry_price: float, 
                     quantity: float, tp: float = None, sl: float = None, 
                     margin_required: float = None):
        """Open a new position."""
        if symbol in self.positions:
            warn(f"⚠️ Position already exists for {symbol}")
            return False
        
        position = Position(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            entry_time=datetime.now().isoformat(),
            tp=tp,
            sl=sl
        )
        
        # Deduct margin from balance (not full notional value if leveraged)
        # If margin_required is provided, use it (for leveraged trades)
        # Otherwise, use full position value (spot trades)
        cost = margin_required if margin_required is not None else (entry_price * quantity)
        
        if cost > self.balance:
            error(f"❌ Insufficient balance: ${self.balance:.2f} < ${cost:.2f}")
            return False
        
        self.balance -= cost
        self.positions[symbol] = position
        
        notional = entry_price * quantity
        success(f"✅ Opened {side} {symbol} @ ${entry_price:.4f} x {quantity:.4f} (margin: ${cost:.2f}, notional: ${notional:.2f})")
        self.save()
        return True
    
    def close_position(self, symbol: str, exit_price: float, 
                      exit_reason: str, fees: float = 0.0):
        """Close an existing position."""
        if symbol not in self.positions:
            warn(f"⚠️ No position found for {symbol}")
            return False
        
        position = self.positions[symbol]
        
        # Calculate PnL
        if position.side == "LONG":
            pnl = (exit_price - position.entry_price) * position.quantity
            pnl_pct = ((exit_price / position.entry_price) - 1) * 100
        else:  # SHORT
            pnl = (position.entry_price - exit_price) * position.quantity
            pnl_pct = ((position.entry_price / exit_price) - 1) * 100
        
        net_pnl = pnl - fees
        
        # Return capital + PnL to balance
        position_value = position.entry_price * position.quantity
        self.balance += position_value + net_pnl
        
        # Update metrics
        self.total_pnl += net_pnl
        self.total_fees += fees
        
        if net_pnl > 0:
            self.win_count += 1
            emoji = "🟢"
        else:
            self.loss_count += 1
            emoji = "🔴"
        
        # Create trade record
        trade = Trade(
            symbol=symbol,
            side=position.side,
            entry_price=position.entry_price,
            exit_price=exit_price,
            quantity=position.quantity,
            entry_time=position.entry_time,
            exit_time=datetime.now().isoformat(),
            exit_reason=exit_reason,
            pnl=pnl,
            pnl_pct=pnl_pct,
            fees=fees,
            net_pnl=net_pnl
        )
        
        self.closed_trades.append(trade)
        del self.positions[symbol]
        
        info(f"{emoji} Closed {position.side} {symbol} @ ${exit_price:.4f} | "
             f"PnL: ${net_pnl:+.2f} ({pnl_pct:+.2f}%) | Reason: {exit_reason}")
        
        self.save()
        return True
    
    def update_positions(self, prices: Dict[str, float]):
        """Update unrealized PnL for all positions."""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].update_pnl(price)
        
        self.save()
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position by symbol."""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, Position]:
        """Get all open positions."""
        return self.positions
    
    def has_position(self, symbol: str) -> bool:
        """Check if position exists."""
        return symbol in self.positions
    
    def get_open_position_count(self) -> int:
        """Get number of open positions."""
        return len(self.positions)
    
    def get_equity(self) -> float:
        """Get total equity (balance + unrealized PnL)."""
        unrealized = sum(
            pos.unrealized_pnl or 0.0 
            for pos in self.positions.values()
        )
        return self.balance + unrealized
    
    def get_win_rate(self) -> float:
        """Calculate win rate percentage."""
        total = self.win_count + self.loss_count
        if total == 0:
            return 0.0
        return (self.win_count / total) * 100
    
    def get_summary(self) -> dict:
        """Get portfolio summary."""
        equity = self.get_equity()
        total_return_pct = ((equity / self.initial_balance) - 1) * 100
        
        return {
            'balance': self.balance,
            'initial_balance': self.initial_balance,
            'equity': equity,
            'total_pnl': self.total_pnl,
            'total_fees': self.total_fees,
            'total_return_pct': total_return_pct,
            'open_positions': len(self.positions),
            'total_trades': len(self.closed_trades),
            'win_count': self.win_count,
            'loss_count': self.loss_count,
            'win_rate': self.get_win_rate(),
        }
    
    def get_statistics(self) -> dict:
        """
        Get detailed portfolio statistics (alias for get_summary with additional fields).
        Used by main_autonomous.py for daily reports.
        """
        summary = self.get_summary()
        
        # Add additional statistics
        summary['total_trades'] = len(self.closed_trades)
        summary['winning_trades'] = self.win_count
        summary['losing_trades'] = self.loss_count
        summary['total_pnl_realized'] = self.total_pnl
        
        # Calculate largest win/loss
        if self.closed_trades:
            summary['largest_win'] = max((t.net_pnl for t in self.closed_trades), default=0.0)
            summary['largest_loss'] = min((t.net_pnl for t in self.closed_trades), default=0.0)
        else:
            summary['largest_win'] = 0.0
            summary['largest_loss'] = 0.0
        
        return summary
    
    def print_summary(self):
        """Print portfolio summary."""
        summary = self.get_summary()
        
        print("\n" + "="*80)
        print("💼 PORTFOLIO SUMMARY")
        print("="*80)
        print(f"Balance:          ${summary['balance']:>12,.2f}")
        print(f"Equity:           ${summary['equity']:>12,.2f}")
        print(f"Total PnL:        ${summary['total_pnl']:>12,.2f}")
        print(f"Total Return:     {summary['total_return_pct']:>12.2f}%")
        print(f"Total Fees:       ${summary['total_fees']:>12,.2f}")
        print("-" * 80)
        print(f"Open Positions:   {summary['open_positions']:>12}")
        print(f"Total Trades:     {summary['total_trades']:>12}")
        print(f"Wins:             {summary['win_count']:>12}")
        print(f"Losses:           {summary['loss_count']:>12}")
        print(f"Win Rate:         {summary['win_rate']:>12.1f}%")
        print("="*80)
        
        if self.positions:
            print("\n📊 OPEN POSITIONS:")
            for pos in self.positions.values():
                pnl_str = f"${pos.unrealized_pnl:+.2f}" if pos.unrealized_pnl else "N/A"
                pnl_pct_str = f"({pos.unrealized_pnl_pct:+.2f}%)" if pos.unrealized_pnl_pct else ""
                print(f"  {pos.side:5} {pos.symbol:12} @ ${pos.entry_price:.4f} | "
                      f"PnL: {pnl_str:>10} {pnl_pct_str}")


if __name__ == "__main__":
    # Test portfolio
    from config.trading_config import PaperConfig
    
    portfolio = Portfolio(
        initial_balance=10000.0,
        portfolio_file=PaperConfig.PORTFOLIO_FILE
    )
    
    # Simulate some trades
    portfolio.open_position("BTCUSDT", "LONG", 50000, 0.1, tp=52000, sl=48000)
    portfolio.open_position("ETHUSDT", "LONG", 3000, 0.5, tp=3200, sl=2900)
    
    # Update prices
    portfolio.update_positions({
        "BTCUSDT": 51000,
        "ETHUSDT": 3100
    })
    
    # Close one position
    portfolio.close_position("BTCUSDT", 51000, "TP", fees=5.0)
    
    # Print summary
    portfolio.print_summary()
