"""
🛡️ Risk Sentinel - Phase 3 (Project Chimera)
Comprehensive gatekeeper and kill switch for trading operations.

Features:
- Daily/Weekly loss circuit breakers
- Symbol whitelist/blacklist enforcement
- Correlation-based exposure limits
- Kill switch file monitoring
- Advanced position sizing with risk-per-trade logic
- Trade validation and rejection
- Real-time risk metrics

Author: Project Chimera Team
Created: 2025
"""
import os
import json
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dataclasses import dataclass, field

try:
    from utils import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    from config.trading_config import RiskConfig, LiveConfig
except ImportError:
    # Fallback to utils.config
    from utils.config import (
        ACCOUNT_EQUITY_USDT,
        DAILY_MAX_LOSS_PCT,
        MAX_CONCURRENT_POSITIONS,
        RISK_PER_TRADE_PCT,
        LEVERAGE,
    )
    
    class RiskConfig:
        INITIAL_CAPITAL = ACCOUNT_EQUITY_USDT
        DAILY_LOSS_LIMIT_PCT = DAILY_MAX_LOSS_PCT / 100.0
        MAX_CONCURRENT_TRADES = MAX_CONCURRENT_POSITIONS
        RISK_PER_TRADE_PCT = RISK_PER_TRADE_PCT / 100.0
        MAX_LEVERAGE = LEVERAGE
    
    class LiveConfig:
        EMERGENCY_STOP_FILE = Path("data/EMERGENCY_STOP")


@dataclass
class RiskMetrics:
    """Real-time risk metrics snapshot."""
    current_equity: float
    daily_pnl: float
    daily_pnl_pct: float
    weekly_pnl: float = 0.0
    weekly_pnl_pct: float = 0.0
    max_daily_loss: float = 0.0
    remaining_daily_risk: float = 0.0
    open_positions: int = 0
    circuit_breaker_active: bool = False
    kill_switch_active: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ValidationResult:
    """Result of signal validation."""
    valid: bool
    reason: str
    warnings: List[str] = field(default_factory=list)


