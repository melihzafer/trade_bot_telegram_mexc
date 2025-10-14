"""
Email Reporter for MEXC Signal Collector.
Sends daily signal reports via email with attached JSONL file.

Usage:
    python email_reporter.py
    
Environment Variables Required:
    SMTP_EMAIL: Gmail address (e.g., your@gmail.com)
    SMTP_PASSWORD: Gmail App Password (not your regular password!)
    REPORT_EMAIL: Recipient email (optional, defaults to SMTP_EMAIL)
    
Setup Gmail App Password:
    1. Go to: https://myaccount.google.com/apppasswords
    2. Select app: Mail
    3. Select device: Other (custom name)
    4. Copy the 16-character password
    5. Add to Railway environment variables
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime
import json
import os


def generate_report_html(stats):
    """Generate HTML report from statistics"""
    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #667eea;
                text-align: center;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin: 20px 0;
            }}
            .stat-card {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }}
            .stat-value {{
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
            }}
            .stat-label {{
                color: #666;
                margin-top: 5px;
            }}
            .channel-list {{
                margin: 20px 0;
            }}
            .channel-item {{
                background: #f8f9fa;
                padding: 10px 15px;
                margin: 5px 0;
                border-radius: 5px;
                display: flex;
                justify-content: space-between;
            }}
            .latest-signal {{
                background: #e9ecef;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
                font-family: monospace;
                white-space: pre-wrap;
            }}
            .footer {{
                text-align: center;
                color: #999;
                margin-top: 30px;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📡 Daily Signal Report</h1>
            <p style="text-align: center; color: #666;">
                {datetime.now().strftime("%B %d, %Y")}
            </p>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{stats['total']}</div>
                    <div class="stat-label">Total Signals</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{stats['channels_count']}</div>
                    <div class="stat-label">Channels</div>
                </div>
            </div>
            
            <h3>📊 Signals by Channel:</h3>
            <div class="channel-list">
    """
    
    # Add channel breakdown
    for channel, count in stats['channels'].items():
        html += f"""
                <div class="channel-item">
                    <span>{channel}</span>
                    <strong>{count}</strong>
                </div>
        """
    
    # Add latest signal
    if stats['latest']:
        html += f"""
            </div>
            
            <h3>🔥 Latest Signal:</h3>
            <div class="latest-signal">
                <strong>Source:</strong> {stats['latest']['source']}<br>
                <strong>Time:</strong> {stats['latest']['ts']}<br>
                <strong>Message:</strong><br>
                {stats['latest']['text']}
            </div>
        """
    
    html += """
            <div class="footer">
                <p>🤖 Automated by MEXC Signal Collector</p>
                <p>Check attached JSONL file for complete data</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def get_stats():
    """Get statistics from raw signals file"""
    raw_file = Path("data/signals_raw.jsonl")
    
    stats = {
        "total": 0,
        "channels": {},
        "channels_count": 0,
        "latest": None
    }
    
    if not raw_file.exists():
        return stats
    
    try:
        with open(raw_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            stats["total"] = len(lines)
            
            for line in lines:
                try:
                    data = json.loads(line.strip())
                    source = data.get("source", "unknown")
                    stats["channels"][source] = stats["channels"].get(source, 0) + 1
                except json.JSONDecodeError:
                    continue
            
            if lines:
                try:
                    stats["latest"] = json.loads(lines[-1].strip())
                except json.JSONDecodeError:
                    pass
            
            stats["channels"] = dict(
                sorted(stats["channels"].items(), key=lambda x: x[1], reverse=True)
            )
            stats["channels_count"] = len(stats["channels"])
    except Exception as e:
        print(f"❌ Error reading stats: {e}")
    
    return stats


def send_email_report():
    """Send email report with signals attachment"""
    # Get environment variables
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")
    receiver_email = os.getenv("REPORT_EMAIL", sender_email)
    
    if not sender_email or not sender_password:
        print("❌ Missing SMTP_EMAIL or SMTP_PASSWORD environment variables!")
        print("📖 Setup guide:")
        print("   1. Go to: https://myaccount.google.com/apppasswords")
        print("   2. Create app password for 'Mail'")
        print("   3. Add to Railway: SMTP_EMAIL and SMTP_PASSWORD")
        return False
    
    # Get statistics
    stats = get_stats()
    
    if stats['total'] == 0:
        print("📭 No signals to report")
        return False
    
    # Create email message
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"📊 Daily Signal Report - {stats['total']} signals - {datetime.now().strftime('%Y-%m-%d')}"
    
    # Plain text version
    text_body = f"""
Daily Signal Report
{datetime.now().strftime("%B %d, %Y")}

Total Signals: {stats['total']}
Channels: {stats['channels_count']}

Signals by Channel:
{chr(10).join(f"  • {ch}: {count}" for ch, count in stats['channels'].items())}

Latest Signal:
{stats['latest']['text'] if stats['latest'] else 'N/A'}

See attached JSONL file for complete data.
"""
    
    # HTML version
    html_body = generate_report_html(stats)
    
    # Attach both versions
    msg.attach(MIMEText(text_body, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))
    
    # Attach JSONL file
    file_path = Path("data/signals_raw.jsonl")
    if file_path.exists():
        with open(file_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = f"signals_{datetime.now().strftime('%Y%m%d')}.jsonl"
            part.add_header('Content-Disposition', f'attachment; filename={filename}')
            msg.attach(part)
    
    # Attach parsed CSV if available
    csv_path = Path("data/signals_parsed.csv")
    if csv_path.exists():
        with open(csv_path, 'rb') as f:
            part = MIMEBase('text', 'csv')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = f"signals_parsed_{datetime.now().strftime('%Y%m%d')}.csv"
            part.add_header('Content-Disposition', f'attachment; filename={filename}')
            msg.attach(part)
    
    # Send email
    try:
        print(f"📧 Sending report to {receiver_email}...")
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"✅ Report sent successfully!")
        print(f"   Total signals: {stats['total']}")
        print(f"   Channels: {stats['channels_count']}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed!")
        print("   Make sure you're using Gmail App Password, not regular password")
        print("   Get it here: https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


if __name__ == "__main__":
    print("📧 MEXC Signal Email Reporter")
    print("=" * 50)
    send_email_report()
