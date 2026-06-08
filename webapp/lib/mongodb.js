const { MongoClient } = require('mongodb');

let cachedDb = null;

async function connectToDatabase() {
    if (cachedDb) return cachedDb;
    const client = new MongoClient(process.env.MONGO_URI);
    await client.connect();
    cachedDb = client.db('kinodb');
    return cachedDb;
}

module.exports = { connectToDatabase };
