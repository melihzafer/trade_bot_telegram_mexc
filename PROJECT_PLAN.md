## ⚙️ PROJE: **MEXC Multi-Telegram Trading System (Backtest + Paper Trading)**

---

### 🧩 **Ana Modüller (6 Katman)**

| Katman                 | Amaç                                   | Açıklama                                                               |
| ---------------------- | -------------------------------------- | ---------------------------------------------------------------------- |
| 1️⃣ Telegram Collector | Sinyal mesajlarını toplar              | Birden fazla kanaldan (`Telethon`) mesajları dinler, JSON’a kaydeder   |
| 2️⃣ Parser Engine      | Mesajları analiz eder                  | “BUY BTCUSDT @ 64800, TP 65000, SL 64500” gibi mesajları parse eder    |
| 3️⃣ Backtest Engine    | Geçmiş veriyi test eder                | `ccxt` ile MEXC’den tarihsel veriyi çeker, sinyalleri mumlara uygular  |
| 4️⃣ Paper Trader       | Gerçek zamanlı simülasyon              | MEXC Futures testnet API’ye 1:1 emir yollar ama sanal bakiyede çalışır |
| 5️⃣ Risk Manager       | Stop-loss, max loss, leverage yönetimi | Kayıp oranı, kaldıraç limiti, tek işlem riski gibi kontroller          |
| 6️⃣ Logger / Dashboard | Raporlama                              | Her sinyali ve sonucu CSV/JSON + opsiyonel web dashboard’a kaydeder    |

---

### 🧠 **Teknoloji Stack**

| Bileşen            | Kullanım                                    |
| ------------------ | ------------------------------------------- |
| **Python 3.10+**   | Ana dil                                     |
| **Telethon**       | Telegram mesajlarını almak                  |
| **ccxt**           | MEXC API (veri çekmek + testnet işlemi)     |
| **pandas / numpy** | Backtest analizi                            |
| **dotenv**         | API key gizlemek                            |
| **plotly**         | Grafik/istatistik raporu (opsiyonel)        |
| **asyncio**        | Paralel olarak birden fazla kanalı dinlemek |

---

### 🧱 **Proje Dizini (Yapı)**

```
mexc-trade-bot/
│
├── main.py                # ana kontrol
├── telegram/
│   ├── collector.py       # kanalları dinler
│   └── parser.py          # mesajları işler
│
├── trading/
│   ├── backtester.py      # tarihsel backtest
│   ├── paper_trader.py    # testnet simülasyon
│   └── risk_manager.py    # risk kontrol
│
├── utils/
│   ├── logger.py
│   ├── config.py
│   └── helpers.py
│
├── data/
│   ├── signals_raw.json
│   ├── signals_parsed.csv
│   └── backtest_results.csv
│
└── .env                   # MEXC API_KEY / SECRET / TELEGRAM SESSION
```

---

### 🚀 **Geliştirme Yol Haritası (Aşamalar)**

#### 🥇 Aşama 1 – Multi Telegram Collector

* 3-5 kanal belirle (`TELEGRAM_CHANNELS = ["@crypto_signals", "@btc_alerts", "@scalpers"]`)
* Telethon ile bu kanallardan gelen mesajları async olarak dinle.
* Mesajları ham halde `data/signals_raw.json` içine kaydet.

#### 🥈 Aşama 2 – Parser Engine

* Regex ile `BUY/SELL`, `ENTRY`, `SL`, `TP` değerlerini çıkar.
* Kötü mesajları filtrele.
* JSON → CSV’ye kaydet (`symbol, side, entry, sl, tp, date, source`).

#### 🥉 Aşama 3 – Backtest Engine

* `ccxt` ile `fetch_ohlcv()` fonksiyonuyla MEXC’den 1h/15m candle verisi çek.
* Her sinyal için:

  * Entry saatinden sonraki X mumda TP/SL test et.
  * Win/Loss oranı, avgPnL, drawdown hesapla.
* Sonuçları CSV + grafikte göster.

#### 🏅 Aşama 4 – Paper Trading Engine

* MEXC Futures Testnet API’ye bağlan:

  * `https://contract.mexc.com/testnet`
