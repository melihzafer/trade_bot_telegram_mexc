"""
Comprehensive test suite for Risk Sentinel.
Tests circuit breaker, validation, position sizing, and kill switch.

Run: python test_risk_sentinel.py
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from trading.risk_manager import RiskSentinel, ValidationResult

try:
    from utils import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


def test_initialization():
    """Test 1: Sentinel initialization."""
    logger.info("\n🧪 Test 1: Initialization\n")
    
    sentinel = RiskSentinel(initial_equity=10000)
    
    assert sentinel.initial_equity == 10000
    assert sentinel.current_equity == 10000
    assert sentinel.daily_pnl == 0
    assert not sentinel.circuit_breaker_active
    
    logger.success("✅ Initialization successful")
    return True


def test_signal_validation_valid():
    """Test 2: Valid signal approval."""
    logger.info("\n🧪 Test 2: Valid Signal Validation\n")
    
    sentinel = RiskSentinel(initial_equity=10000)
    
    result = sentinel.validate_signal(
        symbol="BTCUSDT",
        side="LONG",
        entry=42000.0,
        sl=40000.0,
        tp=45000.0
    )
    
    assert result.valid == True
    assert result.reason == "Signal validated"
    
    logger.success(f"✅ Signal approved: {result.reason}")
    return True


def test_signal_validation_blacklist():
    """Test 3: Blacklisted symbol rejection."""
    logger.info("\n🧪 Test 3: Blacklist Rejection\n")
    
    sentinel = RiskSentinel(initial_equity=10000)
    
    result = sentinel.validate_signal(
        symbol="LUNAUSTD",  # Blacklisted
        side="LONG",
        entry=1.0,
        sl=0.9,
        tp=1.2
    )
    
    assert result.valid == False
    assert "blacklist" in result.reason.lower()
    
    logger.success(f"✅ Signal rejected: {result.reason}")
    return True


def test_signal_validation_invalid_prices():
    """Test 4: Invalid price rejection."""
    logger.info("\n🧪 Test 4: Invalid Price Rejection\n")
    
    sentinel = RiskSentinel(initial_equity=10000)
    
    # Test invalid entry
    result = sentinel.validate_signal(
        symbol="BTCUSDT",
        side="LONG",
        entry=-100.0,  # Invalid
        sl=40000.0,
        tp=45000.0
    )
    
    assert result.valid == False
    assert "invalid" in result.reason.lower()
    
    logger.success(f"✅ Invalid price rejected: {result.reason}")
    return True


def test_signal_validation_wrong_tpsl():
    """Test 5: Wrong TP/SL relationship rejection."""
    logger.info("\n🧪 Test 5: Wrong TP/SL Rejection\n")
    
    sentinel = RiskSentinel(initial_equity=10000)
    
    # LONG with SL above entry (wrong!)
    result = sentinel.validate_signal(
        symbol="BTCUSDT",
        side="LONG",
        entry=42000.0,
        sl=43000.0,  # Should be below entry
        tp=45000.0
    )
    
    assert result.valid == False
    assert "below entry" in result.reason
    
    logger.success(f"✅ Wrong TP/SL rejected: {result.reason}")
    return True


def test_circuit_breaker_activation():
    """Test 6: Circuit breaker activation."""
    logger.info("\n🧪 Test 6: Circuit Breaker Activation\n")
    
    sentinel = RiskSentinel(initial_equity=10000)
    
    # Simulate 6% loss (exceeds 5% limit)
    sentinel.update_equity(9400)
    
    is_triggered = sentinel.check_circuit_breaker()
    
    assert is_triggered == True
    assert sentinel.circuit_breaker_active == True
    
    logger.success("✅ Circuit breaker activated correctly")
    return True


def test_circuit_breaker_blocking():
    """Test 7: Circuit breaker blocks signals."""
    logger.info("\n🧪 Test 7: Circuit Breaker Blocks Signals\n")
    
    sentinel = RiskSentinel(initial_equity=10000)
    
    # Trigger circuit breaker
    sentinel.update_equity(9400)
    sentinel.check_circuit_breaker()
    
    # Try to validate signal
    result = sentinel.validate_signal(
        symbol="BTCUSDT",
        side="LONG",
        entry=42000.0,
        sl=40000.0,
        tp=45000.0
    )
    
    assert result.valid == False
    assert "circuit breaker" in result.reason.lower()
    
    logger.success(f"✅ Signal blocked: {result.reason}")
    return True


def test_position_sizing():
    """Test 8: Position sizing calculation."""
    logger.info("\n🧪 Test 8: Position Sizing Calculation\n")
    
    sentinel = RiskSentinel(initial_equity=10000)
    
    sizing = sentinel.calculate_safe_quantity(
        equity=10000,
        entry_price=42000,
        sl_price=40000,
        risk_pct=0.01  # 1% risk
    )
    
    # Risk amount should be $100 (1% of 10k)
    assert sizing['risk_amount'] == 100.0
    
    # Risk per unit = 42000 - 40000 = 2000
    assert sizing['risk_per_unit'] == 2000.0
    
    # Quantity = 100 / 2000 = 0.05
    assert abs(sizing['quantity'] - 0.05) < 0.001
    
    logger.info(f"   Risk Amount: ${sizing['risk_amount']}")
    logger.info(f"   Quantity: {sizing['quantity']}")
    logger.info(f"   Position Value: ${sizing['position_value']}")
    
    logger.success("✅ Position sizing correct")
    return True


def test_correlation_check():
    """Test 9: Correlation limit enforcement."""
    logger.info("\n🧪 Test 9: Correlation Check\n")
    
    sentinel = RiskSentinel(initial_equity=10000)
    sentinel.max_correlated_trades = 1  # Allow only 1 per group
    
    # Already have BTCUSDT
    open_positions = [{'symbol': 'BTCUSDT'}]
    
    # Try to add ETHUSDT (both in LAYER1 group)
    result = sentinel.validate_signal(
        symbol="ETHUSDT",
        side="LONG",
        entry=2500.0,
        sl=2400.0,
        tp=2700.0,
        open_positions=open_positions
    )
    
    # Should be approved but with warning
    assert result.valid == True
    assert len(result.warnings) > 0
    assert "correlation" in result.warnings[0].lower()
    
    logger.success(f"✅ Correlation warning: {result.warnings[0]}")
    return True


def test_kill_switch():
    """Test 10: Kill switch activation and deactivation."""
    logger.info("\n🧪 Test 10: Kill Switch\n")
    
    sentinel = RiskSentinel(initial_equity=10000)
    
    # Activate kill switch
    sentinel.activate_kill_switch(reason="Test activation")
    
    # Check if active
    is_active = sentinel.check_kill_switch()
    assert is_active == True
    
    # Try to validate signal
    result = sentinel.validate_signal(
        symbol="BTCUSDT",
        side="LONG",
        entry=42000.0,
        sl=40000.0,
        tp=45000.0
    )
    
    assert result.valid == False
    assert "kill switch" in result.reason.lower()
    
    logger.success("✅ Kill switch blocks signals")
    
    # Deactivate
    sentinel.deactivate_kill_switch()
    is_active = sentinel.check_kill_switch()
    assert is_active == False
    
    logger.success("✅ Kill switch deactivated")
    return True


def test_whitelist_blacklist_management():
    """Test 11: Whitelist/Blacklist management."""
    logger.info("\n🧪 Test 11: Whitelist/Blacklist Management\n")
    
    sentinel = RiskSentinel(initial_equity=10000)
    
    # Add to whitelist
    initial_count = len(sentinel.allowed_symbols)
    sentinel.add_to_whitelist("TESTUSDT")
    assert len(sentinel.allowed_symbols) == initial_count + 1
    assert "TESTUSDT" in sentinel.allowed_symbols
    
    logger.success("✅ Added to whitelist")
    
    # Remove from whitelist
    sentinel.remove_from_whitelist("TESTUSDT")
    assert "TESTUSDT" not in sentinel.allowed_symbols
    
    logger.success("✅ Removed from whitelist")
    
    # Add to blacklist
    initial_count = len(sentinel.blacklisted_symbols)
    sentinel.add_to_blacklist("SCAMCOIN")
    assert len(sentinel.blacklisted_symbols) == initial_count + 1
    assert "SCAMCOIN" in sentinel.blacklisted_symbols
    
    logger.success("✅ Added to blacklist")
    
    # Remove from blacklist
    sentinel.remove_from_blacklist("SCAMCOIN")
    assert "SCAMCOIN" not in sentinel.blacklisted_symbols
    
    logger.success("✅ Removed from blacklist")
    return True


def test_risk_metrics():
    """Test 12: Risk metrics calculation."""
    logger.info("\n🧪 Test 12: Risk Metrics\n")
    
    sentinel = RiskSentinel(initial_equity=10000)
    
    # Update equity
    sentinel.update_equity(10500)
    
    metrics = sentinel.get_risk_metrics()
    
    assert metrics.current_equity == 10500
    assert metrics.daily_pnl == 500
    assert metrics.daily_pnl_pct == 5.0
    assert not metrics.circuit_breaker_active
    assert not metrics.kill_switch_active
    
    logger.info(f"   Equity: ${metrics.current_equity:,.2f}")
    logger.info(f"   Daily PnL: ${metrics.daily_pnl:+,.2f} ({metrics.daily_pnl_pct:+.2f}%)")
    
    logger.success("✅ Risk metrics correct")
    return True


def test_statistics():
    """Test 13: Statistics tracking."""
    logger.info("\n🧪 Test 13: Statistics Tracking\n")
    
    sentinel = RiskSentinel(initial_equity=10000)
    
    # Validate a few signals
    sentinel.validate_signal("BTCUSDT", "LONG", 42000, 40000, 45000)
    sentinel.validate_signal("ETHUSDT", "LONG", 2500, 2400, 2700)
    sentinel.validate_signal("LUNAUSTD", "LONG", 1.0, 0.9, 1.2)  # Blacklisted
    
    stats = sentinel.get_stats()
    
    assert stats['total_validations'] == 3
    assert stats['signals_approved'] == 2
    assert stats['signals_rejected'] == 1
    assert stats['approval_rate'] > 0
    
    logger.info(f"   Total Validations: {stats['total_validations']}")
    logger.info(f"   Approved: {stats['signals_approved']}")
    logger.info(f"   Rejected: {stats['signals_rejected']}")
    logger.info(f"   Approval Rate: {stats['approval_rate']:.1f}%")
    
    logger.success("✅ Statistics tracking correct")
    return True


def test_rr_ratio_warning():
    """Test 14: Risk/Reward ratio warning."""
    logger.info("\n🧪 Test 14: Risk/Reward Ratio Warning\n")
    
    sentinel = RiskSentinel(initial_equity=10000)
    
    # Low R:R ratio (1:1)
    result = sentinel.validate_signal(
        symbol="BTCUSDT",
        side="LONG",
        entry=42000.0,
        sl=41000.0,  # -1000 risk
        tp=43000.0   # +1000 reward (R:R = 1:1)
    )
    
    assert result.valid == True
    assert len(result.warnings) > 0
    assert "ratio" in result.warnings[0].lower()
    
    logger.success(f"✅ R:R warning: {result.warnings[0]}")
    return True


def run_all_tests():
    """Run all test suites."""
    logger.info("╔════════════════════════════════════════════════════════════╗")
    logger.info("║  Risk Sentinel - Comprehensive Test Suite                 ║")
    logger.info("╚════════════════════════════════════════════════════════════╝\n")
    
    tests = [
        ("Initialization", test_initialization),
        ("Valid Signal", test_signal_validation_valid),
        ("Blacklist Rejection", test_signal_validation_blacklist),
        ("Invalid Price Rejection", test_signal_validation_invalid_prices),
        ("Wrong TP/SL Rejection", test_signal_validation_wrong_tpsl),
        ("Circuit Breaker Activation", test_circuit_breaker_activation),
        ("Circuit Breaker Blocking", test_circuit_breaker_blocking),
        ("Position Sizing", test_position_sizing),
        ("Correlation Check", test_correlation_check),
        ("Kill Switch", test_kill_switch),
        ("Whitelist/Blacklist Management", test_whitelist_blacklist_management),
        ("Risk Metrics", test_risk_metrics),
        ("Statistics Tracking", test_statistics),
        ("R:R Ratio Warning", test_rr_ratio_warning),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            results.append((name, False))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {status}  {name}")
    
    logger.info("="*60)
    logger.info(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        logger.success("\n🎉 All tests passed!")
    else:
        logger.warn(f"\n⚠️  {total - passed} test(s) failed")
    
    logger.info("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
