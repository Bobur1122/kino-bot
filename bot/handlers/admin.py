"""
Admin CRM — Premium admin panel.
"""
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os

import database as db
import utils
from config import ADMIN_IDS
from keyboards.inline import (
    admin_panel_keyboard, category_select_keyboard,
    skip_keyboard, confirm_movie_keyboard,
    movie_actions_keyboard, movie_list_keyboard,
    confirm_delete_keyboard, confirm_broadcast_keyboard,
    back_to_admin_keyboard, edit_field_keyboard,
    channels_keyboard, channel_type_keyboard, channel_view_keyboard,
    broadcast_target_keyboard
)

router = Router()


class AddMovie(StatesGroup):
    title = State()
    category = State()
    imdb_id = State() # IMDb search
    description = State()
    year = State()
    genre = State()
    rating = State()
    duration = State()
    country = State()
    language = State()
    dub_sub = State()
    trailer = State()
    poster = State()
    video = State()


class BroadcastState(StatesGroup):
    target = State()
    message = State()


class EditField(StatesGroup):
    waiting = State()


class ChannelAddState(StatesGroup):
    channel_id = State()
    kind = State()
    url = State()
    name = State()


class FakeStatsState(StatesGroup):
    users = State()
    views = State()


class AdminSearchState(StatesGroup):
    query = State()


class AdminAddState(StatesGroup):
    admin_id = State()


_BASE_ADMIN_IDS = {admin_id for admin_id in ADMIN_IDS if admin_id and admin_id > 0}


async def is_admin(user_id: int) -> bool:
    if user_id in _BASE_ADMIN_IDS:
        return True
    admin_ids = await db.get_admin_ids()
    return user_id in admin_ids


async def build_dashboard():
    """Premium dashboard text with server status, top searches and recent additions."""
    s = await db.get_stats()
    srv = utils.get_server_status()
    
    # Mashhur qidiruvlar
    popular = await db.get_popular_searches(5)
    pop_text = ""
    if popular:
        pop_text = "\n🔍 <b>Eng ko'p qidirilganlar:</b>\n"
        for i, p in enumerate(popular, 1):
            pop_text += f"  {i}. {p['query']} ({p['count']} marta)\n"
            
    # Oxirgi qo'shilgan 3ta kino
    recent = await db.get_recent_movies(3)
    rec_text = "\n🆕 <b>Oxirgi qo'shilganlar:</b>\n"
    for r in recent:
        rec_text += f"  • {r['title']} ({r.get('year') or '?'})\n"

    # Server holati formatlash
    uptime_h = srv['uptime'] // 3600
    uptime_m = (srv['uptime'] % 3600) // 60
    
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "     ⚙️ <b>ADMIN PREMIUM CRM</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📊 <b>Dashboard ko'rsatkichlari:</b>\n"
        f"  👥 Foydalanuvchilar: <b>{s['users']}</b> (Real: {s['users'] - s['fake_users']}, Fake: {s['fake_users']})\n"
        f"  📈 Bugun qo'shilganlar: <b>{s['today_users']}</b>\n"
        f"  🔥 Haftalik aktivlar: <b>{s['weekly_active']}</b>\n"
        f"  📦 Jami kontent: <b>{s['movies']}</b>\n"
        f"     ├ 🎬 Kinolar: {s['kino']} | 📺 Seriallar: {s['serial']} | 🧸 Multfilmlar: {s['multfilm']}\n"
        f"  👁 Jami ko'rishlar: <b>{s['views']}</b> (Real: {s['views'] - s['fake_views']}, Fake: {s['fake_views']})\n"
        f"  📢 Ulangan kanallar: <b>{s['channels']}</b>\n"
        f"{pop_text}"
        f"{rec_text}\n"
        "🖥 <b>Server va xotira holati:</b>\n"
        f"  ⚡️ CPU Bandlik: <b>{srv['cpu']}%</b>\n"
        f"  🧠 RAM: <b>{srv['ram_used']} GB</b> / {srv['ram_total']} GB ({srv['ram_percent']}%)\n"
        f"  💾 Disk: <b>{srv['disk_used']} GB</b> / {srv['disk_total']} GB ({srv['disk_percent']}%)\n"
        f"  ⏳ Uptime: <b>{uptime_h}s {uptime_m}d</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛠 <b>Boshqarish menyusi:</b>"
    )
    return text


