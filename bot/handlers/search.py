"""
Search handler — Kino qidirish.
Faqat "🔍 Qidirish" tugmasi bosilganda yoki /search buyrug'ida ishlaydi.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter
import database as db

router = Router()


class SearchState(StatesGroup):
    waiting = State()


@router.message(F.text == "🔍 Qidirish")
async def search_prompt(message: Message, state: FSMContext):
    await state.set_state(SearchState.waiting)
    await message.answer(
        "🔍 <b>Kino qidirish</b>\n\n"
        "Kino nomini yozing:",
        parse_mode="HTML"
    )


@router.message(Command("search"))
async def search_cmd(message: Message, state: FSMContext):
    args = message.text.replace("/search", "").strip()
    if args:
        await do_search(message, args)
    else:
        await state.set_state(SearchState.waiting)
        await message.answer("🔍 Kino nomini yozing:", parse_mode="HTML")


@router.message(StateFilter(SearchState.waiting))
async def search_text(message: Message, state: FSMContext):
    await state.clear()
    await do_search(message, message.text)


async def do_search(message: Message, query: str):
    """Qidirish natijalari."""
    query = query.strip()
    if len(query) < 2:
        await message.answer("❌ Kamida 2 ta harf yozing!")
        return

    movies = await db.search_movies(query)
    if not movies:
        await message.answer(
            f"😔 <b>\"{query}\"</b> bo'yicha topilmadi.\n"
            "Boshqa nom bilan qidirib ko'ring.",
            parse_mode="HTML"
        )
        return

    text = f"🔍 <b>\"{query}\"</b> — {len(movies)} ta natija:\n\n"
    buttons = []
    for movie in movies[:10]:
        emoji = {"kino": "🎬", "serial": "📺", "multfilm": "🧸"}.get(movie["category"], "🎬")
        text += f"{emoji} <b>{movie['title']}</b>"
        if movie.get("year"):
            text += f" ({movie['year']})"
        text += f" · 👁 {movie['views']}\n"
        buttons.append([
            InlineKeyboardButton(
                text=f"{emoji} {movie['title']}",
                callback_data=f"watch_{movie['id']}"
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("watch_"))
async def watch_movie(callback: CallbackQuery):
    """Kino ko'rish — video yuborish."""
    movie_id = int(callback.data.split("_")[1])
    movie = await db.get_movie(movie_id)
    if not movie:
        await callback.answer("❌ Kino topilmadi!", show_alert=True)
        return
    if not movie.get("video_file_id"):
        await callback.answer("❌ Ushbu kontent uchun video mavjud emas!", show_alert=True)
        return

    await callback.answer("⏳ Video yuborilmoqda...")
    try:
        emoji = {"kino": "🎬", "serial": "📺", "multfilm": "🧸"}.get(movie["category"], "🎬")
        caption = f"{emoji} <b>{movie['title']}</b>\n"
        if movie.get("year"):
            caption += f"📅 {movie['year']}\n"
        if movie.get("description"):
            caption += f"\n{movie['description']}\n"
        caption += f"\n👁 Ko'rishlar: {movie['views'] + 1}"

        await callback.message.answer_video(
            video=movie["video_file_id"],
            caption=caption,
            parse_mode="HTML"
        )
        await db.increment_views(movie_id)
        await db.add_watch_history(callback.from_user.id, movie_id)
    except Exception as e:
        await callback.message.answer(f"❌ Xatolik: {e}")
