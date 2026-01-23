"""
💼 Portfolio Management CLI
Command-line interface for managing paper trading portfolio.

Usage:
    python manage_portfolio.py --action summary
    python manage_portfolio.py --action close-all
    python manage_portfolio.py --action close --symbol BTCUSDT
    python manage_portfolio.py --action reset
    python manage_portfolio.py --action reset --keep-history
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from trading.portfolio import Portfolio
from config.trading_config import PaperConfig
from utils.binance_api import BinanceClient
from utils.logger import info, success, error, warn


def get_current_prices(portfolio: Portfolio) -> dict:
    """Get current prices for all open positions."""
    if not portfolio.positions:
        return {}
    
    symbols = list(portfolio.positions.keys())
    info(f"📊 Fetching current prices for {len(symbols)} symbols...")
    
    api = BinanceClient()
    prices = {}
    
    for symbol in symbols:
        try:
            price = api.get_current_price(symbol)
            if price:
                prices[symbol] = price
        except Exception as e:
            warn(f"⚠️ Failed to get price for {symbol}: {e}")
    
    return prices


def main():
    parser = argparse.ArgumentParser(
        description='💼 Paper Trading Portfolio Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View portfolio summary
  python manage_portfolio.py --action summary
  
  # Close all positions
  python manage_portfolio.py --action close-all
  
  # Close specific position
  python manage_portfolio.py --action close --symbol BTCUSDT
  python manage_portfolio.py --action close --symbol ETHUSDT --price 3500.5
  
  # Reset portfolio (wipe everything)
  python manage_portfolio.py --action reset
  
  # Reset portfolio (keep history)
  python manage_portfolio.py --action reset --keep-history
        """
    )
    
    parser.add_argument(
        '--action',
        type=str,
        required=True,
        choices=['summary', 'close', 'close-all', 'reset'],
        help='Action to perform'
    )
    
    parser.add_argument(
        '--symbol',
        type=str,
        help='Symbol for close action (e.g., BTCUSDT)'
    )
    
    parser.add_argument(
        '--price',
        type=float,
        help='Exit price for close action (uses current price if not provided)'
    )
    
    parser.add_argument(
        '--keep-history',
        action='store_true',
        help='Keep trade history when resetting (only for reset action)'
    )
    
    parser.add_argument(
        '--portfolio-file',
        type=str,
        default=str(PaperConfig.PORTFOLIO_FILE),
        help='Path to portfolio file (default: data/paper_portfolio.json)'
    )
    
    args = parser.parse_args()
    
    # Initialize portfolio
    portfolio = Portfolio(
        initial_balance=PaperConfig.INITIAL_BALANCE,
        portfolio_file=Path(args.portfolio_file)
    )
    
    info("=" * 70)
    info("💼 PAPER TRADING PORTFOLIO MANAGER")
    info("=" * 70)
    
    # Execute action
    if args.action == 'summary':
        portfolio.print_summary()
    
    elif args.action == 'close':
        if not args.symbol:
            error("❌ --symbol required for close action")
            sys.exit(1)
        
        symbol = args.symbol.upper()
        
        if not portfolio.has_position(symbol):
            error(f"❌ No open position for {symbol}")
            sys.exit(1)
        
        # Get exit price
        if args.price:
            exit_price = args.price
            info(f"📍 Using provided exit price: ${exit_price:.4f}")
        else:
            info(f"📊 Fetching current price for {symbol}...")
            api = BinanceClient()
            exit_price = api.get_current_price(symbol)
            
            if not exit_price:
                error(f"❌ Failed to fetch current price for {symbol}")
                error("   Provide --price manually or check API connection")
                sys.exit(1)
            
            info(f"✅ Current price: ${exit_price:.4f}")
        
        # Close position
        if portfolio.force_close_position(symbol, exit_price):
            success(f"✅ Position {symbol} closed successfully")
            portfolio.print_summary()
        else:
            error(f"❌ Failed to close position {symbol}")
            sys.exit(1)
    
    elif args.action == 'close-all':
        if not portfolio.positions:
            info("ℹ️ No open positions to close")
            sys.exit(0)
        
        # Get current prices
        prices = get_current_prices(portfolio)
        
        if not prices:
            error("❌ Failed to fetch any prices. Check API connection.")
            sys.exit(1)
        
        # Close all positions
        closed_count = portfolio.close_all_positions(prices)
        
        if closed_count > 0:
            success(f"✅ Successfully closed {closed_count} positions")
            portfolio.print_summary()
        else:
            warn("⚠️ No positions were closed")
    
    elif args.action == 'reset':
        # Confirm reset
        warn("⚠️ WARNING: This will reset your portfolio!")
        
        if args.keep_history:
            warn("   • Balance will be reset to initial")
            warn("   • All open positions will be closed")
            warn("   • Trade history will be PRESERVED")
        else:
            warn("   • Balance will be reset to initial")
            warn("   • All open positions will be closed")
            warn("   • ALL TRADE HISTORY WILL BE DELETED")
        
        print()
        confirm = input("Type 'RESET' to confirm: ").strip()
        
        if confirm != 'RESET':
            info("❌ Reset cancelled")
            sys.exit(0)
        
        # Reset portfolio
        portfolio.reset_portfolio(keep_history=args.keep_history)
        success("✅ Portfolio reset complete!")
    
    info("=" * 70)


if __name__ == "__main__":
    main()
