"""
Kino Bot tugmalari.
"""
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
)
from config import WEBAPP_URL


def _webapp_button():
    if WEBAPP_URL.startswith("https://"):
        return KeyboardButton(text="📱 Mini App", web_app=WebAppInfo(url=WEBAPP_URL))
    return KeyboardButton(text="📱 Mini App")


def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Kinolar"), KeyboardButton(text="📺 Seriallar")],
            [KeyboardButton(text="🎞 Multfilmlar"), KeyboardButton(text="🔍 Qidirish")],
            [KeyboardButton(text="🎲 Tasodifiy")],
            [_webapp_button()]
        ],
        resize_keyboard=True, is_persistent=True
    )


def kinolar_menu_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="🔥 Yangi kinolar", callback_data="cat_movies_new"),
            InlineKeyboardButton(text="⭐ Eng mashhurlar", callback_data="cat_movies_popular")
        ],
        [
            InlineKeyboardButton(text="🎭 Janr bo'yicha", callback_data="cat_movies_genre")
        ]
    ]
    if WEBAPP_URL.startswith("https://"):
        buttons.append([InlineKeyboardButton(text="📱 Mini Appda ochish", web_app=WebAppInfo(url=WEBAPP_URL))])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def seriallar_menu_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="🔥 Yangi seriallar", callback_data="cat_series_new"),
            InlineKeyboardButton(text="⭐ Top seriallar", callback_data="cat_series_popular")
        ],
        [
            InlineKeyboardButton(text="📂 Janrlar", callback_data="cat_series_genre")
        ]
    ]
    if WEBAPP_URL.startswith("https://"):
        buttons.append([InlineKeyboardButton(text="📱 Mini Appda ochish", web_app=WebAppInfo(url=WEBAPP_URL))])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def multfilmlar_menu_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="🧒 Bolalar uchun", callback_data="cat_cartoons_kids"),
            InlineKeyboardButton(text="🎌 Anime", callback_data="cat_cartoons_anime")
        ],
        [
            InlineKeyboardButton(text="⭐ Mashhur multfilmlar", callback_data="cat_cartoons_popular"),
            InlineKeyboardButton(text="😂 Komediya", callback_data="cat_cartoons_comedy")
        ]
    ]
    if WEBAPP_URL.startswith("https://"):
        buttons.append([InlineKeyboardButton(text="📱 Mini Appda ochish", web_app=WebAppInfo(url=WEBAPP_URL))])
    return InlineKeyboardMarkup(inline_keyboard=buttons)




def channel_subscribe_keyboard(channels: list):
    buttons = []
    for ch in channels:
        if not ch.get("is_hidden"):
            buttons.append([InlineKeyboardButton(
                text=f"📢 {ch.get('channel_name') or 'Kanal'}",
                url=ch["channel_url"]
            )])
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ===== ADMIN =====

def admin_panel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Dashboard", callback_data="admin_dashboard"),
            InlineKeyboardButton(text="🎬 Kontentlar", callback_data="admin_list_movies")
        ],
        [
            InlineKeyboardButton(text="➕ Kino qo'shish", callback_data="admin_add_movie"),
            InlineKeyboardButton(text="🔍 Qidirish", callback_data="admin_search")
        ],
        [
            InlineKeyboardButton(text="📢 Kanallar", callback_data="admin_channels"),
            InlineKeyboardButton(text="👥 Userlar", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="admin_add_admin"),
            InlineKeyboardButton(text="👮 Adminlar", callback_data="admin_list_admins")
        ],
        [
            InlineKeyboardButton(text="📣 Xabar yuborish", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="🏆 Top kinolar", callback_data="admin_top")
        ],
        [InlineKeyboardButton(text="❌ Yopish", callback_data="admin_close")]
    ])


def category_select_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 Kino", callback_data="cat_kino"),
            InlineKeyboardButton(text="📺 Serial", callback_data="cat_serial"),
            InlineKeyboardButton(text="🧸 Multfilm", callback_data="cat_multfilm")
        ],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_cancel")]
    ])


def skip_keyboard(field: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏩ Tashlab ketish", callback_data=f"skip_{field}")]
    ])


def confirm_movie_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm_add"),
            InlineKeyboardButton(text="❌ Bekor", callback_data="admin_cancel")
        ]
    ])


def movie_actions_keyboard(movie_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"edit_{movie_id}"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delete_{movie_id}")
        ],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_list_movies")]
    ])


