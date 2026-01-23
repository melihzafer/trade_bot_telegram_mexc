"""
📊 Backtest Visualizer
Generates charts and HTML reports for backtest results.
"""
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.gridspec import GridSpec
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from utils.logger import info, warn, error


class BacktestVisualizer:
    """
    Generates visualizations and reports for backtest results.
    """
    
    def __init__(self, output_dir: Path):
        """
        Initialize visualizer.
        
        Args:
            output_dir: Directory to save charts and reports
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if not MATPLOTLIB_AVAILABLE:
            warn("⚠️ Matplotlib not installed. Charts will not be generated.")
            warn("   Install with: pip install matplotlib")
    
    def plot_equity_curve(
        self, 
        equity_curve: List[float],
        trades: List[Dict],
        filename: str = "equity_curve.png"
    ):
        """Generate equity curve chart."""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])
            
            # Equity curve
            equity_array = np.array(equity_curve)
            ax1.plot(equity_array, linewidth=2, color='#2E86DE', label='Equity')
            
            # Running max for drawdown visualization
            running_max = np.maximum.accumulate(equity_array)
            ax1.plot(running_max, linewidth=1, linestyle='--', color='gray', alpha=0.5, label='Peak')
            ax1.fill_between(range(len(equity_array)), equity_array, running_max, 
                            alpha=0.2, color='red', label='Drawdown')
            
            ax1.set_title('Equity Curve', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Capital (USDT)', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.legend(loc='best')
            
            # Calculate returns
            returns = np.diff(equity_array) / equity_array[:-1] * 100
            
            # Returns distribution
            ax2.hist(returns, bins=50, color='#2E86DE', alpha=0.7, edgecolor='black')
            ax2.axvline(x=0, color='red', linestyle='--', linewidth=1)
            ax2.set_title('Returns Distribution', fontsize=12)
            ax2.set_xlabel('Return (%)', fontsize=10)
            ax2.set_ylabel('Frequency', fontsize=10)
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            output_path = self.output_dir / filename
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            info(f"✅ Equity curve saved: {output_path}")
            return output_path
        
        except Exception as e:
            error(f"Failed to generate equity curve: {e}")
            return None
    
    def plot_trade_distribution(
        self, 
        trades: List[Dict],
        filename: str = "trade_distribution.png"
    ):
        """Generate trade PnL distribution chart."""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
            
            pnl_values = [t['pnl_net'] for t in trades]
            pnl_pcts = [t['pnl_pct'] for t in trades]
            wins = [p for p in pnl_values if p > 0]
            losses = [p for p in pnl_values if p < 0]
            
            # 1. PnL Distribution (USDT)
            ax1.hist([wins, losses], bins=30, label=['Wins', 'Losses'], 
                    color=['green', 'red'], alpha=0.7, edgecolor='black')
            ax1.axvline(x=0, color='black', linestyle='--', linewidth=1)
            ax1.set_title('Trade PnL Distribution (USDT)', fontsize=12, fontweight='bold')
            ax1.set_xlabel('PnL (USDT)', fontsize=10)
            ax1.set_ylabel('Frequency', fontsize=10)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 2. PnL Distribution (%)
            ax2.hist(pnl_pcts, bins=30, color='#2E86DE', alpha=0.7, edgecolor='black')
            ax2.axvline(x=0, color='red', linestyle='--', linewidth=1)
            ax2.set_title('Trade PnL Distribution (%)', fontsize=12, fontweight='bold')
            ax2.set_xlabel('PnL (%)', fontsize=10)
            ax2.set_ylabel('Frequency', fontsize=10)
            ax2.grid(True, alpha=0.3)
            
            # 3. Win/Loss Pie Chart
            win_count = len(wins)
            loss_count = len(losses)
            ax3.pie([win_count, loss_count], labels=['Wins', 'Losses'], 
                   autopct='%1.1f%%', startangle=90, colors=['green', 'red'])
            ax3.set_title(f'Win Rate: {win_count/(win_count+loss_count)*100:.1f}%', 
                         fontsize=12, fontweight='bold')
            
            # 4. Exit Reasons
            exit_reasons = [t['exit_reason'] for t in trades]
            reason_counts = pd.Series(exit_reasons).value_counts()
            colors_map = {'TP': 'green', 'SL': 'red', 'TIMEOUT': 'orange'}
            colors = [colors_map.get(r, 'gray') for r in reason_counts.index]
            
            ax4.bar(reason_counts.index, reason_counts.values, color=colors, alpha=0.7, edgecolor='black')
            ax4.set_title('Exit Reasons', fontsize=12, fontweight='bold')
            ax4.set_xlabel('Reason', fontsize=10)
            ax4.set_ylabel('Count', fontsize=10)
            ax4.grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout()
            
            output_path = self.output_dir / filename
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            info(f"✅ Trade distribution saved: {output_path}")
            return output_path
        
        except Exception as e:
            error(f"Failed to generate trade distribution: {e}")
            return None
    
    def plot_monthly_heatmap(
        self, 
        monthly_returns: Dict[str, float],
        filename: str = "monthly_heatmap.png"
    ):
        """Generate monthly returns heatmap."""
        if not MATPLOTLIB_AVAILABLE or not monthly_returns:
            return None
        
        try:
            # Parse month periods and organize by year/month
            data = []
            for period_str, pnl in monthly_returns.items():
                year, month = period_str.split('-')
                data.append({'year': int(year), 'month': int(month), 'pnl': pnl})
            
            df = pd.DataFrame(data)
            
            # Pivot to year x month matrix
            pivot = df.pivot_table(index='year', columns='month', values='pnl', fill_value=0)
            
            fig, ax = plt.subplots(figsize=(14, 6))
            
            # Create heatmap
            im = ax.imshow(pivot.values, cmap='RdYlGn', aspect='auto', 
                          vmin=pivot.values.min(), vmax=pivot.values.max())
            
            # Set ticks
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_yticks(range(len(pivot.index)))
            ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][:len(pivot.columns)])
            ax.set_yticklabels(pivot.index)
            
            # Add values to cells
            for i in range(len(pivot.index)):
                for j in range(len(pivot.columns)):
                    value = pivot.values[i, j]
                    if value != 0:
                        text_color = 'white' if abs(value) > pivot.values.std() else 'black'
                        ax.text(j, i, f'${value:.0f}', ha='center', va='center', 
                               color=text_color, fontsize=9, fontweight='bold')
            
            ax.set_title('Monthly Returns Heatmap', fontsize=14, fontweight='bold')
            ax.set_xlabel('Month', fontsize=12)
            ax.set_ylabel('Year', fontsize=12)
            
            # Colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('PnL (USDT)', fontsize=10)
            
            plt.tight_layout()
            
            output_path = self.output_dir / filename
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            info(f"✅ Monthly heatmap saved: {output_path}")
            return output_path
        
        except Exception as e:
            error(f"Failed to generate monthly heatmap: {e}")
            return None
    
    def plot_channel_comparison(
        self,
        channel_metrics: Dict[str, Dict],
        filename: str = "channel_comparison.png"
    ):
        """
        Generate channel performance comparison chart.
        
        Args:
            channel_metrics: Dict of channel name -> metrics dict
            filename: Output filename
        """
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            # Filter out channels with no trades
            channels = {k: v for k, v in channel_metrics.items() if v.get('total_trades', 0) > 0}
            
            if not channels:
                warn("No channel data to plot")
                return None
            
            # Sort by total PnL
            sorted_channels = sorted(channels.items(), key=lambda x: x[1].get('total_pnl', 0), reverse=True)
            channel_names = [name[:20] for name, _ in sorted_channels]  # Truncate long names
            
            # Create 2x2 subplot
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle('Channel Performance Comparison', fontsize=16, fontweight='bold')
            
            # 1. Total PnL by Channel
            ax1 = axes[0, 0]
            pnls = [metrics.get('total_pnl', 0) for _, metrics in sorted_channels]
            colors = ['green' if p > 0 else 'red' for p in pnls]
            ax1.barh(channel_names, pnls, color=colors, alpha=0.7)
            ax1.set_xlabel('Total PnL (USDT)', fontsize=10)
            ax1.set_title('Total PnL by Channel', fontsize=12, fontweight='bold')
            ax1.axvline(0, color='black', linestyle='-', linewidth=0.8)
            ax1.grid(axis='x', alpha=0.3)
            
            # 2. Win Rate by Channel
            ax2 = axes[0, 1]
            win_rates = [metrics.get('win_rate', 0) * 100 for _, metrics in sorted_channels]
            bars = ax2.barh(channel_names, win_rates, color='steelblue', alpha=0.7)
            ax2.set_xlabel('Win Rate (%)', fontsize=10)
            ax2.set_title('Win Rate by Channel', fontsize=12, fontweight='bold')
            ax2.axvline(50, color='red', linestyle='--', linewidth=1, label='50% threshold')
            ax2.legend()
            ax2.grid(axis='x', alpha=0.3)
            
            # 3. Trade Count by Channel
            ax3 = axes[1, 0]
            trade_counts = [metrics.get('total_trades', 0) for _, metrics in sorted_channels]
            ax3.barh(channel_names, trade_counts, color='orange', alpha=0.7)
            ax3.set_xlabel('Number of Trades', fontsize=10)
            ax3.set_title('Trade Count by Channel', fontsize=12, fontweight='bold')
            ax3.grid(axis='x', alpha=0.3)
            
            # 4. Profit Factor by Channel
            ax4 = axes[1, 1]
            profit_factors = [metrics.get('profit_factor', 0) for _, metrics in sorted_channels]
            colors = ['green' if pf > 1 else 'red' for pf in profit_factors]
            ax4.barh(channel_names, profit_factors, color=colors, alpha=0.7)
            ax4.set_xlabel('Profit Factor', fontsize=10)
            ax4.set_title('Profit Factor by Channel', fontsize=12, fontweight='bold')
            ax4.axvline(1.0, color='black', linestyle='--', linewidth=1, label='Break-even')
            ax4.legend()
            ax4.grid(axis='x', alpha=0.3)
            
            plt.tight_layout()
            
            output_path = self.output_dir / filename
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            info(f"✅ Channel comparison saved: {output_path}")
            return output_path
        
        except Exception as e:
            error(f"Failed to generate channel comparison: {e}")
            return None
    
    def generate_html_report(
        self, 
        metrics: Dict,
        trades: List[Dict],
        chart_paths: Dict[str, Path],
        filename: str = "backtest_report.html"
    ) -> Path:
        """Generate comprehensive HTML report."""
        
        # Convert chart paths to relative paths for HTML
        chart_refs = {}
        for key, path in chart_paths.items():
            if path:
                chart_refs[key] = path.name
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtest Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-card h3 {{
            margin: 0 0 10px 0;
            color: #555;
            font-size: 0.9em;
            text-transform: uppercase;
        }}
        .metric-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .metric-card .value.positive {{
            color: #27ae60;
        }}
        .metric-card .value.negative {{
            color: #e74c3c;
        }}
        .chart-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .chart-section h2 {{
            margin-top: 0;
            color: #333;
        }}
        .chart-section img {{
            width: 100%;
            height: auto;
            border-radius: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f9f9f9;
        }}
        .positive-pnl {{
            color: #27ae60;
            font-weight: bold;
        }}
        .negative-pnl {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #999;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Backtest Report</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <h3>Initial Capital</h3>
            <div class="value">${metrics.get('initial_capital', 0):,.2f}</div>
        </div>
        <div class="metric-card">
            <h3>Final Capital</h3>
            <div class="value {'positive' if metrics.get('total_return', 0) > 0 else 'negative'}">${metrics.get('final_capital', 0):,.2f}</div>
        </div>
        <div class="metric-card">
            <h3>Total Return</h3>
            <div class="value {'positive' if metrics.get('total_return', 0) > 0 else 'negative'}">
                ${metrics.get('total_return', 0):,.2f} ({metrics.get('total_return_pct', 0):+.2f}%)
            </div>
        </div>
        <div class="metric-card">
            <h3>Total Trades</h3>
            <div class="value">{metrics.get('total_trades', 0)}</div>
        </div>
        <div class="metric-card">
            <h3>Win Rate</h3>
            <div class="value {'positive' if metrics.get('win_rate', 0) > 50 else 'negative'}">{metrics.get('win_rate', 0):.1f}%</div>
        </div>
        <div class="metric-card">
            <h3>Profit Factor</h3>
            <div class="value {'positive' if metrics.get('profit_factor', 0) > 1 else 'negative'}">{metrics.get('profit_factor', 0):.2f}</div>
        </div>
        <div class="metric-card">
            <h3>Expectancy</h3>
            <div class="value {'positive' if metrics.get('expectancy', 0) > 0 else 'negative'}">${metrics.get('expectancy', 0):.2f}</div>
        </div>
        <div class="metric-card">
            <h3>Max Drawdown</h3>
            <div class="value negative">{metrics.get('max_drawdown_pct', 0):.2f}%</div>
        </div>
        <div class="metric-card">
            <h3>Sharpe Ratio</h3>
            <div class="value {'positive' if metrics.get('sharpe_ratio', 0) > 1 else 'negative'}">{metrics.get('sharpe_ratio', 0):.2f}</div>
        </div>
        <div class="metric-card">
            <h3>Avg Win</h3>
            <div class="value positive">${metrics.get('avg_win', 0):.2f}</div>
        </div>
        <div class="metric-card">
            <h3>Avg Loss</h3>
            <div class="value negative">${metrics.get('avg_loss', 0):.2f}</div>
        </div>
        <div class="metric-card">
            <h3>Total Fees</h3>
            <div class="value">${metrics.get('total_fees', 0):.2f}</div>
        </div>
    </div>
    
    <div class="chart-section">
        <h2>📈 Equity Curve</h2>
        <img src="{chart_refs.get('equity', '')}" alt="Equity Curve">
    </div>
    
    <div class="chart-section">
        <h2>📊 Trade Distribution</h2>
        <img src="{chart_refs.get('distribution', '')}" alt="Trade Distribution">
    </div>
    
    <div class="chart-section">
        <h2>🗓️ Monthly Performance</h2>
        <img src="{chart_refs.get('heatmap', '')}" alt="Monthly Heatmap">
    </div>
    
"""
        
        # Add channel comparison if available
        if metrics.get('channel_metrics'):
            html_content += f"""
    <div class="chart-section">
        <h2>📡 Channel Comparison</h2>
        <img src="{chart_refs.get('channel_comparison', '')}" alt="Channel Comparison">
        
        <table style="margin-top: 20px;">
            <thead>
                <tr>
                    <th>Channel</th>
                    <th>Trades</th>
                    <th>Win Rate</th>
                    <th>Total PnL</th>
                    <th>Avg PnL</th>
                    <th>Profit Factor</th>
                    <th>Best Trade</th>
                    <th>Worst Trade</th>
                </tr>
            </thead>
            <tbody>
"""
            
            # Sort channels by total PnL (best to worst)
            channel_metrics = metrics.get('channel_metrics', {})
            sorted_channels = sorted(
                channel_metrics.items(),
                key=lambda x: x[1]['total_pnl'],
                reverse=True
            )
            
            for channel, data in sorted_channels:
                pnl_class = 'positive-pnl' if data['total_pnl'] > 0 else 'negative-pnl'
                html_content += f"""
                <tr>
                    <td><strong>{channel}</strong></td>
                    <td>{data['total_trades']}</td>
                    <td>{data['win_rate']:.1f}%</td>
                    <td class="{pnl_class}">${data['total_pnl']:.2f}</td>
                    <td class="{pnl_class}">${data['avg_pnl_per_trade']:.2f}</td>
                    <td class="{'positive-pnl' if data['profit_factor'] > 1 else 'negative-pnl'}">{data['profit_factor']:.2f}</td>
                    <td class="positive-pnl">${data['best_trade']:.2f}</td>
                    <td class="negative-pnl">${data['worst_trade']:.2f}</td>
                </tr>
"""
            
            html_content += """
            </tbody>
        </table>
    </div>
"""
        
        html_content += """
    <div class="chart-section">
        <h2>📋 Recent Trades (Last 50)</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Channel</th>
                    <th>Symbol</th>
                    <th>Side</th>
                    <th>Entry</th>
                    <th>Exit</th>
                    <th>Exit Reason</th>
                    <th>PnL (USDT)</th>
                    <th>PnL (%)</th>
                    <th>Bars Held</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # Add last 50 trades
        for i, trade in enumerate(trades[-50:], 1):
            pnl_class = 'positive-pnl' if trade['pnl_net'] > 0 else 'negative-pnl'
            channel = trade.get('source', 'unknown')
            html_content += f"""
                <tr>
                    <td>{i}</td>
                    <td>{channel}</td>
                    <td>{trade['symbol']}</td>
                    <td>{trade['side']}</td>
                    <td>${trade['entry_price']:.4f}</td>
                    <td>${trade['exit_price']:.4f}</td>
                    <td>{trade['exit_reason']}</td>
                    <td class="{pnl_class}">${trade['pnl_net']:.2f}</td>
                    <td class="{pnl_class}">{trade['pnl_pct']:+.2f}%</td>
                    <td>{trade['bars_held']}</td>
                </tr>
"""
        
        html_content += """
            </tbody>
        </table>
    </div>
    
    <div class="footer">
        <p>🤖 Generated by MEXC Multi-Source Trading System</p>
    </div>
</body>
</html>
"""
        
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        info(f"✅ HTML report saved: {output_path}")
        return output_path
    
    def export_trades_csv(
        self, 
        trades: List[Dict],
        filename: str = "backtest_trades.csv"
    ) -> Path:
        """Export trades to CSV for external analysis."""
        df = pd.DataFrame(trades)
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False)
        info(f"✅ Trades CSV exported: {output_path}")
        return output_path
