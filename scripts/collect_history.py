"""
Quick script to collect historical Telegram messages.
Run this once to populate signals_raw.jsonl with past messages.
"""
import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram.history_collector import run_history_collector
from utils.logger import info, warn


def main():
    """
    Main entry point for historical collection.
    """
    print("\n" + "=" * 60)
    print("📚 TELEGRAM HISTORICAL MESSAGE COLLECTOR")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Connect to Telegram using your session")
    print("  2. Fetch last 1000 messages from each channel")
    print("  3. Skip any messages already in signals_raw.jsonl")
    print("  4. Save new messages to data/signals_raw.jsonl")
    print("\n" + "-" * 60)
    
    # Ask for confirmation
    response = input("\n⚠️  Ready to start? This may take 5-10 minutes. (y/n): ").strip().lower()
    
    if response != 'y':
        print("❌ Collection cancelled by user.")
        return
    
    print("\n🚀 Starting collection...\n")
    
    # Run the collector
    try:
        asyncio.run(run_history_collector(limit_per_channel=1000))
        print("\n✅ Collection completed successfully!")
        print("📁 Check data/signals_raw.jsonl for results")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted by user (Ctrl+C)")
        print("💡 Partial data has been saved. You can run again to continue.")
        
    except Exception as e:
        print(f"\n❌ Error during collection: {e}")
        print("💡 Check logs for details")
        raise


if __name__ == "__main__":
    main()