def movie_list_keyboard(movies: list, page: int = 0, per_page: int = 5):
    start = page * per_page
    end = start + per_page
    page_movies = movies[start:end]
    total_pages = max(1, (len(movies) + per_page - 1) // per_page)
    buttons = []
    for m in page_movies:
        e = {"kino": "🎬", "serial": "📺", "multfilm": "🧸"}.get(m["category"], "🎬")
        buttons.append([InlineKeyboardButton(
            text=f"{e} {m['title']} ({m.get('year') or '?'}) · 👁{m['views']}",
            callback_data=f"movie_{m['id']}"
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"📄 {page+1}/{total_pages}", callback_data="noop"))
    if end < len(movies):
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page+1}"))
    buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="🔙 Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_delete_keyboard(movie_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_delete_{movie_id}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data=f"movie_{movie_id}")
        ]
    ])


def confirm_broadcast_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Yuborish", callback_data="confirm_broadcast"),
            InlineKeyboardButton(text="❌ Bekor", callback_data="admin_cancel")
        ]
    ])


def back_to_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Admin Panel", callback_data="admin_panel")]
    ])


def edit_field_keyboard(movie_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Nomi", callback_data=f"editf_title_{movie_id}"),
         InlineKeyboardButton(text="📄 Tavsif", callback_data=f"editf_desc_{movie_id}")],
        [InlineKeyboardButton(text="📂 Kategoriya", callback_data=f"editf_cat_{movie_id}"),
         InlineKeyboardButton(text="📅 Yil", callback_data=f"editf_year_{movie_id}")],
        [InlineKeyboardButton(text="🎭 Janr", callback_data=f"editf_genre_{movie_id}"),
         InlineKeyboardButton(text="⭐ Reyting", callback_data=f"editf_rating_{movie_id}")],
        [InlineKeyboardButton(text="⏱ Davomiylik", callback_data=f"editf_duration_{movie_id}"),
         InlineKeyboardButton(text="🌍 Davlat", callback_data=f"editf_country_{movie_id}")],
        [InlineKeyboardButton(text="🗣 Til/Dublyaj", callback_data=f"editf_dub_{movie_id}")],
        [InlineKeyboardButton(text="🖼 Poster", callback_data=f"editf_poster_{movie_id}"),
         InlineKeyboardButton(text="🎥 Video", callback_data=f"editf_video_{movie_id}")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"movie_{movie_id}")]
    ])


# ===== CHANNEL MANAGEMENT =====

def channels_keyboard(channels: list):
    buttons = []
    buttons.append([
        InlineKeyboardButton(text="🔒 Majburiy kanal qo'shish", callback_data="ch_add_mandatory"),
        InlineKeyboardButton(text="📢 Bildirishnoma qo'shish", callback_data="ch_add_notification")
    ])
    buttons.append([
        InlineKeyboardButton(text="🔒📢 Ikkalasi", callback_data="ch_add_both"),
        InlineKeyboardButton(text="🔐 Maxfiy kanal", callback_data="ch_add_hidden")
    ])
    for ch in channels:
        status = ""
        if ch["is_mandatory"]:
            status += "🔒"
        if ch["is_notification"]:
            status += "📢"
        if ch["is_hidden"]:
            status += "🔐"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {ch.get('channel_name') or ch['channel_id']}",
            callback_data=f"ch_view_{ch['channel_id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def channel_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔒 Majburiy obuna", callback_data="ch_kind_mandatory"),
            InlineKeyboardButton(text="📢 Bildirishnoma", callback_data="ch_kind_notification")
        ],
        [
            InlineKeyboardButton(text="🔒📢 Ikkalasi", callback_data="ch_kind_both"),
            InlineKeyboardButton(text="🔐 Maxfiy", callback_data="ch_kind_hidden")
        ],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_cancel")]
    ])


def channel_view_keyboard(channel_id: int, ch: dict):
    m_text = "🔒 Majburiy ✅" if ch["is_mandatory"] else "🔓 Majburiy ❌"
    n_text = "📢 Bildirish ✅" if ch["is_notification"] else "📢 Bildirish ❌"
    h_text = "🔐 Maxfiy ✅" if ch["is_hidden"] else "🔓 Maxfiy ❌"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=m_text, callback_data=f"ch_toggle_m_{channel_id}")],
        [InlineKeyboardButton(text=n_text, callback_data=f"ch_toggle_n_{channel_id}")],
        [InlineKeyboardButton(text=h_text, callback_data=f"ch_toggle_h_{channel_id}")],
        [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"ch_del_{channel_id}")],
        [InlineKeyboardButton(text="🔙 Kanallar", callback_data="admin_channels")]
    ])


def broadcast_target_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Barcha userlar", callback_data="bc_all")],
        [InlineKeyboardButton(text="📈 Faqat aktivlar (7 kun)", callback_data="bc_active")],
        [InlineKeyboardButton(text="❌ Bekor", callback_data="admin_cancel")]
    ])
