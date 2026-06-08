const { connectToDatabase } = require('../lib/mongodb');

module.exports = async (req, res) => {
    if (req.method === 'OPTIONS') return res.status(200).end();
    try {
        const db = await connectToDatabase();
        const movieId = parseInt(req.query.id);
        const movie = await db.collection('movies').findOne({ id: movieId });
        if (!movie || !movie.poster_file_id) return res.status(404).json({ detail: 'Poster topilmadi' });

        const BOT_TOKEN = process.env.BOT_TOKEN;
        if (!BOT_TOKEN) return res.status(500).json({ detail: 'Bot token not set' });

        const fileRes = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/getFile?file_id=${movie.poster_file_id}`);
        const fileData = await fileRes.json();
        if (!fileData.ok) return res.status(500).json({ detail: 'File not found' });

        const url = `https://api.telegram.org/file/bot${BOT_TOKEN}/${fileData.result.file_path}`;
        res.json({ url });
    } catch (e) {
        console.error(e);
        res.status(500).json({ error: 'Error' });
    }
};
