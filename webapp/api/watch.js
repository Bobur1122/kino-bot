const { connectToDatabase } = require('../lib/mongodb');

module.exports = async (req, res) => {
    if (req.method === 'OPTIONS') return res.status(200).end();
    if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

    try {
        const db = await connectToDatabase();
        const movieId = parseInt(req.query.id);
        const { telegram_id } = req.body;

        const movie = await db.collection('movies').findOne({ id: movieId });
        if (!movie) return res.status(404).json({ detail: 'Kino topilmadi' });

        const BOT_TOKEN = process.env.BOT_TOKEN;
        if (!BOT_TOKEN) return res.status(500).json({ detail: 'Bot token not set' });

        const cat = { kino: '🎬', serial: '📺', multfilm: '🧸' }[movie.category] || '🎬';
        const caption = `${cat} <b>${movie.title}</b>\n\n` +
            `📅 Yili: ${movie.year || '—'}\n` +
            `⭐ IMDb: ${movie.rating || '—'}\n` +
            `🎭 Janri: ${movie.genre || '—'}\n` +
            `🗣 Tili: ${movie.language || '—'} (${movie.dub_sub || 'Asl til'})\n` +
            `⏱ Davomiyligi: ${movie.duration || '—'}\n\n🍿 Yoqimli tomosha!`;

        // Send video via Telegram Bot API directly
        const tgRes = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendVideo`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                chat_id: telegram_id,
                video: movie.video_file_id,
                caption,
                parse_mode: 'HTML'
            })
        });

        if (!tgRes.ok) {
            const err = await tgRes.json();
            return res.status(500).json({ detail: err.description || 'Telegram error' });
        }

        // Increment views
        await db.collection('movies').updateOne({ id: movieId }, { $inc: { views: 1 } });
        // Watch history
        await db.collection('watch_history').insertOne({
            user_id: telegram_id, movie_id: movieId, watched_at: Date.now() / 1000
        });

        res.json({ success: true, message: 'Video yuborildi!' });
    } catch (e) {
        console.error(e);
        res.status(500).json({ detail: e.message });
    }
};
