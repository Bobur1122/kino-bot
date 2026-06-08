const { connectToDatabase } = require('../lib/mongodb');

module.exports = async (req, res) => {
    if (req.method === 'OPTIONS') return res.status(200).end();
    try {
        const db = await connectToDatabase();
        const { limit = '10' } = req.query;
        const movies = await db.collection('movies')
            .find({}, { projection: { _id: 0, poster_data: 0 } })
            .sort({ views: -1 })
            .limit(parseInt(limit))
            .toArray();
        res.json({ movies });
    } catch (e) {
        res.status(500).json({ error: 'DB error' });
    }
};
