"""
Database — MongoDB (motor async driver).
"""
import time
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, ADMIN_IDS

client = None
db = None


async def init_db():
    global client, db
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.kinodb

    # Indexes
    await db.movies.create_index("id", unique=True)
    await db.users.create_index("telegram_id", unique=True)
    await db.ratings.create_index([("user_id", 1), ("movie_id", 1)], unique=True)
    await db.channels.create_index("channel_id", unique=True)
    await db.admins.create_index("telegram_id", unique=True)
    await db.search_queries.create_index("query", unique=True)

    # Counters
    await db.counters.update_one(
        {"_id": "movies"}, {"$setOnInsert": {"seq": 0}}, upsert=True
    )
    # Stats modifier
    await db.stats_modifier.update_one(
        {"_id": "main"},
        {"$setOnInsert": {"fake_users": 0, "fake_views": 0}},
        upsert=True,
    )
    # Base admins
    for aid in ADMIN_IDS:
        if aid and aid > 0:
            await db.admins.update_one(
                {"telegram_id": aid},
                {"$setOnInsert": {"telegram_id": aid, "added_by": 0, "added_at": time.time()}},
                upsert=True,
            )


async def _next_id(name):
    r = await db.counters.find_one_and_update(
        {"_id": name}, {"$inc": {"seq": 1}}, upsert=True, return_document=True
    )
    return r["seq"]


# ==================== USERS ====================

async def add_user(telegram_id: int, username: str = "", full_name: str = ""):
    await db.users.update_one(
        {"telegram_id": telegram_id},
        {"$set": {"username": username, "full_name": full_name},
         "$setOnInsert": {"created_at": time.time(), "is_premium": 0, "is_banned": 0}},
        upsert=True,
    )


async def get_all_users():
    return await db.users.find({"is_banned": 0}, {"_id": 0}).sort("_id", -1).to_list(None)


async def get_today_users():
    today = time.time() - (time.time() % 86400)
    return await db.users.count_documents({"created_at": {"$gte": today}})


async def get_weekly_active():
    week_ago = time.time() - 604800
    pipe = [
        {"$match": {"watched_at": {"$gte": week_ago}}},
        {"$group": {"_id": "$user_id"}},
        {"$count": "t"},
    ]
    r = await db.watch_history.aggregate(pipe).to_list(1)
    return r[0]["t"] if r else 0


# ==================== ADMINS ====================

async def get_admin_ids():
    return [a["telegram_id"] async for a in db.admins.find({}, {"telegram_id": 1})]


async def get_admins():
    return await db.admins.find({}, {"_id": 0}).sort("added_at", -1).to_list(None)


async def add_admin(telegram_id: int, added_by: int = 0):
    await db.admins.update_one(
        {"telegram_id": telegram_id},
        {"$setOnInsert": {"telegram_id": telegram_id, "added_by": added_by, "added_at": time.time()}},
        upsert=True,
    )


async def remove_admin(telegram_id: int):
    await db.admins.delete_one({"telegram_id": telegram_id})


# ==================== MOVIES ====================

async def add_movie(**kwargs):
    mid = await _next_id("movies")
    kwargs["id"] = mid
    kwargs.setdefault("created_at", time.time())
    kwargs.setdefault("views", 0)
    await db.movies.insert_one(kwargs)
    return mid


async def get_movie(movie_id: int):
    return await db.movies.find_one({"id": movie_id}, {"_id": 0})


async def get_movies(limit=50, category=None, sort="id DESC"):
    flt = {"category": category} if category else {}
    parts = sort.split()
    sf = parts[0] if parts else "id"
    sd = -1 if len(parts) > 1 and parts[1].upper() == "DESC" else 1
    return await db.movies.find(flt, {"_id": 0}).sort(sf, sd).limit(limit).to_list(limit)


async def search_movies(query: str):
    return await db.movies.find(
        {"$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"genre": {"$regex": query, "$options": "i"}},
        ]}, {"_id": 0}
    ).sort("views", -1).limit(20).to_list(20)


async def get_top_movies(limit=10):
    return await db.movies.find({}, {"_id": 0}).sort("views", -1).limit(limit).to_list(limit)


async def get_recent_movies(limit=5):
    return await db.movies.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)


async def update_movie(movie_id: int, **kwargs):
    await db.movies.update_one({"id": movie_id}, {"$set": kwargs})


async def delete_movie(movie_id: int):
    await db.movies.delete_one({"id": movie_id})


async def increment_views(movie_id: int):
    await db.movies.update_one({"id": movie_id}, {"$inc": {"views": 1}})


async def check_duplicate(title: str):
    return await db.movies.find_one({"title": title}) is not None


# ==================== WATCH HISTORY ====================

async def add_watch_history(user_id: int, movie_id: int):
    await db.watch_history.insert_one({"user_id": user_id, "movie_id": movie_id, "watched_at": time.time()})


# ==================== CHANNELS ====================