* Gerçek zamanlı sinyali alınca:

  * Emir aç (`create_order`)
  * SL ve TP’yi otomatik ayarla
  * Emirleri logger’a kaydet (kapanışta sonucu yaz)

#### 🧩 Aşama 5 – Risk & Logging

* Risk yöneticisi ekle: max 2 açık işlem, %10’dan fazla risk alma.
* Tüm emirleri `logs/` altında günlük bazlı logla.
* Gerekirse küçük bir dashboard (Flask + Chart.js) ile görselleştir.

---

### 💬 **Kanal Yönetimi (Multi Source)**

Sinyaller genelde benzer formatta gelir ama her kanalın stili farklı olur.
O yüzden `parser.py` içinde her kanal için ayrı bir **parse profili** tanımlayacağız:

```python
if "crypto_signals" in source:
    return parse_style_a(message)
elif "btc_alerts" in source:
    return parse_style_b(message)
```

Bu sayede farklı sinyal şablonlarını destekleriz.

---

### 💰 **Sonuç: Gerçek para öncesi tam güvenlik**

✅ Multi-channel veri
✅ Full backtest
✅ Testnet paper trading
✅ Risk limitleri
✅ Otomatik rapor

---

# MEXC Multi‑Source Trading System — Backtest + Paper Trading (Skeleton v1)

A production‑grade Python skeleton to: (1) collect signals from **multiple Telegram channels**, (2) **parse** them into a unified schema, (3) run **full backtests** against MEXC historical data, and (4) run a **1:1 Paper Trading** engine (virtual orders, live pricing from MEXC public APIs; **no real orders**).

> Stack: Python 3.10+, **Telethon**, **ccxt**, **pandas/numpy**, **pydantic**, **python‑dotenv**, **rich**.

---

## 0) Repo Yapısı

```
mexc-trade-bot/
│
├── main.py                          # Orchestrator (start collectors & engines)
├── requirements.txt
├── .env.sample
│
├── telegram/
│   ├── collector.py                 # Multi-channel async listener (Telethon)
│   └── parser.py                    # Regex-based parsers + channel profiles
│
├── trading/
│   ├── models.py                    # Pydantic models (Signal, Order, Fill, etc.)
│   ├── backtester.py                # Full backtest on historical OHLCV
│   ├── paper_trader.py              # Live paper engine (virtual positions)
│   └── risk_manager.py              # Position sizing, daily loss cap, etc.
│
├── utils/
│   ├── config.py                    # Env + constants
│   ├── logger.py                    # Rich console + CSV/JSON logging
│   └── timeutils.py                 # TZ helpers (Europe/Sofia)
│
├── data/
│   ├── signals_raw.jsonl            # Raw Telegram messages (append-only)
│   ├── signals_parsed.csv           # Unified parsed signals
│   └── backtest_results.csv         # Backtest outcomes
│
└── logs/
    └── runtime.log                  # Rotating log file
```

---

## 1) Kurulum

```bash
# Python 3.10+ tavsiye
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.sample .env                 # .env içeriklerini doldur
```

**requirements.txt**

```
telethon==1.36.0
python-dotenv==1.0.1
ccxt==4.3.77
pandas==2.2.2
numpy==1.26.4
pydantic==2.7.4
rich==13.7.1
```

**.env.sample**

```
# Telegram (Telethon)
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+359XXXXXXXXX
# Kanallar virgülle ayrılmış (@ işaretli ya da ID)
TELEGRAM_CHANNELS=@channel1,@channel2,@channel3

# Trading
EXCHANGE=MEXC
DEFAULT_TIMEFRAME=15m
MAX_CANDLES=1000
# Risk
ACCOUNT_EQUITY_USDT=1000
RISK_PER_TRADE_PCT=1.0
MAX_CONCURRENT_POSITIONS=2
DAILY_MAX_LOSS_PCT=5.0
LEVERAGE=5

# Paths
DATA_DIR=./data
LOG_DIR=./logs
TZ=Europe/Sofia
```

---

## 2) Modeller (trading/models.py)

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

Side = Literal["BUY", "SELL"]

class Signal(BaseModel):
    source: str
    ts: datetime
    symbol: str
    side: Side
    entry: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    note: Optional[str] = None

