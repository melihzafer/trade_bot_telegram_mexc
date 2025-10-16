"""
Trade Logger
Records all paper trading activities to JSONL file
"""
import json
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import DATA_DIR


class TradeLogger:
    """Logs paper trading activities."""
    
    def __init__(self, log_path=None):
        """Initialize logger with output path."""
        if log_path is None:
            log_path = DATA_DIR / "paper_trades.jsonl"
        else:
            log_path = Path(log_path)
        
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_trade(self, trade):
        """
        Record a completed trade.
        
        Args:
            trade: Trade dict with all details
        """
        # Prepare record
        record = {
            'id': trade['id'],
            'timestamp_open': trade['entry_time'].isoformat(),
            'timestamp_close': trade['exit_time'].isoformat(),
            'symbol': trade['symbol'],
            'side': trade['side'],
            'entry_price': trade['entry_price'],
            'exit_price': trade['exit_price'],
            'quantity': trade['quantity'],
            'leverage': trade['leverage'],
            'stop_loss': trade['stop_loss'],
            'take_profits': trade['take_profits'],
            'tp_hit': trade['tp_hit'],
            'pnl_pct': trade['pnl_pct'],
            'pnl_usd': trade['pnl_usd'],
            'exit_reason': trade['exit_reason'],
            'channel': trade['channel'],
            'duration_seconds': trade['duration_seconds'],
            'highest_pnl_pct': trade.get('highest_pnl_pct', 0),
            'lowest_pnl_pct': trade.get('lowest_pnl_pct', 0)
        }
        
        # Write to file
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    def log_signal(self, signal, action="RECEIVED"):
        """
        Log signal reception or rejection.
        
        Args:
            signal: Parsed signal object
            action: Action taken (RECEIVED, REJECTED, OPENED)
        """
        signals_log = self.log_path.parent / "paper_signals.jsonl"
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'symbol': signal.symbol,
            'side': signal.side,
            'entry': signal.entry_min,
            'stop_loss': signal.sl,
            'take_profits': signal.tps,
            'leverage': signal.leverage_x,
            'confidence': signal.confidence,
            'source': signal.source
        }
        
        with open(signals_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    def load_trades(self):
        """
        Load all recorded trades from file.
        
        Returns:
            list: List of trade records
        """
        if not self.log_path.exists():
            return []
        
        trades = []
        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        trade = json.loads(line)
                        trades.append(trade)
                    except json.JSONDecodeError:
                        continue
        
        return trades
    
    def get_stats(self):
        """Get statistics from logged trades."""
        trades = self.load_trades()
        
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_pnl': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'largest_win': 0,
                'largest_loss': 0
            }
        
        total = len(trades)
        wins = [t for t in trades if t['pnl_usd'] > 0]
        losses = [t for t in trades if t['pnl_usd'] <= 0]
        
        total_pnl = sum(t['pnl_usd'] for t in trades)
        avg_pnl = total_pnl / total if total > 0 else 0
        
        avg_win = sum(t['pnl_usd'] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t['pnl_usd'] for t in losses) / len(losses) if losses else 0
        
        largest_win = max((t['pnl_usd'] for t in wins), default=0)
        largest_loss = min((t['pnl_usd'] for t in losses), default=0)
        
        return {
            'total_trades': total,
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': (len(wins) / total * 100) if total > 0 else 0,
            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss
        }
