# 🎬 KinoUz Premium Streaming Bot & Mini App (Netflix Style CRM)

Premium darajadagi Telegram Mini App va CRM boshqaruv tizimiga ega bo'lgan kino, serial va multfilmlar platformasi.

---

## ✨ Asosiy Imkoniyatlar

### 🤖 Telegram Bot (aiogram 3)
*   **🔒 Majburiy obuna tizimi (Dynamic):** Kanallarni dynamic boshqarish (Majburiy, Bildirishnoma, Maxfiy).
*   **🛠 Premium Admin Panel (`/panel`):**
    *   **📊 Rich Dashboard:** Server holati (CPU/RAM/Disk/Uptime), mashhur qidiruv so'zlari, haftalik aktiv foydalanuvchilar va ulangan kanallarning dynamic a'zolari statistikasi.
    *   **🎬 IMDb Auto-Fill Integratsiyasi:** Film nomini yoki IMDb ID (`ttXXXXXXX`) sini kiritish orqali poster, yil, janr, reyting, davomiylik, ishlab chiqarilgan davlat va tilni avtomatik scraping qilish/tuzish.
    *   **📈 Statistika soxtalashtirish (Fake Stats):** Admin tomonidan fake foydalanuvchilar va ko'rishlar sonini o'rnatish.
    *   **📢 Segmentlangan Broadcast:** Barcha yoki faqat aktiv foydalanuvchilarga rasmli, videoli va inline-tugmali reklama yuborish.
    *   **💾 Auto Backup:** SQLite bazasining zaxira nusxasini (.db formatda) adminga yuborish.
*   **📬 Avtomatik Listener:** Bot a'zo bo'lgan kanallarga video yuklanganda uni avtomatik bazaga yozib oladi (IMDb ma'lumotlarini dynamic scraping orqali to'ldiradi).

### 🎨 Netflix-Style Mini App (HTML5 + Vanilla CSS + JS)
*   **🎬 Featured Section:** Asosiy katta banner (eng ommabop yoki tavsiya etilgan film).
*   **🔥 Trenddagilar & Yangilar:** Ko'rishlar soni hamda yuklangan sanaga qarab saralangan horizontal scroll ro'yxati.
*   **❤️ Sevimlilar (Watchlist):** Sevimli kinolarni bir joyga saqlash va boshqarish.
*   **📜 Tomosha Tarixi (History):** Oxirgi ko'rilgan kontentlarni davomiyligi bilan eslab qolish.
*   **👍 Reyting Tizimi:** Kinolarga Like / Dislike (Interaktiv) berish.
*   **💡 Tavsiyalar:** Har bir kinoning ostida unga o'xshash janrdagi boshqa filmlarni ko'rsatish.

---

## 🚀 O'rnatish va Ishga Tushirish

### 1. Talablar
Tizim to'g'ri ishlashi uchun quyidagi kutubxonalar o'rnatilgan bo'lishi kerak:
```bash
pip install -r bot/requirements.txt
```

### 2. Sozlamalar (`bot/.env`)
Loyiha sozlamalarini to'ldiring:
```env
BOT_TOKEN=Sizning_Bot_Tokeningiz
ADMIN_IDS=Sizning_Telegram_IDingiz
DATABASE_PATH=kino_bot.db
PORT=8000
```

### 3. Local-da Ishga Tushirish
Barcha tizimni (ham FastAPI API serveri, ham Bot) bir vaqtda parallel ishga tushirish uchun:
```bash
cd bot
python run.py
```
*   **FastAPI API:** `http://127.0.0.1:8000`
*   **Bot:** Polling rejimida faol.

---

## 📂 Loyiha Tuzilishi

```text
├── bot/
│   ├── api/
│   │   └── routes.py         # FastAPI endpoints (Mini App uchun)
│   ├── handlers/
│   │   ├── admin.py          # CRM /panel boshqaruv logikasi
│   │   ├── start.py          # /start va obunani tekshirish
│   │   ├── search.py         # Bot orqali inline qidiruv
│   │   └── channel_post.py   # Kanaldagi kinolarni avto-saqlovchi listener
│   ├── keyboards/
│   │   └── inline.py         # Dynamic keyboardlar
│   ├── database.py           # SQLite3 bazasi bilan ishlash
│   ├── utils.py              # IMDb scraping, server monitoring, db backup
│   ├── run.py                # Parallel ishga tushirish scripti
│   └── main.py               # Bot webhook / polling entry point
└── webapp/                   # Netflix Style Mini App
    ├── css/
    │   └── style.css         # Premium qora Netflix dizayni
    ├── js/
    │   ├── api.js            # API requests wrapper (Local server detection bilan)
    │   └── app.js            # Mini App logikasi va interaktiv elementlar
    └── index.html            # Asosiy UI tuzilishi
```

---

## 🔒 Xavfsizlik va Kengaytirish
1.  **Faqat `/panel`:** Admin menyusi start xabaridan butunlay yashirilgan, faqat adminlar `/panel` buyrug'i yozganda ochiladi.
2.  **API CORS Sozlamalari:** Dynamic CORS orqali Mini App boshqa serverda turganda ham bemalol bot APIsi bilan ma'lumot almasha oladi.
