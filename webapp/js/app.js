/**
 * KinoUz Mini App - main logic
 */

document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram?.WebApp;
    let telegramUserId = 999999;

    if (tg) {
        tg.ready();
        tg.expand();
        tg.setHeaderColor('#000000');
        tg.setBackgroundColor('#000000');
        if (tg.initDataUnsafe?.user?.id) {
            telegramUserId = tg.initDataUnsafe.user.id;
        }
    }

    const $ = (selector) => document.querySelector(selector);
    const $$ = (selector) => document.querySelectorAll(selector);

    const loadingScreen = $('#loading-screen');
    const app = $('#app');
    const pages = $$('.page');
    const navItems = $$('.nav-item');
    const searchToggle = $('#search-toggle');
    const toast = $('#notification-toast');
    const movieModal = $('#movie-modal');
    const modalClose = $('#modal-close');
    const watchBtn = $('#modal-watch');
    const trailerBtn = $('#modal-trailer');
    const likeBtn = $('#btn-like');
    const dislikeBtn = $('#btn-dislike');
    const likesCount = $('#likes-count');
    const dislikesCount = $('#dislikes-count');
    const searchPageInput = $('#search-page-input');
    const tabBtns = $$('.tab-btn');
    const heroPosters = $('#hero-posters');

    let currentPage = 'home';
    let allMovies = [];
    let currentMovie = null;
    let currentHeroMovie = null;
    let posterCache = {};

    async function init() {
        showToast('Kinolar yuklanmoqda...');
        try {
            await loadAllData();
        } catch (e) {
            console.error('Init error:', e);
            showToast('Ma\'lumotlarni yuklashda xatolik yuz berdi.', 'error');
        }

        setTimeout(() => {
            if (loadingScreen) loadingScreen.classList.add('hidden');
            app.style.display = '';
        }, 800);
    }

    async function loadAllData() {
        try {
            const data = await KinoAPI.getMovies(null, 150);
            allMovies = data.movies || [];
        } catch (e) {
            console.error(e);
            allMovies = [];
        }

        await renderFeatured();
        renderHome();
        renderCategories('all');
    }

    function showToast(message, type = 'info') {
        if (!toast) return;
        toast.textContent = message;
        toast.className = `notification-toast active ${type}`;
        setTimeout(() => {
            toast.classList.remove('active');
        }, 3000);
    }

    async function getPosterSrc(movie) {
        if (!movie?.poster_file_id) return null;
        if (posterCache[movie.id]) return posterCache[movie.id];

        try {
            const data = await KinoAPI.getPosterUrl(movie.id);
            posterCache[movie.id] = data.url;
            return data.url;
        } catch {
            return null;
        }
    }

    function getCategoryEmoji(cat) {
        return { kino: '🎬', serial: '📺', multfilm: '🎞️' }[cat] || '🎬';
    }

    function getCategoryName(cat) {
        return { kino: 'Kino', serial: 'Serial', multfilm: 'Multfilm' }[cat] || cat;
    }

    function createScrollCard(movie) {
        const emoji = getCategoryEmoji(movie.category);
        const card = document.createElement('div');
        card.className = 'card fade-in-up';
        card.onclick = () => openMovieModal(movie.id);

        const posterHtml = movie.poster_file_id
            ? `<img src="" alt="${movie.title}" data-movie-id="${movie.id}" class="lazy-poster" loading="lazy">`
            : `<div class="card-placeholder">${emoji}<span>${movie.title}</span></div>`;

        card.innerHTML = `
            <div class="card-poster">
                ${posterHtml}
                <div class="card-views">👁 ${movie.views || 0}</div>
                ${movie.rating ? `<div class="card-rating">⭐ ${movie.rating}</div>` : ''}
            </div>
            <div class="card-title">${movie.title}</div>
            <div class="card-sub">${movie.year || ''} · ${getCategoryName(movie.category)}</div>
        `;

        if (movie.poster_file_id) {
            loadPosterForCard(card, movie);
        }
        return card;
    }

    function createGridCard(movie) {
        const emoji = getCategoryEmoji(movie.category);
        const card = document.createElement('div');
        card.className = 'grid-card fade-in-up';
        card.onclick = () => openMovieModal(movie.id);

        const posterHtml = movie.poster_file_id
            ? `<img src="" alt="${movie.title}" data-movie-id="${movie.id}" class="lazy-poster" loading="lazy">`
            : `<div class="card-placeholder">${emoji}<span>${movie.title}</span></div>`;

        card.innerHTML = `
            <div class="card-poster">
                ${posterHtml}
                <div class="card-views">👁 ${movie.views || 0}</div>
                ${movie.rating ? `<div class="card-rating">⭐ ${movie.rating}</div>` : ''}
            </div>
            <div class="card-title">${movie.title}</div>
            <div class="card-sub">${movie.year || ''} · ${getCategoryName(movie.category)}</div>
        `;

        if (movie.poster_file_id) {
            loadPosterForCard(card, movie);
        }
        return card;
    }

    async function loadPosterForCard(card, movie) {
        const img = card.querySelector('.lazy-poster');
        if (!img) return;

        try {
            const url = await getPosterSrc(movie);
            if (url) {
                img.src = url;
            } else {
                const emoji = getCategoryEmoji(movie.category);
                img.parentElement.innerHTML = `<div class="card-placeholder">${emoji}<span>${movie.title}</span></div>`;
            }
        } catch {
            const emoji = getCategoryEmoji(movie.category);
            img.parentElement.innerHTML = `<div class="card-placeholder">${emoji}<span>${movie.title}</span></div>`;
        }
    }

    async function renderFeatured() {
        const heroBg = $('#hero-bg');
        const heroTitle = $('#hero-title');
        const heroMeta = $('#hero-meta');
        const heroPlay = $('#hero-play');
        const heroInfo = $('#hero-info');
        const heroTags = $('#hero-tags');

        let recentMovies = [];
        try {
            const data = await KinoAPI.getRecent(5);
            recentMovies = data.movies || [];
        } catch (e) {
            console.error(e);
        }

        if (recentMovies.length === 0) {
            try {
                const fallback = await KinoAPI.getFeatured();
                recentMovies = fallback && fallback.id ? [fallback] : [];
            } catch (e) {
                console.error(e);
            }
        }

        renderHeroPosters(recentMovies);

        const selected = recentMovies[0] || null;
        if (!selected) {
            currentHeroMovie = null;
            heroTitle.textContent = 'KinoUz Premyeralari';
            heroMeta.textContent = 'Premium tomosha platformasi';
            heroTags.innerHTML = '';
            heroBg.style.backgroundImage = '';
            heroPlay.onclick = () => {};
            heroInfo.onclick = () => {};
            return;
        }

        updateHeroMovie(selected);
    }

    function renderHeroPosters(movies) {
        if (!heroPosters) return;
        heroPosters.innerHTML = '';

        movies.slice(0, 5).forEach((movie, index) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = `hero-poster-item${index === 0 ? ' active' : ''}`;
            button.dataset.movieId = movie.id;

            const posterHtml = movie.poster_file_id
                ? `<img src="" alt="${movie.title}" data-movie-id="${movie.id}" class="lazy-poster" loading="lazy">`
                : `<div class="hero-poster-placeholder">${getCategoryEmoji(movie.category)}<span>${movie.title}</span></div>`;

            button.innerHTML = posterHtml;
            button.onclick = () => updateHeroMovie(movie, button);
            heroPosters.appendChild(button);

            if (movie.poster_file_id) {
                loadHeroPoster(button, movie);
            }
        });
    }

    async function loadHeroPoster(button, movie) {
        const img = button.querySelector('.lazy-poster');
        if (!img) return;

        try {
            const url = await getPosterSrc(movie);
            if (url) {
                img.src = url;
            } else {
                img.parentElement.innerHTML = `<div class="hero-poster-placeholder">${getCategoryEmoji(movie.category)}<span>${movie.title}</span></div>`;
            }
        } catch {
            img.parentElement.innerHTML = `<div class="hero-poster-placeholder">${getCategoryEmoji(movie.category)}<span>${movie.title}</span></div>`;
        }
    }

    async function updateHeroMovie(movie, button = null) {
        currentHeroMovie = movie;

        const heroBg = $('#hero-bg');
        const heroTitle = $('#hero-title');
        const heroMeta = $('#hero-meta');
        const heroTags = $('#hero-tags');
        const heroPlay = $('#hero-play');
        const heroInfo = $('#hero-info');

        if (heroPosters) {
            heroPosters.querySelectorAll('.hero-poster-item').forEach((item) => {
                item.classList.toggle('active', Number(item.dataset.movieId) === Number(movie.id));
            });
        }
        if (button) button.classList.add('active');

        heroTitle.textContent = movie.title || 'Noma\'lum';
        heroMeta.textContent = [
            movie.year || '',
            getCategoryName(movie.category),
            movie.language || '',
            `👁 ${movie.views || 0} ko'rish`
        ].filter(Boolean).join('  |  ');

        if (movie.genre) {
            heroTags.innerHTML = movie.genre.split(',').slice(0, 3).map((g) => `<span class="tag">${g.trim()}</span>`).join('');
        } else {
            heroTags.innerHTML = '';
        }

        heroPlay.onclick = () => openMovieModal(movie.id);
        heroInfo.onclick = () => openMovieModal(movie.id);

        if (movie.poster_file_id) {
            const url = await getPosterSrc(movie);
            if (url) heroBg.style.backgroundImage = `url(${url})`;
        } else {
            heroBg.style.backgroundImage = '';
        }
    }

    function renderHome() {
        const popular = [...allMovies].sort((a, b) => (b.views || 0) - (a.views || 0)).slice(0, 10);
        renderScrollSection('popular-cards', popular);

        const latest = [...allMovies].slice(0, 10);
        renderScrollSection('new-cards', latest);

        const kinos = allMovies.filter((m) => m.category === 'kino').slice(0, 10);
        const serials = allMovies.filter((m) => m.category === 'serial').slice(0, 10);
        const multfilms = allMovies.filter((m) => m.category === 'multfilm').slice(0, 10);

        renderScrollSection('kino-preview-cards', kinos);
        renderScrollSection('serial-preview-cards', serials);
        renderScrollSection('multfilm-preview-cards', multfilms);

        toggleSection('section-popular', popular.length);
        toggleSection('section-new', latest.length);
        toggleSection('section-kino-preview', kinos.length);
        toggleSection('section-serial-preview', serials.length);
        toggleSection('section-multfilm-preview', multfilms.length);
    }

    function toggleSection(id, show) {
        const el = document.getElementById(id);
        if (el) el.style.display = show ? '' : 'none';
    }

    function renderScrollSection(containerId, movies) {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.innerHTML = '';
        movies.forEach((movie) => container.appendChild(createScrollCard(movie)));
    }

    function renderCategories(category = 'all') {
        const grid = $('#categories-grid');
        const empty = $('#categories-empty');
        if (!grid) return;

        let filtered = allMovies;
        if (category !== 'all') {
            filtered = allMovies.filter((movie) => movie.category === category);
        }

        grid.innerHTML = '';
        if (filtered.length === 0) {
            empty.style.display = '';
            return;
        }

        empty.style.display = 'none';
        filtered.forEach((movie) => grid.appendChild(createGridCard(movie)));
    }

    async function openMovieModal(movieId) {
        movieModal.classList.add('active');
        document.body.style.overflow = 'hidden';

        const poster = $('#modal-poster');
        const title = $('#modal-title');
        const desc = $('#modal-desc');
        const badge = $('#modal-badge');
        const imdb = $('#modal-rating-imdb');
        const myear = $('#meta-year');
        const mduration = $('#meta-duration');
        const mcountry = $('#meta-country');
        const mlanguage = $('#meta-language');
        const mdub = $('#meta-dub');
        const mgenre = $('#meta-genre');

        poster.style.backgroundImage = '';
        title.textContent = 'Yuklanmoqda...';
        desc.textContent = '';
        imdb.textContent = '⭐ -';
        myear.textContent = '-';
        mduration.textContent = '-';
        mcountry.textContent = '-';
        mlanguage.textContent = '-';
        mdub.textContent = '-';
        mgenre.textContent = '-';
        trailerBtn.style.display = 'none';

        try {
            const movie = await KinoAPI.getMovie(movieId, telegramUserId);
            currentMovie = movie;

            title.textContent = movie.title;
            badge.textContent = getCategoryName(movie.category).toUpperCase();
            imdb.textContent = movie.rating ? `⭐ ${movie.rating}` : '⭐ -';
            desc.textContent = movie.description || 'Tavsif mavjud emas.';

            myear.textContent = movie.year || '-';
            mduration.textContent = movie.duration || '-';
            mcountry.textContent = movie.country || '-';
            mlanguage.textContent = movie.language || '-';
            mdub.textContent = movie.dub_sub || '-';
            mgenre.textContent = movie.genre || '-';

            likesCount.textContent = movie.likes || 0;
            dislikesCount.textContent = movie.dislikes || 0;
            updateRatingButtonsStyle(movie.user_score || 0);

            if (movie.poster_file_id) {
                const url = await getPosterSrc(movie);
                if (url) poster.style.backgroundImage = `url(${url})`;
            }

            if (movie.trailer) {
                trailerBtn.style.display = '';
                trailerBtn.onclick = () => {
                    if (tg) tg.openLink(movie.trailer);
                    else window.open(movie.trailer, '_blank');
                };
            }

            renderRecommendations(movie.recommendations || []);

            watchBtn.onclick = async () => {
                try {
                    await KinoAPI.watchMovie(movie.id, telegramUserId);
                    showToast('Video botdan yuborildi.', 'success');
                    await loadAllData();
                } catch (err) {
                    showToast(`Xatolik: ${err.message}`, 'error');
                }
            };
        } catch (e) {
            title.textContent = 'Xatolik yuz berdi';
            desc.textContent = 'Kino tafsilotlarini yuklab bo\'lmadi.';
        }
    }

    function closeMovieModal() {
        movieModal.classList.remove('active');
        document.body.style.overflow = '';
        currentMovie = null;
    }

    likeBtn?.addEventListener('click', () => submitRate(1));
    dislikeBtn?.addEventListener('click', () => submitRate(-1));

    async function submitRate(score) {
        if (!currentMovie) return;

        let finalScore = score;
        if (currentMovie.user_score === score) {
            finalScore = 0;
        }

        try {
            await KinoAPI.rateMovie(currentMovie.id, telegramUserId, finalScore);
            currentMovie.user_score = finalScore;

            if (finalScore === 1) {
                showToast('Film sizga yoqdi!', 'success');
            } else if (finalScore === -1) {
                showToast('Film sizga yoqmadi.', 'info');
            }

            const updatedMovie = await KinoAPI.getMovie(currentMovie.id, telegramUserId);
            likesCount.textContent = updatedMovie.likes || 0;
            dislikesCount.textContent = updatedMovie.dislikes || 0;
            updateRatingButtonsStyle(finalScore);
        } catch (e) {
            showToast('Ovoz berishda xatolik.', 'error');
        }
    }

    function updateRatingButtonsStyle(score) {
        if (!likeBtn || !dislikeBtn) return;
        likeBtn.classList.toggle('active', score === 1);
        dislikeBtn.classList.toggle('active', score === -1);
    }

    function renderRecommendations(recs) {
        const container = $('#modal-recommendations');
        const wrapper = $('#modal-recommendations-wrapper');
        if (!container) return;

        container.innerHTML = '';
        if (recs.length === 0) {
            if (wrapper) wrapper.style.display = 'none';
            return;
        }

        if (wrapper) wrapper.style.display = '';
        recs.slice(0, 6).forEach((movie) => {
            const card = document.createElement('div');
            card.className = 'rec-card';
            card.onclick = () => openMovieModal(movie.id);

            const posterHtml = movie.poster_file_id
                ? `<img src="" alt="${movie.title}" class="lazy-poster" data-movie-id="${movie.id}">`
                : `<div class="rec-placeholder">🎬</div>`;

            card.innerHTML = `
                ${posterHtml}
                <div class="rec-card-title">${movie.title}</div>
            `;

            if (movie.poster_file_id) {
                loadPosterForCard(card, movie);
            }
            container.appendChild(card);
        });
    }

    function navigateTo(page) {
        currentPage = page;

        pages.forEach((p) => p.classList.remove('active'));
        const target = $(`#page-${page}`);
        if (target) target.classList.add('active');

        navItems.forEach((item) => {
            item.classList.toggle('active', item.dataset.page === page);
        });

        if (page === 'search') {
            setTimeout(() => searchPageInput?.focus(), 300);
        }

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    navItems.forEach((item) => {
        item.addEventListener('click', () => navigateTo(item.dataset.page));
    });

    tabBtns.forEach((btn) => {
        btn.addEventListener('click', () => {
            tabBtns.forEach((button) => button.classList.remove('active'));
            btn.classList.add('active');
            renderCategories(btn.dataset.category);
        });
    });

    let searchTimeout = null;
    searchPageInput?.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        const q = searchPageInput.value.trim();
        const grid = $('#search-grid');
        const empty = $('#search-empty');

        if (q.length < 1) {
            grid.innerHTML = '';
            empty.style.display = '';
            empty.querySelector('p').textContent = 'Kino yoki janr nomini yozing';
            return;
        }

        searchTimeout = setTimeout(async () => {
            try {
                const data = await KinoAPI.searchMovies(q);
                const movies = data.movies || [];
                grid.innerHTML = '';

                if (movies.length === 0) {
                    empty.style.display = '';
                    empty.querySelector('p').textContent = `"${q}" bo'yicha hech narsa topilmadi`;
                } else {
                    empty.style.display = 'none';
                    movies.forEach((movie) => grid.appendChild(createGridCard(movie)));
                }
            } catch (e) {
                console.error(e);
            }
        }, 400);
    });

    searchToggle?.addEventListener('click', () => {
        navigateTo('search');
    });

    modalClose?.addEventListener('click', closeMovieModal);
    movieModal?.addEventListener('click', (e) => {
        if (e.target === movieModal) closeMovieModal();
    });

    if (tg) {
        tg.BackButton.onClick(() => {
            if (movieModal.classList.contains('active')) {
                closeMovieModal();
            } else if (currentPage !== 'home') {
                navigateTo('home');
            } else {
                tg.close();
            }
        });

        const observer = new MutationObserver(() => {
            if (movieModal.classList.contains('active') || currentPage !== 'home') {
                tg.BackButton.show();
            } else {
                tg.BackButton.hide();
            }
        });
        observer.observe(movieModal, { attributes: true, attributeFilter: ['class'] });
    }

    init();
});