class RiskSentinel:
    """
    🛡️ The Guardian of Capital - Risk Sentinel System.
    
    Responsibilities:
    - Enforce daily/weekly loss limits (circuit breaker)
    - Validate symbols against whitelist/blacklist
    - Prevent correlated over-exposure
    - Monitor kill switch file
    - Calculate safe position sizes
    - Track and log all risk decisions
    """

    # Symbol correlation groups (highly correlated assets)
    CORRELATION_GROUPS = {
        'BTC_GROUP': ['BTCUSDT', 'BTCUSD', 'BTCBUSD'],
        'ETH_GROUP': ['ETHUSDT', 'ETHUSD', 'ETHBUSD'],
        'BNB_GROUP': ['BNBUSDT', 'BNBUSD', 'BNBBUSD'],
        'SOL_GROUP': ['SOLUSDT', 'SOLUSD'],
        'LAYER1': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'AVAXUSDT'],
        'DEFI': ['UNIUSDT', 'AAVEUSDT', 'LINKUSDT', 'MKRUSDT'],
        'MEME': ['DOGEUSDT', 'SHIBUSDT', 'PEPEUSDT'],
        "AI_GROUP": ["FETUSDT", "AGIXUSDT", "OCEANUSDT", "RNDRUSDT", "WLDUSDT"],
        "MEME_GROUP": ["DOGEUSDT", "SHIBUSDT", "PEPEUSDT", "BONKUSDT", "FLOKIUSDT", "WIFUSDT"],

        
    }

    def __init__(
        self,
        initial_equity: float = None,
        config_file: Optional[Path] = None
    ):
        """
        Initialize Risk Sentinel.
        
        Args:
            initial_equity: Starting capital (uses RiskConfig if None)
            config_file: Path to risk configuration JSON
        """
        self.initial_equity = initial_equity or RiskConfig.INITIAL_CAPITAL
        self.equity_start_of_day = self.initial_equity
        self.equity_start_of_week = self.initial_equity
        self.current_equity = self.initial_equity
        
        # PnL tracking
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.last_reset_date = datetime.now(timezone.utc).date()
        self.last_reset_week = datetime.now(timezone.utc).isocalendar()[1]
        
        # Circuit breaker state
        self.circuit_breaker_active = False
        self.circuit_breaker_triggered_at: Optional[datetime] = None
        
        # Kill switch
        self.kill_switch_file = LiveConfig.EMERGENCY_STOP_FILE
        
        # Load configuration
        self.config_file = config_file or Path("config/risk_config.json")
        self._load_config()
        
        # Statistics
        self.stats = {
            'total_validations': 0,
            'signals_approved': 0,
            'signals_rejected': 0,
            'circuit_breaker_triggers': 0,
            'kill_switch_checks': 0
        }
        
        logger.info("🛡️ Risk Sentinel initialized")
        logger.info(f"   Initial Equity: ${self.initial_equity:,.2f}")
        logger.info(f"   Daily Loss Limit: {RiskConfig.DAILY_LOSS_LIMIT_PCT*100:.1f}%")
        logger.info(f"   Whitelisted Symbols: {len(self.allowed_symbols)}")
        logger.info(f"   Blacklisted Symbols: {len(self.blacklisted_symbols)}")
    
    def _load_config(self):
        """Load risk configuration from file or use defaults."""
        # Default symbol lists
        self.allowed_symbols: Set[str] = {
           "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "TRXUSDT", "DOTUSDT",
        "LINKUSDT", "MATICUSDT", "LTCUSDT", "BCHUSDT", "UNIUSDT", "ATOMUSDT", "NEARUSDT", "APTUSDT", "INJUSDT", "LDOUSDT",
        "FILUSDT", "ETCUSDT", "ARBUSDT", "OPUSDT", "RNDRUSDT", "VETUSDT", "GRTUSDT", "MKRUSDT", "SNXUSDT", "THETAUSDT",
        "AAVEUSDT", "ALGOUSDT", "AXSUSDT", "SANDUSDT", "EGLDUSDT", "EOSUSDT", "XTZUSDT", "MANAUSDT", "IMXUSDT", "FLOWUSDT",
        "CHZUSDT", "CRVUSDT", "KAVAUSDT", "FTMUSDT", "RUNEUSDT", "ZECUSDT", "KLAYUSDT", "HBARUSDT", "IOTAUSDT", "NEOUSDT",
        "XLMUSDT", "GALAUSDT", "QNTUSDT", "MINAUSDT", "DYDXUSDT", "FXSUSDT", "ARUSDT", "ENJUSDT", "BATUSDT", "MASKUSDT",
        "APEUSDT", "GMTUSDT", "KSMUSDT", "CVXUSDT", "COMPUSDT", "ZILUSDT", "WLDUSDT", "SUIUSDT", "SEIUSDT", "TIAUSDT",
        "BLURUSDT", "PEPEUSDT", "BONKUSDT", "SHIBUSDT", "FLOKIUSDT", "MEMEUSDT", "ORDIUSDT", "SATSUSDT", "1000SATSUSDT",
        "JUPUSDT", "PYTHUSDT", "ENSUSDT", "PENDLEUSDT", "STRKUSDT", "FETUSDT", "AGIXUSDT", "OCEANUSDT", "JASMYUSDT",
        "CFXUSDT", "STXUSDT", "WOOUSDT", "IDUSDT", "MAGICUSDT", "HIGHUSDT", "LPTUSDT", "ANKRUSDT", "GLMRUSDT", "RDNTUSDT"
    
        }
        
        self.blacklisted_symbols: Set[str] = {
            # Scam/rug-pull history
            'LUNAUSTD', 'USTUSDT', 'FTXUSDT',
            # Highly volatile/risky
            'KAMIKAZE', 'VINE', 'ZORA',
            # Delisted
            'BTTUSD', 'TRXUSD'
        }
        
        # Correlation settings
        self.max_correlated_trades = 2  # Max positions in same correlation group
        
        # Load from file if exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                if 'allowed_symbols' in config:
                    self.allowed_symbols = set(config['allowed_symbols'])
                
                if 'blacklisted_symbols' in config:
                    self.blacklisted_symbols = set(config['blacklisted_symbols'])
                
                if 'max_correlated_trades' in config:
                    self.max_correlated_trades = config['max_correlated_trades']
                
                logger.info(f"✅ Risk config loaded from {self.config_file}")
            
            except Exception as e:
                logger.warn(f"⚠️  Failed to load risk config: {e}, using defaults")
        else:
            logger.debug("Using default risk configuration")
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config = {
                'allowed_symbols': list(self.allowed_symbols),
                'blacklisted_symbols': list(self.blacklisted_symbols),
                'max_correlated_trades': self.max_correlated_trades,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"✅ Risk config saved to {self.config_file}")
        
        except Exception as e:
            logger.error(f"❌ Failed to save risk config: {e}")
    
    def reset_daily_counters(self):
        """Reset daily tracking counters at the start of a new day (UTC)."""
        today = datetime.now(timezone.utc).date()
        
        if today > self.last_reset_date:
            logger.info(f"📅 Daily reset: {self.last_reset_date} → {today}")
            self.equity_start_of_day = self.current_equity
            self.daily_pnl = 0.0
            self.last_reset_date = today
            
            # Reset circuit breaker if it was triggered yesterday
            if self.circuit_breaker_active:
                logger.info("🔓 Circuit breaker reset for new day")
                self.circuit_breaker_active = False
                self.circuit_breaker_triggered_at = None
    
    def reset_weekly_counters(self):
        """Reset weekly tracking counters at the start of a new week."""
        current_week = datetime.now(timezone.utc).isocalendar()[1]
        
        if current_week != self.last_reset_week:
            logger.info(f"📅 Weekly reset: Week {self.last_reset_week} → Week {current_week}")
            self.equity_start_of_week = self.current_equity
            self.weekly_pnl = 0.0
            self.last_reset_week = current_week
    
    def update_equity(self, new_equity: float):
        """
        Update current equity and calculate daily/weekly PnL.

        Args:
            new_equity: Updated account equity
        """
        self.reset_daily_counters()
        self.reset_weekly_counters()
        
        self.current_equity = new_equity
        self.daily_pnl = new_equity - self.equity_start_of_day
        self.weekly_pnl = new_equity - self.equity_start_of_week
    
    def check_circuit_breaker(self, current_pnl: Optional[float] = None) -> bool:
        """
        🔴 CIRCUIT BREAKER: Check if daily or weekly loss limits breached.
        
        Args:
            current_pnl: Override PnL (uses self.daily_pnl if None)
        
        Returns:
            True if circuit breaker activated, False otherwise
        """
        self.reset_daily_counters()
        self.reset_weekly_counters()
        
        pnl = current_pnl if current_pnl is not None else self.daily_pnl
        
        # Calculate loss percentages
        daily_loss_pct = abs(pnl / self.equity_start_of_day) if pnl < 0 else 0
        weekly_loss_pct = abs(self.weekly_pnl / self.equity_start_of_week) if self.weekly_pnl < 0 else 0
        
        # Check daily limit
        if daily_loss_pct >= RiskConfig.DAILY_LOSS_LIMIT_PCT:
            if not self.circuit_breaker_active:
                self.circuit_breaker_active = True
                self.circuit_breaker_triggered_at = datetime.now(timezone.utc)
                self.stats['circuit_breaker_triggers'] += 1
                
                logger.error(
                    f"🔴 CIRCUIT BREAKER ACTIVATED: Daily loss limit breached\n"
                    f"   Current PnL: ${pnl:.2f} ({daily_loss_pct*100:.2f}%)\n"
                    f"   Limit: {RiskConfig.DAILY_LOSS_LIMIT_PCT*100:.1f}%\n"
                    f"   ALL TRADING HALTED"
                )
            
            return True
        
        # Check weekly limit (if configured)
        if hasattr(RiskConfig, 'WEEKLY_LOSS_LIMIT_PCT'):
            if weekly_loss_pct >= RiskConfig.WEEKLY_LOSS_LIMIT_PCT:
                if not self.circuit_breaker_active:
                    self.circuit_breaker_active = True
                    self.circuit_breaker_triggered_at = datetime.now(timezone.utc)
                    self.stats['circuit_breaker_triggers'] += 1
                    
                    logger.error(
                        f"🔴 CIRCUIT BREAKER ACTIVATED: Weekly loss limit breached\n"
                        f"   Weekly PnL: ${self.weekly_pnl:.2f} ({weekly_loss_pct*100:.2f}%)\n"
                        f"   Limit: {RiskConfig.WEEKLY_LOSS_LIMIT_PCT*100:.1f}%\n"
                        f"   ALL TRADING HALTED"
                    )
                
                return True
        
        return False
    
    def check_kill_switch(self) -> bool:
        """
        🔪 KILL SWITCH: Check if emergency stop file exists.
        
        Returns:
            True if kill switch active, False otherwise
        """
        self.stats['kill_switch_checks'] += 1
        
        if self.kill_switch_file.exists():
            logger.error(
                f"🔪 KILL SWITCH ACTIVE: {self.kill_switch_file} exists\n"
                f"   Remove file to resume trading"
            )
            return True
        
        return False

    def can_trade(self) -> bool:
        """Return True if trading is allowed (no kill switch/circuit breaker)."""
        if self.check_kill_switch():
            return False
        if self.circuit_breaker_active or self.check_circuit_breaker():
            return False
        return True
    
    def validate_signal(
        self,
        symbol: str,
        side: str,
        entry: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        open_positions: Optional[List[Dict]] = None
    ) -> ValidationResult:
        """
        🛡️ GATEKEEPER: Validate a trading signal against all risk rules.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            side: "LONG" or "SHORT"
            entry: Entry price
            sl: Stop loss price
            tp: Take profit price
            open_positions: List of currently open positions
        
        Returns:
            ValidationResult with valid flag and reason
        """
        self.stats['total_validations'] += 1
        warnings = []
        
        # ===== CRITICAL CHECKS (REJECT IF FAIL) =====
        
        # 1. Kill switch check
        if self.check_kill_switch():
            self.stats['signals_rejected'] += 1
            return ValidationResult(
                valid=False,
                reason="Kill switch active - trading halted"
            )
        
        # 2. Circuit breaker check
        if self.circuit_breaker_active or self.check_circuit_breaker():
            self.stats['signals_rejected'] += 1
            return ValidationResult(
                valid=False,
                reason="Circuit breaker active - loss limits exceeded"
            )
        
        # 3. Whitelist check (if whitelist is enforced)
        if self.allowed_symbols and symbol not in self.allowed_symbols:
            self.stats['signals_rejected'] += 1
            return ValidationResult(
                valid=False,
                reason=f"Symbol {symbol} not in whitelist"
            )
        
        # 4. Blacklist check
        if symbol in self.blacklisted_symbols:
            self.stats['signals_rejected'] += 1
            return ValidationResult(
                valid=False,
                reason=f"Symbol {symbol} is blacklisted"
            )
        
        # 5. Price sanity checks
        if entry <= 0:
            self.stats['signals_rejected'] += 1
            return ValidationResult(
                valid=False,
                reason="Invalid entry price (<= 0)"
            )
        
        if sl and sl <= 0:
            self.stats['signals_rejected'] += 1
            return ValidationResult(
                valid=False,
                reason="Invalid stop loss price (<= 0)"
            )
        
        if tp and tp <= 0:
            self.stats['signals_rejected'] += 1
            return ValidationResult(
                valid=False,
                reason="Invalid take profit price (<= 0)"
            )
        
        # 6. TP/SL relationship validation
        side_upper = side.upper()
        
        if side_upper in ["LONG", "BUY"]:
            if sl and sl >= entry:
                self.stats['signals_rejected'] += 1
                return ValidationResult(
                    valid=False,
                    reason=f"SL ({sl}) must be below entry ({entry}) for LONG"
                )
            
            if tp and tp <= entry:
                self.stats['signals_rejected'] += 1
                return ValidationResult(
                    valid=False,
                    reason=f"TP ({tp}) must be above entry ({entry}) for LONG"
                )
        
        elif side_upper in ["SHORT", "SELL"]:
            if sl and sl <= entry:
                self.stats['signals_rejected'] += 1
                return ValidationResult(
                    valid=False,
                    reason=f"SL ({sl}) must be above entry ({entry}) for SHORT"
                )
            
            if tp and tp >= entry:
                self.stats['signals_rejected'] += 1
                return ValidationResult(
                    valid=False,
                    reason=f"TP ({tp}) must be below entry ({entry}) for SHORT"
                )
        
        # ===== WARNING CHECKS (ALLOW BUT WARN) =====
        
        # 7. Correlation check (prevent over-exposure to correlated assets)
        if open_positions:
            correlation_violation = self._check_correlation_limit(symbol, open_positions)
            if correlation_violation:
                warnings.append(correlation_violation)
        
        # 8. Risk/Reward ratio check
        if sl and tp:
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            rr_ratio = reward / risk if risk > 0 else 0
            
            if rr_ratio < 1.5:
                warnings.append(
                    f"Low R:R ratio {rr_ratio:.2f} (recommended: >1.5)"
                )
        
        # 9. Stop loss too wide check
        if sl:
            sl_distance_pct = abs(entry - sl) / entry * 100
            if sl_distance_pct > 10:
                warnings.append(
                    f"Stop loss very wide: {sl_distance_pct:.1f}% from entry"
                )
        
        # ===== SIGNAL APPROVED =====
        self.stats['signals_approved'] += 1
        
        result = ValidationResult(
            valid=True,
            reason="Signal validated",
            warnings=warnings
        )
        
        if warnings:
            logger.warn(f"⚠️  Signal approved with warnings: {', '.join(warnings)}")
        
        return result
    
    def _check_correlation_limit(
        self,
        new_symbol: str,
        open_positions: List[Dict]
    ) -> Optional[str]:
        """
        Check if adding this symbol would exceed correlation limits.
        
        Args:
            new_symbol: Symbol to check
            open_positions: List of dicts with 'symbol' key
        
        Returns:
            Warning message if limit exceeded, None otherwise
        """
        # Find correlation group(s) for new symbol
        new_symbol_groups = []
        for group_name, symbols in self.CORRELATION_GROUPS.items():
            if new_symbol in symbols:
                new_symbol_groups.append(group_name)
        
        if not new_symbol_groups:
            return None  # Symbol not in any correlation group
        
        # Count existing positions in each group
        for group_name in new_symbol_groups:
            group_symbols = self.CORRELATION_GROUPS[group_name]
            
            # Count how many positions are in this group
            positions_in_group = sum(
                1 for pos in open_positions
                if pos.get('symbol') in group_symbols
            )
            
            if positions_in_group >= self.max_correlated_trades:
                existing_symbols = [
                    pos.get('symbol') for pos in open_positions
                    if pos.get('symbol') in group_symbols
                ]
                return (
                    f"Correlation limit: {positions_in_group}/{self.max_correlated_trades} "
                    f"positions in {group_name} ({', '.join(existing_symbols)})"
                )
        
        return None
    
    def calculate_safe_quantity(
        self,
        equity: float,
        entry_price: float,
        sl_price: Optional[float] = None,
        risk_pct: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate safe position size using risk-per-trade logic.
        
        Formula: 
            Risk Amount = Equity × Risk%
            Position Size = Risk Amount / (Entry - SL)
        
        Args:
            equity: Current account equity
            entry_price: Entry price
            sl_price: Stop loss price (required for accurate sizing)
            risk_pct: Risk percentage override (uses config default if None)
        
        Returns:
            Dict with 'quantity', 'position_value', 'risk_amount'
        """
        # Get risk percentage
        risk_pct = risk_pct or RiskConfig.RISK_PER_TRADE_PCT if hasattr(RiskConfig, 'RISK_PER_TRADE_PCT') else 0.01
        risk_amount = equity * risk_pct
        
        # Calculate position size based on stop loss
        if sl_price and sl_price != entry_price:
            # Risk-based position sizing (recommended)
            risk_per_unit = abs(entry_price - sl_price)
            quantity = risk_amount / risk_per_unit
        else:
            # Fallback: use 2% of entry as assumed risk
            logger.warn("⚠️  No SL provided, using 2% of entry as risk distance")
            risk_per_unit = entry_price * 0.02
            quantity = risk_amount / risk_per_unit
        
        position_value = quantity * entry_price
        
        return {
            'quantity': round(quantity, 6),
            'position_value': round(position_value, 2),
            'risk_amount': round(risk_amount, 2),
            'risk_per_unit': round(risk_per_unit, 6)
        }
    
    def check_position_limit(self, current_positions: int) -> bool:
        """
        Check if maximum concurrent positions limit is reached.

        Args:
            current_positions: Number of currently open positions

        Returns:
            True if limit reached, False otherwise
        """
        if current_positions >= RiskConfig.MAX_CONCURRENT_TRADES:
            logger.warn(
                f"⚠️  Position limit reached: "
                f"{current_positions}/{RiskConfig.MAX_CONCURRENT_TRADES}"
            )
            return True
        return False
    
    def add_to_whitelist(self, symbol: str):
        """Add symbol to whitelist."""
        self.allowed_symbols.add(symbol)
        logger.info(f"➕ Added {symbol} to whitelist")
        self.save_config()
    
    def remove_from_whitelist(self, symbol: str):
        """Remove symbol from whitelist."""
        if symbol in self.allowed_symbols:
            self.allowed_symbols.remove(symbol)
            logger.info(f"➖ Removed {symbol} from whitelist")
            self.save_config()
    
    def add_to_blacklist(self, symbol: str):
        """Add symbol to blacklist."""
        self.blacklisted_symbols.add(symbol)
        logger.info(f"🚫 Added {symbol} to blacklist")
        self.save_config()
    
    def remove_from_blacklist(self, symbol: str):
        """Remove symbol from blacklist."""
        if symbol in self.blacklisted_symbols:
            self.blacklisted_symbols.remove(symbol)
            logger.info(f"✅ Removed {symbol} from blacklist")
            self.save_config()
    
    def activate_kill_switch(self, reason: str = "Manual activation"):
        """
        Activate the kill switch (create emergency stop file).
        
        Args:
            reason: Reason for activation
        """
        try:
            self.kill_switch_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.kill_switch_file, 'w') as f:
                f.write(json.dumps({
                    'activated_at': datetime.now(timezone.utc).isoformat(),
                    'reason': reason
                }, indent=2))
            
            logger.error(f"🔪 KILL SWITCH ACTIVATED: {reason}")
        
        except Exception as e:
            logger.error(f"❌ Failed to activate kill switch: {e}")
    
    def deactivate_kill_switch(self):
        """Deactivate the kill switch (remove emergency stop file)."""
        try:
            if self.kill_switch_file.exists():
                self.kill_switch_file.unlink()
                logger.info("🔓 Kill switch deactivated")
            else:
                logger.info("Kill switch was not active")
        
        except Exception as e:
            logger.error(f"❌ Failed to deactivate kill switch: {e}")
    
    def get_risk_metrics(self) -> RiskMetrics:
        """
        Get comprehensive risk metrics snapshot.
        
        Returns:
            RiskMetrics dataclass with all current metrics
        """
        self.reset_daily_counters()
        self.reset_weekly_counters()
        
        max_daily_loss = self.equity_start_of_day * RiskConfig.DAILY_LOSS_LIMIT_PCT
        remaining_daily_risk = max_daily_loss + self.daily_pnl
        
        daily_pnl_pct = (self.daily_pnl / self.equity_start_of_day * 100) if self.equity_start_of_day > 0 else 0
        weekly_pnl_pct = (self.weekly_pnl / self.equity_start_of_week * 100) if self.equity_start_of_week > 0 else 0
        
        return RiskMetrics(
            current_equity=self.current_equity,
            daily_pnl=self.daily_pnl,
            daily_pnl_pct=daily_pnl_pct,
            weekly_pnl=self.weekly_pnl,
            weekly_pnl_pct=weekly_pnl_pct,
            max_daily_loss=max_daily_loss,
            remaining_daily_risk=remaining_daily_risk,
            circuit_breaker_active=self.circuit_breaker_active,
            kill_switch_active=self.kill_switch_file.exists()
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get sentinel statistics."""
        return {
            **self.stats,
            'approval_rate': (
                self.stats['signals_approved'] / self.stats['total_validations'] * 100
                if self.stats['total_validations'] > 0 else 0
            )
        }
    
    def print_status(self):
        """Print comprehensive status report."""
        metrics = self.get_risk_metrics()
        
        logger.info("\n" + "="*60)
        logger.info("🛡️  RISK SENTINEL STATUS")
        logger.info("="*60)
        logger.info(f"Equity: ${metrics.current_equity:,.2f}")
        logger.info(f"Daily PnL: ${metrics.daily_pnl:+,.2f} ({metrics.daily_pnl_pct:+.2f}%)")
        logger.info(f"Weekly PnL: ${metrics.weekly_pnl:+,.2f} ({metrics.weekly_pnl_pct:+.2f}%)")
        logger.info(f"Remaining Daily Risk: ${metrics.remaining_daily_risk:,.2f}")
        logger.info(f"Circuit Breaker: {'🔴 ACTIVE' if metrics.circuit_breaker_active else '🟢 Normal'}")
        logger.info(f"Kill Switch: {'🔴 ACTIVE' if metrics.kill_switch_active else '🟢 Normal'}")
        logger.info(f"\nWhitelist: {len(self.allowed_symbols)} symbols")
        logger.info(f"Blacklist: {len(self.blacklisted_symbols)} symbols")
        
        stats = self.get_stats()
        logger.info(f"\nValidations: {stats['total_validations']}")
        logger.info(f"Approved: {stats['signals_approved']} ({stats['approval_rate']:.1f}%)")
        logger.info(f"Rejected: {stats['signals_rejected']}")
        logger.info(f"Circuit Breakers: {stats['circuit_breaker_triggers']}")
        logger.info("="*60 + "\n")


# Legacy alias for backward compatibility
class RiskManager(RiskSentinel):
    """Legacy alias - use RiskSentinel instead."""
    pass


if __name__ == "__main__":
    # Test Risk Sentinel
    logger.info("🧪 Testing Risk Sentinel\n")
    
    sentinel = RiskSentinel(initial_equity=10000)
    
    # Test 1: Normal validation
    logger.info("Test 1: Normal signal validation")
    result = sentinel.validate_signal(
        symbol="BTCUSDT",
        side="LONG",
        entry=42000,
        sl=40000,
        tp=45000
    )
    logger.info(f"Result: {result}\n")
    
    # Test 2: Blacklisted symbol
    logger.info("Test 2: Blacklisted symbol")
    result = sentinel.validate_signal(
        symbol="LUNAUSTD",
        side="LONG",
        entry=1.0,
        sl=0.9,
        tp=1.2
    )
    logger.info(f"Result: {result}\n")
    
    # Test 3: Circuit breaker
    logger.info("Test 3: Circuit breaker activation")
    sentinel.update_equity(9400)  # -6% loss
    is_triggered = sentinel.check_circuit_breaker()
    logger.info(f"Circuit breaker triggered: {is_triggered}\n")
    
    # Test 4: Position sizing
    logger.info("Test 4: Safe position sizing")
    sizing = sentinel.calculate_safe_quantity(
        equity=10000,
        entry_price=42000,
        sl_price=40000
    )
    logger.info(f"Position sizing: {sizing}\n")
    
    # Test 5: Print status
    sentinel.print_status()
    
    # Test 6: Statistics
    stats = sentinel.get_stats()
    logger.info(f"Statistics: {stats}\n")
