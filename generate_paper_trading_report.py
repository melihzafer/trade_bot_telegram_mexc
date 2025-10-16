"""
Paper Trading Report Generator
Creates detailed HTML reports for paper trading performance
"""
import json
from datetime import datetime
from pathlib import Path
import webbrowser
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from trading.trade_logger import TradeLogger
from trading.paper_portfolio import PaperPortfolio
from utils.config import DATA_DIR


def generate_paper_trading_report(portfolio=None, logger=None):
    """
    Generate comprehensive paper trading HTML report.
    
    Args:
        portfolio: PaperPortfolio instance (optional, for live positions)
        logger: TradeLogger instance (optional, loads from file if not provided)
    """
    print("📊 Generating paper trading report...")
    
    # Load logger if not provided
    if logger is None:
        logger = TradeLogger()
    
    # Load closed trades
    closed_trades = logger.load_trades()
    
    # Get open positions
    open_positions = []
    if portfolio:
        open_positions = list(portfolio.open_positions.values())
    
    # Calculate statistics
    stats = calculate_stats(closed_trades, open_positions, portfolio)
    
    # Channel performance
    channel_performance = calculate_channel_performance(closed_trades)
    
    # Symbol performance
    symbol_performance = calculate_symbol_performance(closed_trades)
    
    # Generate HTML
    html = generate_html(stats, closed_trades, open_positions, channel_performance, symbol_performance)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = DATA_DIR / f"paper_trading_report_{timestamp}.html"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Report saved: {report_path}")
    print(f"📄 Size: {report_path.stat().st_size / 1024:.1f} KB")
    
    # Open in browser
    webbrowser.open(f'file://{report_path.absolute()}')
    print(f"🌐 Opened in browser\n")
    
    return report_path


def calculate_stats(closed_trades, open_positions, portfolio):
    """Calculate comprehensive statistics."""
    total_closed = len(closed_trades)
    wins = [t for t in closed_trades if t['pnl_usd'] > 0]
    losses = [t for t in closed_trades if t['pnl_usd'] <= 0]
    
    total_pnl = sum(t['pnl_usd'] for t in closed_trades)
    win_rate = (len(wins) / total_closed * 100) if total_closed > 0 else 0
    
    avg_win = sum(t['pnl_usd'] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t['pnl_usd'] for t in losses) / len(losses) if losses else 0
    
    largest_win = max((t['pnl_usd'] for t in wins), default=0)
    largest_loss = min((t['pnl_usd'] for t in losses), default=0)
    
    # Calculate average duration
    avg_duration = sum(t['duration_seconds'] for t in closed_trades) / total_closed if total_closed > 0 else 0
    
    # Portfolio stats
    if portfolio:
        current_balance = portfolio.balance
        initial_balance = portfolio.initial_balance
        open_pnl = sum(pos.get('current_pnl_usd', 0) for pos in open_positions)
    else:
        # Assume initial balance from closed trades
        current_balance = 10000 + total_pnl
        initial_balance = 10000
        open_pnl = 0
    
    return {
        'current_balance': current_balance,
        'initial_balance': initial_balance,
        'total_pnl': total_pnl,
        'total_pnl_pct': (total_pnl / initial_balance * 100),
        'open_pnl': open_pnl,
        'total_closed': total_closed,
        'total_open': len(open_positions),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'largest_win': largest_win,
        'largest_loss': largest_loss,
        'avg_duration_hours': avg_duration / 3600,
        'profit_factor': abs(sum(t['pnl_usd'] for t in wins) / sum(t['pnl_usd'] for t in losses)) if losses and sum(t['pnl_usd'] for t in losses) != 0 else 0
    }


def calculate_channel_performance(closed_trades):
    """Calculate performance by channel."""
    channels = {}
    
    for trade in closed_trades:
        channel = trade.get('channel', 'Unknown')
        
        if channel not in channels:
            channels[channel] = {
                'total': 0,
                'wins': 0,
                'losses': 0,
                'total_pnl': 0,
                'trades': []
            }
        
        channels[channel]['total'] += 1
        channels[channel]['total_pnl'] += trade['pnl_usd']
        channels[channel]['trades'].append(trade)
        
        if trade['pnl_usd'] > 0:
            channels[channel]['wins'] += 1
        else:
            channels[channel]['losses'] += 1
    
    # Calculate metrics
    for channel, data in channels.items():
        data['win_rate'] = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
        data['avg_pnl'] = data['total_pnl'] / data['total'] if data['total'] > 0 else 0
    
    # Sort by total PnL
    sorted_channels = sorted(channels.items(), key=lambda x: x[1]['total_pnl'], reverse=True)
    
    return sorted_channels


