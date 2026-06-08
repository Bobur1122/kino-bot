"""
Channel Post Listener — kanallarga yuborilgan kinolarni avtomatik bazaga saqlash.
"""
from aiogram import Router, F
from aiogram.types import Message
import re

import database as db
import utils

router = Router()


@router.channel_post(F.video)
async def auto_save_channel_movie(message: Message):
    """
    Kanalga video yuborilganda uni avtomatik bazaga saqlash.
    Sarlavha (caption) dan kino nomi va yili aniqlanadi.
    IMDb integratsiyasi yordamida qolgan ma'lumotlar avtomatik to'ldiriladi.
    """
    caption = message.caption or ""
    if not caption:
        return
        
    # Birinchi qatorni kino nomi sifatida olamiz
    lines = [l.strip() for l in caption.split("\n") if l.strip()]
    if not lines:
        return
        
    title_line = lines[0]
    # Nomi ichidan yilni ajratib olishga urinish: "Kino nomi (2024)" -> "Kino nomi", 2024
    year = 0
    year_match = re.search(r'\((\d{4})\)', title_line)
    if year_match:
        year = int(year_match.group(1))
        title = title_line.replace(year_match.group(0), "").strip()
    else:
        # Qavssiz bo'lsa ham oxirida 4ta raqam bo'lsa
        year_end_match = re.search(r'\b(\d{4})\b$', title_line)
        if year_end_match:
            year = int(year_end_match.group(1))
            title = title_line.replace(year_end_match.group(0), "").strip()
        else:
            title = title_line
            
    # Hash-tag va ortiqcha belgilarni tozalash
    title = re.sub(r'[#🎬🍿🔥📺🧸]', '', title).strip()
    
    # Duplicate tekshirish
    if await db.check_duplicate(title):
        # Allaqachon yuklangan
        return
        
    # Video fayl IDsi va poster (video thumb bo'lsa)
    video_file_id = message.video.file_id
    poster_file_id = ""
    if message.video.thumbnail:
        poster_file_id = message.video.thumbnail.file_id
        
    # IMDb dan ma'lumotlarni qidiramiz
    imdb_data = await utils.fetch_imdb_data(title)
    
    category = "kino"
    description = caption
    genre = ""
    rating = 0.0
    duration = ""
    country = ""
    language = ""
    
    if imdb_data["title"]:
        title = imdb_data["title"]
        if imdb_data["description"]:
            description = imdb_data["description"]
        if imdb_data["year"]:
            year = imdb_data["year"]
        genre = imdb_data["genre"]
        rating = imdb_data["rating"]
        duration = imdb_data["duration"]
        country = imdb_data["country"]
        language = imdb_data["language"]
        
    # Kategoriyani aniqlash (janri yoki sarlavhasiga qarab)
    cat_lower = caption.lower()
    if "multfilm" in cat_lower or "cartoon" in cat_lower or "anime" in cat_lower or (imdb_data["genre"] and "Animation" in imdb_data["genre"]):
        category = "multfilm"
    elif "serial" in cat_lower or "qism" in cat_lower or "fasl" in cat_lower or "season" in cat_lower or (imdb_data["genre"] and "TV Series" in imdb_data["genre"]):
        category = "serial"
        
    # Baza saqlash
    await db.add_movie(
        title=title,
        video_file_id=video_file_id,
        category=category,
        description=description,
        poster_file_id=poster_file_id,
        year=year,
        genre=genre,
        rating=rating,
        duration=duration,
        country=country,
        language=language,
        channel_message_id=message.message_id
    )
