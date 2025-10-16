"""
Enhanced Backtest Report Generator with Channel Performance Analysis
Generates comprehensive HTML report with PnL calculations, channel success rates, and advanced visualizations.
"""
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
import math


def calculate_pnl(result):
    """
    Calculate PnL percentage for a trade based on outcome and price levels.
    For WIN: Calculate actual profit based on TP hit
    For LOSS: Calculate loss based on SL hit
    For OPEN/ERROR: Return 0
    Default leverage: 15x if not specified or NaN
    """
    outcome = result.get('outcome', 'ERROR')
    side = result.get('side', '').upper()
    entry = result.get('entry_min', 0)
    tp = result.get('tp', 0)
    sl = result.get('sl', 0)
    leverage = result.get('leverage', 15.0)
    
    # Handle NaN or invalid leverage values
    if leverage is None or (isinstance(leverage, float) and math.isnan(leverage)) or leverage <= 0:
        leverage = 15.0
    
    if outcome == 'WIN' and tp and entry and tp != 'NaN' and not math.isnan(tp):
        # Calculate profit percentage
        if side == 'LONG':
            pnl_pct = ((tp - entry) / entry) * 100 * leverage
        elif side == 'SHORT':
            pnl_pct = ((entry - tp) / entry) * 100 * leverage
        else:
            pnl_pct = 0
        return round(pnl_pct, 2)
    
    elif outcome == 'LOSS' and sl and entry and sl != 'NaN' and not math.isnan(sl):
        # Calculate loss percentage (negative)
        if side == 'LONG':
            pnl_pct = ((sl - entry) / entry) * 100 * leverage
        elif side == 'SHORT':
            pnl_pct = ((entry - sl) / entry) * 100 * leverage
        else:
            pnl_pct = 0
        return round(pnl_pct, 2)
    
    return 0.0


def analyze_channel_performance(results):
    """
    Analyze performance metrics for each channel.
    Returns dict with channel stats including win rate, PnL, trade count.
    """
    channel_stats = defaultdict(lambda: {
        'total': 0,
        'wins': 0,
        'losses': 0,
        'opens': 0,
        'errors': 0,
        'total_pnl': 0.0,
        'pnl_list': [],
        'symbols': set(),
        'sides': {'LONG': 0, 'SHORT': 0}
    })
    
    for result in results:
        channel = result.get('source', 'Unknown')
        outcome = result.get('outcome', 'ERROR')
        pnl = calculate_pnl(result)
        
        stats = channel_stats[channel]
        stats['total'] += 1
        
        if outcome == 'WIN':
            stats['wins'] += 1
        elif outcome == 'LOSS':
            stats['losses'] += 1
        elif outcome == 'OPEN':
            stats['opens'] += 1
        else:
            stats['errors'] += 1
        
        stats['total_pnl'] += pnl
        stats['pnl_list'].append(pnl)
        stats['symbols'].add(result.get('symbol', ''))
        
        side = result.get('side', '').upper()
        if side in ['LONG', 'SHORT']:
            stats['sides'][side] += 1
    
    # Calculate derived metrics
    for channel, stats in channel_stats.items():
        total_closed = stats['wins'] + stats['losses']
        stats['win_rate'] = (stats['wins'] / total_closed * 100) if total_closed > 0 else 0
        stats['avg_pnl'] = stats['total_pnl'] / stats['total'] if stats['total'] > 0 else 0
        stats['symbols_count'] = len(stats['symbols'])
        
        # Calculate Sharpe-like ratio (simplified)
        if len(stats['pnl_list']) > 1:
            mean_pnl = sum(stats['pnl_list']) / len(stats['pnl_list'])
            variance = sum((x - mean_pnl) ** 2 for x in stats['pnl_list']) / len(stats['pnl_list'])
            std_dev = math.sqrt(variance) if variance > 0 else 1
            stats['sharpe'] = mean_pnl / std_dev if std_dev > 0 else 0
        else:
            stats['sharpe'] = 0
    
    return dict(channel_stats)


