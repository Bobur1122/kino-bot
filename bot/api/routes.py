"""
FastAPI API endpoints — Mini App uchun (kengaytirilgan).
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

import database as db

app = FastAPI(title="Kino Bot API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bot_instance = None


def set_bot(bot):
    global bot_instance
    bot_instance = bot


class WatchRequest(BaseModel):
    telegram_id: int


class RateRequest(BaseModel):
    telegram_id: int
    movie_id: int
    score: int # 1 for like, -1 for dislike


@app.get("/api/movies")
async def api_get_movies(category: Optional[str] = None, limit: int = 50):
    """Kinolar ro'yxati."""
    movies = await db.get_movies(limit=limit, category=category)
    return {"movies": movies, "count": len(movies)}


@app.get("/api/movies/popular")
async def api_get_popular(limit: int = 10):
    """Mashhur kinolar (views bo'yicha)."""
    movies = await db.get_top_movies(limit=limit)
    return {"movies": movies}


@app.get("/api/movies/recent")
async def api_get_recent(limit: int = 10):
    """Yangi qo'shilgan kinolar."""
    movies = await db.get_recent_movies(limit=limit)
    return {"movies": movies}


@app.get("/api/movies/search")
async def api_search_movies(q: str = "", limit: int = 20):
    """Kino qidirish va qidiruvni yozib borish."""
    if len(q) < 1:
        return {"movies": []}
    await db.record_search(q)
    movies = await db.search_movies(q)
    return {"movies": movies}


@app.get("/api/featured")
async def api_get_featured():
    """Netflix style uchun asosiy katta banner kino."""
    movies = await db.get_top_movies(1)
    if movies:
        return movies[0]
    # Agar biron kino bo'lmasa oxirgisini beradi
    recent = await db.get_recent_movies(1)
    if recent:
        return recent[0]
    return {}


@app.get("/api/movies/{movie_id}")
async def api_get_movie(movie_id: int, user_id: Optional[int] = None):
    """Bitta kino tafsilotlari (user statuslari bilan)."""
    if user_id:
        movie = await db.get_movie_details_for_user(movie_id, user_id)
    else:
        movie = await db.get_movie(movie_id)
        
    if not movie:
        raise HTTPException(status_code=404, detail="Kino topilmadi")
        
    # Tavsiyalar
    recs = await db.get_recommendations(movie_id)
    movie["recommendations"] = recs
    return movie


@app.post("/api/movies/{movie_id}/watch")
async def api_watch_movie(movie_id: int, req: WatchRequest):
    """Kino tomosha qilish — bot orqali video yuborish."""
    movie = await db.get_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Kino topilmadi")

    if not bot_instance:
        raise HTTPException(status_code=500, detail="Bot ishga tushmagan")

    try:
        # Userni bazaga qo'shish (agar start bosmasdan to'g'ri Mini Appga kirgan bo'lsa)
        await db.add_user(req.telegram_id)
        
        cat_emoji = {"kino": "🎬", "serial": "📺", "multfilm": "🧸"}.get(movie["category"], "🎬")
        caption = (
            f"{cat_emoji} <b>{movie['title']}</b>\n\n"
            f"📅 Yili: {movie.get('year') or '—'}\n"
            f"⭐ IMDb: {movie.get('rating') or '—'}\n"
            f"🎭 Janri: {movie.get('genre') or '—'}\n"
            f"🗣 Tili: {movie.get('language') or '—'} ({movie.get('dub_sub') or 'Asl til'})\n"
            f"⏱ Davomiyligi: {movie.get('duration') or '—'}\n\n"
            f"🍿 Yoqimli tomosha!"
        )

        await bot_instance.send_video(
            chat_id=req.telegram_id,
            video=movie["video_file_id"],
            caption=caption,
            parse_mode="HTML"
        )
        
        await db.increment_views(movie_id)
        await db.add_watch_history(req.telegram_id, movie_id)
        return {"success": True, "message": "Video yuborildi!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/movies/{movie_id}/rate")
async def api_rate_movie(movie_id: int, req: RateRequest):
    if req.score not in (1, -1, 0):
        raise HTTPException(status_code=400, detail="Noto'g'ri baho")
    await db.add_rating(req.telegram_id, movie_id, req.score)
    # Yangilangan reytingni hisoblash
    avg, count = await db.get_movie_rating(movie_id)
    return {"success": True, "rating": avg, "votes": count}


@app.get("/api/poster/{movie_id}")
async def api_poster(movie_id: int):
    """Poster rasm URL qaytarish."""
    movie = await db.get_movie(movie_id)
    if not movie or not movie.get("poster_file_id"):
        raise HTTPException(status_code=404, detail="Poster topilmadi")

    if not bot_instance:
        raise HTTPException(status_code=500, detail="Bot ishga tushmagan")

    try:
        file = await bot_instance.get_file(movie["poster_file_id"])
        url = f"https://api.telegram.org/file/bot{bot_instance.token}/{file.file_path}"
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"status": "ok", "message": "Kino Bot API ishlayapti!"}
