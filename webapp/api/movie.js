const { connectToDatabase } = require('../lib/mongodb');

module.exports = async (req, res) => {
    if (req.method === 'OPTIONS') return res.status(200).end();
    try {
        const db = await connectToDatabase();
        const movieId = parseInt(req.query.id);
        const userId = req.query.user_id ? parseInt(req.query.user_id) : null;

        const movie = await db.collection('movies').findOne({ id: movieId }, { projection: { _id: 0 } });
        if (!movie) return res.status(404).json({ detail: 'Kino topilmadi' });

        // User rating
        if (userId) {
            const rat = await db.collection('ratings').findOne({ user_id: userId, movie_id: movieId });
            movie.user_score = rat ? rat.score : 0;
            movie.likes = await db.collection('ratings').countDocuments({ movie_id: movieId, score: 1 });
            movie.dislikes = await db.collection('ratings').countDocuments({ movie_id: movieId, score: -1 });
        }

        // Recommendations
        const recs = await db.collection('movies')
            .find({
                id: { $ne: movieId },
                $or: [
                    { category: movie.category },
                    { genre: { $regex: movie.genre || '', $options: 'i' } }
                ]
            }, { projection: { _id: 0, poster_data: 0 } })
            .sort({ views: -1 })
            .limit(6)
            .toArray();
        movie.recommendations = recs;

        res.json(movie);
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: 'DB error' });
    }
};
