# Signal Parser - Kanal Formatları

Parser artık tüm Telegram kanallarınızdaki sinyal formatlarını destekliyor.

## Desteklenen Formatlar

### 1. English Format (Emoji ile)
**Örnek:**
```
🟢 LONG
💲 DOGEUSDT
📈 Entry : 0.18869 - 0.18925
🎯 Target 1 - 0.19076
🛑 Stop Loss : 0.17926
```

**Çıktı:**
- Symbol: DOGEUSDT
- Side: LONG
- Entry: 0.18897 (iki değerin ortalaması)
- TP: 0.19076
- SL: 0.17926

---

### 2. SETUP Format
**Örnek:**
```
#ICNT SHORT SETUP 

Target 1: $0.2045
Target 2: $0.2015
Lev: 20x

STOP : $0.2190
```

**Çıktı:**
- Symbol: ICNTUSDT
- Side: SHORT
- Entry: None
- TP: 0.2045
- SL: 0.219
- Leverage: 20x

---

### 3. Turkish Format (Basit)
**Örnek:**
```
avax long 

giriş: 21.60
sl: 21.00
tp: 22.30 - 23.40
```

**Çıktı:**
- Symbol: AVAXUSDT
- Side: LONG
- Entry: 21.6
- TP: 22.85 (iki değerin ortalaması)
- SL: 21.0

---

### 4. Turkish Format (Kaldıraç ile)
**Örnek:**
```
#sol $sol 7x kaldıraç long
giriş: 185 | tp: 200
stop: 178
```

**Çıktı:**
- Symbol: SOLUSDT
- Side: LONG
- Entry: 185.0
- TP: 200.0
- SL: 178.0
- Leverage: 7x

---

## Özellikler

✅ **Çoklu Format Desteği:** 4 farklı sinyal formatını otomatik tanıma
✅ **Esnek Sıralama:** giriş/tp/sl sırası önemli değil
✅ **Kaldıraç Çıkarma:** 7x, 20x gibi leverage değerlerini otomatik bulma
✅ **Sembol Normalizasyonu:** Otomatik USDT ekleme (avax → AVAXUSDT)
✅ **Aralık Desteği:** Entry/TP aralıklarının ortalamasını alma
✅ **Türkçe Anahtar Kelimeler:** giriş, tp, sl, stop, kaldıraç
✅ **İngilizce Anahtar Kelimeler:** Entry, Target, Stop Loss
✅ **Emoji Desteği:** 🟢 🔴 💲 📈 🎯 🛑

---

## Kanal Listesi (.env dosyanızda)

```ini
TELEGRAM_CHANNELS=-1002001037199,@kriptodelisi11,-1001370457350,@kriptokampiislem,@kriptostarr,@kriptosimpsons
```

---

## Test Sonuçları

```
✅ Test 1: English format with emoji - BAŞARILI
✅ Test 2: SETUP format with leverage - BAŞARILI  
✅ Test 3: Turkish format (avax) - BAŞARILI
✅ Test 4: Turkish format with leverage (sol) - BAŞARILI
```

---

## Sıradaki Adımlar

1. **Dependencies kurulumu:** `pip install -r requirements.txt`
2. **İlk collector testi:** `python main.py --mode collector`
3. **24-48 saat sinyal toplama**
4. **Parser çalıştırma:** `python telegram/parser.py`
5. **Backtest yapma:** `python main.py --mode backtest`

---

## Notlar

- Parser, en spesifik formatları önce kontrol eder (SETUP → English → Turkish → Simple)
- Sembol isimleri büyük/küçük harf duyarsız (avax, AVAX, Avax hepsi çalışır)
- Entry belirtilmezse (SETUP formatı gibi) market price kullanılacak
- TP/SL aralığı varsa otomatik ortalama alınır
