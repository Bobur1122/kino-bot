const { connectToDatabase } = require('../lib/mongodb');

module.exports = async (req, res) => {
    if (req.method === 'OPTIONS') return res.status(200).end();
    try {
        const db = await connectToDatabase();
        const { q = '', limit = '20' } = req.query;
        if (q.length < 1) return res.json({ movies: [] });

        // Record search
        if (q.trim().length >= 2) {
            await db.collection('search_queries').updateOne(
                { query: q.trim().toLowerCase() },
                { $inc: { count: 1 }, $setOnInsert: { query: q.trim().toLowerCase() } },
                { upsert: true }
            );
        }

        const movies = await db.collection('movies')
            .find({
                $or: [
                    { title: { $regex: q, $options: 'i' } },
                    { genre: { $regex: q, $options: 'i' } }
                ]
            }, { projection: { _id: 0, poster_data: 0 } })
            .sort({ views: -1 })
            .limit(parseInt(limit))
            .toArray();
        res.json({ movies });
    } catch (e) {
        res.status(500).json({ error: 'DB error' });
    }
};
