"""
Generate comprehensive HTML backtest report with interactive charts.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import info, success, error


def load_backtest_results(results_path: Path) -> List[Dict]:
    """Load backtest results from JSONL file."""
    results = []
    
    if not results_path.exists():
        error(f"❌ Results file not found: {results_path}")
        return results
    
    try:
        with open(results_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))
        
        info(f"📚 Loaded {len(results)} backtest results")
        
    except Exception as e:
        error(f"❌ Error loading results: {e}")
    
    return results


def filter_valid_results(results: List[Dict]) -> List[Dict]:
    """Filter only valid trade results (exclude errors)."""
    return [r for r in results if r.get('status') in ['profit', 'loss', 'open']]


def create_cumulative_pnl_chart(df: pd.DataFrame) -> go.Figure:
    """Create cumulative PnL chart over time."""
    # Sort by timestamp
    df_sorted = df.sort_values('timestamp')
    df_sorted['cumulative_pnl'] = df_sorted['pnl_leveraged'].cumsum()
    
    fig = go.Figure()
    
    # Add cumulative PnL line
    fig.add_trace(go.Scatter(
        x=df_sorted['timestamp'],
        y=df_sorted['cumulative_pnl'],
        mode='lines',
        name='Cumulative PnL',
        line=dict(color='#00D9FF', width=3),
        fill='tozeroy',
        fillcolor='rgba(0, 217, 255, 0.1)'
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig.update_layout(
        title='📈 Cumulative PnL Over Time (Leveraged)',
        xaxis_title='Date',
        yaxis_title='Cumulative PnL (%)',
        template='plotly_dark',
        hovermode='x unified',
        height=500
    )
    
    return fig


def create_channel_performance_chart(df: pd.DataFrame) -> go.Figure:
    """Create channel performance comparison chart."""
    # Group by channel
    channel_stats = df.groupby('channel').agg({
        'pnl_leveraged': 'sum',
        'signal_id': 'count',
        'status': lambda x: (x == 'profit').sum()
    }).reset_index()
    
    channel_stats.columns = ['channel', 'total_pnl', 'total_signals', 'wins']
    channel_stats['win_rate'] = (channel_stats['wins'] / channel_stats['total_signals'] * 100).round(1)
    channel_stats = channel_stats.sort_values('total_pnl', ascending=False)
    
    # Create subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Total PnL by Channel', 'Win Rate by Channel'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )
    
    # PnL chart
    colors = ['#00D9FF' if pnl > 0 else '#FF4444' for pnl in channel_stats['total_pnl']]
    fig.add_trace(
        go.Bar(
            x=channel_stats['channel'],
            y=channel_stats['total_pnl'],
            name='Total PnL',
            marker_color=colors,
            text=channel_stats['total_pnl'].round(2),
            textposition='outside'
        ),
        row=1, col=1
    )
    
    # Win rate chart
    fig.add_trace(
        go.Bar(
            x=channel_stats['channel'],
            y=channel_stats['win_rate'],
            name='Win Rate',
            marker_color='#00FF88',
            text=channel_stats['win_rate'].astype(str) + '%',
            textposition='outside'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title_text='📱 Channel Performance Comparison',
        template='plotly_dark',
        showlegend=False,
        height=500
    )
    
    fig.update_yaxes(title_text='PnL (%)', row=1, col=1)
    fig.update_yaxes(title_text='Win Rate (%)', row=1, col=2)
    
    return fig


def create_tp_sl_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Create TP/SL hit distribution chart."""
    # Count TP hits
    tp_counts = df[df['hit_tp'].notna()]['hit_tp'].value_counts().sort_index()
    sl_count = df['hit_sl'].sum()
    open_count = (df['status'] == 'open').sum()
    
    labels = [f'TP{int(tp)}' for tp in tp_counts.index] + ['Stop Loss', 'Open']
    values = list(tp_counts.values) + [sl_count, open_count]
    colors = ['#00FF88', '#00D9FF', '#FFD700', '#FF4444', '#888888']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker_colors=colors[:len(labels)],
        textinfo='label+percent+value',
        textposition='outside'
    )])
    
    fig.update_layout(
        title='🎯 Take Profit & Stop Loss Distribution',
        template='plotly_dark',
        height=500
    )
    
    return fig


