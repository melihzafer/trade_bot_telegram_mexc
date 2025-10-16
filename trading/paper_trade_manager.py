"""
Paper Trade Manager
Manages opening, tracking, and closing paper trading positions
"""
import math
import uuid
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import MAX_PROFIT_PCT, MAX_LOSS_PCT


class PaperTradeManager:
    """Manages paper trading positions and executions."""
    
    def __init__(self, portfolio):
        """Initialize trade manager with a portfolio."""
        self.portfolio = portfolio
    
    def generate_position_id(self):
        """Generate unique position ID."""
        return str(uuid.uuid4())[:8]
    
    def open_position(self, signal, channel_name="Unknown"):
        """
        Open a new paper trading position.
        
        Args:
            signal: Parsed signal object
            channel_name: Name of the source channel
            
        Returns:
            dict: Position object or None if invalid
        """
        # Validate signal
        if not signal.symbol or not signal.entry_min or not signal.side:
            print(f"⚠️ Invalid signal: missing required fields")
            return None
        
        # Calculate position size
        quantity = self.portfolio.calculate_position_size(signal)
        if quantity <= 0:
            print(f"⚠️ Position size too small or zero")
            return None
        
        # Calculate TP/SL
        stop_loss = self.portfolio.calculate_stop_loss(signal)
        take_profits = self.portfolio.calculate_take_profits(signal)
        
        # Get leverage
        leverage = signal.leverage_x or 15.0
        if leverage is None or math.isnan(leverage) or leverage <= 0:
            leverage = 15.0
        
        # Create position
        position = {
            'id': self.generate_position_id(),
            'symbol': signal.symbol,
            'side': signal.side,
            'entry_price': signal.entry_min,
            'quantity': quantity,
            'leverage': leverage,
            'stop_loss': stop_loss,
            'take_profits': take_profits,
            'tp_hit': [False, False, False],  # Track which TPs hit
            'entry_time': datetime.now(),
            'channel': channel_name,
            'status': 'OPEN',
            'current_pnl_pct': 0.0,
            'current_pnl_usd': 0.0,
            'highest_pnl_pct': 0.0,  # Track peak profit
            'lowest_pnl_pct': 0.0    # Track max drawdown
        }
        
        # Add to portfolio
        self.portfolio.open_positions[position['id']] = position
        
        print(f"✅ Opened {signal.side} {signal.symbol} @ {signal.entry_min:.4f}")
        print(f"   Quantity: {quantity:.4f} | Leverage: {leverage}x")
        print(f"   Stop Loss: {stop_loss:.4f}")
        print(f"   Take Profits: {', '.join(f'{tp:.4f}' for tp in take_profits)}")
        
        return position
    
    def check_stop_hit(self, position, current_price):
        """Check if stop loss is hit."""
        sl = position['stop_loss']
        side = position['side']
        
        if side.upper() == 'LONG':
            return current_price <= sl
        else:  # SHORT
            return current_price >= sl
    
    def check_tp_hit(self, position, current_price):
        """
        Check if any take profit level is hit.
        
        Returns:
            int or None: TP level hit (1, 2, or 3) or None
        """
        tps = position['take_profits']
        tp_hit = position['tp_hit']
        side = position['side']
        
        # Check TPs in order
        for i, tp in enumerate(tps):
            if tp_hit[i]:
                continue  # Already hit
            
            if side.upper() == 'LONG':
                if current_price >= tp:
                    position['tp_hit'][i] = True
                    return i + 1  # TP1, TP2, TP3
            else:  # SHORT
                if current_price <= tp:
                    position['tp_hit'][i] = True
                    return i + 1
        
        return None
    
    def close_position(self, position, exit_reason, exit_price):
        """
        Close a position and update portfolio.
        
        Args:
            position: Position dict
            exit_reason: Reason for exit (STOP_LOSS, TP1, TP2, TP3, MAX_PROFIT, MAX_LOSS)
            exit_price: Exit price
        """
        # Calculate final PnL
        pnl_pct, pnl_usd = self.portfolio.calculate_pnl(position, exit_price)
        
        # Update portfolio balance
        self.portfolio.balance += pnl_usd
        self.portfolio.total_pnl += pnl_usd
        self.portfolio.total_trades += 1
        
        if pnl_usd > 0:
            self.portfolio.winning_trades += 1
        else:
            self.portfolio.losing_trades += 1
        
        # Create trade record
        trade = {
            **position,
            'exit_price': exit_price,
            'exit_time': datetime.now(),
            'exit_reason': exit_reason,
            'pnl_pct': pnl_pct,
            'pnl_usd': pnl_usd,
            'duration_seconds': (datetime.now() - position['entry_time']).total_seconds(),
            'status': 'CLOSED'
        }
        
        # Add to closed trades
        self.portfolio.closed_trades.append(trade)
        
        # Remove from open positions
        del self.portfolio.open_positions[position['id']]
        
        # Log
        emoji = "🟢" if pnl_usd > 0 else "🔴"
        print(f"{emoji} Closed {position['side']} {position['symbol']} @ {exit_price:.4f}")
        print(f"   Reason: {exit_reason} | PnL: {pnl_pct:.2f}% (${pnl_usd:.2f})")
        print(f"   New Balance: ${self.portfolio.balance:.2f}")
        
        return trade
    
    def update_positions(self, current_prices):
        """
        Update all open positions with current prices and check for exits.
        
        Args:
            current_prices: Dict of {symbol: price}
            
        Returns:
            list: Closed trades in this update
        """
        closed_trades = []
        
        # Copy position IDs to avoid modification during iteration
        position_ids = list(self.portfolio.open_positions.keys())
        
        for pos_id in position_ids:
            # Check if position still exists (might have been closed)
            if pos_id not in self.portfolio.open_positions:
                continue
            
            position = self.portfolio.open_positions[pos_id]
            symbol = position['symbol']
            
            # Get current price
            current_price = current_prices.get(symbol)
            if not current_price:
                continue
            
            # Update current PnL
            pnl_pct, pnl_usd = self.portfolio.calculate_pnl(position, current_price)
            position['current_pnl_pct'] = pnl_pct
            position['current_pnl_usd'] = pnl_usd
            
            # Track highest/lowest PnL
            if pnl_pct > position['highest_pnl_pct']:
                position['highest_pnl_pct'] = pnl_pct
            if pnl_pct < position['lowest_pnl_pct']:
                position['lowest_pnl_pct'] = pnl_pct
            
            # Check for exits (priority order)
            
            # 1. Check max profit cap (100%)
            if pnl_pct >= MAX_PROFIT_PCT:
                trade = self.close_position(position, 'MAX_PROFIT', current_price)
                closed_trades.append(trade)
                continue
            
            # 2. Check max loss cap (-30%)
            if pnl_pct <= -MAX_LOSS_PCT:
                trade = self.close_position(position, 'MAX_LOSS', current_price)
                closed_trades.append(trade)
                continue
            
            # 3. Check stop loss
            if self.check_stop_hit(position, current_price):
                trade = self.close_position(position, 'STOP_LOSS', current_price)
                closed_trades.append(trade)
                continue
            
            # 4. Check take profits
            tp_level = self.check_tp_hit(position, current_price)
            if tp_level:
                trade = self.close_position(position, f'TP{tp_level}', current_price)
                closed_trades.append(trade)
                continue
        
        return closed_trades
    
    def get_open_positions_summary(self):
        """Get summary of all open positions."""
        positions = []
        for position in self.portfolio.open_positions.values():
            positions.append({
                'id': position['id'],
                'symbol': position['symbol'],
                'side': position['side'],
                'entry_price': position['entry_price'],
                'current_pnl_pct': position['current_pnl_pct'],
                'current_pnl_usd': position['current_pnl_usd'],
                'stop_loss': position['stop_loss'],
                'take_profits': position['take_profits'],
                'channel': position['channel'],
                'entry_time': position['entry_time']
            })
        return positions
