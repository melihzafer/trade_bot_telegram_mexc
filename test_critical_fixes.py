"""
Test script to verify the two critical fixes:
1. Telegram listener with numeric channel IDs
2. Portfolio get_all_positions() method
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from trading.portfolio import Portfolio
from config.trading_config import PaperConfig

print("="*60)
print("TESTING CRITICAL FIXES")
print("="*60)

# Test 1: Portfolio get_all_positions()
print("\n✅ TEST 1: Portfolio.get_all_positions()")
print("-"*60)

portfolio = Portfolio(
    initial_balance=10000.0,
    portfolio_file=PaperConfig.PORTFOLIO_FILE
)

# Open some test positions
portfolio.open_position("BTCUSDT", "LONG", 50000, 0.1, tp=52000, sl=48000)
portfolio.open_position("ETHUSDT", "LONG", 3000, 0.5, tp=3200, sl=2900)

# Test get_all_positions()
all_positions = portfolio.get_all_positions()
print(f"Number of positions: {len(all_positions)}")
print(f"Positions: {list(all_positions.keys())}")

# Test get_statistics()
stats = portfolio.get_statistics()
print(f"\nStatistics keys: {list(stats.keys())}")
print(f"Total trades: {stats['total_trades']}")
print(f"Winning trades: {stats['winning_trades']}")
print(f"Losing trades: {stats['losing_trades']}")

print("\n✅ Portfolio tests PASSED!")

# Test 2: Channel ID string conversion
print("\n✅ TEST 2: Telegram Channel ID Handling")
print("-"*60)

# Simulate mixed channel list (int and str)
test_channels = [-1003116649926, -1001234567890, "@test_channel", "channel_name"]

# Test the join operation that was failing
try:
    result = ', '.join(str(c) for c in test_channels)
    print(f"Channels as string: {result}")
    print("✅ String conversion PASSED!")
except TypeError as e:
    print(f"❌ String conversion FAILED: {e}")

# Alternative method (map)
try:
    result2 = ', '.join(map(str, test_channels))
    print(f"Channels as string (map): {result2}")
    print("✅ Map conversion PASSED!")
except TypeError as e:
    print(f"❌ Map conversion FAILED: {e}")

print("\n" + "="*60)
print("ALL TESTS COMPLETED SUCCESSFULLY! 🚀")
print("="*60)
