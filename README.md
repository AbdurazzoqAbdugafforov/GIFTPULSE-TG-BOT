# 🎁 GiftPulse — Professional Telegram Gifts Bozor Tahlili va Monitoring Platformasi

**GiftPulse** — Telegram Collectible Gifts (Telegram kolleksiya sovg'alari) bozorini chuqur tahlil qilish, kolleksiyalar va individual modellar floor narxlarini kuzatish, noyoblik darajalarini (rarity) aniqlash, moslashtirilgan narx signallari, shaxsiy sovg'alar portfeli hamda bozor indeksini (TGGI) taqdim etuvchi premium analitika platformasi.

Platforma ikki xil uzviy bog'langan interfeys orqali ishlaydi:
1. 🤖 **Professional Telegram Bot (Aiogram 3.x):** O'zbek tili (birlamchi), ingliz va rus tillarida interaktiv menyular, inline paginatsiya va push-xabarnomalar.
2. 📱 **Telegram Mini App (React + TypeScript + Vite):** Telegram ichida ochiluvchi ixcham pastki oyna (Compact BottomSheet) va to'liq kengaytirilgan (Expanded) rejimdagi zamonaviy vizual interfeys.

---

## 📌 1. Mahsulot Kontseptsiyasi va Bozor Ma'lumotlari

### ⚠️ Muhim Bozor Chegaralari
- **Analitik Ma'lumot:** GiftPulse faqat tahliliy va axborot beruvchi monitoring platformasidir.
- **Savdo Qilmaydi:** Sovg'alarni to'g'ridan-to'g'ri sotib olmaydi, sotmaydi va o'tkazmaydi.
- **Xavfsiz:** Foydalanuvchilarning Telegram maxfiy parollari, 2FA kodlari, sessiya fayllari yoki hamyon maxfiy kalitlarini talab qilmaydi.
- **Kunlik Snapshotlar:** Birlamchi ochiq ma'lumotlar manbasi sifatida **TG Gifts Open Data** kunlik snapshotlaridan foydalanadi. Platforma kunlik snapshotlarni soxta soniyalik "jonli order-book" sifatida ko'rsatmaydi va har bir ekranda ma'lumot sanasi hamda yangilanish holatini ko'rsatadi.

### 🌐 Rasmiy Ma'lumot Manbasi va Attributsiya
GiftPulse [TG Gifts](https://tggifts.com) ochiq ma'lumotlar bazasiga tayanadi:
- **Kolleksiyalar tarixi:** `https://tggifts.com/data/floors-daily.json`
- **Modellar va noyoblik tarixi:** `https://tggifts.com/data/models-daily.json`
- **Bozor indeksi:** `https://tggifts.com/data/index.json`
- **Litsenziya:** Barcha ma'lumotlar **Creative Commons Attribution 4.0 International (CC BY 4.0)** litsenziyasi asosida taqdim etiladi.

> [!NOTE]
> Barcha tahliliy ekranlarda majburiy havolali attributsiya mavjud:  
> **Data: [TG Gifts (tggifts.com)](https://tggifts.com)** (CC BY 4.0)

---

## 💎 2. Asosiy Funksional Imkoniyatlar

### 📊 1. Sovg'a Kolleksiyalari Bozori (Gift Market)
- Kolleksiyalar ro'yxati, qidiruv va filtrlash (nomi, floor narxi, 24 soatlik o'zgarishi).
- Har bir kolleksiya uchun eng so'nggi floor narxi (GRAM birligida).
- 1 kunlik va 7 kunlik narx o'zgarishi dinamikasi (% larda).
- Oxirgi kunlardagi sotuvlar hajmi (recent sales count).
- Tarixiy floor narxlari grafigi va observation sanalari.

### 🦄 2. Modellar va Noyoblik (Models & Rarity)
- Kolleksiya ichidagi barcha alohida modellarni ko'rish va taqqoslash.
- **Haqiqiy Noyoblik Hisobi:** Rarity permille qiymati aniq formulada foizga aylantiriladi:  
  $$\text{Noyoblik foizi} = \frac{\text{rarity\_permille}}{10}$$  
  *(Masalan: 25 permille = 2.5%, 500 permille = 50.0%)*.
- Mavjud "Buy-Now" sotuvlar soni.
- Modellar bo'yicha tarixiy narx o'zgarishlari.

### 🔔 3. Narx Signallari Dvigateli (Alert Engine)
Platforma 7 xil shartli signallarni qo'llab-quvvatlaydi:
1. `COLLECTION_FLOOR_ABOVE` — Kolleksiya floor narxi belgilangan chegaradan oshganda.
2. `COLLECTION_FLOOR_BELOW` — Kolleksiya floor narxi belgilangan chegaradan tushganda.
3. `COLLECTION_FLOOR_PCT_UP` — Kolleksiya floor narxi bir kunda belgilangan foizdan ko'p o'sganda.
4. `COLLECTION_FLOOR_PCT_DOWN` — Kolleksiya floor narxi bir kunda belgilangan foizdan ko'p tushganda.
5. `MODEL_FLOOR_ABOVE` — Muayyan model floor narxi belgilangan chegaradan oshganda (PRO/ELITE).
6. `MODEL_FLOOR_BELOW` — Muayyan model floor narxi belgilangan chegaradan tushganda (PRO/ELITE).
7. `MODEL_FLOOR_PCT_CHANGE` — Model floor narxi bir kunda har qanday tomonga belgilangan foizdan ko'p o'zgarganda.

- **Deduplikatsiya:** Idempotent `deduplication_key` yordamida ayni bir kunlik snapshot bir xil signalni bir necha bor yuborishi qat'iyan man etiladi.
- **Avtomatik Re-arm:** Takroriy (recurring) signallar uchun narx avval qarama-qarshi tomonga qaytishi va 24 soatlik kouldaun o'tishi tekshiriladi.

### 💼 4. Shaxsiy Portfel Tahlili (Portfolio Valuation)
- Shaxsan egalik qilinayotgan sovg'alarni qo'lda kiritish (kolleksiya, model, xarid narxi, miqdori).
- **Qat'iy Baholash Ierarxiyasi:**
  1. Agar model ko'rsatilgan bo'lsa va uning floor narxi mavjud bo'lsa — **Model Floor** asosida baholanadi.
  2. Agar model floor mavjud bo'lmasa — **Collection Floor Fallback** orqali baholanadi va foydalanuvchiga aniq ogohlantirish (warning) ko'rsatiladi.
- Sof amalga oshmagan foyda/zarar (Unrealized PnL) va PnL foizi.
- Kolleksiyalar bo'yicha aktivlar taqsimoti.

### 🧭 5. Bozor Radari (Market Radar) & Indeks (TGGI)
- So'nggi 24 soat va 7 kun davomida eng ko'p o'sgan va tushgan kolleksiyalar.
- Eng faol sotilayotgan likvid sovg'alar.
- **TGGI (TG Gifts Index):** Butun bozor kapitallashuvi va likvidligini aks ettiruvchi umumiy indeks dinamikasi, vaznlar taqsimoti va grafiklari.

### 💎 6. Obuna Tizimi va Monetizatsiya
- **FREE:** 3 ta signal, 5 ta kuzatuv kolleksiyasi, asosiy bozor tahlili.
- **PRO (19,900 so'm / 30 kun):** 30 ta signal, 50 ta kuzatuv kolleksiyasi, model-level signallar, to'liq bozor radari, CSV eksport, 09:00 kunlik hisobot.
- **ELITE (49,900 so'm / 30 kun):** 100 ta signal, 200 ta kuzatuv kolleksiyasi, ustuvor bildirishnomalar, barcha premium funksiyalar.
- **To'lov Oqimi:** Foydalanuvchi karta rekvizitlariga to'lov qilib, tranzaksiya ma'lumotlarini kiritadi. Telegram ID ruxsat ro'yxatidagi administratorlar `/admin` paneli orqali bitta tugma bilan tasdiqlaydi yoki rad etadi.

---

## 🛠 3. Texnologik Stek

- **Backend:** Python 3.12+, FastAPI, Aiogram 3.x, SQLAlchemy 2.0 (async), Pydantic Settings.
- **Frontend:** React 19, TypeScript, Vite, Telegram Mini Apps SDK, Recharts, Lucide Icons.
- **Ma'lumotlar bazasi va kesh:** PostgreSQL 16, Alembic migratsiyalari, Redis 7 (avtomatik In-Memory fallback bilan ta'minlangan).
- **Testlash va Sifat:** Pytest (42 ta unit va integratsiya testlari), TypeScript strict compiler.
- **Konteynerlashtirish:** Docker, Docker Compose (multi-stage build).

---

## 🚀 4. O'rnatish va Ishga Tushirish

### 4.1. Talablar
- Python 3.12 yoki undan yuqori
- Node.js 20+ va npm
- PostgreSQL 16 (yoki Docker)
- Telegram Bot Token ([@BotFather](https://t.me/BotFather) orqali olingan)

### 4.2. Loyihani Klounlash va Muhitni Sozlash
```powershell
# Repozitoriyaga o'ting
cd "C:\Users\acer\Desktop\CRYPTO BOT"

# Python virtual muhitini yarating va faollashtiring
python -m venv venv
.\venv\Scripts\Activate.ps1

# Python paketlarini o'rnating
pip install -r requirements.txt
```

### 4.3. Konfiguratsiya (.env)
Loyihaning ildiz papkasidagi `.env` faylini tekshiring yoki sozlang:
```env
BOT_TOKEN=8878962222:AAEVZE8waDu1uOyOzc-et4MQUAJVfxuPJQU
ADMIN_IDS=7832582270

DATABASE_URL=postgresql+asyncpg://giftpulse:giftpulse_password@localhost:5432/giftpulse
REDIS_URL=redis://localhost:6379/0

TG_GIFTS_BASE_URL=https://tggifts.com
TG_GIFTS_FLOORS_URL=https://tggifts.com/data/floors-daily.json
TG_GIFTS_MODELS_URL=https://tggifts.com/data/models-daily.json
TG_GIFTS_INDEX_URL=https://tggifts.com/data/index.json

MINI_APP_URL=https://your-domain-or-tunnel.loca.lt
JWT_SECRET=your_super_secure_jwt_secret_giftpulse_key_2026
DEFAULT_TIMEZONE=Asia/Tashkent
DEFAULT_LANGUAGE=uz

PRO_PLAN_PRICE=19900
ELITE_PLAN_PRICE=49900

PAYMENT_CARD_NUMBER=6262470041977708
PAYMENT_CARD_HOLDER=GiftPulse LLC
```

### 4.4. Frontend Mini App-ni Yig'ish (Vite Build)
```powershell
cd frontend
npm install
npm run build
cd ..
```
*Yig'ilgan statik fayllar `frontend/dist/` papkasida hosil bo'ladi va FastAPI orqali avtomatik xizmat ko'rsatiladi.*

### 4.5. Ma'lumotlar Bazasini Migratsiya Qilish va Boshlang'ich Rejalarni Kiritish
```powershell
# Alembic orqali jadvallarni yaratish
alembic upgrade head

# Boshlang'ich obuna rejalarini (FREE, PRO, ELITE) bazaga kiritish
python scripts/seed_data.py
```

### 4.6. Loyihani Ishga Tushirish

Barcha modullarni birgalikda ishga tushirish uchun:
```powershell
python -m app.main --all
```

Alohida jarayonlar sifatida ishga tushirish:
```powershell
# 1. FastAPI Web Server (Mini App API va statik fayllar)
python -m app.main --api

# 2. Telegram Bot (Aiogram 3.x)
python -m app.main --bot

# 3. Data Ingestion Worker & Kunlik Hisobotlar (Har 1 soatda tggifts.com yangilanishi)
python -m app.main --worker
```

---

## 🐳 5. Docker Compose Orqali Ishga Tushirish

Konteynerlashtirilgan ishlab chiqarish muhitida ishga tushirish:
```bash
docker compose up --build -d
```
Tizim avtomatik tarzda:
- PostgreSQL 16 va Redis 7 konteynerlarini ko'taradi.
- Migratsiya va seed skriptlarini ishga tushiradi.
- `giftpulse_api`, `giftpulse_bot` va `giftpulse_worker` konteynerlarini sog'liq tekshiruvi (healthcheck) orqali boshqaradi.

---

## 🤖 6. BotFather Sozlamalari

Telegramda qulay foydalanuvchi tajribasini ta'minlash uchun [@BotFather](https://t.me/BotFather) orqali quyidagilarni sozlang:

### Bot Buyruqlari (`/setcommands`):
```text
start - Botni ishga tushirish va asosiy menyu
market - Sovg'alar bozori va floor narxlari
models - Sovg'a modellari va noyoblik darajasi
alerts - Narx signallarini sozlash va ko'rish
portfolio - Shaxsiy sovg'alar portfeli
radar - Bozor radari (top o'sish va tushishlar)
index - TGGI bozor indeksi tahlili
subscription - Obuna tariflari (PRO va ELITE)
settings - Til va vaqt mintaqasi sozlamalari
help - Yordam va ma'lumotlar metodologiyasi
```

### Menu Button (`/setmenubutton`):
- Tugma matni: `🎁 GiftPulse`
- Web App URL: Sizning domen manzilingiz (masalan, `https://your-domain.com` yoki tunnel URL).

---
  
## 🧪 7. Testlar va Sifat Nazorati

Platforma to'liq avtomatlashtirilgan test to'plamiga ega:
```powershell
# Barcha backend testlarini ishga tushirish
.\venv\Scripts\pytest.exe -v
```
**Test qamrovi:**
- `test_alert_evaluator.py` — Barcha 7 ta signal turi, kouldaun, takroriy rejim va bir xil kunda qayta ishlamaslik kafolati (10 ta test).
- `test_gift_ingestion_parser.py` — TG Gifts Open Data formatlari va noyoblik permille (`permille / 10`) konvertatsiyasi (3 ta test).
- `test_portfolio_service.py` — Model floor ustuvorligi, collection floor fallback va ogohlantirishlar (2 ta test).
- `test_security.py` & `test_telegram_auth.py` — Telegram HMAC-SHA256 initData imzo tekshiruvi, JWT tokenlar va admin ruxsatlari (12 ta test).
- `test_subscriptions.py` — FREE/PRO/ELITE limitlari, to'lovni tasdiqlash va duplikatlarning oldini olish (4 ta test).
- `test_database_repos.py` — Watchlist, alert, portfolio va user omborlari (4 ta test).
- `test_api_v1.py` — Mini App API v1 barcha marshrutlarining to'liq integratsiya testlari (7 ta test).

**Natija: 42 ta test 100% muvaffaqiyatli o'tadi.**

---

## 📜 8. Attributsiya va Mualliflik Huquqi

- Sovg'alar bozorining ommaviy tahliliy ma'lumotlari [TG Gifts](https://tggifts.com) tomonidan taqdim etiladi va **CC BY 4.0** litsenziyasi ostida tarqatiladi.
- Ushbu dastur Telegram FZ-LLC yoki Fragment bilan rasmiy bog'lanmagan mustaqil tahlil vositasidir.
