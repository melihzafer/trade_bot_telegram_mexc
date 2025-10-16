"""
Simple HTML Report Generator for Backtest Results
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import info, success, error


def main():
    info("=" * 70)
    info("📊 GENERATING HTML BACKTEST REPORT")
    info("=" * 70)
    
    # Load backtest results
    results_path = Path("data/backtest_results.jsonl")
    
    if not results_path.exists():
        error(f"❌ Results file not found: {results_path}")
        return
    
    results = []
    with open(results_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    
    info(f"✅ Loaded {len(results)} backtest results")
    
    # Calculate statistics
    total = len(results)
    wins = sum(1 for r in results if r.get('outcome') == 'WIN')
    losses = sum(1 for r in results if r.get('outcome') == 'LOSS')
    opens = sum(1 for r in results if r.get('outcome') == 'OPEN')
    errors = sum(1 for r in results if r.get('outcome') == 'ERROR')
    
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    
    # Symbol distribution
    symbols = Counter(r['symbol'] for r in results)
    top_symbols = symbols.most_common(10)
    
    # Side distribution
    sides = Counter(r['side'] for r in results)
    
    # Channel distribution
    channels = Counter(r['source'] for r in results)
    top_channels = channels.most_common(10)
    
    # Generate HTML
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(f"reports/backtest_report_{timestamp}.html")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtest Raporu - {timestamp}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
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
            font-size: 2.8em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{ transform: translateY(-5px); }}
        
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
        
        .stat-card.win {{ border-left: 5px solid #10b981; }}
        .stat-card.loss {{ border-left: 5px solid #ef4444; }}
        .stat-card.open {{ border-left: 5px solid #f59e0b; }}
        .stat-card.winrate {{ border-left: 5px solid #667eea; }}
        
        .section {{
            padding: 40px;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .section:last-child {{ border-bottom: none; }}
        
        .section h2 {{
            font-size: 1.8em;
            color: #333;
            margin-bottom: 25px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
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
            min-width: 120px;
            font-weight: 600;
            color: #333;
            font-size: 0.95em;
        }}
        
        .bar-container {{
            flex: 1;
            background: #e9ecef;
            border-radius: 10px;
            height: 35px;
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
            padding-right: 12px;
            color: white;
            font-weight: 600;
            font-size: 0.9em;
        }}
        
        .signal-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
        }}
        
        .signal-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }}
        
        .signal-card.win {{ border-left-color: #10b981; background: #f0fdf4; }}
        .signal-card.loss {{ border-left-color: #ef4444; background: #fef2f2; }}
        .signal-card.open {{ border-left-color: #f59e0b; background: #fffbeb; }}
        
        .signal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        
        .signal-symbol {{
            font-size: 1.2em;
            font-weight: 700;
            color: #333;
        }}
        
        .signal-outcome {{
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 0.85em;
            text-transform: uppercase;
        }}
        
        .signal-outcome.win {{ background: #10b981; color: white; }}
        .signal-outcome.loss {{ background: #ef4444; color: white; }}
        .signal-outcome.open {{ background: #f59e0b; color: white; }}
        
        .signal-details {{
            font-size: 0.9em;
            color: #666;
            line-height: 1.6;
        }}
        
        .signal-details strong {{ color: #333; }}
        
        .footer {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #666;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{ grid-template-columns: 1fr; }}
            .signal-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Backtest Analiz Raporu</h1>
            <p>{datetime.now().strftime("%d %B %Y, %H:%M")}</p>
            <p style="margin-top: 10px; font-size: 0.95em;">93 Telegram Kanalı • 74,163 Mesaj • 329 Sinyal</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Toplam Sinyal</h3>
                <div class="value">{total}</div>
                <div class="label">Test edilen</div>
            </div>
            
            <div class="stat-card win">
                <h3>✅ Kazanan</h3>
                <div class="value">{wins}</div>
                <div class="label">{wins/total*100:.1f}% başarı</div>
            </div>
            
            <div class="stat-card loss">
                <h3>❌ Kaybeden</h3>
                <div class="value">{losses}</div>
                <div class="label">{losses/total*100:.1f}% kayıp</div>
            </div>
            
            <div class="stat-card open">
                <h3>⏳ Açık</h3>
                <div class="value">{opens}</div>
                <div class="label">{opens/total*100:.1f}% beklemede</div>
            </div>
            
            <div class="stat-card winrate">
                <h3>📈 Win Rate</h3>
                <div class="value">{win_rate:.1f}%</div>
                <div class="label">Başarı oranı</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 En Çok Test Edilen Coinler</h2>
            <div class="bar-chart">
"""
    
    max_count = top_symbols[0][1] if top_symbols else 1
    for symbol, count in top_symbols:
        percentage = (count / max_count * 100)
        html += f"""
                <div class="bar-item">
                    <div class="bar-label">{symbol}</div>
                    <div class="bar-container">
                        <div class="bar-fill" style="width: {percentage}%">{count} sinyal</div>
                    </div>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Yön Dağılımı</h2>
            <div class="bar-chart">
"""
    
    total_sides = sum(sides.values())
    for side, count in sides.most_common():
        percentage = (count / total_sides * 100) if total_sides > 0 else 0
        html += f"""
                <div class="bar-item">
                    <div class="bar-label">{side}</div>
                    <div class="bar-container">
                        <div class="bar-fill" style="width: {percentage}%">{count} ({percentage:.1f}%)</div>
                    </div>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <div class="section">
            <h2>📱 En Aktif Kanallar</h2>
            <div class="bar-chart">
"""
    
    max_ch = top_channels[0][1] if top_channels else 1
    for channel, count in top_channels:
        percentage = (count / max_ch * 100)
        # Truncate long channel names
        display_name = channel[:30] + "..." if len(channel) > 30 else channel
        html += f"""
                <div class="bar-item">
                    <div class="bar-label" title="{channel}">{display_name}</div>
                    <div class="bar-container">
                        <div class="bar-fill" style="width: {percentage}%">{count}</div>
                    </div>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <div class="section">
            <h2>🎯 Sinyal Detayları (Son 30)</h2>
            <div class="signal-grid">
"""
    
    # Show last 30 signals
    sorted_results = sorted(results, key=lambda x: x.get('timestamp', ''), reverse=True)
    for signal in sorted_results[:30]:
        outcome = signal.get('outcome', 'UNKNOWN').lower()
        outcome_class = 'win' if outcome == 'win' else 'loss' if outcome == 'loss' else 'open'
        
        entry_str = f"{signal.get('entry_min', 'N/A')}"
        tp_str = f"{signal.get('tp', 'N/A')}"
        sl_str = f"{signal.get('sl', 'N/A')}"
        leverage = signal.get('leverage', 'N/A')
        
        html += f"""
                <div class="signal-card {outcome_class}">
                    <div class="signal-header">
                        <div class="signal-symbol">{signal['symbol']}</div>
                        <div class="signal-outcome {outcome_class}">{outcome.upper()}</div>
                    </div>
                    <div class="signal-details">
                        <strong>Yön:</strong> {signal['side']}<br>
                        <strong>Entry:</strong> {entry_str}<br>
                        <strong>TP:</strong> {tp_str}<br>
                        <strong>SL:</strong> {sl_str}<br>
                        <strong>Kaldıraç:</strong> {leverage}x<br>
                        <strong>Kanal:</strong> {signal.get('source', 'Unknown')[:25]}
                    </div>
                </div>
"""
    
    html += f"""
            </div>
        </div>
        
        <div class="footer">
            <p><strong>OMNI Tech Solutions</strong> - Telegram Trading Bot</p>
            <p>Adaptive Whitelist Parser • Enhanced Signal Analysis • MEXC Backtest</p>
            <p>Oluşturulma: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Save report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    success(f"✅ Report generated: {report_path}")
    info(f"📊 File size: {report_path.stat().st_size / 1024:.1f} KB")
    
    # Open in browser
    import webbrowser
    try:
        webbrowser.open(str(report_path.absolute()))
        success("🌐 Opening report in browser...")
    except Exception as e:
        error(f"⚠️ Could not open browser: {e}")
        info(f"📂 Open manually: file:///{report_path.absolute()}")
    
    info("=" * 70)


if __name__ == "__main__":
    main()