async def add_channel(channel_id: int, url="", name="",
                      mandatory=False, notification=False, hidden=False):
    await db.channels.update_one(
        {"channel_id": channel_id},
        {"$set": {
            "channel_id": channel_id, "channel_url": url, "channel_name": name,
            "is_mandatory": int(mandatory), "is_notification": int(notification),
            "is_hidden": int(hidden), "added_at": time.time(),
        }},
        upsert=True,
    )


async def remove_channel(channel_id: int):
    await db.channels.delete_one({"channel_id": channel_id})


async def get_channels():
    return await db.channels.find({}, {"_id": 0}).sort("_id", 1).to_list(None)


async def get_mandatory_channels():
    return await db.channels.find({"is_mandatory": 1}, {"_id": 0}).to_list(None)


async def get_notification_channels():
    return await db.channels.find({"is_notification": 1}, {"_id": 0}).to_list(None)


# ==================== RATINGS ====================

async def add_rating(user_id: int, movie_id: int, score: int):
    await db.ratings.update_one(
        {"user_id": user_id, "movie_id": movie_id},
        {"$set": {"score": score, "created_at": time.time()}},
        upsert=True,
    )


async def get_movie_rating(movie_id: int):
    pipe = [
        {"$match": {"movie_id": movie_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$score"}, "cnt": {"$sum": 1}}},
    ]
    r = await db.ratings.aggregate(pipe).to_list(1)
    if r:
        return (round(r[0]["avg"], 1), r[0]["cnt"])
    return (0, 0)


# ==================== STATS ====================

async def get_stats():
    s = {}
    s["users"] = await db.users.count_documents({})
    s["movies"] = await db.movies.count_documents({})
    s["kino"] = await db.movies.count_documents({"category": "kino"})
    s["serial"] = await db.movies.count_documents({"category": "serial"})
    s["multfilm"] = await db.movies.count_documents({"category": "multfilm"})

    pipe = [{"$group": {"_id": None, "total": {"$sum": "$views"}}}]
    vr = await db.movies.aggregate(pipe).to_list(1)
    real_views = vr[0]["total"] if vr else 0

    mod = await db.stats_modifier.find_one({"_id": "main"})
    fu = mod["fake_users"] if mod else 0
    fv = mod["fake_views"] if mod else 0

    s["users"] += fu
    s["views"] = real_views + fv
    s["fake_users"] = fu
    s["fake_views"] = fv
    s["today_users"] = await get_today_users()
    s["weekly_active"] = await get_weekly_active()
    s["channels"] = await db.channels.count_documents({})
    return s


async def update_fake_stats(fake_users: int, fake_views: int):
    await db.stats_modifier.update_one(
        {"_id": "main"}, {"$set": {"fake_users": fake_users, "fake_views": fake_views}}, upsert=True
    )


# ==================== SEARCH ====================

async def record_search(query: str):
    q = query.strip().lower()
    if len(q) < 2:
        return
    await db.search_queries.update_one(
        {"query": q}, {"$inc": {"count": 1}, "$setOnInsert": {"query": q}}, upsert=True
    )


async def get_popular_searches(limit=10):
    return await db.search_queries.find({}, {"_id": 0}).sort("count", -1).limit(limit).to_list(limit)


# ==================== RECOMMENDATIONS ====================

async def get_recommendations(movie_id: int, limit=6):
    movie = await get_movie(movie_id)
    if not movie:
        return []
    flt = {"id": {"$ne": movie_id}, "$or": [
        {"category": movie["category"]},
        {"genre": {"$regex": movie.get("genre") or "", "$options": "i"}},
    ]}
    res = await db.movies.find(flt, {"_id": 0}).sort("views", -1).limit(limit).to_list(limit)
    if len(res) < limit:
        ids = [movie_id] + [r["id"] for r in res]
        more = await db.movies.find({"id": {"$nin": ids}}, {"_id": 0}).sort("views", -1).limit(limit - len(res)).to_list(limit - len(res))
        res.extend(more)
    return res


async def get_movie_details_for_user(movie_id: int, user_id: int):
    movie = await get_movie(movie_id)
    if not movie:
        return None
    rat = await db.ratings.find_one({"user_id": user_id, "movie_id": movie_id})
    movie["user_score"] = rat["score"] if rat else 0
    movie["likes"] = await db.ratings.count_documents({"movie_id": movie_id, "score": 1})
    movie["dislikes"] = await db.ratings.count_documents({"movie_id": movie_id, "score": -1})
    return movie


async def get_random_movie():
    pipe = [{"$sample": {"size": 1}}, {"$project": {"_id": 0}}]
    r = await db.movies.aggregate(pipe).to_list(1)
    return r[0] if r else None


async def get_filtered_movies(category=None, genre=None, country=None, year=None, limit=20, sort="id DESC"):
    flt = {}
    if category:
        flt["category"] = category
    if genre:
        flt["genre"] = {"$regex": genre, "$options": "i"}
    if country:
        flt["country"] = {"$regex": country, "$options": "i"}
    if year:
        flt["year"] = int(year)
    parts = sort.split()
    sf = parts[0] if parts else "id"
    sd = -1 if len(parts) > 1 and parts[1].upper() == "DESC" else 1
    return await db.movies.find(flt, {"_id": 0}).sort(sf, sd).limit(limit).to_list(limit)
