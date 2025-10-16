"""
Historical Signal Collection & Backtest with HTML Report
Collects historical messages from Telegram channels and generates detailed analysis report.
"""
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.sessions import StringSession
import sys

sys.path.insert(0, str(Path(__file__).parent))

from utils.config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_CHANNELS, DATA_DIR
from parsers.enhanced_parser import EnhancedParser
from utils.logger import info, warn, error


async def collect_historical_signals(limit=100):
    """
    Collect historical messages from configured Telegram channels.
    
    Args:
        limit: Number of messages to collect per channel
    
    Returns:
        List of collected messages
    """
    info("=" * 70)
    info("📥 HISTORICAL SIGNAL COLLECTION")
    info("=" * 70)
    
    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        error("❌ Telegram API credentials not set. Check .env file.")
        return []
    
    if not TELEGRAM_CHANNELS:
        error("❌ No channels configured. Set TELEGRAM_CHANNELS in .env")
        return []
    
    phone = os.getenv("TELEGRAM_PHONE")
    if not phone:
        error("❌ TELEGRAM_PHONE not set in .env file")
        return []
    
    info(f"📱 Connecting to Telegram...")
    client = TelegramClient(StringSession(), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    
    all_messages = []
    
    try:
        await client.start(phone=phone)
        info(f"✅ Connected as {phone}")
        
        for channel in TELEGRAM_CHANNELS:
            try:
                info(f"\n📡 Collecting from: {channel}")
                
                # Get channel entity
                if isinstance(channel, str) and channel.lstrip('-').isdigit():
                    channel = int(channel)
                
                entity = await client.get_entity(channel)
                channel_name = getattr(entity, "title", getattr(entity, "username", str(channel)))
                
                # Collect messages
                messages = []
                async for message in client.iter_messages(entity, limit=limit):
                    if message.text:
                        messages.append({
                            'channel': channel_name,
                            'channel_id': str(channel),
                            'message_id': message.id,
                            'text': message.text,
                            'date': message.date.isoformat(),
                            'timestamp': message.date.timestamp()
                        })
                
                info(f"   ✅ Collected {len(messages)} messages")
                all_messages.extend(messages)
                
            except Exception as e:
                warn(f"   ⚠️ Failed to collect from {channel}: {e}")
        
        info(f"\n📊 Total collected: {len(all_messages)} messages from {len(TELEGRAM_CHANNELS)} channels")
        
    except Exception as e:
        error(f"❌ Collection error: {e}")
    finally:
        await client.disconnect()
    
    return all_messages


def parse_signals(messages):
    """
    Parse collected messages using enhanced parser with whitelist.
    
    Returns:
        List of successfully parsed signals
    """
    info("\n" + "=" * 70)
    info("🔍 PARSING SIGNALS")
    info("=" * 70)
    
    parser = EnhancedParser()
    parsed_signals = []
    
    for msg in messages:
        try:
            signal = parser.parse(msg['text'])
            
            if signal.symbol and signal.confidence >= 0.6:
                parsed_signals.append({
                    'channel': msg['channel'],
                    'date': msg['date'],
                    'raw_text': msg['text'],
                    'symbol': signal.symbol,
                    'side': signal.side,
                    'entries': signal.entries,
                    'tps': signal.tps,
                    'sl': signal.sl,
                    'leverage': signal.leverage_x,
                    'confidence': signal.confidence,
                    'locale': signal.locale,
                    'notes': signal.parsing_notes
                })
        except Exception as e:
            # Silently skip unparseable messages
            pass
    
    info(f"✅ Successfully parsed: {len(parsed_signals)}/{len(messages)} signals")
    
    # Print parser stats
    stats = parser.get_stats()
    info(f"\n📊 Parser Performance:")
    for key, value in stats.items():
        info(f"   {key}: {value}")
    
    return parsed_signals


def generate_html_report(messages, parsed_signals):
    """
    Generate detailed HTML report with visualizations and statistics.
    """
    info("\n" + "=" * 70)
    info("📝 GENERATING HTML REPORT")
    info("=" * 70)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path("reports") / f"signal_analysis_{timestamp}.html"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Calculate statistics
    total_messages = len(messages)
    total_parsed = len(parsed_signals)
    parse_rate = (total_parsed / total_messages * 100) if total_messages > 0 else 0
    
    # Symbol distribution
    symbols = {}
    for sig in parsed_signals:
        sym = sig['symbol']
        symbols[sym] = symbols.get(sym, 0) + 1
    
    top_symbols = sorted(symbols.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Side distribution
    sides = {'long': 0, 'short': 0, 'unknown': 0}
    for sig in parsed_signals:
        side = sig.get('side', 'unknown')
        sides[side] = sides.get(side, 0) + 1
    
    # Confidence distribution
    high_conf = sum(1 for s in parsed_signals if s['confidence'] >= 0.8)
    med_conf = sum(1 for s in parsed_signals if 0.6 <= s['confidence'] < 0.8)
    low_conf = sum(1 for s in parsed_signals if s['confidence'] < 0.6)
    
    # Language distribution
    locales = {}
    for sig in parsed_signals:
        loc = sig.get('locale', 'unknown')
        locales[loc] = locales.get(loc, 0) + 1
    
    # Channel distribution
    channels = {}
    for msg in messages:
        ch = msg['channel']
        channels[ch] = channels.get(ch, 0) + 1
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sinyal Analiz Raporu - {timestamp}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.15);
        }}
        
        .stat-card h3 {{
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: 700;
            color: #333;
            margin-bottom: 5px;
        }}
        
        .stat-card .label {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .section {{
            padding: 40px;
        }}
        
        .section h2 {{
            font-size: 1.8em;
            color: #333;
            margin-bottom: 25px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        
        .chart {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .bar-chart {{
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}
        
        .bar-item {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .bar-label {{
            min-width: 100px;
            font-weight: 600;
            color: #333;
        }}
        
        .bar-container {{
            flex: 1;
            background: #e9ecef;
            border-radius: 10px;
            height: 30px;
            position: relative;
            overflow: hidden;
        }}
        
        .bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
            color: white;
            font-weight: 600;
            font-size: 0.9em;
            transition: width 0.5s ease;
        }}
        
        .signal-list {{
            display: grid;
            gap: 15px;
        }}
        
        .signal-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }}
        
        .signal-card.long {{
            border-left-color: #10b981;
        }}
        
        .signal-card.short {{
            border-left-color: #ef4444;
        }}
        
        .signal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .signal-symbol {{
            font-size: 1.3em;
            font-weight: 700;
            color: #333;
        }}
        
        .signal-side {{
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
            text-transform: uppercase;
        }}
        
        .signal-side.long {{
            background: #10b981;
            color: white;
        }}
        
        .signal-side.short {{
            background: #ef4444;
            color: white;
        }}
        
        .signal-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 10px;
        }}
        
        .signal-detail {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 8px;
        }}
        
        .signal-detail-label {{
            font-size: 0.8em;
            color: #666;
            margin-bottom: 5px;
        }}
        
        .signal-detail-value {{
            font-weight: 600;
            color: #333;
        }}
        
        .signal-channel {{
            color: #666;
            font-size: 0.9em;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e9ecef;
        }}
        
        .badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 600;
            margin-left: 5px;
        }}
        
        .badge.success {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .badge.warning {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .badge.info {{
            background: #dbeafe;
            color: #1e40af;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #666;
        }}
        
        .footer p {{
            margin: 5px 0;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .signal-details {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Sinyal Analiz Raporu</h1>
            <p>{datetime.now().strftime("%d %B %Y, %H:%M")}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Toplam Mesaj</h3>
                <div class="value">{total_messages}</div>
                <div class="label">Telegram'dan toplanan</div>
            </div>
            
            <div class="stat-card">
                <h3>Parse Edilen</h3>
                <div class="value">{total_parsed}</div>
                <div class="label">{parse_rate:.1f}% başarı oranı</div>
            </div>
            
            <div class="stat-card">
                <h3>Long Sinyaller</h3>
                <div class="value">{sides['long']}</div>
                <div class="label">{sides['long']/max(1,total_parsed)*100:.1f}% alım</div>
            </div>
            
            <div class="stat-card">
                <h3>Short Sinyaller</h3>
                <div class="value">{sides['short']}</div>
                <div class="label">{sides['short']/max(1,total_parsed)*100:.1f}% satım</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 En Çok Sinyal Verilen Coinler</h2>
            <div class="chart">
                <div class="bar-chart">
"""
    
    # Top symbols bar chart
    max_count = top_symbols[0][1] if top_symbols else 1
    for symbol, count in top_symbols:
        percentage = (count / max_count * 100)
        html += f"""
                    <div class="bar-item">
                        <div class="bar-label">{symbol}</div>
                        <div class="bar-container">
                            <div class="bar-fill" style="width: {percentage}%">{count}</div>
                        </div>
                    </div>
"""
    
    html += """
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🎯 Güven Skorları</h2>
            <div class="chart">
                <div class="bar-chart">
"""
    
    # Confidence distribution
    total_conf = high_conf + med_conf + low_conf
    if total_conf > 0:
        html += f"""
                    <div class="bar-item">
                        <div class="bar-label">Yüksek (≥0.8)</div>
                        <div class="bar-container">
                            <div class="bar-fill" style="width: {high_conf/total_conf*100}%">{high_conf}</div>
                        </div>
                    </div>
                    <div class="bar-item">
                        <div class="bar-label">Orta (0.6-0.8)</div>
                        <div class="bar-container">
                            <div class="bar-fill" style="width: {med_conf/total_conf*100}%">{med_conf}</div>
                        </div>
                    </div>
"""
    
    html += """
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>💬 Kanal Dağılımı</h2>
            <div class="chart">
                <div class="bar-chart">
"""
    
    # Channel distribution
    sorted_channels = sorted(channels.items(), key=lambda x: x[1], reverse=True)
    max_ch = sorted_channels[0][1] if sorted_channels else 1
    for channel, count in sorted_channels:
        percentage = (count / max_ch * 100)
        html += f"""
                    <div class="bar-item">
                        <div class="bar-label">{channel[:20]}</div>
                        <div class="bar-container">
                            <div class="bar-fill" style="width: {percentage}%">{count}</div>
                        </div>
                    </div>
"""
    
    html += """
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 Son Sinyaller (En Yeni 20)</h2>
            <div class="signal-list">
"""
    
    # Show latest 20 signals
    for signal in sorted(parsed_signals, key=lambda x: x['date'], reverse=True)[:20]:
        side = signal.get('side', 'unknown')
        side_class = 'long' if side == 'long' else 'short' if side == 'short' else ''
        
        entries_str = ', '.join(f"{e:.4f}" for e in signal['entries']) if signal['entries'] else 'N/A'
        tps_str = ', '.join(f"{tp:.4f}" for tp in signal['tps']) if signal['tps'] else 'N/A'
        sl_str = f"{signal['sl']:.4f}" if signal['sl'] else 'N/A'
        
        conf_class = 'success' if signal['confidence'] >= 0.8 else 'warning' if signal['confidence'] >= 0.6 else 'info'
        locale_flag = '🇹🇷' if signal['locale'] == 'tr' else '🇬🇧' if signal['locale'] == 'en' else '🌐'
        
        html += f"""
                <div class="signal-card {side_class}">
                    <div class="signal-header">
                        <div class="signal-symbol">{signal['symbol']}</div>
                        <div class="signal-side {side_class}">{side.upper() if side != 'unknown' else 'N/A'}</div>
                    </div>
                    <div class="signal-details">
                        <div class="signal-detail">
                            <div class="signal-detail-label">Giriş</div>
                            <div class="signal-detail-value">{entries_str}</div>
                        </div>
                        <div class="signal-detail">
                            <div class="signal-detail-label">Hedefler</div>
                            <div class="signal-detail-value">{tps_str}</div>
                        </div>
                        <div class="signal-detail">
                            <div class="signal-detail-label">Stop Loss</div>
                            <div class="signal-detail-value">{sl_str}</div>
                        </div>
                        <div class="signal-detail">
                            <div class="signal-detail-label">Kaldıraç</div>
                            <div class="signal-detail-value">{signal['leverage'] if signal['leverage'] else 'N/A'}</div>
                        </div>
                    </div>
                    <div class="signal-channel">
                        {locale_flag} {signal['channel']} • {signal['date'][:16]}
                        <span class="badge {conf_class}">Güven: {signal['confidence']:.0%}</span>
                    </div>
                </div>
"""
    
    html += f"""
            </div>
        </div>
        
        <div class="footer">
            <p><strong>OMNI Tech Solutions</strong> - Telegram Sinyal Analiz Sistemi</p>
            <p>Adaptive Whitelist ile geliştirilmiş parser • {total_parsed} sinyal analiz edildi</p>
            <p>Oluşturulma: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Save report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    info(f"✅ Report saved: {report_path}")
    info(f"📊 File size: {report_path.stat().st_size / 1024:.1f} KB")
    
    return report_path


async def main():
    """Main execution flow."""
    info("=" * 70)
    info("🚀 TELEGRAM HISTORICAL SIGNAL ANALYSIS")
    info("=" * 70)
    
    # Step 1: Collect historical signals
    messages = await collect_historical_signals(limit=200)  # 200 messages per channel
    
    if not messages:
        error("❌ No messages collected. Check your Telegram configuration.")
        return
    
    # Save raw messages
    raw_path = DATA_DIR / "signals_raw_historical.jsonl"
    with open(raw_path, 'w', encoding='utf-8') as f:
        for msg in messages:
            f.write(json.dumps(msg, ensure_ascii=False) + '\n')
    info(f"💾 Saved raw messages: {raw_path}")
    
    # Step 2: Parse signals
    parsed_signals = parse_signals(messages)
    
    if not parsed_signals:
        warn("⚠️ No signals could be parsed. Check parser configuration.")
        return
    
    # Save parsed signals
    parsed_path = DATA_DIR / "signals_parsed_historical.json"
    with open(parsed_path, 'w', encoding='utf-8') as f:
        json.dump(parsed_signals, f, ensure_ascii=False, indent=2)
    info(f"💾 Saved parsed signals: {parsed_path}")
    
    # Step 3: Generate HTML report
    report_path = generate_html_report(messages, parsed_signals)
    
    # Step 4: Open report
    info("\n" + "=" * 70)
    info("✅ ANALYSIS COMPLETE!")
    info("=" * 70)
    info(f"📄 HTML Report: {report_path}")
    info(f"📊 Total messages: {len(messages)}")
    info(f"✅ Parsed signals: {len(parsed_signals)}")
    info(f"📈 Parse rate: {len(parsed_signals)/len(messages)*100:.1f}%")
    info("=" * 70)
    
    # Open in browser
    import webbrowser
    try:
        webbrowser.open(str(report_path.absolute()))
        info("🌐 Opening report in browser...")
    except Exception as e:
        warn(f"⚠️ Could not open browser: {e}")
        info(f"📂 Open manually: {report_path.absolute()}")


if __name__ == "__main__":
    asyncio.run(main())
