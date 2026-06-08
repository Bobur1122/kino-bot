const { connectToDatabase } = require('../lib/mongodb');

module.exports = async (req, res) => {
    if (req.method === 'OPTIONS') return res.status(200).end();
    try {
        const db = await connectToDatabase();
        const { category, limit = '50' } = req.query;
        const filter = category && category !== 'all' ? { category } : {};
        const movies = await db.collection('movies')
            .find(filter, { projection: { _id: 0, poster_data: 0 } })
            .sort({ id: -1 })
            .limit(parseInt(limit))
            .toArray();
        res.json({ movies, count: movies.length });
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: 'DB error' });
    }
};