class Order(BaseModel):
    id: str
    signal_id: str
    symbol: str
    side: Side
    qty: float
    entry_price: float
    sl: Optional[float]
    tp: Optional[float]
    opened_at: datetime
    closed_at: Optional[datetime] = None
    status: Literal["OPEN", "CLOSED", "CANCELED"] = "OPEN"
    pnl_usdt: float = 0.0

class Candle(BaseModel):
    ts: int
    open: float
    high: float
    low: float
    close: float
    volume: float
```

---

## 3) Config & Logger (utils/config.py, utils/logger.py)

**utils/config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", "./data")
LOG_DIR = os.getenv("LOG_DIR", "./logs")
TZ = os.getenv("TZ", "Europe/Sofia")
DEFAULT_TIMEFRAME = os.getenv("DEFAULT_TIMEFRAME", "15m")
MAX_CANDLES = int(os.getenv("MAX_CANDLES", "1000"))

TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE", "")
TELEGRAM_CHANNELS = [c.strip() for c in os.getenv("TELEGRAM_CHANNELS", "").split(",") if c.strip()]

ACCOUNT_EQUITY_USDT = float(os.getenv("ACCOUNT_EQUITY_USDT", "1000"))
RISK_PER_TRADE_PCT = float(os.getenv("RISK_PER_TRADE_PCT", "1.0"))
MAX_CONCURRENT_POSITIONS = int(os.getenv("MAX_CONCURRENT_POSITIONS", "2"))
DAILY_MAX_LOSS_PCT = float(os.getenv("DAILY_MAX_LOSS_PCT", "5.0"))
LEVERAGE = float(os.getenv("LEVERAGE", "5"))
```

**utils/logger.py**

```python
from rich.console import Console
from rich.table import Table
from pathlib import Path
import logging
from .config import LOG_DIR

console = Console()
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=f"{LOG_DIR}/runtime.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

log = logging.getLogger("mexc-bot")

def info(msg: str):
    log.info(msg)
    console.log(msg)

def warn(msg: str):
    log.warning(msg)
    console.log(f"[yellow]{msg}[/yellow]")

def error(msg: str):
    log.error(msg)
    console.log(f"[red]{msg}[/red]")
```

---

## 4) Telegram Collector (telegram/collector.py)

```python
import asyncio, json
from pathlib import Path
from telethon import TelegramClient, events
from utils.config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, TELEGRAM_CHANNELS, DATA_DIR
from utils.logger import info

RAW_PATH = Path(DATA_DIR) / "signals_raw.jsonl"
RAW_PATH.parent.mkdir(parents=True, exist_ok=True)

async def run_collector():
    client = TelegramClient("session", TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.start(phone=TELEGRAM_PHONE)

    @client.on(events.NewMessage(chats=TELEGRAM_CHANNELS))
    async def handler(event):
        msg = {
            "source": event.chat.username if event.chat else str(event.chat_id),
            "ts": event.message.date.isoformat(),
            "text": event.raw_text
        }
        with open(RAW_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
        info(f"RAW >> {msg['source']} | {msg['ts']} | {msg['text'][:80]}...")

    info(f"Listening channels: {TELEGRAM_CHANNELS}")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(run_collector())
```

---

## 5) Parser (telegram/parser.py)

