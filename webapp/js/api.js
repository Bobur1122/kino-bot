/**
 * KinoUz Mini App - API wrapper
 */

const KinoAPI = (() => {
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const metaBaseUrl = document.querySelector('meta[name="kino-api-base-url"]')?.content?.trim();
    const configBaseUrl = window.KINO_APP_CONFIG?.apiBaseUrl || window.__KINO_API_BASE_URL__;
    let BASE_URL = (configBaseUrl || metaBaseUrl || (isLocal ? 'http://localhost:8000' : window.location.origin)).replace(/\/$/, '');

    async function request(endpoint, options = {}) {
        const url = `${BASE_URL}${endpoint}`;
        const res = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }

        return res.json();
    }

    return {
        getMovies(category = null, limit = 50) {
            let url = `/api/movies?limit=${limit}`;
            if (category && category !== 'all') url += `&category=${category}`;
            return request(url);
        },

        getPopular(limit = 10) {
            return request(`/api/movies/popular?limit=${limit}`);
        },

        getRecent(limit = 10) {
            return request(`/api/movies/recent?limit=${limit}`);
        },

        getFeatured() {
            return request('/api/featured');
        },

        searchMovies(query, limit = 20) {
            return request(`/api/movies/search?q=${encodeURIComponent(query)}&limit=${limit}`);
        },

        getMovie(id, userId = null) {
            let url = `/api/movies/${id}`;
            if (userId) url += `?user_id=${userId}`;
            return request(url);
        },

        watchMovie(movieId, telegramId) {
            return request(`/api/movies/${movieId}/watch`, {
                method: 'POST',
                body: JSON.stringify({ telegram_id: telegramId })
            });
        },

        rateMovie(movieId, userId, score) {
            return request(`/api/movies/${movieId}/rate`, {
                method: 'POST',
                body: JSON.stringify({ telegram_id: userId, movie_id: movieId, score })
            });
        },

        getPosterUrl(movieId) {
            return request(`/api/poster/${movieId}`);
        },

        setBaseUrl(url) {
            BASE_URL = String(url || '').replace(/\/$/, '');
        },

        getBaseUrl() {
            return BASE_URL;
        }
    };
})();