def analyze_symbol_performance(results):
    """Analyze performance by symbol."""
    symbol_stats = defaultdict(lambda: {
        'total': 0,
        'wins': 0,
        'losses': 0,
        'win_rate': 0,
        'total_pnl': 0.0,
        'avg_pnl': 0.0
    })
    
    for result in results:
        symbol = result.get('symbol', 'Unknown')
        outcome = result.get('outcome', 'ERROR')
        pnl = calculate_pnl(result)
        
        stats = symbol_stats[symbol]
        stats['total'] += 1
        
        if outcome == 'WIN':
            stats['wins'] += 1
        elif outcome == 'LOSS':
            stats['losses'] += 1
        
        stats['total_pnl'] += pnl
    
    # Calculate derived metrics
    for symbol, stats in symbol_stats.items():
        total_closed = stats['wins'] + stats['losses']
        stats['win_rate'] = (stats['wins'] / total_closed * 100) if total_closed > 0 else 0
        stats['avg_pnl'] = stats['total_pnl'] / stats['total'] if stats['total'] > 0 else 0
    
    return dict(symbol_stats)


def generate_html_report(results):
    """Generate comprehensive HTML report with advanced analytics."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path("reports") / f"detailed_backtest_report_{timestamp}.html"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Basic statistics
    total = len(results)
    wins = sum(1 for r in results if r.get('outcome') == 'WIN')
    losses = sum(1 for r in results if r.get('outcome') == 'LOSS')
    opens = sum(1 for r in results if r.get('outcome') == 'OPEN')
    errors = sum(1 for r in results if r.get('outcome') == 'ERROR')
    
    total_closed = wins + losses
    win_rate = (wins / total_closed * 100) if total_closed > 0 else 0
    
    # Calculate total PnL
    total_pnl = sum(calculate_pnl(r) for r in results)
    avg_pnl = total_pnl / total if total > 0 else 0
    
    # Analyze by channel
    channel_stats = analyze_channel_performance(results)
    sorted_channels = sorted(
        channel_stats.items(),
        key=lambda x: (x[1]['total_pnl'], x[1]['win_rate']),
        reverse=True
    )
    
    # Analyze by symbol
    symbol_stats = analyze_symbol_performance(results)
    sorted_symbols = sorted(
        symbol_stats.items(),
        key=lambda x: x[1]['total_pnl'],
        reverse=True
    )[:15]  # Top 15
    
    # Side distribution
    sides_count = Counter(r.get('side', 'UNKNOWN').upper() for r in results)
    
    # Leverage distribution
    leverage_count = Counter(r.get('leverage', 0) for r in results)
    
    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Detaylı Backtest Raporu - {timestamp}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
            padding: 20px;
            color: #333;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 50px 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 4s ease-in-out infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); opacity: 0.5; }}
            50% {{ transform: scale(1.1); opacity: 0.8; }}
        }}
        
        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            font-weight: 700;
            position: relative;
            z-index: 1;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header .subtitle {{
            font-size: 1.3em;
            opacity: 0.95;
            position: relative;
            z-index: 1;
        }}
        
        .header .date {{
            font-size: 1.1em;
            margin-top: 10px;
            opacity: 0.9;
            position: relative;
            z-index: 1;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        }}
        
        .summary-card {{
            background: white;
            border-radius: 15px;
            padding: 30px 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            border-left: 5px solid #667eea;
            position: relative;
            overflow: hidden;
        }}
        
        .summary-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }}
        
        .summary-card:hover {{
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 12px 30px rgba(0,0,0,0.2);
        }}
        
        .summary-card:hover::before {{
            transform: scaleX(1);
        }}
        
        .summary-card.positive {{
            border-left-color: #10b981;
        }}
        
        .summary-card.negative {{
            border-left-color: #ef4444;
        }}
        
        .summary-card.neutral {{
            border-left-color: #f59e0b;
        }}
        
        .summary-card h3 {{
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        
        .summary-card .value {{
            font-size: 2.8em;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 8px;
            line-height: 1;
        }}
        
        .summary-card .label {{
            color: #6b7280;
            font-size: 0.95em;
            font-weight: 500;
        }}
        
        .section {{
            padding: 50px 40px;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .section:last-child {{
            border-bottom: none;
        }}
        
        .section h2 {{
            font-size: 2em;
            color: #1f2937;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 4px solid #667eea;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .section h2::before {{
            content: '';
            width: 8px;
            height: 40px;
            background: linear-gradient(180deg, #667eea, #764ba2);
            border-radius: 4px;
        }}
        
        .channel-grid {{
            display: grid;
            gap: 25px;
            margin-top: 30px;
        }}
        
        .channel-card {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }}
        
        .channel-card:hover {{
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
            border-color: #667eea;
            transform: translateX(5px);
        }}
        
        .channel-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f3f4f6;
        }}
        
        .channel-name {{
            font-size: 1.5em;
            font-weight: 700;
            color: #1f2937;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .rank-badge {{
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 700;
            box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
        }}
        
        .rank-badge.gold {{
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
        }}
        
        .rank-badge.silver {{
            background: linear-gradient(135deg, #e5e7eb, #9ca3af);
        }}
        
        .rank-badge.bronze {{
            background: linear-gradient(135deg, #fb923c, #ea580c);
        }}
        
        .channel-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .metric {{
            background: linear-gradient(135deg, #f9fafb, #f3f4f6);
            padding: 18px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid #e5e7eb;
        }}
        
        .metric-label {{
            font-size: 0.85em;
            color: #6b7280;
            margin-bottom: 8px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .metric-value {{
            font-size: 1.8em;
            font-weight: 700;
            color: #1f2937;
        }}
        
        .metric-value.positive {{
            color: #10b981;
        }}
        
        .metric-value.negative {{
            color: #ef4444;
        }}
        
        .progress-bar {{
            height: 12px;
            background: #e5e7eb;
            border-radius: 6px;
            overflow: hidden;
            margin-top: 15px;
            position: relative;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #10b981, #059669);
            border-radius: 6px;
            transition: width 1s ease;
            position: relative;
        }}
        
        .progress-fill::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: shimmer 2s infinite;
        }}
        
        @keyframes shimmer {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}
        
        .chart-container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-top: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }}
        
        .bar-chart {{
            display: flex;
            flex-direction: column;
            gap: 18px;
        }}
        
        .bar-item {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .bar-label {{
            min-width: 140px;
            font-weight: 600;
            color: #374151;
            font-size: 0.95em;
        }}
        
        .bar-container {{
            flex: 1;
            background: #f3f4f6;
            border-radius: 8px;
            height: 40px;
            position: relative;
            overflow: hidden;
        }}
        
        .bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 15px;
            color: white;
            font-weight: 700;
            font-size: 0.9em;
            transition: width 1s ease;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .bar-fill.positive {{
            background: linear-gradient(90deg, #10b981, #059669);
        }}
        
        .bar-fill.negative {{
            background: linear-gradient(90deg, #ef4444, #dc2626);
        }}
        
        .signal-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        
        .signal-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            border-left: 5px solid #667eea;
            transition: all 0.3s ease;
        }}
        
        .signal-card:hover {{
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
            transform: translateY(-3px);
        }}
        
        .signal-card.win {{
            border-left-color: #10b981;
            background: linear-gradient(135deg, #ffffff, #f0fdf4);
        }}
        
        .signal-card.loss {{
            border-left-color: #ef4444;
            background: linear-gradient(135deg, #ffffff, #fef2f2);
        }}
        
        .signal-card.open {{
            border-left-color: #f59e0b;
            background: linear-gradient(135deg, #ffffff, #fffbeb);
        }}
        
        .signal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .signal-symbol {{
            font-size: 1.4em;
            font-weight: 700;
            color: #1f2937;
        }}
        
        .signal-badge {{
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .signal-badge.win {{
            background: #10b981;
            color: white;
        }}
        
        .signal-badge.loss {{
            background: #ef4444;
            color: white;
        }}
        
        .signal-badge.open {{
            background: #f59e0b;
            color: white;
        }}
        
        .signal-details {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 15px;
        }}
        
        .signal-detail {{
            background: rgba(0,0,0,0.02);
            padding: 12px;
            border-radius: 8px;
            border: 1px solid rgba(0,0,0,0.05);
        }}
        
        .signal-detail-label {{
            font-size: 0.75em;
            color: #6b7280;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }}
        
        .signal-detail-value {{
            font-weight: 700;
            color: #1f2937;
            font-size: 1.1em;
        }}
        
        .signal-pnl {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-top: 15px;
            font-weight: 700;
            font-size: 1.2em;
        }}
        
        .signal-pnl.positive {{
            background: linear-gradient(135deg, #10b981, #059669);
        }}
        
        .signal-pnl.negative {{
            background: linear-gradient(135deg, #ef4444, #dc2626);
        }}
        
        .signal-footer {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e5e7eb;
            font-size: 0.9em;
            color: #6b7280;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .footer {{
            background: linear-gradient(135deg, #1f2937, #111827);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .footer h3 {{
            font-size: 1.5em;
            margin-bottom: 15px;
            color: #f9fafb;
        }}
        
        .footer p {{
            margin: 8px 0;
            opacity: 0.9;
            font-size: 1.05em;
        }}
        
        .pie-chart {{
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 30px 0;
        }}
        
        .pie-chart svg {{
            max-width: 300px;
            height: auto;
        }}
        
        @media (max-width: 1024px) {{
            .summary-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .signal-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2em;
            }}
            
            .summary-grid {{
                grid-template-columns: 1fr;
            }}
            
            .channel-metrics {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Detaylı Backtest Analiz Raporu</h1>
            <div class="subtitle">Kanal Performans Analizi ve PnL Hesaplamaları</div>
            <div class="date">{datetime.now().strftime("%d %B %Y, %H:%M")}</div>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Toplam Sinyal</h3>
                <div class="value">{total}</div>
                <div class="label">Test edilen işlem</div>
            </div>
            
            <div class="summary-card positive">
                <h3>✅ Kazanan</h3>
                <div class="value">{wins}</div>
                <div class="label">{wins/total*100:.1f}% başarı</div>
            </div>
            
            <div class="summary-card negative">
                <h3>❌ Kaybeden</h3>
                <div class="value">{losses}</div>
                <div class="label">{losses/total*100:.1f}% kayıp</div>
            </div>
            
            <div class="summary-card neutral">
                <h3>⏳ Açık</h3>
                <div class="value">{opens}</div>
                <div class="label">{opens/total*100:.1f}% beklemede</div>
            </div>
            
            <div class="summary-card {'positive' if win_rate >= 50 else 'negative'}">
                <h3>📈 Win Rate</h3>
                <div class="value">{win_rate:.1f}%</div>
                <div class="label">Kazanma oranı</div>
            </div>
            
            <div class="summary-card {'positive' if total_pnl > 0 else 'negative'}">
                <h3>💰 Toplam PnL</h3>
                <div class="value">{total_pnl:+.2f}%</div>
                <div class="label">Kaldıraçlı kar/zarar</div>
            </div>
            
            <div class="summary-card {'positive' if avg_pnl > 0 else 'negative'}">
                <h3>📊 Ortalama PnL</h3>
                <div class="value">{avg_pnl:+.2f}%</div>
                <div class="label">İşlem başına</div>
            </div>
            
            <div class="summary-card">
                <h3>🎯 Risk/Reward</h3>
                <div class="value">{abs(total_pnl/max(losses, 1)):.2f}</div>
                <div class="label">Kazanç/kayıp oranı</div>
            </div>
        </div>
        
        <div class="section">
            <h2>🏆 Kanal Performans Sıralaması</h2>
            <p style="color: #6b7280; margin-bottom: 25px; font-size: 1.1em;">
                Kanallar toplam PnL ve kazanma oranına göre sıralanmıştır. 
                En başarılı kanallar listenin başında yer almaktadır.
            </p>
            <div class="channel-grid">
"""
    
    # Channel performance cards
    for idx, (channel, stats) in enumerate(sorted_channels[:15], 1):  # Top 15 channels
        rank_class = 'gold' if idx == 1 else 'silver' if idx == 2 else 'bronze' if idx == 3 else ''
        rank_emoji = '🥇' if idx == 1 else '🥈' if idx == 2 else '🥉' if idx == 3 else f'#{idx}'
        
        html += f"""
                <div class="channel-card">
                    <div class="channel-header">
                        <div class="channel-name">
                            {channel[:50]}
                        </div>
                        <div class="rank-badge {rank_class}">{rank_emoji}</div>
                    </div>
                    
                    <div class="channel-metrics">
                        <div class="metric">
                            <div class="metric-label">Toplam Sinyal</div>
                            <div class="metric-value">{stats['total']}</div>
                        </div>
                        
                        <div class="metric">
                            <div class="metric-label">Win Rate</div>
                            <div class="metric-value {'positive' if stats['win_rate'] >= 50 else 'negative'}">{stats['win_rate']:.1f}%</div>
                        </div>
                        
                        <div class="metric">
                            <div class="metric-label">Toplam PnL</div>
                            <div class="metric-value {'positive' if stats['total_pnl'] > 0 else 'negative'}">{stats['total_pnl']:+.2f}%</div>
                        </div>
                        
                        <div class="metric">
                            <div class="metric-label">Ort. PnL</div>
                            <div class="metric-value {'positive' if stats['avg_pnl'] > 0 else 'negative'}">{stats['avg_pnl']:+.2f}%</div>
                        </div>
                        
                        <div class="metric">
                            <div class="metric-label">Kazanan</div>
                            <div class="metric-value positive">{stats['wins']}</div>
                        </div>
                        
                        <div class="metric">
                            <div class="metric-label">Kaybeden</div>
                            <div class="metric-value negative">{stats['losses']}</div>
                        </div>
                        
                        <div class="metric">
                            <div class="metric-label">Farklı Coin</div>
                            <div class="metric-value">{stats['symbols_count']}</div>
                        </div>
                        
                        <div class="metric">
                            <div class="metric-label">Sharpe Ratio</div>
                            <div class="metric-value {'positive' if stats['sharpe'] > 0 else 'negative'}">{stats['sharpe']:.2f}</div>
                        </div>
                    </div>
                    
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {stats['win_rate']}%"></div>
                    </div>
                    
                    <div style="margin-top: 15px; display: flex; justify-content: space-between; font-size: 0.9em; color: #6b7280;">
                        <span>LONG: {stats['sides']['LONG']} | SHORT: {stats['sides']['SHORT']}</span>
                        <span>Açık: {stats['opens']} | Hata: {stats['errors']}</span>
                    </div>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <div class="section">
            <h2>💎 En Başarılı Coinler (PnL'ye Göre)</h2>
            <div class="chart-container">
                <div class="bar-chart">
"""
    
    # Symbol performance
    for symbol, stats in sorted_symbols:
        pnl_class = 'positive' if stats['total_pnl'] > 0 else 'negative'
        bar_width = min(abs(stats['total_pnl']) / max(abs(s[1]['total_pnl']) for s in sorted_symbols) * 100, 100)
        
        html += f"""
                    <div class="bar-item">
                        <div class="bar-label">{symbol}</div>
                        <div class="bar-container">
                            <div class="bar-fill {pnl_class}" style="width: {bar_width}%">
                                {stats['total_pnl']:+.2f}% ({stats['wins']}W/{stats['losses']}L)
                            </div>
                        </div>
                    </div>
"""
    
    html += f"""
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Side ve Leverage Dağılımı</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 30px;">
                <div class="chart-container">
                    <h3 style="margin-bottom: 20px; color: #1f2937;">LONG vs SHORT</h3>
                    <div class="bar-chart">
                        <div class="bar-item">
                            <div class="bar-label">LONG</div>
                            <div class="bar-container">
                                <div class="bar-fill positive" style="width: {sides_count.get('LONG', 0)/total*100}%">
                                    {sides_count.get('LONG', 0)} ({sides_count.get('LONG', 0)/total*100:.1f}%)
                                </div>
                            </div>
                        </div>
                        <div class="bar-item">
                            <div class="bar-label">SHORT</div>
                            <div class="bar-container">
                                <div class="bar-fill negative" style="width: {sides_count.get('SHORT', 0)/total*100}%">
                                    {sides_count.get('SHORT', 0)} ({sides_count.get('SHORT', 0)/total*100:.1f}%)
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3 style="margin-bottom: 20px; color: #1f2937;">Kaldıraç Kullanımı</h3>
                    <div class="bar-chart">
"""
    
    # Leverage distribution
    sorted_leverage = sorted(leverage_count.items(), key=lambda x: x[0] if not math.isnan(x[0]) else 0)
    max_lev_count = max(leverage_count.values()) if leverage_count else 1
    for leverage, count in sorted_leverage:
        lev_display = f"{int(leverage)}x" if not math.isnan(leverage) and leverage > 0 else 'N/A'
        html += f"""
                        <div class="bar-item">
                            <div class="bar-label">{lev_display}</div>
                            <div class="bar-container">
                                <div class="bar-fill" style="width: {count/max_lev_count*100}%">
                                    {count} ({count/total*100:.1f}%)
                                </div>
                            </div>
                        </div>
"""
    
    html += """
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 Son 30 Sinyal Detayı</h2>
            <div class="signal-grid">
"""
    
    # Recent signals with PnL
    sorted_results = sorted(results, key=lambda x: x.get('timestamp', ''), reverse=True)[:30]
    for result in sorted_results:
        outcome = result.get('outcome', 'ERROR')
        outcome_class = outcome.lower()
        pnl = calculate_pnl(result)
        pnl_class = 'positive' if pnl > 0 else 'negative' if pnl < 0 else ''
        
        symbol = result.get('symbol', 'N/A')
        side = result.get('side', 'N/A').upper()
        entry = result.get('entry_min', 0)
        tp = result.get('tp', 0)
        sl = result.get('sl', 0)
        leverage = result.get('leverage', 1)
        channel = result.get('source', 'Unknown')
        timestamp = result.get('timestamp', '')[:16] if result.get('timestamp') else 'N/A'
        
        tp_display = f"{tp:.4f}" if tp and not math.isnan(tp) else 'N/A'
        sl_display = f"{sl:.4f}" if sl and not math.isnan(sl) else 'N/A'
        
        # Handle leverage display - default to 15x if not specified
        if leverage and not math.isnan(leverage) and leverage > 0:
            lev_display = f"{int(leverage)}x"
        else:
            lev_display = "15x"
        
        html += f"""
                <div class="signal-card {outcome_class}">
                    <div class="signal-header">
                        <div class="signal-symbol">{symbol}</div>
                        <div class="signal-badge {outcome_class}">{outcome}</div>
                    </div>
                    
                    <div class="signal-details">
                        <div class="signal-detail">
                            <div class="signal-detail-label">Side</div>
                            <div class="signal-detail-value">{side}</div>
                        </div>
                        <div class="signal-detail">
                            <div class="signal-detail-label">Leverage</div>
                            <div class="signal-detail-value">{lev_display}</div>
                        </div>
                        <div class="signal-detail">
                            <div class="signal-detail-label">Entry</div>
                            <div class="signal-detail-value">{entry:.6f}</div>
                        </div>
                        <div class="signal-detail">
                            <div class="signal-detail-label">Take Profit</div>
                            <div class="signal-detail-value">{tp_display}</div>
                        </div>
                        <div class="signal-detail">
                            <div class="signal-detail-label">Stop Loss</div>
                            <div class="signal-detail-value">{sl_display}</div>
                        </div>
                    </div>
                    
                    <div class="signal-pnl {pnl_class}">
                        PnL: {pnl:+.2f}%
                    </div>
                    
                    <div class="signal-footer">
                        <span>📡 {channel[:30]}</span>
                        <span>🕐 {timestamp}</span>
                    </div>
                </div>
"""
    
    html += f"""
            </div>
        </div>
        
        <div class="footer">
            <h3>🚀 OMNI Tech Solutions</h3>
            <p><strong>Telegram Trading Bot</strong> - Gelişmiş Backtest Analiz Sistemi</p>
            <p>Adaptive Whitelist • Enhanced Parser • MEXC Exchange</p>
            <p>📊 {total} sinyal analiz edildi • {len(channel_stats)} kanal izlendi</p>
            <p style="margin-top: 20px; opacity: 0.8;">Oluşturulma: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Save report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return report_path


def main():
    """Main execution."""
    print("=" * 70)
    print("📊 DETAILED BACKTEST REPORT GENERATION")
    print("=" * 70)
    
    results_path = Path("data/backtest_results.jsonl")
    
    if not results_path.exists():
        print(f"❌ Results file not found: {results_path}")
        return
    
    # Load results
    results = []
    with open(results_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    if not results:
        print("❌ No valid results found")
        return
    
    print(f"✅ Loaded {len(results)} backtest results")
    
    # Generate report
    print("\n📝 Generating detailed HTML report...")
    report_path = generate_html_report(results)
    
    print(f"✅ Report generated: {report_path}")
    print(f"📊 File size: {report_path.stat().st_size / 1024:.1f} KB")
    
    # Open in browser
    import webbrowser
    try:
        webbrowser.open(str(report_path.absolute()))
        print("🌐 Opening report in browser...")
    except Exception as e:
        print(f"⚠️ Could not open browser: {e}")
        print(f"📂 Open manually: {report_path.absolute()}")
    
    print("=" * 70)
    print("✅ REPORT GENERATION COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    main()
