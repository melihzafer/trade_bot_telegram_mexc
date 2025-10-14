"""
Flask Web API for MEXC Signal Collector.
Provides web interface to view stats and download collected signals.

Usage:
    python api.py
    
Access:
    http://localhost:8080 (local)
    https://your-app.railway.app (production)
"""
from flask import Flask, send_file, jsonify, render_template_string
from pathlib import Path
import json
from datetime import datetime
import os

app = Flask(__name__)

# HTML template with beautiful dashboard
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>📡 MEXC Signal Collector</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            color: white;
        }
        h1 {
            text-align: center;
            margin-bottom: 40px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255,255,255,0.2);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .stat-value {
            font-size: 3em;
            font-weight: bold;
            margin: 15px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .stat-label {
            font-size: 1em;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .download-section {
            margin: 30px 0;
        }
        .btn {
            display: block;
            width: 100%;
            padding: 18px;
            margin: 15px 0;
            background: rgba(255,255,255,0.3);
            border: 2px solid rgba(255,255,255,0.5);
            border-radius: 12px;
            color: white;
            font-size: 1.2em;
            font-weight: bold;
            cursor: pointer;
            text-decoration: none;
            text-align: center;
            transition: all 0.3s;
            backdrop-filter: blur(5px);
        }
        .btn:hover {
            background: rgba(255,255,255,0.5);
            transform: translateY(-3px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
        }
        .channels-section {
            margin-top: 40px;
        }
        .channels-title {
            font-size: 1.5em;
            margin-bottom: 20px;
            text-align: center;
        }
        .channel-list {
            display: grid;
            gap: 10px;
        }
        .channel-item {
            background: rgba(255,255,255,0.15);
            padding: 15px 20px;
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.3s;
        }
        .channel-item:hover {
            background: rgba(255,255,255,0.25);
        }
        .channel-name {
            font-weight: 500;
        }
        .channel-count {
            background: rgba(255,255,255,0.3);
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
        }
        .latest-signal {
            background: rgba(0,0,0,0.2);
            padding: 20px;
            border-radius: 15px;
            margin-top: 30px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            line-height: 1.6;
        }
        .latest-signal-title {
            font-size: 1.3em;
            margin-bottom: 15px;
            font-family: 'Segoe UI', sans-serif;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            opacity: 0.7;
            font-size: 0.9em;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            background: #4ade80;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .no-data {
            text-align: center;
            padding: 40px;
            font-size: 1.2em;
            opacity: 0.7;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📡 MEXC Signal Collector</h1>
        
        {% if stats.total > 0 %}
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Signals</div>
                <div class="stat-value">{{ stats.total }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Channels</div>
                <div class="stat-value">{{ stats.channels_count }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Last Update</div>
                <div class="stat-value" style="font-size: 1.8em;">{{ stats.last_update }}</div>
            </div>
        </div>
        
        <div class="download-section">
            <h2 style="text-align: center; margin-bottom: 20px;">
                <span class="status-indicator"></span>
                Download Collected Data
            </h2>
            <a href="/download/raw" class="btn btn-primary">📥 Download Raw Signals (JSONL)</a>
            <a href="/download/parsed" class="btn">📊 Download Parsed Signals (CSV)</a>
            <a href="/api/stats" class="btn">🔌 JSON API Stats</a>
        </div>
        
        {% if stats.channels %}
        <div class="channels-section">
            <div class="channels-title">📊 Signals by Channel</div>
            <div class="channel-list">
                {% for channel, count in stats.channels.items() %}
                <div class="channel-item">
                    <span class="channel-name">{{ channel }}</span>
                    <span class="channel-count">{{ count }}</span>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if stats.latest %}
        <div class="latest-signal">
            <div class="latest-signal-title">🔥 Latest Signal</div>
            <strong>Source:</strong> {{ stats.latest.source }}<br>
            <strong>Time:</strong> {{ stats.latest.ts }}<br>
            <strong>Message:</strong><br>
            {{ stats.latest.text }}
        </div>
        {% endif %}
        
        {% else %}
        <div class="no-data">
            <h2>📭 No Signals Collected Yet</h2>
            <p style="margin-top: 20px;">Collector is running... Please wait for signals to arrive.</p>
        </div>
        {% endif %}
        
        <div class="footer">
            <p>🤖 Automated Signal Collection System</p>
            <p>Last checked: {{ now }}</p>
        </div>
    </div>
</body>
</html>
"""


@app.route('/')
def home():
    """Homepage with stats dashboard"""
    stats = get_stats()
    return render_template_string(
        HTML_TEMPLATE,
        stats=stats,
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


@app.route('/download/raw')
def download_raw():
    """Download raw signals JSONL file"""
    file_path = Path("data/signals_raw.jsonl")
    
    if not file_path.exists():
        return "📭 No signals collected yet. Please check back later.", 404
    
    filename = f"signals_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/x-ndjson'
    )


@app.route('/download/parsed')
def download_parsed():
    """Download parsed signals CSV file"""
    file_path = Path("data/signals_parsed.csv")
    
    if not file_path.exists():
        return "📭 No parsed signals yet. Run parser first: python telegram/parser.py", 404
    
    filename = f"signals_parsed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )


@app.route('/api/stats')
def api_stats():
    """JSON API endpoint for statistics"""
    return jsonify(get_stats())


@app.route('/health')
def health():
    """Health check endpoint for Railway"""
    return jsonify({
        "status": "healthy",
        "service": "mexc-signal-collector",
        "timestamp": datetime.now().isoformat()
    })


def get_stats():
    """Calculate collection statistics from raw signals"""
    raw_file = Path("data/signals_raw.jsonl")
    
    stats = {
        "total": 0,
        "channels": {},
        "channels_count": 0,
        "latest": None,
        "last_update": "N/A"
    }
    
    if not raw_file.exists():
        return stats
    
    try:
        with open(raw_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            stats["total"] = len(lines)
            
            # Count signals by channel
            for line in lines:
                try:
                    data = json.loads(line.strip())
                    source = data.get("source", "unknown")
                    stats["channels"][source] = stats["channels"].get(source, 0) + 1
                except json.JSONDecodeError:
                    continue
            
            # Get latest signal
            if lines:
                try:
                    stats["latest"] = json.loads(lines[-1].strip())
                    # Format timestamp
                    ts = stats["latest"]["ts"].replace('Z', '+00:00')
                    dt = datetime.fromisoformat(ts)
                    stats["last_update"] = dt.strftime("%H:%M:%S")
                except (json.JSONDecodeError, KeyError):
                    pass
            
            # Sort channels by count (descending)
            stats["channels"] = dict(
                sorted(stats["channels"].items(), key=lambda x: x[1], reverse=True)
            )
            stats["channels_count"] = len(stats["channels"])
            
    except Exception as e:
        print(f"❌ Error reading stats: {e}")
    
    return stats


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    
    print(f"🚀 Starting Flask API on port {port}")
    print(f"📡 Access dashboard: http://localhost:{port}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
