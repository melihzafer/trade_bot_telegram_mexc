"""
🧪 Run Backtest
Command-line interface for running backtests with customizable parameters.
"""
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from trading.backtest_engine import BacktestEngine
from trading.backtest_visualizer import BacktestVisualizer
from utils.logger import info, error, success


def load_signals(signals_file: Path) -> list:
    """Load signals from JSONL file."""
    if not signals_file.exists():
        error(f"Signals file not found: {signals_file}")
        return []
    
    signals = []
    with open(signals_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    signals.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    return signals


def main():
    parser = argparse.ArgumentParser(
        description='🧪 Run backtest on historical trading signals',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run backtest with default settings
  python run_backtest.py
  
  # Custom capital and risk
  python run_backtest.py --capital 50000 --risk 0.03
  
  # Filter by date range
  python run_backtest.py --start-date 2024-01-01 --end-date 2024-12-31
  
  # Custom fees and slippage
  python run_backtest.py --maker-fee 0.0001 --taker-fee 0.0005 --slippage 0.002
  
  # Use custom signals file
  python run_backtest.py --signals data/my_signals.jsonl
        """
    )
    
    # Input/Output
    parser.add_argument(
        '--signals',
        type=str,
        default='data/signals_parsed.jsonl',
        help='Path to signals JSONL file (default: data/signals_parsed.jsonl)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='reports',
        help='Output directory for reports (default: reports)'
    )
    
    # Capital & Risk
    parser.add_argument(
        '--capital',
        type=float,
        default=10000.0,
        help='Initial capital in USDT (default: 10000)'
    )
    parser.add_argument(
        '--risk',
        type=float,
        default=0.02,
        help='Risk percentage per trade (default: 0.02 = 2%%)'
    )
    
    # Fees & Slippage
    parser.add_argument(
        '--maker-fee',
        type=float,
        default=0.0002,
        help='Maker fee percentage (default: 0.0002 = 0.02%%)'
    )
    parser.add_argument(
        '--taker-fee',
        type=float,
        default=0.0006,
        help='Taker fee percentage (default: 0.0006 = 0.06%%)'
    )
    parser.add_argument(
        '--slippage',
        type=float,
        default=0.001,
        help='Average slippage percentage (default: 0.001 = 0.1%%)'
    )
    
    # Time Parameters
    parser.add_argument(
        '--max-bars',
        type=int,
        default=96,
        help='Maximum candles to hold position (default: 96 = 24h for 15m)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date filter (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date filter (YYYY-MM-DD)'
    )
    
    # Visualization
    parser.add_argument(
        '--no-charts',
        action='store_true',
        help='Skip chart generation'
    )
    parser.add_argument(
        '--no-html',
        action='store_true',
        help='Skip HTML report generation'
    )
    
    args = parser.parse_args()
    
    # Load signals
    signals_file = Path(args.signals)
    info(f"Loading signals from: {signals_file}")
    signals = load_signals(signals_file)
    
    if not signals:
        error("No signals found. Exiting.")
        return
    
    info(f"Loaded {len(signals)} signals")
    
    # Initialize backtest engine
    engine = BacktestEngine(
        initial_capital=args.capital,
        risk_pct=args.risk,
        maker_fee=args.maker_fee,
        taker_fee=args.taker_fee,
        slippage_pct=args.slippage,
        max_bars_held=args.max_bars
    )
    
    # Run backtest
    trades, metrics = engine.run_backtest(
        signals=signals,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    if not trades:
        error("❌ No trades executed. Check signal format and data availability.")
        return
    
    # Save results
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save metrics JSON
    metrics_file = output_dir / f"backtest_metrics_{timestamp}.json"
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics.to_dict(), f, indent=2)
    info(f"💾 Metrics saved: {metrics_file}")
    
    # Save trades JSONL
    trades_file = output_dir / f"backtest_trades_{timestamp}.jsonl"
    with open(trades_file, 'w', encoding='utf-8') as f:
        for trade in trades:
            f.write(json.dumps(trade.to_dict()) + '\n')
    info(f"💾 Trades log saved: {trades_file}")
    
    # Generate visualizations
    if not args.no_charts or not args.no_html:
        visualizer = BacktestVisualizer(output_dir)
        
        chart_paths = {}
        
        if not args.no_charts:
            info("📊 Generating charts...")
            
            # Equity curve
            equity_path = visualizer.plot_equity_curve(
                engine.equity_curve,
                [t.to_dict() for t in trades],
                filename=f"equity_curve_{timestamp}.png"
            )
            chart_paths['equity'] = equity_path
            
            # Trade distribution
            dist_path = visualizer.plot_trade_distribution(
                [t.to_dict() for t in trades],
                filename=f"trade_distribution_{timestamp}.png"
            )
            chart_paths['distribution'] = dist_path
            
            # Monthly heatmap
            if metrics.monthly_returns:
                heatmap_path = visualizer.plot_monthly_heatmap(
                    metrics.monthly_returns,
                    filename=f"monthly_heatmap_{timestamp}.png"
                )
                chart_paths['heatmap'] = heatmap_path
            
            # Channel comparison
            if metrics.channel_metrics:
                channel_path = visualizer.plot_channel_comparison(
                    metrics.channel_metrics,
                    filename=f"channel_comparison_{timestamp}.png"
                )
                chart_paths['channel_comparison'] = channel_path
        
        if not args.no_html:
            info("Generating HTML report...")
            html_path = visualizer.generate_html_report(
                metrics.to_dict(),
                [t.to_dict() for t in trades],
                chart_paths,
                filename=f"backtest_report_{timestamp}.html"
            )
            success(f"\nBacktest complete! Open report: {html_path}")
        
        # Export CSV
        csv_path = visualizer.export_trades_csv(
            [t.to_dict() for t in trades],
            filename=f"backtest_trades_{timestamp}.csv"
        )
    
    info("\n" + "=" * 70)
    info("BACKTEST COMPLETE")
    info("=" * 70)


if __name__ == "__main__":
    main()
