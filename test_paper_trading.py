"""
Paper Trading System Test
Tests paper trading engine with mock signals
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers.enhanced_parser import EnhancedParser
from trading.paper_portfolio import PaperPortfolio
from trading.paper_trade_manager import PaperTradeManager
from trading.trade_logger import TradeLogger
from generate_paper_trading_report import generate_paper_trading_report


# Mock signals for testing
TEST_SIGNALS = [
    # Signal 1: LONG with all fields
    """
    🔥 BTC/USDT LONG
    Entry: 45000-45500
    TP1: 46000
    TP2: 47000
    TP3: 48000
    SL: 44000
    Leverage: 10x
    """,
    
    # Signal 2: SHORT without TP/SL (should use defaults)
    """
    💎 ETH/USDT SHORT
    Entry: 2500
    Leverage: 15x
    """,
    
    # Signal 3: LONG without leverage (should use default 15x)
    """
    🚀 SOL/USDT LONG
    Entry: 100
    TP1: 105
    TP2: 110
    SL: 95
    """,
    
    # Signal 4: Invalid signal (missing entry)
    """
    BTC/USDT LONG
    TP1: 50000
    SL: 40000
    """,
]


# Mock price movements for testing
PRICE_SCENARIOS = {
    'BTCUSDT': [
        45000,  # Entry
        45500,  # Move up
        46500,  # TP1 hit
        47500,  # TP2 hit
    ],
    'ETHUSDT': [
        2500,   # Entry
        2450,   # Move down (profit for SHORT)
        2400,   # More profit
        2350,   # Even more
    ],
    'SOLUSDT': [
        100,    # Entry
        98,     # Move down
        95,     # Stop loss hit
    ]
}


def test_signal_parsing():
    """Test 1: Signal parsing with default values."""
    print("=" * 70)
    print("TEST 1: Signal Parsing with Defaults")
    print("=" * 70)
    
    parser = EnhancedParser()
    
    for i, signal_text in enumerate(TEST_SIGNALS, 1):
        print(f"\n📝 Signal {i}:")
        print(signal_text.strip())
        
        signal = parser.parse(signal_text)
        
        print(f"\n✅ Parsed:")
        print(f"   Symbol: {signal.symbol}")
        print(f"   Side: {signal.side}")
        print(f"   Entries: {signal.entries}")
        print(f"   Stop Loss: {signal.sl}")
        print(f"   Take Profits: {signal.tps}")
        print(f"   Leverage: {signal.leverage_x}")
        print(f"   Confidence: {signal.confidence:.2f}")
    
    print("\n" + "=" * 70 + "\n")


def test_portfolio_calculations():
    """Test 2: Portfolio position sizing and PnL calculations."""
    print("=" * 70)
    print("TEST 2: Portfolio Calculations")
    print("=" * 70)
    
    parser = EnhancedParser()
    portfolio = PaperPortfolio(initial_balance=10000)
    
    # Parse signal
    signal_text = TEST_SIGNALS[0]  # BTC LONG
    signal = parser.parse(signal_text)
    
    print(f"\n📊 Initial Balance: ${portfolio.balance:.2f}")
    print(f"📊 Position Size %: {portfolio.get_available_balance() * 0.05:.2f} (5% of portfolio)")
    
    # Calculate position size
    quantity = portfolio.calculate_position_size(signal)
    print(f"\n✅ Position Quantity: {quantity:.4f} BTC")
    
    # Calculate stop loss
    sl = portfolio.calculate_stop_loss(signal)
    print(f"✅ Stop Loss: ${sl:.2f}")
    
    # Calculate take profits
    tps = portfolio.calculate_take_profits(signal)
    print(f"✅ Take Profits: {', '.join(f'${tp:.2f}' for tp in tps)}")
    
    # Test PnL calculation
    position = {
        'entry_price': signal.entry_min,
        'quantity': quantity,
        'leverage': signal.leverage_x or 15.0,
        'side': signal.side
    }
    
    print(f"\n💰 PnL Scenarios:")
    test_prices = [45000, 46000, 47000, 48000, 44000]
    for price in test_prices:
        pnl_pct, pnl_usd = portfolio.calculate_pnl(position, price)
        print(f"   Price ${price}: {pnl_pct:.2f}% (${pnl_usd:.2f})")
    
    print("\n" + "=" * 70 + "\n")


def test_default_tp_sl_calculation():
    """Test 3: Default TP/SL calculation (1R, 2R, 3R)."""
    print("=" * 70)
    print("TEST 3: Default TP/SL Calculation (No TP/SL in signal)")
    print("=" * 70)
    
    parser = EnhancedParser()
    portfolio = PaperPortfolio()
    
    # Parse signal without TP/SL
    signal_text = TEST_SIGNALS[1]  # ETH SHORT, no TP/SL
    signal = parser.parse(signal_text)
    
    print(f"\n📝 Signal: {signal.symbol} {signal.side}")
    print(f"   Entry: ${signal.entry_min}")
    print(f"   Leverage: {signal.leverage_x or 15}x")
    print(f"   SL in signal: {signal.sl}")
    print(f"   TPs in signal: {signal.tps}")
    
    # Calculate defaults
    sl = portfolio.calculate_stop_loss(signal)
    tps = portfolio.calculate_take_profits(signal)
    
    print(f"\n✅ Calculated Stop Loss: ${sl:.2f}")
    print(f"   Distance from entry: {abs(signal.entry_min - sl):.2f} (R)")
    print(f"   Max loss with leverage: {abs((sl - signal.entry_min) / signal.entry_min * 100 * (signal.leverage_x or 15)):.2f}%")
    
    print(f"\n✅ Calculated Take Profits:")
    risk = abs(signal.entry_min - sl)
    for i, tp in enumerate(tps, 1):
        distance = abs(tp - signal.entry_min)
        ratio = distance / risk
        print(f"   TP{i}: ${tp:.2f} ({ratio:.1f}R)")
    
    print("\n" + "=" * 70 + "\n")


def test_position_lifecycle():
    """Test 4: Full position lifecycle with price updates."""
    print("=" * 70)
    print("TEST 4: Position Lifecycle (Open → Update → Close)")
    print("=" * 70)
    
    parser = EnhancedParser()
    portfolio = PaperPortfolio(initial_balance=10000)
    trade_manager = PaperTradeManager(portfolio)
    logger = TradeLogger()
    
    # Open position
    signal_text = TEST_SIGNALS[2]  # SOL LONG
    signal = parser.parse(signal_text)
    
    print(f"\n🔓 Opening position: {signal.symbol} {signal.side}")
    position = trade_manager.open_position(signal, "Test Channel")
    
    if not position:
        print("❌ Failed to open position")
        return
    
    print(f"   Entry: ${position['entry_price']:.2f}")
    print(f"   Stop Loss: ${position['stop_loss']:.2f}")
    print(f"   Take Profits: {', '.join(f'${tp:.2f}' for tp in position['take_profits'])}")
    
    # Simulate price movements
    prices = PRICE_SCENARIOS[signal.symbol]
    
    print(f"\n📈 Price movements:")
    for i, price in enumerate(prices):
        print(f"\n   Price Update {i+1}: ${price:.2f}")
        
        # Update positions
        current_prices = {signal.symbol: price}
        closed_trades = trade_manager.update_positions(current_prices)
        
        if position['id'] in portfolio.open_positions:
            pos = portfolio.open_positions[position['id']]
            print(f"      Current PnL: {pos['current_pnl_pct']:.2f}% (${pos['current_pnl_usd']:.2f})")
        
        if closed_trades:
            print(f"\n   🔒 Position closed!")
            trade = closed_trades[0]
            print(f"      Exit Price: ${trade['exit_price']:.2f}")
            print(f"      Exit Reason: {trade['exit_reason']}")
            print(f"      Final PnL: {trade['pnl_pct']:.2f}% (${trade['pnl_usd']:.2f})")
            print(f"      New Balance: ${portfolio.balance:.2f}")
            break
    
    print("\n" + "=" * 70 + "\n")


def test_full_system():
    """Test 5: Full system with multiple trades."""
    print("=" * 70)
    print("TEST 5: Full System Test (Multiple Trades)")
    print("=" * 70)
    
    parser = EnhancedParser()
    portfolio = PaperPortfolio(initial_balance=10000)
    trade_manager = PaperTradeManager(portfolio)
    logger = TradeLogger()
    
    # Clear previous test data
    if logger.log_path.exists():
        logger.log_path.unlink()
    
    print(f"\n💰 Initial Balance: ${portfolio.balance:.2f}\n")
    
    # Process valid signals
    valid_signals = [TEST_SIGNALS[0], TEST_SIGNALS[1], TEST_SIGNALS[2]]
    
    for i, signal_text in enumerate(valid_signals, 1):
        signal = parser.parse(signal_text)
        
        print(f"📝 Signal {i}: {signal.symbol} {signal.side}")
        
        # Open position
        position = trade_manager.open_position(signal, f"Test Channel {i}")
        
        if not position:
            print(f"   ❌ Failed to open\n")
            continue
        
        # Simulate price to TP1
        symbol = signal.symbol
        if symbol in PRICE_SCENARIOS:
            prices = PRICE_SCENARIOS[symbol]
            
            # Move to TP1/profit
            target_price = prices[2] if len(prices) > 2 else prices[1]
            current_prices = {symbol: target_price}
            
            closed_trades = trade_manager.update_positions(current_prices)
            
            if closed_trades:
                trade = closed_trades[0]
                logger.log_trade(trade)
                print(f"   ✅ Closed at ${trade['exit_price']:.2f}")
                print(f"   PnL: {trade['pnl_pct']:.2f}% (${trade['pnl_usd']:.2f})")
                print(f"   Balance: ${portfolio.balance:.2f}\n")
    
    # Print final stats
    stats = portfolio.get_stats()
    print("\n" + "=" * 70)
    print("📊 FINAL STATISTICS")
    print("=" * 70)
    print(f"Initial Balance: ${stats['initial_balance']:.2f}")
    print(f"Final Balance: ${stats['current_balance']:.2f}")
    print(f"Total PnL: ${stats['total_pnl']:.2f} ({stats['total_pnl_pct']:.2f}%)")
    print(f"Total Trades: {stats['total_trades']}")
    print(f"Win Rate: {stats['win_rate']:.1f}% ({stats['winning_trades']}W / {stats['losing_trades']}L)")
    print("=" * 70 + "\n")
    
    # Generate report
    print("📊 Generating test report...")
    generate_paper_trading_report(portfolio, logger)


def run_all_tests():
    """Run all tests."""
    print("\n" + "🧪" * 35)
    print("PAPER TRADING SYSTEM TEST SUITE")
    print("🧪" * 35 + "\n")
    
    try:
        test_signal_parsing()
        test_portfolio_calculations()
        test_default_tp_sl_calculation()
        test_position_lifecycle()
        test_full_system()
        
        print("\n" + "✅" * 35)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("✅" * 35 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
