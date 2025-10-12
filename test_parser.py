"""
Test parser with sample signals from your channels.
"""
from telegram.parser import parse_message

# Test signals from your channels
test_signals = [
    # Signal 1: English format with emoji
    {
        "source": "test_channel_1",
        "ts": "2025-10-13T12:00:00",
        "text": """🟢 LONG
💲 DOGEUSDT
📈 Entry : 0.18869 - 0.18925
🎯 Target 1 - 0.19076
🎯 Target 2 - 0.19228
🎯 Target 3 - 0.19379
🎯 Target 4 - 0.19531
🎯 Target 5 - 0.19682
🛑 Stop Loss : 0.17926

This is not investment advice.""",
    },
    # Signal 2: SETUP format
    {
        "source": "kriptodelisi11",
        "ts": "2025-10-13T12:05:00",
        "text": """#ICNT SHORT SETUP 

Target 1: $0.2045
Target 2: $0.2015
Target 3: $0.1960
Lev: 20x

STOP : $0.2190

Yeni işlem""",
    },
    # Signal 3: Turkish format (avax)
    {
        "source": "kriptokampiislem",
        "ts": "2025-10-13T12:10:00",
        "text": """avax long 

giriş: 21.60
sl: 21.00
tp: 22.30 - 23.40""",
    },
    # Signal 4: Turkish format with leverage (sol)
    {
        "source": "kriptosimpsons",
        "ts": "2025-10-13T12:15:00",
        "text": """#sol $sol 7x kaldıraç long
giriş: 185 | tp: 200
stop: 178""",
    },
]


def test_parser():
    """Test parser with all signal formats."""
    print("\n" + "=" * 80)
    print("TESTING SIGNAL PARSER")
    print("=" * 80 + "\n")

    for i, signal in enumerate(test_signals, 1):
        print(f"Test {i}: {signal['source']}")
        print("-" * 80)
        print("INPUT:")
        print(signal["text"][:150] + "..." if len(signal["text"]) > 150 else signal["text"])
        print("\nOUTPUT:")

        parsed = parse_message(signal)

        if parsed:
            print(f"✅ PARSED SUCCESSFULLY")
            print(f"   Symbol:    {parsed['symbol']}")
            print(f"   Side:      {parsed['side']}")
            print(f"   Entry:     {parsed['entry']}")
            print(f"   TP:        {parsed['tp']}")
            print(f"   SL:        {parsed['sl']}")
            print(f"   Leverage:  {parsed['leverage']}")
        else:
            print("❌ FAILED TO PARSE")

        print("\n")


if __name__ == "__main__":
    test_parser()
