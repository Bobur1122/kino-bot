const { connectToDatabase } = require('../lib/mongodb');

module.exports = async (req, res) => {
    if (req.method === 'OPTIONS') return res.status(200).end();
    try {
        const db = await connectToDatabase();
        const movies = await db.collection('movies')
            .find({}, { projection: { _id: 0, poster_data: 0 } })
            .sort({ views: -1 })
            .limit(1)
            .toArray();
        if (movies.length > 0) return res.json(movies[0]);
        const recent = await db.collection('movies')
            .find({}, { projection: { _id: 0, poster_data: 0 } })
            .sort({ created_at: -1 })
            .limit(1)
            .toArray();
        res.json(recent[0] || {});
    } catch (e) {
        res.status(500).json({ error: 'DB error' });
    }
};