@router.message(Command("panel"))
async def admin_panel_cmd(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Kechirasiz, siz bot administratori emassiz!")
        return
    await state.clear()
    await message.answer(
        await build_dashboard(),
        reply_markup=admin_panel_keyboard(), parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_panel")
async def admin_panel_cb(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text(
        await build_dashboard(),
        reply_markup=admin_panel_keyboard(), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_dashboard")
async def admin_dashboard_cb(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        await build_dashboard(),
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_users")
async def admin_users_cb(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    users = await db.get_all_users()
    today = await db.get_today_users()
    active = await db.get_weekly_active()
    sample = users[:10]
    text = (
        "👥 <b>Userlar bo'limi</b>\n\n"
        f"Jami userlar: <b>{len(users)}</b>\n"
        f"Bugun qo'shilganlar: <b>{today}</b>\n"
        f"Haftalik aktivlar: <b>{active}</b>\n\n"
        "<b>So'nggi userlar:</b>\n"
    )
    if sample:
        for u in sample:
            name = u.get("full_name") or u.get("username") or str(u["telegram_id"])
            text += f"• {name} <code>{u['telegram_id']}</code>\n"
    else:
        text += "• Hozircha userlar yo'q.\n"
    try:
        await callback.message.edit_text(text, reply_markup=back_to_admin_keyboard(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=back_to_admin_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_add_admin")
async def admin_add_admin_start(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await state.set_state(AdminAddState.admin_id)
    await callback.message.edit_text(
        "➕ <b>Yangi admin qo'shish</b>\n\n"
        "Telegram ID ni kiriting:",
        reply_markup=back_to_admin_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminAddState.admin_id)
async def admin_add_admin_save(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    try:
        new_admin_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Faqat raqamli Telegram ID kiriting!")
        return
    if new_admin_id <= 0:
        await message.answer("❌ Noto'g'ri Telegram ID!")
        return
    if new_admin_id in _BASE_ADMIN_IDS:
        await state.clear()
        await message.answer("ℹ️ Bu ID allaqachon asosiy adminlar ichida bor.", reply_markup=back_to_admin_keyboard())
        return
    await db.add_admin(new_admin_id, added_by=message.from_user.id)
    await state.clear()
    await message.answer(
        f"✅ Admin qo'shildi: <code>{new_admin_id}</code>",
        reply_markup=back_to_admin_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_list_admins")
async def admin_list_admins(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    admins = await db.get_admins()
    text = "👮 <b>Adminlar ro'yxati</b>\n\n"
    if not admins and not _BASE_ADMIN_IDS:
        text += "• Hozircha admin yo'q.\n"
    else:
        shown = set()
        for admin_id in sorted(_BASE_ADMIN_IDS):
            text += f"• <code>{admin_id}</code> — asosiy admin\n"
            shown.add(admin_id)
        for admin in admins:
            aid = admin["telegram_id"]
            if aid in shown:
                continue
            text += f"• <code>{aid}</code> — qo'shilgan admin\n"
    await callback.message.edit_text(
        text,
        reply_markup=back_to_admin_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_close")
async def admin_close(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()


@router.callback_query(F.data == "admin_cancel")
async def admin_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Amallar bekor qilindi.",
        reply_markup=back_to_admin_keyboard(), parse_mode="HTML"
    )
    await callback.answer()


# ===== ADD MOVIE WITH IMDB SUPPORT =====

@router.callback_query(F.data == "admin_add_movie")
async def add_movie_start(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await state.set_state(AddMovie.title)
    await callback.message.edit_text(
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "     🎬 <b>YANGI KINO QO'SHISH</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 Film / Serial nomini yozing:",
        parse_mode="HTML"
    )


@router.message(AddMovie.title)
async def add_movie_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddMovie.category)
    await message.answer(
        "📂 Kategoriyani tanlang:",
        reply_markup=category_select_keyboard(), parse_mode="HTML"
    )


@router.callback_query(AddMovie.category, F.data.startswith("cat_"))
async def add_movie_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.replace("cat_", "")
    await state.update_data(category=category)
    await state.set_state(AddMovie.imdb_id)
    await callback.message.edit_text(
        "ℹ️ <b>IMDb Integratsiyasi</b>\n\n"
        "Agar film IMDb ma'lumotlarini avtomatik yuklamoqchi bo'lsangiz:\n"
        "filmning <b>IMDb ID</b>sini yozing (masalan: <code>tt0111161</code>)\n"
        "yoki qidirish uchun film nomini yozing.\n\n"
        "<i>Tashlab ketish tugmasini bossangiz, ma'lumotlarni qo'lda kiritasiz.</i>",
        reply_markup=skip_keyboard("imdb"), parse_mode="HTML"
    )


@router.message(AddMovie.imdb_id)
async def add_movie_imdb(message: Message, state: FSMContext):
    query = message.text.strip()
    await message.answer("🔍 IMDb ma'lumotlari qidirilmoqda, iltimos kuting...")
    
    imdb_data = await utils.fetch_imdb_data(query)
    if imdb_data["title"]:
        # Ma'lumotlarni saqlaymiz
        await state.update_data(
            title=imdb_data["title"],
            description=imdb_data["description"],
            year=imdb_data["year"],
            genre=imdb_data["genre"],
            rating=imdb_data["rating"],
            duration=imdb_data["duration"],
            country=imdb_data["country"],
            language=imdb_data["language"],
            poster_url=imdb_data["poster_url"]
        )
        # Sarlavha yangilandi
        await message.answer(
            f"✅ Film topildi: <b>{imdb_data['title']} ({imdb_data['year']})</b>\n"
            f"⭐ Reyting: {imdb_data['rating']}\n"
            f"🎭 Janr: {imdb_data['genre']}\n"
            f"🌎 Davlat: {imdb_data['country']}\n\n"
            "Endi dublyaj / subtitr turini yozing:",
            reply_markup=skip_keyboard("dub_sub"), parse_mode="HTML"
        )
        await state.set_state(AddMovie.dub_sub)
    else:
        await message.answer(
            "❌ IMDb dan hech narsa topilmadi. Tafsifni o'zingiz yozing:",
            reply_markup=skip_keyboard("description"), parse_mode="HTML"
        )
        await state.set_state(AddMovie.description)


@router.callback_query(F.data == "skip_imdb")
async def skip_imdb(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddMovie.description)
    await callback.message.edit_text(
        "📄 Film tavsifini yozing:",
        reply_markup=skip_keyboard("description"), parse_mode="HTML"
    )


@router.message(AddMovie.description)
async def add_movie_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddMovie.year)
    await message.answer("📅 Film yilini kiriting (masalan: 2024):", reply_markup=skip_keyboard("year"))


@router.callback_query(F.data == "skip_description")
async def skip_desc(callback: CallbackQuery, state: FSMContext):
    await state.update_data(description="")
    await state.set_state(AddMovie.year)
    await callback.message.edit_text("📅 Film yilini kiriting (masalan: 2024):", reply_markup=skip_keyboard("year"))


@router.message(AddMovie.year)
async def add_movie_year(message: Message, state: FSMContext):
    try:
        y = int(message.text)
    except ValueError:
        y = 0
    await state.update_data(year=y)
    await state.set_state(AddMovie.genre)
    await message.answer("🎭 Film janrini yozing (masalan: Jangari, Komediya):", reply_markup=skip_keyboard("genre"))


@router.callback_query(F.data == "skip_year")
async def skip_year(callback: CallbackQuery, state: FSMContext):
    await state.update_data(year=0)
    await state.set_state(AddMovie.genre)
    await callback.message.edit_text("🎭 Film janrini yozing:", reply_markup=skip_keyboard("genre"))


@router.message(AddMovie.genre)
async def add_movie_genre(message: Message, state: FSMContext):
    await state.update_data(genre=message.text)
    await state.set_state(AddMovie.rating)
    await message.answer("⭐ IMDb reytingini kiriting (masalan: 8.5):", reply_markup=skip_keyboard("rating"))


@router.callback_query(F.data == "skip_genre")
async def skip_genre(callback: CallbackQuery, state: FSMContext):
    await state.update_data(genre="")
    await state.set_state(AddMovie.rating)
    await callback.message.edit_text("⭐ IMDb reytingini kiriting:", reply_markup=skip_keyboard("rating"))


@router.message(AddMovie.rating)
async def add_movie_rating(message: Message, state: FSMContext):
    try:
        r = float(message.text)
    except ValueError:
        r = 0.0
    await state.update_data(rating=r)
    await state.set_state(AddMovie.duration)
    await message.answer("⏱ Davomiyligini yozing (masalan: 2 soat 10 daqiqa):", reply_markup=skip_keyboard("duration"))


@router.callback_query(F.data == "skip_rating")
async def skip_rating(callback: CallbackQuery, state: FSMContext):
    await state.update_data(rating=0.0)
    await state.set_state(AddMovie.duration)
    await callback.message.edit_text("⏱ Davomiyligini yozing:", reply_markup=skip_keyboard("duration"))


@router.message(AddMovie.duration)
async def add_movie_duration(message: Message, state: FSMContext):
    await state.update_data(duration=message.text)
    await state.set_state(AddMovie.country)
    await message.answer("🌎 Ishlab chiqarilgan davlatni yozing:", reply_markup=skip_keyboard("country"))


@router.callback_query(F.data == "skip_duration")
async def skip_duration(callback: CallbackQuery, state: FSMContext):
    await state.update_data(duration="")
    await state.set_state(AddMovie.country)
    await callback.message.edit_text("🌎 Ishlab chiqarilgan davlatni yozing:", reply_markup=skip_keyboard("country"))


@router.message(AddMovie.country)
async def add_movie_country(message: Message, state: FSMContext):
    await state.update_data(country=message.text)
    await state.set_state(AddMovie.language)
    await message.answer("🗣 Film tilini yozing (masalan: O'zbekcha):", reply_markup=skip_keyboard("language"))


@router.callback_query(F.data == "skip_country")
async def skip_country(callback: CallbackQuery, state: FSMContext):
    await state.update_data(country="")
    await state.set_state(AddMovie.language)
    await callback.message.edit_text("🗣 Film tilini yozing:", reply_markup=skip_keyboard("language"))


@router.message(AddMovie.language)
async def add_movie_language(message: Message, state: FSMContext):
    await state.update_data(language=message.text)
    await state.set_state(AddMovie.dub_sub)
    await message.answer("🎙 Dublyaj / Subtitr turini yozing (masalan: Professional):", reply_markup=skip_keyboard("dub_sub"))


@router.callback_query(F.data == "skip_language")
async def skip_language(callback: CallbackQuery, state: FSMContext):
    await state.update_data(language="")
    await state.set_state(AddMovie.dub_sub)
    await callback.message.edit_text("🎙 Dublyaj / Subtitr turini yozing:", reply_markup=skip_keyboard("dub_sub"))


@router.message(AddMovie.dub_sub)
async def add_movie_dub(message: Message, state: FSMContext):
    await state.update_data(dub_sub=message.text)
    await state.set_state(AddMovie.trailer)
    await message.answer("🎥 Film treyler havolasini yozing (YouTube/Telegram link):", reply_markup=skip_keyboard("trailer"))


@router.callback_query(F.data == "skip_dub_sub")
async def skip_dub(callback: CallbackQuery, state: FSMContext):
    await state.update_data(dub_sub="")
    await state.set_state(AddMovie.trailer)
    await callback.message.edit_text("🎥 Film treyler havolasini yozing:", reply_markup=skip_keyboard("trailer"))


@router.message(AddMovie.trailer)
async def add_movie_trailer(message: Message, state: FSMContext):
    await state.update_data(trailer=message.text)
    await state.set_state(AddMovie.poster)
    await message.answer("🖼 Poster rasmini yuboring (fayl sifatida emas, rasm ko'rinishida):", reply_markup=skip_keyboard("poster"))


@router.callback_query(F.data == "skip_trailer")
async def skip_trailer(callback: CallbackQuery, state: FSMContext):
    await state.update_data(trailer="")
    await state.set_state(AddMovie.poster)
    await callback.message.edit_text("🖼 Poster rasmini yuboring:", reply_markup=skip_keyboard("poster"))


@router.message(AddMovie.poster, F.photo)
async def add_movie_poster_file(message: Message, state: FSMContext):
    await state.update_data(poster_file_id=message.photo[-1].file_id)
    await state.set_state(AddMovie.video)
    await message.answer("🎥 Endi kino video faylini yuboring:")


@router.callback_query(F.data == "skip_poster")
async def skip_poster_file(callback: CallbackQuery, state: FSMContext):
    # Agar IMDb orqali yuklangan bo'lsa poster_url bor
    data = await state.get_data()
    if data.get("poster_url"):
        # Kelajakda front-endda render qilish uchun yoki yuklab olish uchun saqlanadi
        await state.update_data(poster_file_id="")
    else:
        await state.update_data(poster_file_id="")
    await state.set_state(AddMovie.video)
    await callback.message.edit_text("🎥 Endi kino video faylini yuboring:")


@router.message(AddMovie.video, F.video)
async def add_movie_video(message: Message, state: FSMContext):
    await state.update_data(video_file_id=message.video.file_id)
    data = await state.get_data()
    
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "     ✅ KINO MA'LUMOTLARI\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 Nomi: <b>{data['title']}</b>\n"
        f"📂 Kategoriya: {data['category'].upper()}\n"
        f"📅 Yili: {data.get('year') or '—'} | ⭐ IMDb: {data.get('rating') or '—'}\n"
        f"🎭 Janr: {data.get('genre') or '—'}\n"
        f"🌎 Davlat: {data.get('country') or '—'} | Til: {data.get('language') or '—'}\n"
        f"🎙 Dublyaj: {data.get('dub_sub') or '—'}\n"
        f"⏱ Davomiyligi: {data.get('duration') or '—'}\n"
        f"🔗 Treyler: {data.get('trailer') or '—'}\n"
        f"🖼 Poster: {'✅ Rasm' if data.get('poster_file_id') or data.get('poster_url') else '❌'}\n"
        f"🎥 Video: ✅\n\n"
        "Ushbu kinoni ma'lumotlar bazasiga qo'shishni tasdiqlaysizmi?"
    )
    await message.answer(text, reply_markup=confirm_movie_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "confirm_add")
async def confirm_add_movie_save(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    
    movie_id = await db.add_movie(
        title=data['title'],
        video_file_id=data['video_file_id'],
        category=data['category'],
        description=data.get('description', ''),
        poster_file_id=data.get('poster_file_id', ''),
        trailer=data.get('trailer', ''),
        year=data.get('year', 0),
        genre=data.get('genre', ''),
        rating=data.get('rating', 0.0),
        duration=data.get('duration', ''),
        country=data.get('country', ''),
        language=data.get('language', ''),
        dub_sub=data.get('dub_sub', '')
    )
    
    # Avtomatik bildirishnoma kanali (bazadan notification kanallarini olamiz)
    notif_channels = await db.get_notification_channels()
    caption = (
        f"🆕 <b>YANGI YUKLANGAN KONTENT!</b>\n\n"
        f"🍿 <b>{data['title']}</b>\n"
        f"📂 Kategoriya: #{data['category']}\n"
        f"📅 Yili: {data.get('year') or '—'}\n"
        f"⭐ Reyting: {data.get('rating') or '—'}\n"
        f"🎭 Janri: {data.get('genre') or '—'}\n"
        f"🗣 Tili: {data.get('language') or '—'} ({data.get('dub_sub') or 'Asl til'})\n"
        f"⏱ Davomiyligi: {data.get('duration') or '—'}\n\n"
        f"🤖 Boshlash uchun botimizga kiring: @{callback.bot._me.username}"
    )
    
    for ch in notif_channels:
        try:
            if data.get("poster_file_id"):
                await callback.bot.send_photo(ch["channel_id"], data["poster_file_id"], caption=caption, parse_mode="HTML")
            else:
                await callback.bot.send_message(ch["channel_id"], caption, parse_mode="HTML")
        except Exception:
            pass
            
    await callback.message.edit_text(
        f"✅ <b>Kino muvaffaqiyatli saqlandi!</b>\n🆔 ID: <code>{movie_id}</code>\n"
        f"📢 Yangiliklar kanaliga bildirishnomalar yuborildi (agar mavjud bo'lsa).",
        reply_markup=back_to_admin_keyboard(), parse_mode="HTML"
    )


# ===== KINO QIDIRISH VA FILTRLASH =====

@router.callback_query(F.data == "admin_search")
async def admin_search_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminSearchState.query)
    await callback.message.edit_text(
        "🔍 <b>FILTR VA QIDIRUV</b>\n\n"
        "Nom yoki janr yozib yuboring (yoki ID bo'yicha topish uchun shunchaki ID yozing):",
        reply_markup=back_to_admin_keyboard(), parse_mode="HTML"
    )


@router.message(AdminSearchState.query)
async def admin_search_result(message: Message, state: FSMContext):
    query = message.text.strip()
    await state.clear()
    
    # ID bo'yicha qidiruv
    if query.isdigit():
        movie = await db.get_movie(int(query))
        results = [movie] if movie else []
    else:
        results = await db.search_movies(query)
        
    if not results:
        await message.answer("❌ Hech qanday ma'lumot topilmadi.", reply_markup=back_to_admin_keyboard())
        return
        
    await message.answer(
        f"🔍 Qidiruv natijalari (jami: {len(results)} ta):",
        reply_markup=movie_list_keyboard(results, 0), parse_mode="HTML"
    )


# ===== LIST MOVIES =====

@router.callback_query(F.data == "admin_list_movies")
async def list_movies(callback: CallbackQuery):
    movies = await db.get_movies(limit=100)
    if not movies:
        await callback.message.edit_text("📋 Bazada kinolar mavjud emas.", reply_markup=back_to_admin_keyboard())
        return
    await callback.message.edit_text(
        "📋 <b>Jami kinolar:</b>",
        reply_markup=movie_list_keyboard(movies, 0), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("page_"))
async def page_movies(callback: CallbackQuery):
    page = int(callback.data.split("_")[1])
    movies = await db.get_movies(limit=100)
    await callback.message.edit_reply_markup(reply_markup=movie_list_keyboard(movies, page))


@router.callback_query(F.data.startswith("movie_"))
async def show_movie(callback: CallbackQuery):
    movie_id = int(callback.data.split("_")[1])
    movie = await db.get_movie(movie_id)
    if not movie:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return
    text = (
        f"🎬 <b>{movie['title']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{movie['id']}</code>\n"
        f"📂 Kategoriya: {movie['category'].upper()}\n"
        f"📅 Yil: {movie.get('year') or '—'} | ⭐ Reyting: {movie.get('rating') or '—'}\n"
        f"🎭 Janr: {movie.get('genre') or '—'}\n"
        f"⏱ Davomiyligi: {movie.get('duration') or '—'}\n"
        f"🗣 Dublyaj: {movie.get('dub_sub') or '—'}\n"
        f"👁 Ko'rishlar: <b>{movie['views']}</b>\n"
        f"🔗 Treyler: {movie.get('trailer') or '—'}"
    )
    await callback.message.delete()
    if movie.get("poster_file_id"):
        await callback.message.answer_photo(
            movie["poster_file_id"], caption=text,
            reply_markup=movie_actions_keyboard(movie_id), parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            text, reply_markup=movie_actions_keyboard(movie_id), parse_mode="HTML"
        )


# ===== EDIT / DELETE =====

@router.callback_query(F.data.startswith("edit_"))
async def edit_movie_fields(callback: CallbackQuery):
    movie_id = int(callback.data.split("_")[1])
    await callback.message.delete()
    await callback.message.answer(
        "📝 O'zgartirmoqchi bo'lgan maydonni tanlang:",
        reply_markup=edit_field_keyboard(movie_id)
    )


@router.callback_query(F.data.startswith("editf_"))
async def edit_field_waiting(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    field = parts[1]
    movie_id = int(parts[2])
    
    await state.set_state(EditField.waiting)
    await state.update_data(edit_field=field, edit_movie_id=movie_id)
    
    prompts = {
        "title": "Nomini kiriting:",
        "desc": "Tavsifini kiriting:",
        "cat": "Kategoriyani tanlang:",
        "year": "Yilini kiriting:",
        "genre": "Janrini kiriting:",
        "rating": "IMDb reytingini kiriting:",
        "duration": "Davomiyligini kiriting:",
        "country": "Davlatini kiriting:",
        "language": "Tilini kiriting:",
        "dub": "Dublyaj/Subtitr turini kiriting:",
        "poster": "Yangi poster rasmini yuboring:",
        "video": "Yangi video faylini yuboring:"
    }
    
    if field == "cat":
        await callback.message.edit_text(prompts[field], reply_markup=category_select_keyboard())
    else:
        await callback.message.edit_text(prompts.get(field, "Qiymat kiriting:"))


@router.callback_query(EditField.waiting, F.data.startswith("cat_"))
async def edit_field_save_cat(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await db.update_movie(data["edit_movie_id"], category=callback.data.replace("cat_", ""))
    await state.clear()
    await callback.message.edit_text("✅ Kategoriya yangilandi!", reply_markup=back_to_admin_keyboard())


@router.message(EditField.waiting)
async def edit_field_save_text(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data["edit_field"]
    movie_id = data["edit_movie_id"]
    
    val = message.text
    
    mapping = {
        "title": "title", "desc": "description", "year": "year", "genre": "genre",
        "rating": "rating", "duration": "duration", "country": "country",
        "language": "language", "dub": "dub_sub"
    }
    
    db_col = mapping.get(field)
    if not db_col:
        # Photo / Video checks
        if message.photo and field == "poster":
            await db.update_movie(movie_id, poster_file_id=message.photo[-1].file_id)
        elif message.video and field == "video":
            await db.update_movie(movie_id, video_file_id=message.video.file_id)
        else:
            await message.answer("❌ Mos fayl yuborilmadi!")
            return
    else:
        if db_col == "year":
            val = int(val) if val.isdigit() else 0
        elif db_col == "rating":
            try: val = float(val)
            except ValueError: val = 0.0
        await db.update_movie(movie_id, **{db_col: val})
        
    await state.clear()
    await message.answer("✅ Muvaffaqiyatli yangilandi!", reply_markup=back_to_admin_keyboard())


@router.callback_query(F.data.startswith("delete_"))
async def ask_delete(callback: CallbackQuery):
    movie_id = int(callback.data.split("_")[1])
    await callback.message.edit_reply_markup(reply_markup=confirm_delete_keyboard(movie_id))


@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_save(callback: CallbackQuery):
    movie_id = int(callback.data.replace("confirm_delete_", ""))
    await db.delete_movie(movie_id)
    await callback.message.edit_text("🗑 Kino butunlay o'chirildi!", reply_markup=back_to_admin_keyboard())


# ===== STATS FAKING =====

@router.callback_query(F.data == "admin_stats")
async def show_stats_edit(callback: CallbackQuery, state: FSMContext):
    s = await db.get_stats()
    await state.set_state(FakeStatsState.users)
    await callback.message.edit_text(
        "📊 <b>Statistikani soxtalashtirish / o'zgartirish</b>\n\n"
        f"Hozirgi soxta foydalanuvchilar: <b>{s['fake_users']}</b>\n"
        f"Hozirgi soxta ko'rishlar: <b>{s['fake_views']}</b>\n\n"
        "👥 Yangi soxta foydalanuvchilar sonini kiriting (0 - o'chirish):",
        reply_markup=back_to_admin_keyboard(), parse_mode="HTML"
    )


@router.message(FakeStatsState.users)
async def fake_users_save(message: Message, state: FSMContext):
    try:
        users = int(message.text)
    except ValueError:
        await message.answer("Raqam kiriting!")
        return
    await state.update_data(fake_users=users)
    await state.set_state(FakeStatsState.views)
    await message.answer("👁 Yangi soxta ko'rishlar sonini kiriting:")


@router.message(FakeStatsState.views)
async def fake_views_save(message: Message, state: FSMContext):
    try:
        views = int(message.text)
    except ValueError:
        await message.answer("Raqam kiriting!")
        return
    data = await state.get_data()
    await state.clear()
    
    await db.update_fake_stats(data["fake_users"], views)
    await message.answer("✅ Statistika o'zgartirildi!", reply_markup=back_to_admin_keyboard())


# ===== CHANNELS MANAGEMENT =====

@router.callback_query(F.data == "admin_channels")
async def list_channels(callback: CallbackQuery):
    channels = await db.get_channels()
    mandatory_cnt = sum(1 for ch in channels if ch["is_mandatory"])
    notification_cnt = sum(1 for ch in channels if ch["is_notification"])
    hidden_cnt = sum(1 for ch in channels if ch["is_hidden"])
    await callback.message.edit_text(
        "🔒 <b>Kanallar boshqaruvi (Majburiy obuna va bildirishnomalar)</b>\n\n"
        f"Majburiy: <b>{mandatory_cnt}</b> | Bildirishnoma: <b>{notification_cnt}</b> | Maxfiy: <b>{hidden_cnt}</b>\n\n"
        "Mavjud kanallar ro'yxati:",
        reply_markup=channels_keyboard(channels), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ch_add"))
async def add_channel_start(callback: CallbackQuery, state: FSMContext):
    add_kind = "mandatory"
    if callback.data == "ch_add_notification":
        add_kind = "notification"
    elif callback.data == "ch_add_both":
        add_kind = "both"
    elif callback.data == "ch_add_hidden":
        add_kind = "hidden"
    await state.set_state(ChannelAddState.channel_id)
    await state.update_data(
        mandatory=add_kind in ("mandatory", "both"),
        notification=add_kind in ("notification", "both"),
        hidden=add_kind == "hidden",
    )
    kind_text = {
        "mandatory": "majburiy obuna",
        "notification": "bildirishnoma",
        "both": "majburiy obuna + bildirishnoma",
        "hidden": "maxfiy"
    }.get(add_kind, "oddiy")
    await callback.message.edit_text(
        f"📢 <b>{kind_text}</b> uchun kanal ID-sini kiriting (masalan: -1001234567890):",
        parse_mode="HTML",
        reply_markup=back_to_admin_keyboard()
    )
    await callback.answer()


@router.message(ChannelAddState.channel_id)
async def add_channel_id(message: Message, state: FSMContext):
    try:
        cid = int(message.text)
    except ValueError:
        await message.answer("Faqat raqamli ID kiriting!")
        return
    await state.update_data(channel_id=cid)
    await state.set_state(ChannelAddState.url)
    data = await state.get_data()
    type_text = []
    if data.get("mandatory"):
        type_text.append("majburiy")
    if data.get("notification"):
        type_text.append("bildirishnoma")
    if data.get("hidden"):
        type_text.append("maxfiy")
    type_text = ", ".join(type_text) if type_text else "oddiy"
    await message.answer(
        f"Tanlangan tur: <b>{type_text}</b>\n\n🔗 Kanal havolasini kiriting (https://t.me/kanal):",
        parse_mode="HTML"
    )


@router.message(ChannelAddState.url)
async def add_channel_url(message: Message, state: FSMContext):
    url = message.text.strip()
    await state.update_data(url=url)
    await state.set_state(ChannelAddState.name)
    await message.answer("📝 Kanal nomini kiriting (masalan: Premyeralar):")


@router.message(ChannelAddState.name)
async def add_channel_name(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    
    await db.add_channel(
        channel_id=data["channel_id"],
        url=data["url"],
        name=message.text.strip(),
        mandatory=data.get("mandatory", False),
        notification=data.get("notification", False),
        hidden=data.get("hidden", False)
    )
    await message.answer("✅ Kanal muvaffaqiyatli qo'shildi!", reply_markup=back_to_admin_keyboard())


@router.callback_query(F.data.startswith("ch_view_"))
async def view_channel(callback: CallbackQuery):
    cid = int(callback.data.split("_")[2])
    channels = await db.get_channels()
    ch = next((c for c in channels if c["channel_id"] == cid), None)
    if not ch:
        return
        
    await callback.message.edit_text(
        f"📢 <b>Kanal: {ch['channel_name']}</b>\n"
        f"🆔 ID: <code>{ch['channel_id']}</code>\n"
        f"🔗 Havola: {ch['channel_url']}\n\n"
        "Sozlamalarni o'zgartirish:",
        reply_markup=channel_view_keyboard(cid, ch), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("ch_toggle_"))
async def toggle_channel_setting(callback: CallbackQuery):
    parts = callback.data.split("_")
    action = parts[2] # m, n, h
    cid = int(parts[3])
    
    channels = await db.get_channels()
    ch = next((c for c in channels if c["channel_id"] == cid), None)
    if not ch:
        return
        
    if action == "m":
        await db.add_channel(cid, ch["channel_url"], ch["channel_name"], not ch["is_mandatory"], ch["is_notification"], ch["is_hidden"])
    elif action == "n":
        await db.add_channel(cid, ch["channel_url"], ch["channel_name"], ch["is_mandatory"], not ch["is_notification"], ch["is_hidden"])
    elif action == "h":
        await db.add_channel(cid, ch["channel_url"], ch["channel_name"], ch["is_mandatory"], ch["is_notification"], not ch["is_hidden"])
        
    # Refresh view
    channels = await db.get_channels()
    ch = next((c for c in channels if c["channel_id"] == cid), None)
    await callback.message.edit_reply_markup(reply_markup=channel_view_keyboard(cid, ch))


@router.callback_query(F.data.startswith("ch_del_"))
async def delete_channel(callback: CallbackQuery):
    cid = int(callback.data.split("_")[2])
    await db.remove_channel(cid)
    await callback.message.edit_text("🗑 Kanal olib tashlandi!", reply_markup=back_to_admin_keyboard())


# ===== BROADCAST TARGET AND EXECUTION =====

@router.callback_query(F.data == "admin_broadcast")
async def broadcast_target(callback: CallbackQuery):
    await callback.message.edit_text(
        "📣 <b>Xabar yuborish bo'limi</b>\n\n"
        "Kimlarga yubormoqchisiz?",
        reply_markup=broadcast_target_keyboard(), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("bc_"))
async def broadcast_target_selected(callback: CallbackQuery, state: FSMContext):
    target = callback.data.replace("bc_", "")
    await state.update_data(target=target)
    await state.set_state(BroadcastState.message)
    await callback.message.edit_text(
        "📝 Yubormoqchi bo'lgan xabaringizni yozing (matn, rasm yoki video):\n"
        "<i>Tugmali reklama uchun sarlavha tagidan inline formatda yozishingiz mumkin.</i>",
        reply_markup=back_to_admin_keyboard()
    )


@router.message(BroadcastState.message)
async def broadcast_msg_receive(message: Message, state: FSMContext):
    msg_data = {"type": "text", "text": message.text or ""}
    if message.photo:
        msg_data = {"type": "photo", "file_id": message.photo[-1].file_id, "caption": message.caption or ""}
    elif message.video:
        msg_data = {"type": "video", "file_id": message.video.file_id, "caption": message.caption or ""}
        
    await state.update_data(broadcast_data=msg_data)
    data = await state.get_data()
    
    # Target users
    if data["target"] == "active":
        active_cnt = await db.get_weekly_active()
        cnt = active_cnt
    else:
        all_u = await db.get_all_users()
        cnt = len(all_u)
        
    await message.answer(
        f"📣 Xabar <b>{cnt}</b> ta foydalanuvchiga yuborilmoqda. Tasdiqlaysizmi?",
        reply_markup=confirm_broadcast_keyboard(), parse_mode="HTML"
    )


@router.callback_query(F.data == "confirm_broadcast")
async def broadcast_run(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    
    msg = data.get("broadcast_data", {})
    target = data.get("target")
    
    if target == "active":
        # Bizda butun foydalanuvchilar orasidan oxirgi haftaliklarni ajratish kerak
        week_ago = utils.time.time() - 604800
        async with db.aiosqlite.connect(db.DB) as conn:
            cur = await conn.execute("SELECT DISTINCT user_id FROM watch_history WHERE watched_at>=?", (week_ago,))
            rows = await cur.fetchall()
            users = [{"telegram_id": r[0]} for r in rows]
    else:
        users = await db.get_all_users()
        
    sent, failed = 0, 0
    await callback.message.edit_text("⏳ Reklama jo'natilmoqda...")
    
    for u in users:
        try:
            uid = u["telegram_id"]
            if msg["type"] == "photo":
                await callback.bot.send_photo(uid, msg["file_id"], caption=msg.get("caption"), parse_mode="HTML")
            elif msg["type"] == "video":
                await callback.bot.send_video(uid, msg["file_id"], caption=msg.get("caption"), parse_mode="HTML")
            else:
                await callback.bot.send_message(uid, msg["text"], parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1
            
    await callback.message.edit_text(
        f"✅ <b>Yuborish yakunlandi!</b>\n\n"
        f"📤 Yuborildi: <b>{sent}</b>\n"
        f"❌ Xatolik: <b>{failed}</b>",
        reply_markup=back_to_admin_keyboard(), parse_mode="HTML"
    )


# ===== TOP MOVIES & BACKUP =====

@router.callback_query(F.data == "admin_top")
async def admin_top_movies(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    movies = await db.get_top_movies(10)
    if not movies:
        await callback.message.edit_text(
            "🏆 <b>Top kinolar</b>\n\nHozircha bazada kino yo'q.",
            reply_markup=back_to_admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    await callback.message.edit_text(
        "🏆 <b>Top kinolar</b>\n\nKo'rishlar bo'yicha saralangan ro'yxat:",
        reply_markup=movie_list_keyboard(movies, 0),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(Command("backup"))
async def admin_backup_cmd(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Kechirasiz, siz bot administratori emassiz!")
        return
    await message.answer("⏳ Ma'lumotlar bazasi zaxiralanmoqda...", parse_mode="HTML")
    backup_file = utils.create_backup()
    await message.answer_document(
        FSInputFile(backup_file),
        caption=f"💾 <b>Ma'lumotlar bazasi zaxira nusxasi</b>\n📅 Sana: {utils.time.strftime('%Y-%m-%d %H:%M:%S')}",
        parse_mode="HTML"
    )