def calculate_symbol_performance(closed_trades):
    """Calculate performance by symbol."""
    symbols = {}
    
    for trade in closed_trades:
        symbol = trade['symbol']
        
        if symbol not in symbols:
            symbols[symbol] = {
                'total': 0,
                'wins': 0,
                'total_pnl': 0
            }
        
        symbols[symbol]['total'] += 1
        symbols[symbol]['total_pnl'] += trade['pnl_usd']
        
        if trade['pnl_usd'] > 0:
            symbols[symbol]['wins'] += 1
    
    # Sort by total PnL
    sorted_symbols = sorted(symbols.items(), key=lambda x: x[1]['total_pnl'], reverse=True)
    
    return sorted_symbols[:15]  # Top 15


def generate_html(stats, closed_trades, open_positions, channel_performance, symbol_performance):
    """Generate HTML report."""
    
    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Paper Trading Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
            text-align: center;
        }}
        
        .header h1 {{
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .header p {{
            color: #666;
            font-size: 1.1em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.2);
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        
        .stat-value.positive {{
            color: #10b981;
        }}
        
        .stat-value.negative {{
            color: #ef4444;
        }}
        
        .section {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        tr:hover {{
            background: #f9fafb;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .badge.long {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .badge.short {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .badge.open {{
            background: #dbeafe;
            color: #1e40af;
        }}
        
        .badge.closed {{
            background: #e5e7eb;
            color: #374151;
        }}
        
        .badge.win {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .badge.loss {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .progress-bar {{
            background: #e5e7eb;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #10b981 0%, #059669 100%);
            transition: width 0.3s ease;
        }}
        
        .chart {{
            margin: 20px 0;
        }}
        
        .bar {{
            display: flex;
            align-items: center;
            margin: 10px 0;
        }}
        
        .bar-label {{
            width: 150px;
            font-size: 0.9em;
            color: #666;
        }}
        
        .bar-fill {{
            flex: 1;
            height: 30px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 5px;
            display: flex;
            align-items: center;
            padding: 0 10px;
            color: white;
            font-weight: 600;
            font-size: 0.85em;
        }}
        
        .empty-state {{
            text-align: center;
            padding: 40px;
            color: #999;
        }}
        
        .footer {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            color: #666;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Paper Trading Report</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Current Balance</div>
                <div class="stat-value">${stats['current_balance']:.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total PnL</div>
                <div class="stat-value {'positive' if stats['total_pnl'] >= 0 else 'negative'}">${stats['total_pnl']:.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">PnL %</div>
                <div class="stat-value {'positive' if stats['total_pnl_pct'] >= 0 else 'negative'}">{stats['total_pnl_pct']:.2f}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Win Rate</div>
                <div class="stat-value">{stats['win_rate']:.1f}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Trades</div>
                <div class="stat-value">{stats['total_closed']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Open Positions</div>
                <div class="stat-value">{stats['total_open']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Win</div>
                <div class="stat-value positive">${stats['avg_win']:.2f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Loss</div>
                <div class="stat-value negative">${stats['avg_loss']:.2f}</div>
            </div>
        </div>
"""
    
    # Open positions section
    if open_positions:
        html += """
        <div class="section">
            <h2>🔓 Open Positions</h2>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Side</th>
                        <th>Entry</th>
                        <th>Current PnL</th>
                        <th>Stop Loss</th>
                        <th>Take Profits</th>
                        <th>Channel</th>
                        <th>Duration</th>
                    </tr>
                </thead>
                <tbody>
"""
        for pos in open_positions:
            duration = (datetime.now() - pos['entry_time']).total_seconds() / 3600
            pnl_class = 'positive' if pos.get('current_pnl_usd', 0) >= 0 else 'negative'
            
            tps_str = ', '.join(f"{tp:.4f}" for tp in pos['take_profits'])
            
            html += f"""
                    <tr>
                        <td><strong>{pos['symbol']}</strong></td>
                        <td><span class="badge {pos['side'].lower()}">{pos['side']}</span></td>
                        <td>{pos['entry_price']:.4f}</td>
                        <td class="{pnl_class}"><strong>{pos.get('current_pnl_pct', 0):.2f}%</strong> (${pos.get('current_pnl_usd', 0):.2f})</td>
                        <td>{pos['stop_loss']:.4f}</td>
                        <td style="font-size: 0.85em;">{tps_str}</td>
                        <td>{pos['channel']}</td>
                        <td>{duration:.1f}h</td>
                    </tr>
"""
        html += """
                </tbody>
            </table>
        </div>
"""
    
    # Channel performance section
    if channel_performance:
        html += """
        <div class="section">
            <h2>📡 Channel Performance</h2>
            <table>
                <thead>
                    <tr>
                        <th>Channel</th>
                        <th>Total Trades</th>
                        <th>Win Rate</th>
                        <th>Total PnL</th>
                        <th>Avg PnL</th>
                    </tr>
                </thead>
                <tbody>
"""
        for channel, data in channel_performance:
            pnl_class = 'positive' if data['total_pnl'] >= 0 else 'negative'
            
            html += f"""
                    <tr>
                        <td><strong>{channel}</strong></td>
                        <td>{data['total']} ({data['wins']}W / {data['losses']}L)</td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {data['win_rate']:.1f}%"></div>
                            </div>
                            {data['win_rate']:.1f}%
                        </td>
                        <td class="{pnl_class}"><strong>${data['total_pnl']:.2f}</strong></td>
                        <td class="{pnl_class}">${data['avg_pnl']:.2f}</td>
                    </tr>
"""
        html += """
                </tbody>
            </table>
        </div>
"""
    
    # Symbol performance section
    if symbol_performance:
        html += """
        <div class="section">
            <h2>💎 Top Symbols by PnL</h2>
            <div class="chart">
"""
        max_pnl = max(abs(s[1]['total_pnl']) for s in symbol_performance) if symbol_performance else 1
        
        for symbol, data in symbol_performance:
            width = abs(data['total_pnl']) / max_pnl * 100 if max_pnl > 0 else 0
            html += f"""
                <div class="bar">
                    <div class="bar-label">{symbol}</div>
                    <div class="bar-fill" style="width: {width}%">
                        ${data['total_pnl']:.2f} ({data['total']} trades, {data['wins']}W)
                    </div>
                </div>
"""
        html += """
            </div>
        </div>
"""
    
    # Recent closed trades
    if closed_trades:
        recent_trades = sorted(closed_trades, key=lambda x: x['timestamp_close'], reverse=True)[:20]
        
        html += """
        <div class="section">
            <h2>📜 Recent Closed Trades (Last 20)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Side</th>
                        <th>Entry</th>
                        <th>Exit</th>
                        <th>PnL</th>
                        <th>Exit Reason</th>
                        <th>Channel</th>
                        <th>Duration</th>
                    </tr>
                </thead>
                <tbody>
"""
        for trade in recent_trades:
            duration_hours = trade['duration_seconds'] / 3600
            pnl_class = 'win' if trade['pnl_usd'] > 0 else 'loss'
            
            html += f"""
                    <tr>
                        <td><strong>{trade['symbol']}</strong></td>
                        <td><span class="badge {trade['side'].lower()}">{trade['side']}</span></td>
                        <td>{trade['entry_price']:.4f}</td>
                        <td>{trade['exit_price']:.4f}</td>
                        <td>
                            <span class="badge {pnl_class}">
                                {trade['pnl_pct']:.2f}% (${trade['pnl_usd']:.2f})
                            </span>
                        </td>
                        <td>{trade['exit_reason']}</td>
                        <td>{trade['channel']}</td>
                        <td>{duration_hours:.1f}h</td>
                    </tr>
"""
        html += """
                </tbody>
            </table>
        </div>
"""
    else:
        html += """
        <div class="section">
            <div class="empty-state">
                <h2>📭 No closed trades yet</h2>
                <p>Start paper trading to see results here!</p>
            </div>
        </div>
"""
    
    # Footer
    html += f"""
        <div class="footer">
            <p>Paper Trading Report • Generated with ❤️ by OMNI Tech Solutions</p>
            <p style="margin-top: 10px; font-size: 0.9em;">
                Initial Balance: ${stats['initial_balance']:.2f} | 
                Profit Factor: {stats['profit_factor']:.2f} | 
                Avg Duration: {stats['avg_duration_hours']:.1f}h
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


if __name__ == "__main__":
    # Generate report from logged trades
    generate_paper_trading_report()