def create_symbol_performance_chart(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Create top performing symbols chart."""
    # Group by symbol
    symbol_stats = df.groupby('symbol').agg({
        'pnl_leveraged': 'sum',
        'signal_id': 'count'
    }).reset_index()
    
    symbol_stats.columns = ['symbol', 'total_pnl', 'count']
    symbol_stats = symbol_stats[symbol_stats['count'] >= 2]  # At least 2 trades
    symbol_stats = symbol_stats.sort_values('total_pnl', ascending=False).head(top_n)
    
    colors = ['#00D9FF' if pnl > 0 else '#FF4444' for pnl in symbol_stats['total_pnl']]
    
    fig = go.Figure(data=[go.Bar(
        x=symbol_stats['symbol'],
        y=symbol_stats['total_pnl'],
        marker_color=colors,
        text=symbol_stats['total_pnl'].round(2),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>PnL: %{y:.2f}%<br>Trades: %{customdata}<extra></extra>',
        customdata=symbol_stats['count']
    )])
    
    fig.update_layout(
        title=f'💹 Top {top_n} Performing Symbols',
        xaxis_title='Symbol',
        yaxis_title='Total PnL (%)',
        template='plotly_dark',
        height=500
    )
    
    return fig


def create_daily_performance_chart(df: pd.DataFrame) -> go.Figure:
    """Create daily performance chart."""
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    
    daily_stats = df.groupby('date').agg({
        'pnl_leveraged': ['sum', 'count'],
        'status': lambda x: (x == 'profit').sum()
    }).reset_index()
    
    daily_stats.columns = ['date', 'pnl', 'count', 'wins']
    daily_stats['win_rate'] = (daily_stats['wins'] / daily_stats['count'] * 100).round(1)
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Daily PnL', 'Daily Win Rate'),
        vertical_spacing=0.15
    )
    
    # Daily PnL
    colors = ['#00D9FF' if pnl > 0 else '#FF4444' for pnl in daily_stats['pnl']]
    fig.add_trace(
        go.Bar(
            x=daily_stats['date'],
            y=daily_stats['pnl'],
            marker_color=colors,
            name='Daily PnL',
            hovertemplate='<b>%{x}</b><br>PnL: %{y:.2f}%<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Daily Win Rate
    fig.add_trace(
        go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['win_rate'],
            mode='lines+markers',
            marker_color='#00FF88',
            name='Win Rate',
            hovertemplate='<b>%{x}</b><br>Win Rate: %{y:.1f}%<extra></extra>'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title_text='📅 Daily Performance Analysis',
        template='plotly_dark',
        showlegend=False,
        height=700
    )
    
    fig.update_yaxes(title_text='PnL (%)', row=1, col=1)
    fig.update_yaxes(title_text='Win Rate (%)', row=2, col=1)
    fig.update_xaxes(title_text='Date', row=2, col=1)
    
    return fig


def generate_html_report(results: List[Dict], output_path: Path):
    """Generate comprehensive HTML report with charts."""
    info("📊 Generating HTML report...")
    
    # Filter valid results
    valid_results = filter_valid_results(results)
    
    if not valid_results:
        error("❌ No valid results to generate report")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(valid_results)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Calculate statistics
    total = len(valid_results)
    profits = len([r for r in valid_results if r.get('status') == 'profit'])
    losses = len([r for r in valid_results if r.get('status') == 'loss'])
    opens = len([r for r in valid_results if r.get('status') == 'open'])
    
    win_rate = (profits / total * 100) if total > 0 else 0
    total_pnl = df['pnl_leveraged'].sum()
    avg_win = df[df['status'] == 'profit']['pnl_leveraged'].mean() if profits > 0 else 0
    avg_loss = df[df['status'] == 'loss']['pnl_leveraged'].mean() if losses > 0 else 0
    
    total_wins = df[df['pnl_leveraged'] > 0]['pnl_leveraged'].sum()
    total_losses = abs(df[df['pnl_leveraged'] < 0]['pnl_leveraged'].sum())
    profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
    
    # Generate charts
    info("   Creating charts...")
    fig_cumulative = create_cumulative_pnl_chart(df)
    fig_channels = create_channel_performance_chart(df)
    fig_tp_sl = create_tp_sl_distribution_chart(df)
    fig_symbols = create_symbol_performance_chart(df, top_n=10)
    fig_daily = create_daily_performance_chart(df)
    
    # Generate HTML
    info("   Building HTML...")
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtest Report - Telegram Trading Signals</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        
        header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 3px solid #667eea;
        }}
        
        h1 {{
            font-size: 3em;
            color: #667eea;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .subtitle {{
            font-size: 1.2em;
            color: #666;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            transition: transform 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-card h3 {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
        }}
        
        .stat-card.positive {{
            background: linear-gradient(135deg, #00D9FF 0%, #00FF88 100%);
        }}
        
        .stat-card.negative {{
            background: linear-gradient(135deg, #FF4444 0%, #FF6B6B 100%);
        }}
        
        .chart-container {{
            margin: 40px 0;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .recommendation {{
            margin: 40px 0;
            padding: 30px;
            background: linear-gradient(135deg, #00FF88 0%, #00D9FF 100%);
            color: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 255, 136, 0.3);
        }}
        
        .recommendation h2 {{
            font-size: 2em;
            margin-bottom: 15px;
        }}
        
        .recommendation p {{
            font-size: 1.2em;
            line-height: 1.6;
        }}
        
        .warning {{
            background: linear-gradient(135deg, #FF4444 0%, #FF6B6B 100%);
        }}
        
        footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 30px;
            border-top: 2px solid #eee;
            color: #666;
        }}
        
        .channel-table {{
            width: 100%;
            margin: 30px 0;
            border-collapse: collapse;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .channel-table th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        .channel-table td {{
            padding: 15px;
            border-bottom: 1px solid #eee;
        }}
        
        .channel-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .badge.excellent {{
            background: #00FF88;
            color: white;
        }}
        
        .badge.good {{
            background: #00D9FF;
            color: white;
        }}
        
        .badge.poor {{
            background: #FF4444;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 Backtest Report</h1>
            <p class="subtitle">Telegram Trading Signals Performance Analysis</p>
            <p class="subtitle">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Signals</h3>
                <div class="value">{total}</div>
            </div>
            <div class="stat-card positive">
                <h3>Win Rate</h3>
                <div class="value">{win_rate:.1f}%</div>
            </div>
            <div class="stat-card {'positive' if total_pnl > 0 else 'negative'}">
                <h3>Total PnL</h3>
                <div class="value">{total_pnl:+.2f}%</div>
            </div>
            <div class="stat-card positive">
                <h3>Profit Factor</h3>
                <div class="value">{'∞' if profit_factor == float('inf') else f'{profit_factor:.2f}'}</div>
            </div>
            <div class="stat-card">
                <h3>Profitable Trades</h3>
                <div class="value">{profits}</div>
            </div>
            <div class="stat-card">
                <h3>Loss Trades</h3>
                <div class="value">{losses}</div>
            </div>
            <div class="stat-card">
                <h3>Average Win</h3>
                <div class="value">+{avg_win:.2f}%</div>
            </div>
            <div class="stat-card">
                <h3>Average Loss</h3>
                <div class="value">{avg_loss:.2f}%</div>
            </div>
        </div>
        
        <div class="recommendation {'warning' if win_rate < 50 else ''}">
            <h2>{'🎉 Recommendation: GO LIVE!' if win_rate >= 60 and total_pnl > 0 else '⚠️ Recommendation: CAUTION' if win_rate >= 50 else '❌ Recommendation: DO NOT TRADE'}</h2>
            <p>
                {'Your backtest shows excellent results with a strong win rate and positive returns. These signals are profitable and ready for live trading!' if win_rate >= 60 and total_pnl > 0 else 'Results are moderate. Consider filtering channels and optimizing strategy before live trading.' if win_rate >= 50 else 'Performance is poor. These signals are not profitable. Avoid live trading with this strategy.'}
            </p>
        </div>
        
        <div class="chart-container">
            <div id="chart-cumulative"></div>
        </div>
        
        <div class="chart-container">
            <div id="chart-channels"></div>
        </div>
        
        <h2 style="margin: 40px 0 20px 0; color: #667eea;">📊 Channel Performance Details</h2>
        <table class="channel-table">
            <thead>
                <tr>
                    <th>Channel</th>
                    <th>Signals</th>
                    <th>Win Rate</th>
                    <th>Total PnL</th>
                    <th>Rating</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # Add channel details
    channel_stats = df.groupby('channel').agg({
        'signal_id': 'count',
        'pnl_leveraged': 'sum',
        'status': lambda x: (x == 'profit').sum() / len(x) * 100
    }).reset_index()
    
    channel_stats.columns = ['channel', 'signals', 'pnl', 'win_rate']
    channel_stats = channel_stats.sort_values('pnl', ascending=False)
    
    for _, row in channel_stats.iterrows():
        rating = 'excellent' if row['win_rate'] >= 70 else 'good' if row['win_rate'] >= 50 else 'poor'
        rating_text = 'EXCELLENT' if row['win_rate'] >= 70 else 'GOOD' if row['win_rate'] >= 50 else 'POOR'
        
        html_content += f"""
                <tr>
                    <td><strong>{row['channel']}</strong></td>
                    <td>{int(row['signals'])}</td>
                    <td>{row['win_rate']:.1f}%</td>
                    <td style="color: {'#00FF88' if row['pnl'] > 0 else '#FF4444'}; font-weight: bold;">{row['pnl']:+.2f}%</td>
                    <td><span class="badge {rating}">{rating_text}</span></td>
                </tr>
"""
    
    html_content += """
            </tbody>
        </table>
        
        <div class="chart-container">
            <div id="chart-tpsl"></div>
        </div>
        
        <div class="chart-container">
            <div id="chart-symbols"></div>
        </div>
        
        <div class="chart-container">
            <div id="chart-daily"></div>
        </div>
        
        <footer>
            <p><strong>OMNI Tech Solutions</strong> | Trade Bot Telegram MEXC</p>
            <p>Backtest Engine v1.0</p>
        </footer>
    </div>
    
    <script>
"""
    
    # Add Plotly charts
    html_content += f"""
        Plotly.newPlot('chart-cumulative', {fig_cumulative.to_json()}.data, {fig_cumulative.to_json()}.layout);
        Plotly.newPlot('chart-channels', {fig_channels.to_json()}.data, {fig_channels.to_json()}.layout);
        Plotly.newPlot('chart-tpsl', {fig_tp_sl.to_json()}.data, {fig_tp_sl.to_json()}.layout);
        Plotly.newPlot('chart-symbols', {fig_symbols.to_json()}.data, {fig_symbols.to_json()}.layout);
        Plotly.newPlot('chart-daily', {fig_daily.to_json()}.data, {fig_daily.to_json()}.layout);
    </script>
</body>
</html>
"""
    
    # Save HTML file
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        success(f"✅ HTML report generated: {output_path}")
        info(f"   📂 Open in browser: file:///{output_path.absolute()}")
        
    except Exception as e:
        error(f"❌ Error saving HTML report: {e}")


def main():
    """Main report generation."""
    print("\n" + "="*80)
    print("📊 BACKTEST REPORT GENERATOR")
    print("="*80)
    
    # Paths
    data_dir = Path("data")
    results_path = data_dir / "backtest_results.jsonl"
    output_path = data_dir / "backtest_report.html"
    
    # Load results
    results = load_backtest_results(results_path)
    
    if not results:
        error("❌ No results found!")
        return
    
    # Generate report
    generate_html_report(results, output_path)
    
    print("="*80)
    success("✅ Report generation complete!")
    print(f"\n📂 Open report: file:///{output_path.absolute()}\n")


if __name__ == "__main__":
    main()