```python
import re, json, csv
from pathlib import Path
from datetime import datetime
from utils.config import DATA_DIR

RAW_PATH = Path(DATA_DIR) / "signals_raw.jsonl"
PARSED_PATH = Path(DATA_DIR) / "signals_parsed.csv"

# Basit, kanal-agnostik bir şablon (kanal profilleri eklenebilir)
PATTERN = re.compile(r"\b(BUY|SELL)\b\s+([A-Z]{2,10}USDT)\b.*?(?:ENTRY[:\s]*([0-9]+\.?[0-9]*))?.*?(?:TP[:\s]*([0-9]+\.?[0-9]*))?.*?(?:SL[:\s]*([0-9]+\.?[0-9]*))?", re.IGNORECASE | re.DOTALL)

FIELDS = ["source","ts","symbol","side","entry","tp","sl","note"]

def parse_line(obj: dict):
    text = obj.get("text", "")
    m = PATTERN.search(text)
    if not m:
        return None
    side = m.group(1).upper()
    symbol = m.group(2).upper()
    entry = float(m.group(3)) if m.group(3) else None
    tp = float(m.group(4)) if m.group(4) else None
    sl = float(m.group(5)) if m.group(5) else None
    return {
        "source": obj.get("source"),
        "ts": obj.get("ts"),
        "symbol": symbol,
        "side": side,
        "entry": entry,
        "tp": tp,
        "sl": sl,
        "note": text[:200]
    }

def run_parser():
    Path(PARSED_PATH).parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if PARSED_PATH.exists():
        with open(PARSED_PATH, newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                existing.add((row["ts"], row["source"]))

    with open(PARSED_PATH, "a", newline="", encoding="utf-8") as out, open(RAW_PATH, encoding="utf-8") as inp:
        w = csv.DictWriter(out, fieldnames=FIELDS)
        if out.tell() == 0:
            w.writeheader()
        for line in inp:
            obj = json.loads(line)
            key = (obj.get("ts"), obj.get("source"))
            if key in existing:
                continue
            parsed = parse_line(obj)
            if parsed:
                w.writerow(parsed)

if __name__ == "__main__":
    run_parser()
```

> Not: İleride `parse_style_x()` fonksiyonları ile kanal bazlı şablonlar ekleyebilirsin.

---

## 6) Full Backtest (trading/backtester.py)

```python
import ccxt, pandas as pd
from pathlib import Path
from utils.config import DATA_DIR, DEFAULT_TIMEFRAME, MAX_CANDLES
from utils.logger import info

PARSED_PATH = Path(DATA_DIR) / "signals_parsed.csv"
RESULTS_PATH = Path(DATA_DIR) / "backtest_results.csv"

def fetch_ohlcv(symbol: str, timeframe: str = DEFAULT_TIMEFRAME, limit: int = MAX_CANDLES):
    ex = ccxt.mexc()
    bars = ex.fetch_ohlcv(symbol.replace("USDT", "/USDT"), timeframe=timeframe, limit=limit)
    df = pd.DataFrame(bars, columns=["ts","open","high","low","close","volume"])
    return df

def evaluate_signal(row, df: pd.DataFrame, lookahead=96):  # 96 * 15m ≈ 24h
    # Entry yoksa, ilk close’u entry say
    entry = row["entry"] or float(df.iloc[-1]["close"])  # basit fallback
    tp = row["tp"]
    sl = row["sl"]

    sub = df.tail(lookahead)
    hit_tp = hit_sl = False

    if row["side"] == "BUY":
        if tp is not None:
            hit_tp = (sub["high"] >= tp).any()
        if sl is not None:
            hit_sl = (sub["low"] <= sl).any()
    else:  # SELL
        if tp is not None:
            hit_tp = (sub["low"] <= tp).any()
        if sl is not None:
            hit_sl = (sub["high"] >= sl).any()

    if hit_tp and hit_sl:
        # İlk hangisi? (yaklaşık):
        first_tp = sub[sub["high"] >= tp].index.min() if tp is not None else None
        first_sl = sub[sub["low"] <= sl].index.min() if sl is not None else None
        if first_tp is not None and first_sl is not None:
            hit_tp = first_tp < first_sl
            hit_sl = not hit_tp

    if hit_tp:
        return "WIN"
    if hit_sl:
        return "LOSS"
    # Aksi halde sonuçsuz / open
    return "OPEN"

def run_backtest():
    df_sig = pd.read_csv(PARSED_PATH)
    records = []
    for _, row in df_sig.iterrows():
        try:
            df = fetch_ohlcv(row["symbol"])
            outcome = evaluate_signal(row, df)
            records.append({
                **row.to_dict(),
                "outcome": outcome
            })
        except Exception as e:
            records.append({**row.to_dict(), "outcome": f"ERROR: {e}"})
    pd.DataFrame(records).to_csv(RESULTS_PATH, index=False)
    info(f"Backtest complete → {RESULTS_PATH}")

if __name__ == "__main__":
    run_backtest()
```

> İyileştirme: sinyal timestamp’ine göre **o andan sonraki** mumları alacak şekilde `since` parametresi kullanarak daha kesin bir test yapılabilir.

