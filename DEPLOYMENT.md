# 🚀 Cloud Deployment Klavuzu

## Railway.app ile 7/24 Deployment (Önerilen)

### ✅ Avantajlar
- Tamamen ücretsiz ($5 aylık kredi, bu bot için fazlasıyla yeterli)
- Persistent disk (Telegram session kaybolmaz)
- Auto-restart on failure
- GitHub ile otomatik deploy
- Environment variables yönetimi

---

## 📋 Adım Adım Railway Deployment

### 1️⃣ Railway Hesabı Oluştur

1. https://railway.app/ adresine git
2. "Start a New Project" tıkla
3. GitHub ile giriş yap

### 2️⃣ Projeyi Deploy Et

```bash
# Railway CLI kurulumu (opsiyonel)
npm install -g @railway/cli

# Ya da GitHub üzerinden:
# 1. Railway Dashboard → New Project
# 2. Deploy from GitHub repo seç
# 3. melihzafer/trade_bot_telegram_mexc seç
```

### 3️⃣ Environment Variables Ekle

Railway Dashboard'da **Variables** sekmesine şunları ekle:

```env
TELEGRAM_API_ID=28115427
TELEGRAM_API_HASH=dee3e8cdaf87c416dabd1db1a224cee1
TELEGRAM_PHONE=+359892958483
TELEGRAM_CHANNELS=-1002001037199,@kriptodelisi11,-1001370457350,@kriptokampiislem,@kriptostarr,@kriptosimpsons

EXCHANGE=mexc
DEFAULT_TIMEFRAME=15m
MAX_CANDLES=1000

ACCOUNT_EQUITY_USDT=1000
RISK_PER_TRADE_PCT=1.0
MAX_CONCURRENT_POSITIONS=2
DAILY_MAX_LOSS_PCT=5.0
LEVERAGE=5

DATA_DIR=./data
LOG_DIR=./logs
TZ=Europe/Sofia
```

### 4️⃣ Persistent Disk Ekle (ÖNEMLİ!)

Telegram session dosyasını kaybetmemek için:

1. Railway Dashboard → Settings
2. **Volumes** sekmesi
3. "Add Volume" tıkla
4. Mount path: `/app/data`
5. Size: 1GB (yeterli)

### 5️⃣ İlk Deployment

Railway otomatik deploy edecek. İlk çalıştırmada:

1. **Logs** sekmesine git
2. Telegram authentication kodu isteyecek
3. **SORUN:** Railway terminal interactive değil, kod giremezsin!

**Çözüm:** İlk authentication'ı local'de yapalım:

```powershell
# Local'de session oluştur
python main.py --mode collector
# Telegram kodunu gir
# Ctrl+C ile durdur

# Session dosyasını Railway'e yükle
railway volume add data
railway volume upload data/telegram.session
```

---

## 🔄 Alternatif: Render.com

### Avantajlar
- Tamamen ücretsiz
- Background worker desteği
- Kolay setup

### Dezavantajlar
- 15 dakika inactivity sonrası sleep
- Cron job ile wake up gerekir

### Setup

1. https://render.com/ → New Background Worker
2. GitHub repo bağla
3. Start Command: `python main.py --mode collector`
4. Environment variables ekle
5. Deploy

**Sleep problemi çözümü:**
```python
# main.py içinde her 10 dakikada bir dummy log
import time
while True:
    # ... collector code ...
    time.sleep(600)  # 10 dakika
    print("keepalive")  # Render'i uyandırır
```

---

## 🐳 Docker ile Deployment (Tüm platformlar)

### Dockerfile Oluştur

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py", "--mode", "collector"]
```

### Deploy

```bash
# Docker Hub'a push
docker build -t mexc-trading-bot .
docker push yourusername/mexc-trading-bot

# Railway/Render/Fly.io'da deploy
```

---

## 🆓 Diğer Ücretsiz Seçenekler

### 1. **Fly.io**
```bash
# Fly CLI kurulum
curl -L https://fly.io/install.sh | sh

# Deploy
fly launch
fly deploy
```

### 2. **Heroku** (Ücretli oldu, önermeyen)
- Artık ücretsiz tier yok

### 3. **Oracle Cloud** (Forever Free)
- ARM VM ücretsiz
- Biraz karmaşık setup
- SSH ile manual kurulum gerekir

### 4. **Google Cloud Run**
- $300 ücretsiz kredi (90 gün)
- Sonrasında çok düşük ücret

---

## 📊 Maliyet Karşılaştırması

| Platform | Ücretsiz Tier | 7/24 | Persistent Disk | Kurulum |
|----------|---------------|------|-----------------|---------|
| Railway | $5/ay kredi | ✅ | ✅ | ⭐⭐⭐ |
| Render | Unlimited | ⚠️ Sleep | ✅ | ⭐⭐⭐ |
| Fly.io | 3 VM | ✅ | ✅ | ⭐⭐ |
| Oracle | Forever Free | ✅ | ✅ | ⭐ |
| PythonAnywhere | Limited | ❌ | ✅ | ⭐⭐⭐ |

---

## 🎯 Önerim

**Başlangıç için:** Railway.app
- En kolay setup
- $5 kredi bu bot için 2-3 ay yeter
- Persistent disk
- Auto-restart

**Uzun vadeli:** Fly.io veya Oracle Cloud
- Tamamen ücretsiz
- Biraz daha karmaşık setup

---

## 🔧 Railway Deployment Checklist

- [ ] Railway hesabı oluştur
- [ ] GitHub repo bağla
- [ ] Environment variables ekle
- [ ] Persistent volume ekle (1GB)
- [ ] Local'de Telegram session oluştur
- [ ] Session'ı Railway'e upload et
- [ ] Deploy butonuna bas
- [ ] Logs'u izle ve çalıştığını doğrula

---

## 🆘 Sorun Giderme

### Problem: "Telegram session not found"
```bash
# Local'de session oluştur
python main.py --mode collector
# Telegram kodunu gir

# Railway CLI ile upload
railway volume add data
railway run python main.py --mode collector
```

### Problem: "Out of memory"
- Railway'de plan upgrade et (512MB → 1GB)
- Veya başka platforma geç

### Problem: "Connection timeout"
- Railway'in outbound network kurallarını kontrol et
- Telegram API erişiminin engellenmediğinden emin ol

---

## 📞 İletişim

Deploy sırasında sorun yaşarsan, Railway Dashboard'daki logs'u paylaş!
