"""
Paper Trading Bot
Monitors selected Telegram channels and auto-trades signals in paper mode
"""
import asyncio
import ccxt.async_support as ccxt
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from telethon import TelegramClient, events
from telethon.sessions import StringSession

from utils.config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_PHONE,
    PAPER_TRADING_CHANNELS,
    PAPER_TRADING_ENABLED,
    EXCHANGE_NAME
)
from parsers.enhanced_parser import EnhancedParser
from trading.paper_portfolio import PaperPortfolio
from trading.paper_trade_manager import PaperTradeManager
from trading.trade_logger import TradeLogger


# Channel ID to name mapping (for logging)
CHANNEL_NAMES = {
    -1001370457350: "Crypto Neon",
    -1001787704873: "Deep Web Kripto",
    -1001585663048: "Kripto Kampı",
    -1002293653904: "Kripto Star",
    -1002422904239: "Kripto Simpsons",
    -1001858456624: "Crypto Trading ®",
    -1002001037199: "Kripto Delisi VIP"
}


class PaperTradingBot:
    """Paper trading bot with live signal monitoring."""
    
    def __init__(self):
        """Initialize bot components."""
        self.client = None
        self.exchange = None
        self.parser = EnhancedParser()
        self.portfolio = PaperPortfolio()
        self.trade_manager = PaperTradeManager(self.portfolio)
        self.logger = TradeLogger()
        
        print("=" * 70)
        print("🤖 PAPER TRADING BOT")
        print("=" * 70)
        print(f"Initial Balance: ${self.portfolio.initial_balance:.2f}")
        print(f"Position Size: {self.portfolio.get_available_balance():.2f} per trade")
        print(f"Monitoring {len(PAPER_TRADING_CHANNELS)} channels")
        print("=" * 70)
    
    async def initialize_exchange(self):
        """Initialize CCXT exchange connection."""
        print(f"📊 Connecting to {EXCHANGE_NAME.upper()}...")
        
        if EXCHANGE_NAME.lower() == "mexc":
            self.exchange = ccxt.mexc({
                'enableRateLimit': True,
                'options': {'defaultType': 'swap'}  # Futures
            })
        else:
            self.exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            })
        
        await self.exchange.load_markets()
        print(f"✅ Connected to {EXCHANGE_NAME.upper()} ({len(self.exchange.markets)} markets)")
    
    async def get_current_prices(self, symbols):
        """
        Get current prices for multiple symbols.
        
        Args:
            symbols: List of symbols (e.g., ['BTC/USDT', 'ETH/USDT'])
            
        Returns:
            dict: {symbol: price}
        """
        prices = {}
        
        for symbol in symbols:
            try:
                ticker = await self.exchange.fetch_ticker(symbol)
                prices[symbol] = ticker['last']
            except Exception as e:
                print(f"⚠️ Failed to fetch {symbol}: {e}")
        
        return prices
    
    async def price_monitor(self):
        """Background task to monitor prices and update positions."""
        print("📈 Starting price monitor...")
        
        while True:
            try:
                # Get symbols of open positions
                symbols = list(set(
                    pos['symbol'] for pos in self.portfolio.open_positions.values()
                ))
                
                if symbols:
                    # Fetch current prices
                    prices = await self.get_current_prices(symbols)
                    
                    # Update positions and check for exits
                    closed_trades = self.trade_manager.update_positions(prices)
                    
                    # Log closed trades
                    for trade in closed_trades:
                        self.logger.log_trade(trade)
                
                # Update every 5 seconds
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"⚠️ Price monitor error: {e}")
                await asyncio.sleep(10)
    
    async def handle_signal(self, event):
        """
        Handle incoming signal from Telegram.
        
        Args:
            event: Telethon new message event
        """
        try:
            message = event.message.text
            channel_id = event.chat_id
            channel_name = CHANNEL_NAMES.get(channel_id, f"Channel {channel_id}")
            
            # Parse signal
            signal = self.parser.parse(message)
            
            # Log signal reception
            self.logger.log_signal(signal, "RECEIVED")
            
            # Validate signal
            if not signal.symbol or not signal.side or not signal.entry_min:
                print(f"⚠️ [{channel_name}] Invalid signal (missing fields)")
                self.logger.log_signal(signal, "REJECTED")
                return
            
            if signal.confidence < 0.7:
                print(f"⚠️ [{channel_name}] Low confidence signal: {signal.confidence:.2f}")
                self.logger.log_signal(signal, "REJECTED")
                return
            
            # Check if symbol exists on exchange
            if signal.symbol not in self.exchange.markets:
                print(f"⚠️ [{channel_name}] Symbol not found on exchange: {signal.symbol}")
                self.logger.log_signal(signal, "REJECTED")
                return
            
            # Open position
            print(f"\n🎯 [{channel_name}] New signal: {signal.side} {signal.symbol}")
            position = self.trade_manager.open_position(signal, channel_name)
            
            if position:
                self.logger.log_signal(signal, "OPENED")
                
                # Print portfolio stats
                stats = self.portfolio.get_stats()
                print(f"💰 Balance: ${stats['current_balance']:.2f} | PnL: ${stats['total_pnl']:.2f} ({stats['total_pnl_pct']:.2f}%)")
                print(f"📊 Open: {stats['open_positions']} | Total: {stats['total_trades']} | Win Rate: {stats['win_rate']:.1f}%\n")
            else:
                self.logger.log_signal(signal, "REJECTED")
        
        except Exception as e:
            print(f"⚠️ Error handling signal: {e}")
    
    async def start(self):
        """Start the paper trading bot."""
        if not PAPER_TRADING_ENABLED:
            print("❌ Paper trading is disabled in config")
            return
        
        if not PAPER_TRADING_CHANNELS:
            print("❌ No channels configured for paper trading")
            return
        
        # Initialize exchange
        await self.initialize_exchange()
        
        # Initialize Telegram client
        print(f"\n📱 Connecting to Telegram...")
        self.client = TelegramClient(StringSession(), TELEGRAM_API_ID, TELEGRAM_API_HASH)
        await self.client.start(phone=TELEGRAM_PHONE)
        print(f"✅ Connected as {TELEGRAM_PHONE}\n")
        
        # Print monitored channels
        print("📡 Monitoring channels:")
        for channel_id in PAPER_TRADING_CHANNELS:
            name = CHANNEL_NAMES.get(channel_id, f"Unknown ({channel_id})")
            print(f"   • {name}")
        print()
        
        # Register signal handler
        @self.client.on(events.NewMessage(chats=PAPER_TRADING_CHANNELS))
        async def message_handler(event):
            await self.handle_signal(event)
        
        # Start price monitor in background
        asyncio.create_task(self.price_monitor())
        
        print("✅ Paper trading bot is running!")
        print("=" * 70)
        print("Press Ctrl+C to stop\n")
        
        # Keep running
        await self.client.run_until_disconnected()
    
    async def stop(self):
        """Stop the bot and cleanup."""
        print("\n🛑 Stopping bot...")
        
        if self.client:
            await self.client.disconnect()
        
        if self.exchange:
            await self.exchange.close()
        
        # Print final stats
        stats = self.portfolio.get_stats()
        print("\n" + "=" * 70)
        print("📊 FINAL STATISTICS")
        print("=" * 70)
        print(f"Initial Balance: ${stats['initial_balance']:.2f}")
        print(f"Final Balance: ${stats['current_balance']:.2f}")
        print(f"Total PnL: ${stats['total_pnl']:.2f} ({stats['total_pnl_pct']:.2f}%)")
        print(f"Total Trades: {stats['total_trades']}")
        print(f"Win Rate: {stats['win_rate']:.1f}% ({stats['winning_trades']}W / {stats['losing_trades']}L)")
        print(f"Open Positions: {stats['open_positions']}")
        print("=" * 70)


async def main():
    """Main entry point."""
    bot = PaperTradingBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