---

## 7) Paper Trader (trading/paper_trader.py)

Virtual engine: emirleri **simüle eder**, canlı fiyatı `ccxt` public endpoint’inden okur, PnL ve kapanışı mantıkla hesaplar.

```python
import asyncio, time
import ccxt
import pandas as pd
from datetime import datetime
from pathlib import Path
from utils.config import DATA_DIR, ACCOUNT_EQUITY_USDT, RISK_PER_TRADE_PCT, LEVERAGE, MAX_CONCURRENT_POSITIONS
from utils.logger import info, warn

PARSED_PATH = Path(DATA_DIR) / "signals_parsed.csv"

class PaperExchange:
    def __init__(self):
        self.ex = ccxt.mexc()

    def last_price(self, symbol: str) -> float:
        t = self.ex.fetch_ticker(symbol.replace("USDT", "/USDT"))
        return float(t["last"]) if t and t.get("last") else float(t["close"]) if t.get("close") else float(t["info"].get("p", 0))

class PaperTrader:
    def __init__(self):
        self.cash = ACCOUNT_EQUITY_USDT
        self.positions = []  # list of dicts
        self.ex = PaperExchange()

    def position_size(self, entry: float) -> float:
        risk_usdt = self.cash * (RISK_PER_TRADE_PCT/100.0)
        # Basit: risk = (entry - sl) * qty  (BUY için)
        # SL yoksa nominal pozisyon: risk_usdt / (entry * 0.01)
        nominal = risk_usdt / max(entry * 0.01, 1e-6)
        base_qty = nominal * LEVERAGE / entry
        return round(base_qty, 6)

    def open_position(self, sig):
        price = self.ex.last_price(sig["symbol"]) if not sig["entry"] else sig["entry"]
        qty = self.position_size(price)
        if len(self.positions) >= MAX_CONCURRENT_POSITIONS:
            warn("Max concurrent positions reached. Skipping.")
            return
        pos = {
            "symbol": sig["symbol"],
            "side": sig["side"],
            "entry": price,
            "qty": qty,
            "sl": sig["sl"],
            "tp": sig["tp"],
            "opened_at": datetime.utcnow(),
        }
        self.positions.append(pos)
        info(f"OPEN {pos['side']} {pos['symbol']} qty={qty} @ {price}")

    def mark_and_maybe_close(self, pos):
        price = self.ex.last_price(pos["symbol"])
        pnl = 0.0
        if pos["side"] == "BUY":
            pnl = (price - pos["entry"]) * pos["qty"]
            if pos.get("tp") and price >= pos["tp"]:
                pos["closed_at"] = datetime.utcnow(); pos["pnl"] = pnl; return True
            if pos.get("sl") and price <= pos["sl"]:
                pos["closed_at"] = datetime.utcnow(); pos["pnl"] = pnl; return True
        else:  # SELL
            pnl = (pos["entry"] - price) * pos["qty"]
            if pos.get("tp") and price <= pos["tp"]:
                pos["closed_at"] = datetime.utcnow(); pos["pnl"] = pnl; return True
            if pos.get("sl") and price >= pos["sl"]:
                pos["closed_at"] = datetime.utcnow(); pos["pnl"] = pnl; return True
        pos["pnl"] = pnl
        return False

    async def loop(self):
        df = pd.read_csv(PARSED_PATH)
        # Basit: yeni sinyallerin hepsini aç (gerçekte zaman filtresi gerekir)
        for _, sig in df.iterrows():
            self.open_position(sig)
            await asyncio.sleep(0.2)
        # İzleme döngüsü
        while True:
            for pos in list(self.positions):
                closed = self.mark_and_maybe_close(pos)
                if closed:
                    info(f"CLOSE {pos['side']} {pos['symbol']} pnl={pos['pnl']:.2f} USDT")
                    self.cash += pos['pnl']
                    self.positions.remove(pos)
            await asyncio.sleep(2)

async def run_paper():
    trader = PaperTrader()
    await trader.loop()

if __name__ == "__main__":
    asyncio.run(run_paper())
```

