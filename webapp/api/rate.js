const { connectToDatabase } = require('../lib/mongodb');

module.exports = async (req, res) => {
    if (req.method === 'OPTIONS') return res.status(200).end();
    if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

    try {
        const db = await connectToDatabase();
        const movieId = parseInt(req.query.id);
        const { telegram_id, score } = req.body;

        if (![1, -1, 0].includes(score)) return res.status(400).json({ detail: "Noto'g'ri baho" });

        await db.collection('ratings').updateOne(
            { user_id: telegram_id, movie_id: movieId },
            { $set: { score, created_at: Date.now() / 1000 } },
            { upsert: true }
        );

        const likes = await db.collection('ratings').countDocuments({ movie_id: movieId, score: 1 });
        const dislikes = await db.collection('ratings').countDocuments({ movie_id: movieId, score: -1 });
        const pipeline = [
            { $match: { movie_id: movieId } },
            { $group: { _id: null, avg: { $avg: '$score' }, cnt: { $sum: 1 } } }
        ];
        const aggResult = await db.collection('ratings').aggregate(pipeline).toArray();
        const avg = aggResult.length ? Math.round(aggResult[0].avg * 10) / 10 : 0;

        res.json({ success: true, rating: avg, votes: aggResult.length ? aggResult[0].cnt : 0, likes, dislikes });
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: 'DB error' });
    }
};
