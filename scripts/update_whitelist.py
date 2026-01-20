"""
🔄 Auto-Whitelist Updater - Phase 4 Enhancement

Automatically fetches the Top 100 USDT Futures pairs by 24h trading volume from Binance
and updates the whitelist in data/risk_config.json.

This ensures we're always trading the most liquid and actively traded pairs.

Usage:
    python scripts/update_whitelist.py
"""

import sys
import json
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import ccxt
    from rich.console import Console
    from rich.table import Table
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install with: pip install ccxt rich")
    sys.exit(1)

console = Console()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RISK_CONFIG_PATH = DATA_DIR / "risk_config.json"


def fetch_top_futures_pairs(top_n: int = 100) -> List[str]:
    """
    Fetch top N USDT Futures pairs by 24h quote volume from Binance.
    
    Args:
        top_n: Number of top pairs to return
    
    Returns:
        List of symbol strings (e.g., ['BTCUSDT', 'ETHUSDT', ...])
    """
    console.log("🔗 Connecting to Binance (public API)...")
    
    try:
        # Initialize Binance (no API key needed for public endpoints)
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # Use futures market
            }
        })
        
        console.log("📊 Fetching all tickers...")
        
        # Fetch all tickers
        tickers = exchange.fetch_tickers()
        
        # Filter for USDT perpetual futures
        usdt_futures = []
        for symbol, ticker in tickers.items():
            # Check if it's a USDT pair and has volume data
            if '/USDT' in symbol and ticker.get('quoteVolume'):
                # Extract base symbol (remove /USDT)
                base_symbol = symbol.replace('/USDT', '').replace('/', '') + 'USDT'
                
                usdt_futures.append({
                    'symbol': base_symbol,
                    'quote_volume': float(ticker['quoteVolume'])
                })
        
        console.log(f"✅ Found {len(usdt_futures)} USDT futures pairs")
        
        # Sort by 24h quote volume (descending)
        usdt_futures.sort(key=lambda x: x['quote_volume'], reverse=True)
        
        # Take top N
        top_pairs = usdt_futures[:top_n]
        
        # Extract just the symbols
        symbols = [pair['symbol'] for pair in top_pairs]
        
        # Display top 10 in console
        console.log("\n📈 Top 10 pairs by 24h volume:")
        table = Table(show_header=True)
        table.add_column("Rank", style="cyan")
        table.add_column("Symbol", style="green")
        table.add_column("24h Volume (USDT)", style="yellow", justify="right")
        
        for i, pair in enumerate(top_pairs[:10], 1):
            volume_formatted = f"${pair['quote_volume']:,.0f}"
            table.add_row(str(i), pair['symbol'], volume_formatted)
        
        console.print(table)
        
        return symbols
    
    except Exception as e:
        console.log(f"❌ Error fetching tickers: {e}", style="bold red")
        raise


def update_risk_config(whitelist: List[str]) -> None:
    """
    Update the whitelist in data/risk_config.json.
    
    Args:
        whitelist: List of symbol strings to save
    """
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load existing config or create new one
    if RISK_CONFIG_PATH.exists():
        console.log(f"📂 Loading existing config from {RISK_CONFIG_PATH}")
        with open(RISK_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        console.log(f"📝 Creating new config at {RISK_CONFIG_PATH}")
        config = {}
    
    # Update whitelist
    config['whitelist'] = whitelist
    config['last_updated'] = str(Path(__file__).stat().st_mtime)
    
    # Save back
    with open(RISK_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    console.log(f"✅ Saved {len(whitelist)} symbols to {RISK_CONFIG_PATH}", style="bold green")


def main():
    """Main execution."""
    console.rule("🔄 [bold cyan]Auto-Whitelist Updater - Phase 4[/bold cyan]")
    
    try:
        # Fetch top 100 pairs from Binance
        top_symbols = fetch_top_futures_pairs(top_n=100)
        
        console.log(f"\n✅ Fetched {len(top_symbols)} top symbols")
        
        # Update risk config
        update_risk_config(top_symbols)
        
        console.rule("[bold green]✅ Whitelist Update Complete[/bold green]")
        console.log(f"\n📋 Whitelist now contains: {len(top_symbols)} symbols")
        console.log(f"📁 Config file: {RISK_CONFIG_PATH}")
        
        # Display first 20 symbols
        console.log("\n🎯 First 20 symbols in whitelist:")
        console.print(", ".join(top_symbols[:20]))
        
        return 0
    
    except Exception as e:
        console.log(f"\n❌ Failed to update whitelist: {e}", style="bold red")
        return 1


if __name__ == "__main__":
    sys.exit(main())
