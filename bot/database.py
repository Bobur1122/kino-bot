"""
Database — SQLite (aiosqlite).
Channels table qo'shildi + movie fieldlar kengaytirildi.
"""
import aiosqlite
import time
from config import DATABASE_PATH, ADMIN_IDS

DB = DATABASE_PATH


async def init_db():
    async with aiosqlite.connect(DB) as conn:
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT DEFAULT '',
                full_name TEXT DEFAULT '',
                created_at REAL DEFAULT 0,
                is_premium INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                video_file_id TEXT NOT NULL,
                category TEXT DEFAULT 'kino',
                description TEXT DEFAULT '',
                poster_file_id TEXT DEFAULT '',
                trailer TEXT DEFAULT '',
                channel_message_id INTEGER DEFAULT 0,
                year INTEGER DEFAULT 0,
                genre TEXT DEFAULT '',
                rating REAL DEFAULT 0,
                duration TEXT DEFAULT '',
                country TEXT DEFAULT '',
                language TEXT DEFAULT '',
                dub_sub TEXT DEFAULT '',
                views INTEGER DEFAULT 0,
                created_at REAL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS watch_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                movie_id INTEGER NOT NULL,
                watched_at REAL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER UNIQUE NOT NULL,
                channel_url TEXT DEFAULT '',
                channel_name TEXT DEFAULT '',
                is_mandatory INTEGER DEFAULT 0,
                is_notification INTEGER DEFAULT 0,
                is_hidden INTEGER DEFAULT 0,
                added_at REAL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                movie_id INTEGER NOT NULL,
                score INTEGER DEFAULT 0,
                created_at REAL DEFAULT 0,
                UNIQUE(user_id, movie_id)
            );
            CREATE TABLE IF NOT EXISTS stats_modifier (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fake_users INTEGER DEFAULT 0,
                fake_views INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS search_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT UNIQUE NOT NULL,
                count INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS admins (
                telegram_id INTEGER PRIMARY KEY,
                added_by INTEGER DEFAULT 0,
                added_at REAL DEFAULT 0
            );
            INSERT OR IGNORE INTO stats_modifier (id, fake_users, fake_views) VALUES (1, 0, 0);
        """)
        for admin_id in ADMIN_IDS:
            if admin_id and admin_id > 0:
                await conn.execute(
                    "INSERT OR IGNORE INTO admins (telegram_id, added_by, added_at) VALUES (?,?,?)",
                    (admin_id, 0, time.time())
                )
        await conn.commit()


# ==================== USERS ====================

async def add_user(telegram_id: int, username: str = "", full_name: str = ""):
    async with aiosqlite.connect(DB) as conn:
        await conn.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username, full_name, created_at) VALUES (?,?,?,?)",
            (telegram_id, username, full_name, time.time())
        )
        await conn.execute(
            "UPDATE users SET username=?, full_name=? WHERE telegram_id=?",
            (username, full_name, telegram_id)
        )
        await conn.commit()


async def get_all_users():
    async with aiosqlite.connect(DB) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM users WHERE is_banned=0 ORDER BY id DESC")
        return [dict(r) for r in await cur.fetchall()]


async def get_today_users():
    today_start = time.time() - (time.time() % 86400)
    async with aiosqlite.connect(DB) as conn:
        cur = await conn.execute("SELECT COUNT(*) FROM users WHERE created_at>=?", (today_start,))
        row = await cur.fetchone()
        return row[0] if row else 0


async def get_weekly_active():
    week_ago = time.time() - 604800
    async with aiosqlite.connect(DB) as conn:
        cur = await conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM watch_history WHERE watched_at>=?", (week_ago,)
        )
        row = await cur.fetchone()
        return row[0] if row else 0


# ==================== ADMINS ====================

async def get_admin_ids():
    async with aiosqlite.connect(DB) as conn:
        cur = await conn.execute("SELECT telegram_id FROM admins ORDER BY telegram_id")
        rows = await cur.fetchall()
        return [r[0] for r in rows]


async def get_admins():
    async with aiosqlite.connect(DB) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM admins ORDER BY added_at DESC, telegram_id ASC")
        return [dict(r) for r in await cur.fetchall()]


async def add_admin(telegram_id: int, added_by: int = 0):
    async with aiosqlite.connect(DB) as conn:
        await conn.execute(
            "INSERT OR IGNORE INTO admins (telegram_id, added_by, added_at) VALUES (?,?,?)",
            (telegram_id, added_by, time.time())
        )
        await conn.commit()


async def remove_admin(telegram_id: int):
    async with aiosqlite.connect(DB) as conn:
        await conn.execute("DELETE FROM admins WHERE telegram_id=?", (telegram_id,))
        await conn.commit()


# ==================== MOVIES ====================

async def add_movie(**kwargs):
    kwargs.setdefault("created_at", time.time())
    cols = ", ".join(kwargs.keys())
    vals = ", ".join(["?"] * len(kwargs))
    async with aiosqlite.connect(DB) as conn:
        cur = await conn.execute(f"INSERT INTO movies ({cols}) VALUES ({vals})", list(kwargs.values()))
        await conn.commit()
        return cur.lastrowid


async def get_movie(movie_id: int):
    async with aiosqlite.connect(DB) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM movies WHERE id=?", (movie_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_movies(limit=50, category=None, sort="id DESC"):
    async with aiosqlite.connect(DB) as conn:
        conn.row_factory = aiosqlite.Row
        if category:
            cur = await conn.execute(
                f"SELECT * FROM movies WHERE category=? ORDER BY {sort} LIMIT ?", (category, limit)
            )
        else:
            cur = await conn.execute(f"SELECT * FROM movies ORDER BY {sort} LIMIT ?", (limit,))
        return [dict(r) for r in await cur.fetchall()]


async def search_movies(query: str):
    async with aiosqlite.connect(DB) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            "SELECT * FROM movies WHERE title LIKE ? OR genre LIKE ? ORDER BY views DESC LIMIT 20",
            (f"%{query}%", f"%{query}%")
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_top_movies(limit=10):
    async with aiosqlite.connect(DB) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM movies ORDER BY views DESC LIMIT ?", (limit,))
        return [dict(r) for r in await cur.fetchall()]


async def get_recent_movies(limit=5):
    async with aiosqlite.connect(DB) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM movies ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in await cur.fetchall()]


async def update_movie(movie_id: int, **kwargs):
    sets = ", ".join(f"{k}=?" for k in kwargs)
    async with aiosqlite.connect(DB) as conn:
        await conn.execute(f"UPDATE movies SET {sets} WHERE id=?", [*kwargs.values(), movie_id])
        await conn.commit()


async def delete_movie(movie_id: int):
    async with aiosqlite.connect(DB) as conn:
        await conn.execute("DELETE FROM movies WHERE id=?", (movie_id,))
        await conn.commit()


async def increment_views(movie_id: int):
    async with aiosqlite.connect(DB) as conn:
        await conn.execute("UPDATE movies SET views = views + 1 WHERE id=?", (movie_id,))
        await conn.commit()


async def check_duplicate(title: str):
    async with aiosqlite.connect(DB) as conn:
        cur = await conn.execute("SELECT id FROM movies WHERE title=?", (title,))
        return await cur.fetchone() is not None


# ==================== WATCH HISTORY ====================

async def add_watch_history(user_id: int, movie_id: int):
    async with aiosqlite.connect(DB) as conn:
        await conn.execute(
            "INSERT INTO watch_history (user_id, movie_id, watched_at) VALUES (?,?,?)",
            (user_id, movie_id, time.time())
        )
        await conn.commit()


# ==================== CHANNELS ====================

async def add_channel(channel_id: int, url: str = "", name: str = "",
                      mandatory: bool = False, notification: bool = False, hidden: bool = False):
    async with aiosqlite.connect(DB) as conn:
        await conn.execute(
            "INSERT OR REPLACE INTO channels (channel_id,channel_url,channel_name,is_mandatory,is_notification,is_hidden,added_at) VALUES (?,?,?,?,?,?,?)",
            (channel_id, url, name, int(mandatory), int(notification), int(hidden), time.time())
        )
        await conn.commit()


async def remove_channel(channel_id: int):
    async with aiosqlite.connect(DB) as conn:
        await conn.execute("DELETE FROM channels WHERE channel_id=?", (channel_id,))
        await conn.commit()


async def get_channels():
    async with aiosqlite.connect(DB) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM channels ORDER BY id")
        return [dict(r) for r in await cur.fetchall()]


async def get_mandatory_channels():
    async with aiosqlite.connect(DB) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM channels WHERE is_mandatory=1")
        return [dict(r) for r in await cur.fetchall()]


async def get_notification_channels():
    async with aiosqlite.connect(DB) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM channels WHERE is_notification=1")
        return [dict(r) for r in await cur.fetchall()]


# ==================== RATINGS ====================

async def add_rating(user_id: int, movie_id: int, score: int):
    async with aiosqlite.connect(DB) as conn:
        await conn.execute(
            "INSERT OR REPLACE INTO ratings (user_id, movie_id, score, created_at) VALUES (?,?,?,?)",
            (user_id, movie_id, score, time.time())
        )
        await conn.commit()


async def get_movie_rating(movie_id: int):
    async with aiosqlite.connect(DB) as conn:
        cur = await conn.execute(
            "SELECT AVG(score), COUNT(*) FROM ratings WHERE movie_id=?", (movie_id,)
        )
        row = await cur.fetchone()
        return (round(row[0], 1) if row[0] else 0, row[1])


# ==================== STATS ====================

async def get_stats():
    async with aiosqlite.connect(DB) as conn:
        s = {}
        cur = await conn.execute("SELECT COUNT(*) FROM users")
        real_users = (await cur.fetchone())[0]
        cur = await conn.execute("SELECT COUNT(*) FROM movies")
        s["movies"] = (await cur.fetchone())[0]
        cur = await conn.execute("SELECT COUNT(*) FROM movies WHERE category='kino'")
        s["kino"] = (await cur.fetchone())[0]
        cur = await conn.execute("SELECT COUNT(*) FROM movies WHERE category='serial'")
        s["serial"] = (await cur.fetchone())[0]
        cur = await conn.execute("SELECT COUNT(*) FROM movies WHERE category='multfilm'")
        s["multfilm"] = (await cur.fetchone())[0]
        cur = await conn.execute("SELECT COALESCE(SUM(views),0) FROM movies")
        real_views = (await cur.fetchone())[0]
        
        # Modifiers
        cur_mod = await conn.execute("SELECT fake_users, fake_views FROM stats_modifier WHERE id=1")
        row_mod = await cur_mod.fetchone()
        fake_u, fake_v = (row_mod[0], row_mod[1]) if row_mod else (0, 0)
        
        s["users"] = real_users + fake_u
        s["views"] = real_views + fake_v
        s["today_users"] = await get_today_users()
        s["weekly_active"] = await get_weekly_active()
        cur = await conn.execute("SELECT COUNT(*) FROM channels")
        s["channels"] = (await cur.fetchone())[0]
        s["fake_users"] = fake_u
        s["fake_views"] = fake_v
        return s


async def update_fake_stats(fake_users: int, fake_views: int):
    async with aiosqlite.connect(DB) as conn:
        await conn.execute(
            "INSERT OR REPLACE INTO stats_modifier (id, fake_users, fake_views) VALUES (1, ?, ?)",
            (fake_users, fake_views)
        )
        await conn.commit()


# ==================== SEARCH RECORDING ====================

async def record_search(query: str):
    query = query.strip().lower()
    if len(query) < 2:
        return
    async with aiosqlite.connect(DB) as conn:
        await conn.execute(
            "INSERT INTO search_queries (query, count) VALUES (?, 1) "
            "ON CONFLICT(query) DO UPDATE SET count = count + 1",
            (query,)
        )
        await conn.commit()


async def get_popular_searches(limit=10):
    async with aiosqlite.connect(DB) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM search_queries ORDER BY count DESC LIMIT ?", (limit,))
        return [dict(r) for r in await cur.fetchall()]


# ==================== RECS ====================

async def get_recommendations(movie_id: int, limit=6):
    async with aiosqlite.connect(DB) as conn:
        conn.row_factory = aiosqlite.Row
        movie = await get_movie(movie_id)
        if not movie:
            return []
        
        # O'xshash janr yoki kategoriya bo'yicha (kino o'zidan tashqari)
        cur = await conn.execute(
            "SELECT * FROM movies WHERE id != ? AND (category = ? OR genre LIKE ?) ORDER BY views DESC LIMIT ?",
            (movie_id, movie["category"], f"%{movie.get('genre') or ''}%", limit)
        )
        res = [dict(r) for r in await cur.fetchall()]
        if len(res) < limit:
            # Agar kam bo'lsa, eng ko'p ko'rilgan boshqa kinolardan to'ldiramiz
            needed = limit - len(res)
            exclude_ids = [movie_id] + [r["id"] for r in res]
            placeholders = ",".join(["?"] * len(exclude_ids))
            cur2 = await conn.execute(
                f"SELECT * FROM movies WHERE id NOT IN ({placeholders}) ORDER BY views DESC LIMIT ?",
                (*exclude_ids, needed)
            )
            res.extend([dict(r) for r in await cur2.fetchall()])
        return res


async def get_movie_details_for_user(movie_id: int, user_id: int):
    movie = await get_movie(movie_id)
    if not movie:
        return None
        
    async with aiosqlite.connect(DB) as conn:
        # User bahosi
        cur_rat = await conn.execute(
            "SELECT score FROM ratings WHERE user_id=? AND movie_id=?", (user_id, movie_id)
        )
        row_rat = await cur_rat.fetchone()
        user_score = row_rat[0] if row_rat else 0
        
        # Umumiy like/dislike soni
        cur_likes = await conn.execute(
            "SELECT COUNT(*) FROM ratings WHERE movie_id=? AND score=1", (movie_id,)
        )
        likes = (await cur_likes.fetchone())[0]
        
        cur_dislikes = await conn.execute(
            "SELECT COUNT(*) FROM ratings WHERE movie_id=? AND score=-1", (movie_id,)
        )
        dislikes = (await cur_dislikes.fetchone())[0]

    movie["user_score"] = user_score
    movie["likes"] = likes
    movie["dislikes"] = dislikes
    return movie


async def get_random_movie():
    async with aiosqlite.connect(DB) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM movies ORDER BY RANDOM() LIMIT 1")
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_filtered_movies(category=None, genre=None, country=None, year=None, limit=20, sort="id DESC"):
    async with aiosqlite.connect(DB) as conn:
        conn.row_factory = aiosqlite.Row
        conditions = []
        params = []
        if category:
            conditions.append("category = ?")
            params.append(category)
        if genre:
            conditions.append("genre LIKE ?")
            params.append(f"%{genre}%")
        if country:
            conditions.append("country LIKE ?")
            params.append(f"%{country}%")
        if year:
            conditions.append("year = ?")
            params.append(int(year))
        
        where = " AND ".join(conditions)
        query = "SELECT * FROM movies"
        if where:
            query += f" WHERE {where}"
        query += f" ORDER BY {sort} LIMIT ?"
        params.append(limit)
        
        cur = await conn.execute(query, params)
        return [dict(r) for r in await cur.fetchall()]

