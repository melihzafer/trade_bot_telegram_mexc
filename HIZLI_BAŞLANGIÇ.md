# 🚀 HIZLI BAŞLANGIÇ KLAVUZU

## ✅ Tamamlananlar

- [x] Python 3.14 kuruldu
- [x] Virtual environment oluşturuldu (`.venv`)
- [x] Tüm dependencies kuruldu
- [x] Telegram API alındı (api_id: 28115427)
- [x] `.env` dosyası yapılandırıldı
- [x] 6 kanal eklendi
- [x] Parser 4 farklı sinyal formatını destekliyor

---

## 📋 Şimdi Yapılacaklar

### 1️⃣ İlk Collector Testi (5 dakika)

```powershell
# Virtual environment'ı aktif et (henüz aktif değilse)
.venv\Scripts\Activate.ps1

# Collector'ı başlat
python main.py --mode collector
```

**Ne olacak:**
- Telegram'dan SMS kodu gelecek (veya uygulama bildirimi)
- Kodu terminale yapıştır
- Session oluşturulacak (`telegram.session` dosyası)
- 6 kanaldan mesaj dinlemeye başlayacak
- Tüm sinyaller `data/signals_raw.jsonl` dosyasına kaydedilecek

**Çıktı örneği:**
```
🔑 Telegram authentication required
Enter code: 12345
✅ Authenticated successfully
📡 Listening to 6 channels...
📥 Message from @kriptodelisi11
📥 Message from @kriptosimpsons
...
```

---

### 2️⃣ 24-48 Saat Bekle

Sistem, kanallardan gelen tüm sinyalleri toplayacak.

**İpucu:** Collector'ı arkaplanda çalıştır:
```powershell
# Ctrl+C ile durdur
# Tekrar başlatmak için:
python main.py --mode collector
```

---

### 3️⃣ Sinyalleri Parse Et (2 dakika)

```powershell
# Ham sinyalleri yapılandırılmış CSV'ye dönüştür
python telegram/parser.py
```

**Çıktı:**
- `data/signals_parsed.csv` oluşturulacak
- Kaç sinyal parse edildiğini göreceksin

**CSV formatı:**
```
source,ts,symbol,side,entry,tp,sl,leverage,note
kriptodelisi11,2025-10-13T12:00:00,ICNTUSDT,SHORT,None,0.2045,0.219,20,...
```

---

### 4️⃣ Backtest Yap (5 dakika)

```powershell
# Toplanan sinyallerle geçmiş performans testi
python main.py --mode backtest
```

**Ne test edilecek:**
- Parse edilen sinyaller
- Risk yönetimi (stop loss, take profit)
- Position sizing
- Toplam kar/zarar

**Çıktı örneği:**
```
📊 Backtest Results
─────────────────────────────
Total Signals:    47
Profitable:       32 (68%)
Losing:           15 (32%)
Total PnL:        +$234.50
Max Drawdown:     -$45.00
Sharpe Ratio:     1.85
```

---

### 5️⃣ Paper Trading Başlat (opsiyonel)

```powershell
# Gerçek para kullanmadan simülasyon
python main.py --mode paper
```

**Ne yapacak:**
- Gerçek zamanlı sinyalleri dinleyecek
- Sanal pozisyonlar açacak
- Risk yönetimi uygulayacak
- PnL takip edecek

---

## 🎯 İlk Hedef

**Bugün:** Collector'ı başlat ve Telegram authentication'ı tamamla

**24-48 saat içinde:** Backtest sonuçlarını gör

**1 hafta içinde:** Paper trading ile canlı sinyal performansını izle

---

## ⚙️ Yapılandırma Dosyası

**`.env` dosyanızda:**

```ini
# ✅ Telegram (HAZIR)
TELEGRAM_API_ID=28115427
TELEGRAM_API_HASH=dee3e8cdaf87c416dabd1db1a224cee1
TELEGRAM_PHONE=+359892958483
TELEGRAM_CHANNELS=-1002001037199,@kriptodelisi11,-1001370457350,@kriptokampiislem,@kriptostarr,@kriptosimpsons

# ⚙️ Risk Management (İSTERSEN DEĞİŞTİR)
ACCOUNT_EQUITY_USDT=1000
RISK_PER_TRADE_PCT=1.0
MAX_CONCURRENT_POSITIONS=2
DAILY_MAX_LOSS_PCT=5.0
LEVERAGE=5

# 📊 Exchange
EXCHANGE=mexc
DEFAULT_TIMEFRAME=15m
MAX_CANDLES=1000

# 🕐 Timezone
TZ=Europe/Sofia
```

---

## 🆘 Sorun Giderme

### Problem: "No module named 'telethon'"
```powershell
pip install -r requirements.txt
```

### Problem: "TELEGRAM_API_ID not set"
```powershell
# .env.sample yerine .env dosyası kullan
copy .env.sample .env
```

### Problem: Telegram kodu gelmiyor
- my.telegram.org'da oluşturduğun app'i kontrol et
- Telefon numarasının doğru olduğundan emin ol (+359892958483)
- Telegram Desktop/Mobile uygulamasını kontrol et

### Problem: Parser sinyal bulamıyor
```powershell
# Test et
python test_parser.py
```

---

## 📁 Proje Yapısı

```
trade_bot_telegram_mexc/
├── .env                    # ✅ Yapılandırma (senin ayarların)
├── .venv/                  # ✅ Virtual environment
├── main.py                 # 🎯 Ana program
├── telegram/
│   ├── collector.py        # 📡 Mesaj dinleyici
│   └── parser.py           # 🔍 Sinyal parser
├── trading/
│   ├── backtester.py       # 📊 Geçmiş test
│   ├── paper_trader.py     # 💰 Simülasyon
│   └── risk_manager.py     # ⚠️ Risk kontrol
└── data/
    ├── signals_raw.jsonl   # 📥 Ham mesajlar
    └── signals_parsed.csv  # 📋 Parse edilmiş sinyaller
```

---

## 🎬 Şimdi Başla!

```powershell
# 1. Virtual environment'ı aktif et
.venv\Scripts\Activate.ps1

# 2. Collector'ı başlat
python main.py --mode collector
```

**Telegram kodunu gir ve sinyalleri toplamaya başla!** 🚀
