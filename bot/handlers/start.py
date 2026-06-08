"""
Start handler - /start, menyu, majburiy obuna (bazadan kanallar).
"""
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

import database as db
from config import WEBAPP_URL
from keyboards.inline import (
    main_menu_keyboard,
    channel_subscribe_keyboard,
    kinolar_menu_keyboard,
    seriallar_menu_keyboard,
    multfilmlar_menu_keyboard,
)

router = Router()


async def check_all_subscriptions(bot, user_id: int) -> list:
    """Barcha majburiy kanallarga obuna tekshirish."""
    channels = await db.get_mandatory_channels()
    not_subscribed = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch["channel_id"], user_id)
            if member.status not in ("member", "administrator", "creator"):
                not_subscribed.append(ch)
        except Exception:
            pass
    return not_subscribed


@router.message(CommandStart())
async def cmd_start(message: Message):
    try:
        user = message.from_user
        await db.add_user(telegram_id=user.id, username=user.username or "", full_name=user.full_name or "")

        not_subscribed = await check_all_subscriptions(message.bot, user.id)
        if not_subscribed:
            await message.answer(
                "🎬 <b>KINO UZ - Rasmiy botiga xush kelibsiz!</b> 🍿\n\n"
                "Siz bu yerda eng so'nggi premyeralar, ommabop seriallar va multfilmlarni tomosha qilishingiz mumkin.\n\n"
                "⚠️ <b>Botdan foydalanish uchun rasmiy kanallarimizga obuna bo'ling:</b>",
                reply_markup=channel_subscribe_keyboard(not_subscribed),
                parse_mode="HTML",
            )
            return

        await message.answer(
            f"🌟 <b>Salom, {user.first_name}! KINO UZ platformasiga xush kelibsiz!</b> 🎉\n\n"
            "Siz uchun eng sara kinolar, tarjima seriallar va sevimli multfilmlar to'plandi!\n\n"
            "<b>🔥 Bizning qulayliklar:</b>\n"
            "  • 📱 <b>Mini App orqali</b> Netflix uslubidagi qulay UI/UX dizayn\n"
            "  • 👍 Filmlarga baho (Like/Dislike) berish\n"
            "  • 🎬 Kinoni botdan yuborib ko'rish",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML",
        )

        # Mini App inline tugmasini alohida xabarda yuborish
        if WEBAPP_URL.startswith("https://"):
            inline_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="📱 Mini App ochish",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )]
            ])
            await message.answer(
            "👇 <b>Mini App</b>'ni ochish uchun quyidagi tugmani bosing:",
            reply_markup=inline_kb,
            parse_mode="HTML",
        )
    except Exception as e:
        import logging
        logging.error(f"Start handler error: {e}", exc_info=True)
        await message.answer(f"❌ Xatolik yuz berdi: {e}")


