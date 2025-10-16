"""
Backtest Engine - Simulates signal execution with historical price data.
Calculates profit/loss for each signal considering entry, take-profit, stop-loss.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import info, success, warn, error


class BacktestEngine:
    """
    Backtests trading signals against historical price data.
    """
    
    def __init__(self, price_cache_dir: Path):
        """
        Initialize backtest engine.
        
        Args:
            price_cache_dir: Directory with cached price data
        """
        self.price_cache_dir = price_cache_dir
        info("🧪 Backtest Engine initialized")
    
    def load_price_data(self, symbol: str, timestamp: datetime) -> Optional[Dict]:
        """
        Load cached price data for a signal.
        
        Args:
            symbol: Trading symbol
            timestamp: Signal timestamp
            
        Returns:
            Price data dict or None
        """
        date_str = timestamp.strftime("%Y-%m-%d")
        cache_file = self.price_cache_dir / f"{symbol}_{date_str}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                warn(f"⚠️ Error loading price data: {e}")
        
        return None
    
    def simulate_trade(self, signal: Dict, price_data: Dict) -> Dict:
        """
        Simulate a single trade execution.
        
        Strategy:
        1. Enter at entry_max (worst case for LONG, best for SHORT)
        2. Check if price reached any TP levels (take first TP hit)
        3. Check if price hit SL (stop loss)
        4. Calculate profit/loss based on leverage
        
        Args:
            signal: Parsed signal dict
            price_data: Historical price data
            
        Returns:
            Dict with trade result
        """
        direction = signal.get('direction')
        entry_min = signal.get('entry_min')
        entry_max = signal.get('entry_max')
        stop_loss = signal.get('stop_loss')
        take_profits = signal.get('take_profits', [])
        leverage = signal.get('leverage')
        
        # Default leverage to 1 if None
        if leverage is None:
            leverage = 1
        
        # Get price data
        price_high = price_data.get('high')
        price_low = price_data.get('low')
        price_close = price_data.get('close')
        
        # Initialize result early for error handling
        result = {
            'status': 'unknown',
            'entry_price': None,
            'exit_price': None,
            'pnl_percent': 0.0,
            'pnl_leveraged': 0.0,
            'hit_tp': None,
            'hit_sl': False,
            'reason': ''
        }
        
        # Validate price data
        if None in [price_high, price_low, price_close]:
            result['status'] = 'error'
            result['reason'] = 'Invalid price data (None values)'
            return result
        
        # Use conservative entry (worst case)
        entry_price = entry_max if direction == 'LONG' else entry_min
        
        # Validate entry price
        if entry_price is None:
            result['status'] = 'error'
            result['reason'] = 'Invalid entry price (None)'
            return result
        
        # Update result with validated entry
        result['entry_price'] = entry_price
        
        if direction == 'LONG':
            # LONG trade
            # Check Stop Loss first (price dropped below SL)
            if stop_loss and price_low <= stop_loss:
                result['status'] = 'loss'
                result['exit_price'] = stop_loss
                result['hit_sl'] = True
                result['pnl_percent'] = ((stop_loss - entry_price) / entry_price) * 100
                result['pnl_leveraged'] = result['pnl_percent'] * leverage
                result['reason'] = 'Stop Loss hit'
                return result
            
            # Check Take Profit levels
            for tp in take_profits:
                tp_price = tp.get('tp_price')
                if price_high >= tp_price:
                    result['status'] = 'profit'
                    result['exit_price'] = tp_price
                    result['hit_tp'] = tp.get('tp_number')
                    result['pnl_percent'] = ((tp_price - entry_price) / entry_price) * 100
                    result['pnl_leveraged'] = result['pnl_percent'] * leverage
                    result['reason'] = f"TP{tp.get('tp_number')} reached"
                    return result
            
            # No TP or SL hit - trade still open (use close price)
            result['status'] = 'open'
            result['exit_price'] = price_close
            result['pnl_percent'] = ((price_close - entry_price) / entry_price) * 100
            result['pnl_leveraged'] = result['pnl_percent'] * leverage
            result['reason'] = 'No TP/SL hit, using close price'
            
        elif direction == 'SHORT':
            # SHORT trade
            # Check Stop Loss first (price went above SL)
            if stop_loss and price_high >= stop_loss:
                result['status'] = 'loss'
                result['exit_price'] = stop_loss
                result['hit_sl'] = True
                result['pnl_percent'] = ((entry_price - stop_loss) / entry_price) * 100
                result['pnl_leveraged'] = result['pnl_percent'] * leverage
                result['reason'] = 'Stop Loss hit'
                return result
            
            # Check Take Profit levels
            for tp in take_profits:
                tp_price = tp.get('tp_price')
                if price_low <= tp_price:
                    result['status'] = 'profit'
                    result['exit_price'] = tp_price
                    result['hit_tp'] = tp.get('tp_number')
                    result['pnl_percent'] = ((entry_price - tp_price) / entry_price) * 100
                    result['pnl_leveraged'] = result['pnl_percent'] * leverage
                    result['reason'] = f"TP{tp.get('tp_number')} reached"
                    return result
            
            # No TP or SL hit - trade still open
            result['status'] = 'open'
            result['exit_price'] = price_close
            result['pnl_percent'] = ((entry_price - price_close) / entry_price) * 100
            result['pnl_leveraged'] = result['pnl_percent'] * leverage
            result['reason'] = 'No TP/SL hit, using close price'
        
        return result
    
    def backtest_signal(self, signal: Dict) -> Dict:
        """
        Backtest a single signal.
        
        Args:
            signal: Parsed signal dict
            
        Returns:
            Dict with backtest results
        """
        symbol = signal.get('symbol')
        timestamp_str = signal.get('timestamp')
        
        if not symbol or not timestamp_str:
            return {
                'status': 'error',
                'error': 'Missing symbol or timestamp'
            }
        
        try:
            # Parse timestamp
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            # Load price data
            price_data = self.load_price_data(symbol, timestamp)
            
            if not price_data:
                return {
                    'status': 'error',
                    'error': 'No price data available'
                }
            
            # Simulate trade
            trade_result = self.simulate_trade(signal, price_data)
            
            # Add signal metadata
            trade_result['signal_id'] = signal.get('message_id')
            trade_result['symbol'] = symbol
            trade_result['direction'] = signal.get('direction')
            trade_result['channel'] = signal.get('channel_title')
            trade_result['timestamp'] = timestamp_str
            trade_result['leverage'] = signal.get('leverage', 1)
            
            return trade_result
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }


def load_complete_signals(parsed_path: Path) -> List[Dict]:
    """
    Load complete parsed signals that have price data.
    
    Args:
        parsed_path: Path to signals_parsed.jsonl
        
    Returns:
        List of complete signal dicts
    """
    signals = []
    
    if not parsed_path.exists():
        error(f"❌ File not found: {parsed_path}")
        return signals
    
    try:
        with open(parsed_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    signal = json.loads(line)
                    # Only load complete signals
                    if signal.get('is_complete'):
                        signals.append(signal)
        
        info(f"📚 Loaded {len(signals)} complete signals")
        
    except Exception as e:
        error(f"❌ Error loading signals: {e}")
    
    return signals


def save_backtest_results(results: List[Dict], output_path: Path):
    """
    Save backtest results to JSONL file.
    
    Args:
        results: List of backtest result dicts
        output_path: Path to save results
    """
    if not results:
        warn("⚠️ No results to save")
        return
    
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for result in results:
                json_line = json.dumps(result, ensure_ascii=False)
                f.write(json_line + '\n')
        
        success(f"💾 Saved {len(results)} backtest results to {output_path}")
        
    except Exception as e:
        error(f"❌ Error saving results: {e}")


def print_statistics(results: List[Dict]):
    """
    Print detailed backtest statistics.
    
    Args:
        results: List of backtest result dicts
    """
    # Filter valid results
    valid_results = [r for r in results if r.get('status') in ['profit', 'loss', 'open']]
    
    if not valid_results:
        warn("⚠️ No valid results to analyze")
        return
    
    # Calculate statistics
    total = len(valid_results)
    profits = [r for r in valid_results if r.get('status') == 'profit']
    losses = [r for r in valid_results if r.get('status') == 'loss']
    open_trades = [r for r in valid_results if r.get('status') == 'open']
    
    win_count = len(profits)
    loss_count = len(losses)
    open_count = len(open_trades)
    
    win_rate = (win_count / total * 100) if total > 0 else 0
    
    # PnL calculations
    total_pnl = sum(r.get('pnl_leveraged', 0) for r in valid_results)
    avg_win = sum(r.get('pnl_leveraged', 0) for r in profits) / win_count if win_count > 0 else 0
    avg_loss = sum(r.get('pnl_leveraged', 0) for r in losses) / loss_count if loss_count > 0 else 0
    
    # Profit factor
    total_wins = sum(r.get('pnl_leveraged', 0) for r in profits if r.get('pnl_leveraged', 0) > 0)
    total_losses = abs(sum(r.get('pnl_leveraged', 0) for r in losses if r.get('pnl_leveraged', 0) < 0))
    profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
    
    # Channel breakdown
    channel_stats = {}
    for r in valid_results:
        channel = r.get('channel', 'Unknown')
        if channel not in channel_stats:
            channel_stats[channel] = {'total': 0, 'wins': 0, 'pnl': 0}
        channel_stats[channel]['total'] += 1
        if r.get('status') == 'profit':
            channel_stats[channel]['wins'] += 1
        channel_stats[channel]['pnl'] += r.get('pnl_leveraged', 0)
    
    # Print results
    print("\n" + "="*80)
    print("📊 BACKTEST RESULTS")
    print("="*80)
    
    print(f"\n📈 Overall Performance:")
    print(f"   Total Signals: {total}")
    print(f"   ✅ Profitable: {win_count} ({win_rate:.1f}%)")
    print(f"   ❌ Losses: {loss_count} ({loss_count/total*100 if total > 0 else 0:.1f}%)")
    print(f"   ⏳ Still Open: {open_count}")
    
    print(f"\n💰 Profit & Loss:")
    print(f"   Total PnL (Leveraged): {total_pnl:+.2f}%")
    print(f"   Average Win: +{avg_win:.2f}%")
    print(f"   Average Loss: {avg_loss:.2f}%")
    print(f"   Profit Factor: {profit_factor:.2f}")
    
    print(f"\n📱 By Channel:")
    for channel, stats in sorted(channel_stats.items(), key=lambda x: x[1]['pnl'], reverse=True):
        wr = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"   {channel}:")
        print(f"      Signals: {stats['total']} | Win Rate: {wr:.1f}% | PnL: {stats['pnl']:+.2f}%")
    
    print("\n" + "="*80)
    
    # Final verdict
    if win_rate >= 60 and total_pnl > 0:
        success("\n🎉 EXCELLENT! Signals are profitable! Consider live trading.")
    elif win_rate >= 50 and total_pnl > 0:
        info("\n✅ GOOD! Positive performance, but needs optimization.")
    elif win_rate >= 40:
        warn("\n⚠️ MODERATE. Performance is borderline. Review strategy.")
    else:
        error("\n❌ POOR. Signals are not profitable. Avoid live trading!")


def run_backtest():
    """Main backtest execution."""
    print("\n" + "="*80)
    print("🧪 BACKTEST ENGINE")
    print("="*80)
    
    # Paths
    data_dir = Path("data")
    parsed_path = data_dir / "signals_parsed.jsonl"
    price_cache_dir = data_dir / "historical_prices"
    results_path = data_dir / "backtest_results.jsonl"
    
    # Initialize engine
    engine = BacktestEngine(price_cache_dir)
    
    # Load signals
    signals = load_complete_signals(parsed_path)
    
    if not signals:
        error("❌ No complete signals found!")
        return
    
    # Run backtest
    info(f"\n🔄 Backtesting {len(signals)} signals...")
    
    results = []
    stats = {'total': len(signals), 'success': 0, 'error': 0}
    
    for i, signal in enumerate(signals, 1):
        if i % 20 == 0 or i == 1:
            info(f"   Progress: {i}/{stats['total']} ({i*100//stats['total']}%)")
        
        result = engine.backtest_signal(signal)
        
        if result.get('status') in ['profit', 'loss', 'open']:
            stats['success'] += 1
        else:
            stats['error'] += 1
        
        results.append(result)
    
    # Save results
    save_backtest_results(results, results_path)
    
    # Print statistics
    print_statistics(results)
    
    info(f"\n📁 Results saved to: {results_path}")
    print("="*80)


if __name__ == "__main__":
    run_backtest()