> Not: Paper trader gerçek zamanlıya yakın çalışır; gerçek 1:1 akış için `signals_parsed.csv` yerine canlı **parser pipeline** ile besleyebilirsin (main.py bunu yapar).

---

## 8) Risk Manager (trading/risk_manager.py)

```python
from utils.config import ACCOUNT_EQUITY_USDT, DAILY_MAX_LOSS_PCT

class RiskManager:
    def __init__(self):
        self.equity_start = ACCOUNT_EQUITY_USDT

    def daily_hard_stop(self, current_equity: float) -> bool:
        max_loss = self.equity_start * (DAILY_MAX_LOSS_PCT/100.0)
        return (self.equity_start - current_equity) >= max_loss
```

---

## 9) Orchestrator (main.py)

Canlıda: Collector → Parser → PaperTrader akışı.

```python
import asyncio
from telegram.collector import run_collector
from telegram.parser import run_parser
from trading.paper_trader import run_paper
from utils.logger import info

async def parser_worker():
    # Basit periyodik parser; istersen raw stream ile event-driven yap
    import time
    while True:
        run_parser()
        await asyncio.sleep(5)

async def main():
    info("Starting MEXC Multi-Source System …")
    # Collector, Parser, Paper Trader birlikte
    await asyncio.gather(
        run_collector(),
        parser_worker(),
        run_paper(),
    )

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 10) Çalıştırma Sırası

1. **Telethon ilk login:** `python telegram/collector.py` → SMS/login akışıyla session oluşur.
2. **Ana sistem:** `python main.py`

   * Collector kanalları dinler → raw JSONL yazar
   * Parser 5 sn’de bir parsed CSV’yi günceller
   * Paper trader parsed sinyallere göre sanal pozisyon açar ve TP/SL ile kapatır
3. **Backtest:** `python trading/backtester.py`

---

## 11) Sonraki İyileştirmeler (Roadmap)

* [ ] Kanal başına özel parser profilleri (TP1/TP2/TP3, % hedefler, entry range)
* [ ] Sinyal timestamp’ine göre **since** tabanlı backtest (lookahead yanlılığını azalt)
* [ ] Paper trader’da **fee**, **slippage**, **funding** simülasyonu
* [ ] Günlük PnL, max drawdown, Sharpe raporu
* [ ] Basit Flask dashboard + websockets
* [ ] Webhook/Discord/Telegram bildirimleri (trade open/close)
* [ ] “No-trade” filtreleri (volatilite, spread, minimum R:R)

```
```


### Ne yapıyorsun şimdi? (hızlı kurulum)

1. Python 3.10+ kurulu olsun.
2. Proje klasöründe:

```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.sample .env
```

3. `.env` doldur:

* `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`
* `TELEGRAM_CHANNELS=@kanal1,@kanal2,@kanal3`
* Risk ve equity parametrelerini kendi planına göre ayarla.

4. **Telethon login** (ilk kez):

```
python telegram/collector.py
```

SMS kodunu gir, session oluşsun.

5. **Tüm sistemi başlat**:

```
python main.py
```

* Collector canlı mesajları `data/signals_raw.jsonl`’a düşürür.
* Parser 5 sn’de bir `signals_parsed.csv` günceller.
* Paper trader canlı fiyatla sanal pozisyon açıp TP/SL ile kapatır (gerçek emir yok).

6. **Full Backtest** (tarihsel veriyle):

```
python trading/backtester.py
```

Çıktı: `data/backtest_results.csv`.

---

### Notlar / Zor kısımlar

* Parser şu an “genel regex”. Kanalların formatına özel profil ekleyeceğiz (TP1/TP2/TP3, entry range vs.).
* Paper trader 1:1 mantıkla **gerçek fiyat** akışından simüle ediyor; fee/slippage/funding eklemek istiyorsan roadmap’te var.
* İstersen MEXC Futures testnet’e gerçek emir gönderen bir modüle de evriltiriz; ama önce bu simülasyonu sağlamlaştıralım.

Hazırsan bana **kanal @usernamelerini** yaz; parser’a kanal-özel kurallar ekleyip V2’ye geçeyim. Ayrıca istersen risk kurallarını (% risk, max açık pozisyon vs.) senin günlük hedeflerine göre optimize edeyim.