@router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery):
    not_subscribed = await check_all_subscriptions(callback.bot, callback.from_user.id)
    if not_subscribed:
        await callback.answer("❌ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        return

    await callback.message.delete()
    await callback.message.answer(
        "✅ <b>Obuna tasdiqlandi!</b>\n\n"
        "🚀 <b>KINO UZ</b> platformasining to'liq imkoniyatlaridan foydalanishingiz mumkin!\n\n"
        "👇 Quyidagi <b>🚀 Kinolar</b> tugmasini bosing va premyeralarni tomosha qiling!",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


def make_movie_list_inline(movies: list) -> InlineKeyboardMarkup:
    buttons = []
    for m in movies:
        emoji = {"kino": "🎬", "serial": "📺", "multfilm": "🎞️"}.get(m["category"], "🎬")
        title = m["title"]
        if len(title) > 32:
            title = title[:29] + "..."
        buttons.append([InlineKeyboardButton(text=f"{emoji} {title}", callback_data=f"watch_{m['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "🎬 Kinolar")
async def show_kinolar_menu(message: Message):
    await message.answer(
        "🎬 <b>KINO UZ - Kinolar Bo'limi</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=kinolar_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(F.text == "📺 Seriallar")
async def show_seriallar_menu(message: Message):
    await message.answer(
        "📺 <b>KINO UZ - Seriallar Bo'limi</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=seriallar_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(F.text == "🎞 Multfilmlar")
async def show_multfilmlar_menu(message: Message):
    await message.answer(
        "🎞 <b>KINO UZ - Multfilmlar Bo'limi</b>\n\n"
        "Quyidagi toifalardan birini tanlang:",
        reply_markup=multfilmlar_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(F.text == "🎲 Tasodifiy")
async def show_random_movie(message: Message):
    movie = await db.get_random_movie()
    if not movie:
        await message.answer("😔 Hozircha bazada kinolar mavjud emas.")
        return

    cat_emoji = {"kino": "🎬", "serial": "📺", "multfilm": "🎞️"}.get(movie["category"], "🎬")
    caption = (
        "🎲 <b>Tasodifiy Premyera:</b>\n\n"
        f"{cat_emoji} <b>{movie['title']}</b>\n\n"
        f"📅 Yili: {movie.get('year') or '—'}\n"
        f"⭐ IMDb: {movie.get('rating') or '—'}\n"
        f"🎭 Janri: {movie.get('genre') or '—'}\n"
        f"⏱ Davomiyligi: {movie.get('duration') or '—'}\n\n"
        "🍿 Yoqimli tomosha!"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🍿 Ko'rish", callback_data=f"watch_{movie['id']}")]]
    )

    if movie.get("poster_file_id"):
        try:
            await message.answer_photo(movie["poster_file_id"], caption=caption, reply_markup=kb, parse_mode="HTML")
            return
        except Exception:
            pass

    await message.answer(caption, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.regexp(r"^cat_(movies|series|cartoons)_"))
async def category_callbacks(callback: CallbackQuery):
    action = callback.data.split("_")[1]
    subtype = callback.data.split("_")[2]

    await callback.answer()

    category = {"movies": "kino", "series": "serial", "cartoons": "multfilm"}.get(action)

    if subtype == "new":
        movies = await db.get_movies(limit=10, category=category, sort="created_at DESC")
        if not movies:
            await callback.message.answer("❌ Yangi kontentlar topilmadi.")
            return
        await callback.message.answer("🔥 <b>Yangi qo'shilganlar:</b>", reply_markup=make_movie_list_inline(movies), parse_mode="HTML")
        return

    if subtype == "popular":
        movies = await db.get_movies(limit=10, category=category, sort="views DESC")
        if not movies:
            await callback.message.answer("❌ Mashhur kontentlar topilmadi.")
            return
        await callback.message.answer("⭐ <b>Eng ko'p ko'rilganlar:</b>", reply_markup=make_movie_list_inline(movies), parse_mode="HTML")
        return

    if subtype == "kids":
        movies = await db.get_filtered_movies(category="multfilm", genre="Bolalar", limit=10)
        if not movies:
            movies = await db.get_movies(limit=10, category="multfilm")
        if not movies:
            await callback.message.answer("❌ Bolalar uchun multfilmlar topilmadi.")
            return
        await callback.message.answer("🧒 <b>Bolalar uchun multfilmlar:</b>", reply_markup=make_movie_list_inline(movies), parse_mode="HTML")
        return

    if subtype == "anime":
        movies = await db.get_filtered_movies(category="multfilm", genre="Anime", limit=10)
        if not movies:
            movies = await db.get_movies(limit=10, category="multfilm")
        if not movies:
            await callback.message.answer("❌ Anime multfilmlar topilmadi.")
            return
        await callback.message.answer("🎌 <b>Anime multfilmlar:</b>", reply_markup=make_movie_list_inline(movies), parse_mode="HTML")
        return

    if subtype == "comedy" and category == "multfilm":
        movies = await db.get_filtered_movies(category="multfilm", genre="Komediya", limit=10)
        if not movies:
            movies = await db.get_movies(limit=10, category="multfilm")
        if not movies:
            await callback.message.answer("❌ Komediya multfilmlar topilmadi.")
            return
        await callback.message.answer("😂 <b>Komediya multfilmlar:</b>", reply_markup=make_movie_list_inline(movies), parse_mode="HTML")
        return

    if subtype == "genre":
        genres = ["Tarjima", "Komediya", "Drama", "Qo'rqinchli", "Aksiya"]
        buttons = []
        for g in genres:
            buttons.append([InlineKeyboardButton(text=f"🎭 {g}", callback_data=f"flt_genre_{category}_{g}")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.answer("🎭 <b>Janrni tanlang:</b>", reply_markup=kb, parse_mode="HTML")
        return

    await callback.message.answer("❌ Noto'g'ri bo'lim tanlandi.")


@router.callback_query(F.data.startswith("flt_"))
async def filter_results_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    filter_type = parts[1]
    category = parts[2]
    value = parts[3]

    await callback.answer("⏳ Yuklanmoqda...")

    if filter_type == "genre":
        movies = await db.get_filtered_movies(category=category, genre=value, limit=10)
    else:
        movies = []

    if not movies:
        movies = await db.get_filtered_movies(category=category, limit=10)
    if not movies:
        await callback.message.answer("❌ Natija topilmadi.")
        return

    await callback.message.answer(
        f"🔍 Natijalar ({value}):",
        reply_markup=make_movie_list_inline(movies),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    await callback.answer()
