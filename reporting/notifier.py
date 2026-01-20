"""
📢 Telegram Notifier - The Voice of Project Chimera
Sends alerts, trade notifications, and reports to admin via Telegram Bot API.

Author: Project Chimera Team
Version: 1.0.2 (Manual DNS resolution for Windows)
"""

import os
import socket
import asyncio
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
import aiohttp
from dataclasses import dataclass

from utils.logger import info, error, warn, success


@dataclass
class NotificationStats:
    """Tracks notification statistics."""
    total_sent: int = 0
    alerts_sent: int = 0
    trades_sent: int = 0
    reports_sent: int = 0
    failures: int = 0
    last_sent: Optional[datetime] = None


class TelegramNotifier:
    """
    🔔 Telegram Notifier
    
    Sends real-time notifications to admin via Telegram Bot API.
    Separate from TelegramClient (which listens). This sends.
    
    Features:
    - Async, non-blocking notifications
    - Trade alerts (entry, exit, rejected)
    - Risk alerts (circuit breaker, kill switch)
    - Daily PnL reports
    - Retry logic with exponential backoff
    - Statistics tracking
    - Manual DNS resolution (Windows IPv6 fix)
    
    Usage:
        notifier = TelegramNotifier()
        await notifier.send_alert("⚠️ Circuit breaker activated!")
        await notifier.send_trade_notification(signal, result)
    """
    
    # Telegram API hostname
    TELEGRAM_HOST = "api.telegram.org"
    
    def __init__(
        self,
        bot_token: Optional[str] = None,
        admin_chat_id: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Telegram Notifier.
        
        Args:
            bot_token: Telegram Bot API token (from @BotFather)
            admin_chat_id: Admin's chat ID (your Telegram user ID)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        # Load from environment if not provided
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.admin_chat_id = admin_chat_id or os.getenv("ADMIN_CHAT_ID")
        
        if not self.bot_token:
            error("❌ TELEGRAM_BOT_TOKEN not set! Notifications disabled.")
            self.enabled = False
        elif not self.admin_chat_id:
            error("❌ ADMIN_CHAT_ID not set! Notifications disabled.")
            self.enabled = False
        else:
            self.enabled = True
            info(f"📢 Telegram Notifier initialized (Admin: {self.admin_chat_id})")
        
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Statistics
        self.stats = NotificationStats()
        
        # Session (reuse for performance)
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
        
        # Manual DNS resolution cache
        self._resolved_ip: Optional[str] = None
        self._dns_cache_time: Optional[datetime] = None
        self._dns_cache_ttl = 300  # 5 minutes
    
    def _resolve_telegram_ip(self) -> Optional[str]:
        """
        Manually resolve Telegram API hostname to IP address.
        
        This bypasses aiohttp's internal DNS resolver which fails on Windows
        when IPv6 is attempted but not properly configured.
        
        Returns:
            IP address string or None if resolution fails
        """
        try:
            # Check if cached IP is still valid
            if self._resolved_ip and self._dns_cache_time:
                age = (datetime.now() - self._dns_cache_time).total_seconds()
                if age < self._dns_cache_ttl:
                    return self._resolved_ip
            
            # Manually resolve DNS using socket (IPv4 only)
            ip_address = socket.gethostbyname(self.TELEGRAM_HOST)
            
            # Cache the result
            self._resolved_ip = ip_address
            self._dns_cache_time = datetime.now()
            
            info(f"✅ Resolved {self.TELEGRAM_HOST} → {ip_address}")
            return ip_address
            
        except socket.gaierror as e:
            error(f"❌ DNS resolution failed for {self.TELEGRAM_HOST}: {e}")
            return None
        except Exception as e:
            error(f"❌ Unexpected error during DNS resolution: {e}")
            return None
    
    def _get_base_url(self) -> tuple[str, Dict[str, str]]:
        """
        Get base URL and headers for Telegram API requests.
        
        Uses manual DNS resolution to get direct IP, then constructs URL.
        The Host header is CRITICAL for Telegram to accept the connection.
        
        Returns:
            Tuple of (base_url, headers_dict)
        """
        # Try manual DNS resolution
        ip_address = self._resolve_telegram_ip()
        
        if ip_address:
            # Use direct IP in URL
            base_url = f"https://{ip_address}/bot{self.bot_token}"
            # CRITICAL: Must set Host header for Telegram to accept request
            headers = {"Host": self.TELEGRAM_HOST}
            return base_url, headers
        else:
            # Fallback to hostname (will likely fail on Windows but worth trying)
            warn(f"⚠️ DNS resolution failed, falling back to hostname URL")
            base_url = f"https://{self.TELEGRAM_HOST}/bot{self.bot_token}"
            headers = {}
            return base_url, headers
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create aiohttp session with Windows IPv4 fix.
        
        This creates a session with IPv4-only connector to avoid Windows
        DNS/IPv6 issues. Combined with manual DNS resolution above.
        """
        if self._session is None or self._session.closed:
            # Create TCP connector with IPv4 only (fixes Windows DNS issue)
            self._connector = aiohttp.TCPConnector(
                family=socket.AF_INET,  # Force IPv4 (no IPv6)
                ssl=False,  # Disable SSL verification (needed for direct IP)
                limit=10,  # Connection pool limit
                ttl_dns_cache=300  # Cache DNS for 5 minutes
            )
            
            # Create session with the connector
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                trust_env=True  # Use system proxy settings if configured
            )
            
            info("✅ aiohttp session created (IPv4-only, manual DNS)")
        
        return self._session
    
    async def start(self):
        """Initialize and start the notifier."""
        info("📢 Telegram Notifier starting...")
        # Pre-initialize session if enabled
        if self.enabled:
            await self._get_session()
    
    async def stop(self):
        """Gracefully shut down the notifier (alias for close)."""
        info("🛑 Telegram Notifier stopping...")
        await self.close()
    
    async def close(self):
        """Close the aiohttp session and connector."""
        if self._session and not self._session.closed:
            await self._session.close()
            info("📢 Telegram Notifier session closed")
        
        if self._connector and not self._connector.closed:
            await self._connector.close()
            info("📢 Telegram Notifier connector closed")
    
    async def _send_message(
        self,
        text: str,
        parse_mode: str = "HTML",
        disable_notification: bool = False
    ) -> bool:
        """
        Internal method to send message to admin.
        
        Args:
            text: Message text (max 4096 chars)
            parse_mode: HTML or Markdown
            disable_notification: Silent notification
        
        Returns:
            bool: Success status
        """
        if not self.enabled:
            warn("⚠️ Notifier disabled. Message not sent.")
            return False
        
        # Truncate if too long
        if len(text) > 4096:
            text = text[:4093] + "..."
        
        # Get base URL and headers (with manual DNS resolution)
        base_url, headers = self._get_base_url()
        url = f"{base_url}/sendMessage"
        
        # Prepare payload
        payload = {
            "chat_id": self.admin_chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification
        }
        
        # Retry logic with exponential backoff
        for attempt in range(1, self.max_retries + 1):
            try:
                session = await self._get_session()
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        self.stats.total_sent += 1
                        self.stats.last_sent = datetime.now()
                        return True
                    else:
                        response_text = await response.text()
                        error(f"❌ Telegram API error {response.status}: {response_text}")
                        
                        # Don't retry on client errors (400-499)
                        if 400 <= response.status < 500:
                            self.stats.failures += 1
                            return False
            
            except asyncio.TimeoutError:
                warn(f"⏱️ Telegram notification timeout (attempt {attempt}/{self.max_retries})")
            
            except aiohttp.ClientConnectorError as e:
                error(f"❌ Connection error (attempt {attempt}/{self.max_retries}): {e}")
                
                # Clear DNS cache on connection error (might be stale)
                if self._resolved_ip:
                    warn(f"🔄 Clearing DNS cache and retrying...")
                    self._resolved_ip = None
                    self._dns_cache_time = None
                
                if attempt == self.max_retries:
                    error(f"💡 Hint: Check internet connection. Windows DNS/IPv6 issue may persist.")
            
            except aiohttp.ClientError as e:
                error(f"❌ aiohttp client error (attempt {attempt}/{self.max_retries}): {e}")
                if attempt == self.max_retries:
                    # Log full traceback on final attempt
                    error(f"Full traceback:\n{traceback.format_exc()}")
            
            except Exception as e:
                error(f"❌ Unexpected error (attempt {attempt}/{self.max_retries}): {type(e).__name__}: {e}")
                if attempt == self.max_retries:
                    error(f"Full traceback:\n{traceback.format_exc()}")
            
            # Exponential backoff
            if attempt < self.max_retries:
                wait_time = 2 ** attempt  # 2, 4, 8 seconds
                await asyncio.sleep(wait_time)
        
        # All retries failed
        self.stats.failures += 1
        error(f"❌ Failed to send notification after {self.max_retries} attempts")
        return False
    
    async def send_alert(self, message: str, critical: bool = False) -> bool:
        """
        Send a general alert to admin.
        
        Args:
            message: Alert message
            critical: If True, sends with sound notification
        
        Returns:
            bool: Success status
        
        Example:
            await notifier.send_alert("⚠️ Circuit breaker activated!", critical=True)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"🔔 <b>Alert</b> [{timestamp}]\n\n{message}"
        
        success_status = await self._send_message(
            formatted,
            disable_notification=not critical
        )
        
        if success_status:
            self.stats.alerts_sent += 1
        
        return success_status
    
    async def send_trade_notification(
        self,
        signal: Any,
        success: bool,
        reason: str = ""
    ) -> bool:
        """
        Send a trade execution notification.
        
        Args:
            signal: Parsed signal object (ParsedSignal) or dict
            success: True if executed, False if rejected/failed
            reason: Rejection/failure reason (optional)
        
        Returns:
            bool: Success status
        
        Example:
            await notifier.send_trade_notification(parsed_signal, True)
            await notifier.send_trade_notification(parsed_signal, False, "Risk limit exceeded")
        """
        timestamp = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        
        # Convert ParsedSignal to dict if needed
        if hasattr(signal, 'to_dict'):
            signal_dict = signal.to_dict()
        elif isinstance(signal, dict):
            signal_dict = signal
        else:
            # Assume it has attributes we can access
            signal_dict = {
                'symbol': getattr(signal, 'symbol', 'N/A'),
                'side': getattr(signal, 'side', 'N/A'),
                'entries': getattr(signal, 'entries', []),
                'tps': getattr(signal, 'tps', []),
                'sl': getattr(signal, 'sl', None),
                'leverage_x': getattr(signal, 'leverage_x', 1),
            }
        
        # Choose emoji and title based on success
        if success:
            emoji = "✅"
            title = "Trade Executed"
            status = "executed"
        else:
            emoji = "🚫"
            title = "Trade Rejected"
            status = "rejected"
        
        # Build message
        message = f"{emoji} <b>{title}</b> [{timestamp}]\n\n"
        
        # Signal details
        symbol = signal_dict.get("symbol", "N/A")
        side = signal_dict.get("side", "N/A")
        entries = signal_dict.get("entries", signal_dict.get("entry", []))
        tps = signal_dict.get("tps", signal_dict.get("tp", []))
        sl = signal_dict.get("sl", None)
        leverage = signal_dict.get("leverage_x", signal_dict.get("leverage", 1))
        
        message += f"📊 <b>Symbol:</b> {symbol}\n"
        message += f"📈 <b>Side:</b> {side.upper() if isinstance(side, str) else side}\n"
        
        # Handle entries (list or single value)
        if isinstance(entries, list) and entries:
            message += f"🎯 <b>Entry:</b> {entries[0]:.4f}"
            if len(entries) > 1:
                message += f" - {entries[-1]:.4f}"
            message += "\n"
        elif entries:
            message += f"🎯 <b>Entry:</b> {float(entries):.4f}\n"
        
        # Handle TPs (list)
        if isinstance(tps, list) and tps:
            message += f"🎯 <b>TP:</b> {tps[0]:.4f}"
            if len(tps) > 1:
                message += f" - {tps[-1]:.4f}"
            message += "\n"
        elif tps:
            message += f"🎯 <b>TP:</b> {float(tps):.4f}\n"
        
        # Handle SL
        if sl:
            message += f"🛑 <b>SL:</b> {float(sl):.4f}\n"
        
        # Handle leverage
        if leverage and leverage > 1:
            message += f"⚡ <b>Leverage:</b> {leverage}x\n"
        
        # Status and reason
        message += f"\n<b>Status:</b> {status.upper()}\n"
        
        if reason:
            message += f"<b>Reason:</b> {reason}\n"
        
        success_status = await self._send_message(message)
        
        if success_status:
            self.stats.trades_sent += 1
        
        return success_status
    
    async def send_daily_report(self, stats: Dict[str, Any]) -> bool:
        """
        Send daily PnL and performance report.
        
        Args:
            stats: Dictionary with daily statistics
                - total_trades: Total number of trades
                - winning_trades: Number of winning trades
                - losing_trades: Number of losing trades
                - total_pnl: Total PnL in USDT
                - win_rate: Win rate percentage
                - largest_win: Largest winning trade
                - largest_loss: Largest losing trade
                - equity: Current equity
        
        Returns:
            bool: Success status
        
        Example:
            await notifier.send_daily_report({
                "total_trades": 15,
                "winning_trades": 9,
                "losing_trades": 6,
                "total_pnl": 350.50,
                "win_rate": 60.0,
                "equity": 10350.50
            })
        """
        timestamp = datetime.now().strftime("%d/%m/%Y")
        
        # Build report
        message = f"📊 <b>Daily Performance Report</b>\n"
        message += f"📅 <b>Date:</b> {timestamp}\n\n"
        
        # Trading activity
        total_trades = stats.get("total_trades", 0)
        winning_trades = stats.get("winning_trades", 0)
        losing_trades = stats.get("losing_trades", 0)
        
        message += f"📈 <b>Trading Activity</b>\n"
        message += f"   Total Trades: {total_trades}\n"
        message += f"   Winning: {winning_trades} ✅\n"
        message += f"   Losing: {losing_trades} ❌\n\n"
        
        # Performance metrics
        total_pnl = stats.get("total_pnl", 0)
        win_rate = stats.get("win_rate", 0)
        
        pnl_emoji = "🟢" if total_pnl > 0 else "🔴" if total_pnl < 0 else "⚪"
        
        message += f"💰 <b>Performance</b>\n"
        message += f"   Total PnL: {pnl_emoji} {total_pnl:+.2f} USDT\n"
        message += f"   Win Rate: {win_rate:.1f}%\n"
        
        if "largest_win" in stats:
            message += f"   Largest Win: +{stats['largest_win']:.2f} USDT\n"
        
        if "largest_loss" in stats:
            message += f"   Largest Loss: {stats['largest_loss']:.2f} USDT\n"
        
        message += "\n"
        
        # Portfolio status
        equity = stats.get("equity", 0)
        
        message += f"💼 <b>Portfolio</b>\n"
        message += f"   Current Equity: {equity:.2f} USDT\n"
        
        if "open_positions" in stats:
            message += f"   Open Positions: {stats['open_positions']}\n"
        
        if "daily_loss_pct" in stats:
            loss_pct = stats["daily_loss_pct"]
            message += f"   Daily Loss: {loss_pct:.2f}%\n"
        
        # Risk status
        if stats.get("circuit_breaker_active"):
            message += f"\n⚠️ <b>Circuit Breaker:</b> ACTIVE 🔴\n"
        
        if stats.get("kill_switch_active"):
            message += f"⚠️ <b>Kill Switch:</b> ACTIVE 🔴\n"
        
        success_status = await self._send_message(message)
        
        if success_status:
            self.stats.reports_sent += 1
        
        return success_status
    
    async def send_startup_notification(self) -> bool:
        """Send notification when bot starts."""
        message = (
            "🚀 <b>Project Chimera Started</b>\n\n"
            "The autonomous trading system is now online.\n"
            f"Started at: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n\n"
            "System Status: ✅ OPERATIONAL"
        )
        return await self._send_message(message)
    
    async def send_startup_alert(self, trading_mode: str) -> bool:
        """Send notification when bot starts (alias with mode info)."""
        message = (
            "🚀 <b>Project Chimera Started</b>\n\n"
            "The autonomous trading system is now online.\n"
            f"Started at: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n"
            f"Trading Mode: <b>{trading_mode.upper()}</b>\n\n"
            "System Status: ✅ OPERATIONAL"
        )
        return await self._send_message(message)
    
    async def send_shutdown_notification(self, reason: str = "Manual shutdown") -> bool:
        """Send notification when bot shuts down."""
        message = (
            "🛑 <b>Project Chimera Shutdown</b>\n\n"
            f"Reason: {reason}\n"
            f"Stopped at: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n\n"
            "System Status: ⏸️ OFFLINE"
        )
        return await self._send_message(message)
    
    async def send_error_notification(self, error_msg: str, critical: bool = True) -> bool:
        """Send error notification."""
        message = (
            "⚠️ <b>System Error Detected</b>\n\n"
            f"<code>{error_msg}</code>\n\n"
            f"Time: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}"
        )
        return await self._send_message(message, disable_notification=not critical)
    
    async def send_risk_alert(self, alert_type: str, details: str) -> bool:
        """Send risk management alert."""
        message = (
            f"🚨 <b>Risk Alert: {alert_type}</b>\n\n"
            f"{details}\n\n"
            f"Time: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}"
        )
        return await self._send_message(message, disable_notification=False)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics."""
        return {
            "total_sent": self.stats.total_sent,
            "alerts_sent": self.stats.alerts_sent,
            "trades_sent": self.stats.trades_sent,
            "reports_sent": self.stats.reports_sent,
            "failures": self.stats.failures,
            "last_sent": self.stats.last_sent.isoformat() if self.stats.last_sent else None,
            "success_rate": (
                (self.stats.total_sent / (self.stats.total_sent + self.stats.failures) * 100)
                if (self.stats.total_sent + self.stats.failures) > 0
                else 0.0
            )
        }
    
    def print_stats(self):
        """Print notification statistics."""
        stats = self.get_stats()
        print("\n" + "="*50)
        print("📢 TELEGRAM NOTIFIER STATISTICS")
        print("="*50)
        print(f"Total Sent:     {stats['total_sent']}")
        print(f"Alerts:         {stats['alerts_sent']}")
        print(f"Trades:         {stats['trades_sent']}")
        print(f"Reports:        {stats['reports_sent']}")
        print(f"Failures:       {stats['failures']}")
        print(f"Success Rate:   {stats['success_rate']:.1f}%")
        print(f"Last Sent:      {stats['last_sent'] or 'Never'}")
        print("="*50 + "\n")


# ============================================
# Usage Example
# ============================================
if __name__ == "__main__":
    async def test_notifier():
        """Test the notifier."""
        notifier = TelegramNotifier()
        
        if not notifier.enabled:
            print("❌ Notifier not configured. Set TELEGRAM_BOT_TOKEN and ADMIN_CHAT_ID.")
            return
        
        # Test alert
        await notifier.send_alert("🧪 Test alert from Project Chimera")
        await asyncio.sleep(1)
        
        # Test trade notification
        signal = {
            "symbol": "BTCUSDT",
            "side": "LONG",
            "entry": [42000.0],
            "tp": [45000.0, 47000.0],
            "sl": 40000.0,
            "leverage": 5
        }
        
        result = {
            "status": "executed",
            "order_id": "TEST_12345",
            "quantity": 0.05,
            "message": "Order executed successfully"
        }
        
        await notifier.send_trade_notification(signal, result)
        await asyncio.sleep(1)
        
        # Test daily report
        stats = {
            "total_trades": 15,
            "winning_trades": 9,
            "losing_trades": 6,
            "total_pnl": 350.50,
            "win_rate": 60.0,
            "largest_win": 120.50,
            "largest_loss": -80.30,
            "equity": 10350.50,
            "open_positions": 2,
            "daily_loss_pct": -1.5
        }
        
        await notifier.send_daily_report(stats)
        
        # Print stats
        notifier.print_stats()
        
        # Clean up
        await notifier.close()
    
    asyncio.run(test_notifier())
