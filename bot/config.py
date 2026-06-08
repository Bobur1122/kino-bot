"""
Kino Bot konfiguratsiya fayli.
Barcha sozlamalar .env yoki Render Environment Variables orqali o'rnatiladi.
"""
import os
from dotenv import load_dotenv

# .env faylni yuklash
load_dotenv()

# Bot Token — @BotFather dan oling
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Admin ID lar — vergul bilan ajratilgan Telegram ID lar
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "0").split(",")))

# Kanal sozlamalari — kinolar saqlanadigan kanal
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/your_channel")

# Mini App URL — Vercel URL
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://kinowebapp-nine.vercel.app")

# MongoDB Atlas
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/kinodb")

# Webhook URL — Render Web Service URL + /webhook
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# Server port
PORT = int(os.getenv("PORT", "10000"))
