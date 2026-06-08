"""
Yordamchi funksiyalar: IMDb parser, Server stats, DB Backup.
"""
import os
import shutil
import time
import psutil
import aiohttp
from bs4 import BeautifulSoup
import json
from config import DATABASE_PATH

# IMDb parser uchun sarlavhalar (IMDb request bloklamasligi uchun)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept-Language": "uz,en-US;q=0.9,en;q=0.8"
}


async def fetch_imdb_data(query: str) -> dict:
    """
    IMDb saytidan film ma'lumotlarini qidirish va parsing qilish.
    Agar query 'tt' bilan boshlansa to'g'ridan-to'g'ri ID bo'yicha oladi.
    """
    result = {
        "title": "",
        "year": 0,
        "genre": "",
        "rating": 0.0,
        "duration": "",
        "country": "",
        "language": "",
        "description": "",
        "poster_url": ""
    }
    
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        imdb_id = None
        if query.strip().startswith("tt") and len(query.strip()) >= 5:
            imdb_id = query.strip()
        else:
            # Nom bo'yicha qidirish
            search_url = f"https://www.imdb.com/find/?q={query.replace(' ', '+')}&s=tt&ttype=ft"
            try:
                async with session.get(search_url, timeout=10) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, "html.parser")
                        # Birinchi natijani topish
                        link = soup.find("a", class_="ipc-metadata-list-summary-item__t")
                        if link and "href" in link.attrs:
                            href = link.attrs["href"]
                            # /title/tt1234567/
                            parts = href.split("/")
                            for p in parts:
                                if p.startswith("tt"):
                                    imdb_id = p
                                    break
            except Exception:
                pass
                
        if not imdb_id:
            return result

        movie_url = f"https://www.imdb.com/title/{imdb_id}/"
        try:
            async with session.get(movie_url, timeout=10) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # LD+JSON dan to'liq ma'lumotlarni o'qiymiz (IMDb shu formatda saqlaydi)
                    json_script = soup.find("script", type="application/ld+json")
                    if json_script:
                        data = json.loads(json_script.string)
                        result["title"] = data.get("name", "")
                        
                        # Yil
                        release_date = data.get("releasedEvent", {}) or {}
                        if isinstance(release_date, dict):
                            date_str = release_date.get("startDate", "")
                            if date_str and len(date_str) >= 4:
                                try:
                                    result["year"] = int(date_str[:4])
                                except ValueError:
                                    pass
                        elif isinstance(release_date, list) and len(release_date) > 0:
                            date_str = release_date[0].get("startDate", "")
                            if date_str and len(date_str) >= 4:
                                try:
                                    result["year"] = int(date_str[:4])
                                except ValueError:
                                    pass
                        
                        # Agar LD+JSON da yil bo'lmasa, nomidan yoki boshqa joydan olishga urinish
                        if not result["year"] and "datePublished" in data:
                            try:
                                result["year"] = int(data["datePublished"][:4])
                            except Exception:
                                pass
                                
                        # Janrlar
                        genres = data.get("genre", [])
                        if isinstance(genres, list):
                            result["genre"] = ", ".join(genres)
                        else:
                            result["genre"] = str(genres)
                            
                        # Reyting
                        rating_info = data.get("aggregateRating", {}) or {}
                        if rating_info:
                            try:
                                result["rating"] = float(rating_info.get("ratingValue", 0.0))
                            except ValueError:
                                pass
                                
                        # Davomiyligi
                        duration_str = data.get("duration", "") # PT2H2M
                        if duration_str:
                            # PT2H2M formatidan o'qish
                            import re
                            hours = re.search(r'(\d+)H', duration_str)
                            mins = re.search(r'(\d+)M', duration_str)
                            h = f"{hours.group(1)} soat " if hours else ""
                            m = f"{mins.group(1)} daqiqa" if mins else ""
                            result["duration"] = (h + m).strip()
                            
                        # Poster
                        result["poster_url"] = data.get("image", "")
                        
                        # Tavsif
                        result["description"] = data.get("description", "")
                    
                    # LD+JSON da davlat va til ko'pincha yo'q, ularni HTML dan olamiz
                    # Davlat
                    country_el = soup.find("a", href=lambda x: x and "/search/title/?country_of_origin=" in x)
                    if country_el:
                        result["country"] = country_el.get_text(strip=True)
                        
                    # Til
                    lang_el = soup.find("a", href=lambda x: x and "/search/title?primary_language=" in x)
                    if lang_el:
                        result["language"] = lang_el.get_text(strip=True)
                        
        except Exception:
            pass
            
    return result


def get_server_status() -> dict:
    """Server xotira va tizim holati."""
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('.')
    
    return {
        "cpu": cpu,
        "ram_used": round(ram.used / (1024 ** 3), 2),
        "ram_total": round(ram.total / (1024 ** 3), 2),
        "ram_percent": ram.percent,
        "disk_used": round(disk.used / (1024 ** 3), 2),
        "disk_total": round(disk.total / (1024 ** 3), 2),
        "disk_percent": disk.percent,
        "uptime": round(time.time() - psutil.boot_time())
    }


def create_backup() -> str:
    """SQLite faylini backup papkaga nusxalash va fayl yo'lini qaytarish."""
    os.makedirs("backups", exist_ok=True)
    filename = f"backups/db_backup_{int(time.time())}.db"
    shutil.copy2(DATABASE_PATH, filename)
    return filename
