/**
 * MovieScope — Client-side JavaScript
 * Handles SPA navigation, real-time REST API consumption, filtering,
 * modal dialogs, recommendations, and analytics chart updates.
 */

// State Object
const AppState = {
  currentSection: 'dashboard',
  movies: {
    search: '',
    genre: 'all',
    minRating: 0,
    minVotes: 0,
    sort: 'rating',
    order: 'desc',
    page: 1,
    pageSize: 12,
    totalPages: 1,
    totalCount: 0,
  },
  genresList: [],
  allMoviesCatalog: [],
  selectedTargetMovieId: null,
};

// DOM References
const DOM = {
  sidebar: document.getElementById('sidebar'),
  mobileToggleBtn: document.getElementById('mobileToggleBtn'),
  mobileCloseBtn: document.getElementById('mobileCloseBtn'),
  navItems: document.querySelectorAll('.nav-item'),
  pageSections: document.querySelectorAll('.page-section'),
  breadcrumbSection: document.getElementById('breadcrumbSection'),

  // Topbar
  globalSearchInput: document.getElementById('globalSearchInput'),
  refreshDataBtn: document.getElementById('refreshDataBtn'),
  exportMenuBtn: document.getElementById('exportMenuBtn'),
  exportMenu: document.getElementById('exportMenu'),
  sidebarDatasetName: document.getElementById('sidebarDatasetName'),
  topDataStatusText: document.getElementById('topDataStatusText'),

  // Dashboard
  kpiTotalMovies: document.getElementById('kpiTotalMovies'),
  kpiTotalRatings: document.getElementById('kpiTotalRatings'),
  kpiUniqueUsers: document.getElementById('kpiUniqueUsers'),
  kpiTotalGenres: document.getElementById('kpiTotalGenres'),
  kpiOverallRating: document.getElementById('kpiOverallRating'),
  kpiHighestRatedTitle: document.getElementById('kpiHighestRatedTitle'),
  kpiHighestRatedScore: document.getElementById('kpiHighestRatedScore'),
  dashboardTopRatedList: document.getElementById('dashboardTopRatedList'),
  dashboardPopularList: document.getElementById('dashboardPopularList'),
  heroExploreBtn: document.getElementById('heroExploreBtn'),
  heroRecommendBtn: document.getElementById('heroRecommendBtn'),

  // Explorer
  filterSearch: document.getElementById('filterSearch'),
  filterGenre: document.getElementById('filterGenre'),
  filterMinRating: document.getElementById('filterMinRating'),
  minRatingLabel: document.getElementById('minRatingLabel'),
  filterMinVotes: document.getElementById('filterMinVotes'),
  filterSort: document.getElementById('filterSort'),
  clearFiltersBtn: document.getElementById('clearFiltersBtn'),
  explorerResultsCount: document.getElementById('explorerResultsCount'),
  moviesGrid: document.getElementById('moviesGrid'),
  prevPageBtn: document.getElementById('prevPageBtn'),
  nextPageBtn: document.getElementById('nextPageBtn'),
  paginationInfo: document.getElementById('paginationInfo'),

  // Recommendations
  recMovieSelect: document.getElementById('recMovieSelect'),
  recLimitSelect: document.getElementById('recLimitSelect'),
  generateRecsBtn: document.getElementById('generateRecsBtn'),
  targetMoviePreview: document.getElementById('targetMoviePreview'),
  targetTitle: document.getElementById('targetTitle'),
  targetGenres: document.getElementById('targetGenres'),
  targetRating: document.getElementById('targetRating'),
  targetVotes: document.getElementById('targetVotes'),
  recommendationsResults: document.getElementById('recommendationsResults'),

  // Genre Analytics
  genreTableBody: document.getElementById('genreTableBody'),
  genreChartImg: document.getElementById('genreChartImg'),

  // Rating Insights Charts
  ratingDistChartImg: document.getElementById('ratingDistChartImg'),
  popularityChartImg: document.getElementById('popularityChartImg'),
  heatmapChartImg: document.getElementById('heatmapChartImg'),
  trendsChartImg: document.getElementById('trendsChartImg'),

  // Data Quality
  qSource: document.getElementById('qSource'),
  qMoviesRetained: document.getElementById('qMoviesRetained'),
  qMoviesDups: document.getElementById('qMoviesDups'),
  qRatingsRetained: document.getElementById('qRatingsRetained'),
  qRatingsDups: document.getElementById('qRatingsDups'),
  qRatingsInvalid: document.getElementById('qRatingsInvalid'),
  qualityLogList: document.getElementById('qualityLogList'),
  resetSampleDataBtn: document.getElementById('resetSampleDataBtn'),
  uploadDatasetForm: document.getElementById('uploadDatasetForm'),

  // Modal
  movieDetailModal: document.getElementById('movieDetailModal'),
  modalCloseBtn: document.getElementById('modalCloseBtn'),
  modalMovieTitle: document.getElementById('modalMovieTitle'),
  modalMovieMeta: document.getElementById('modalMovieMeta'),
  modalAvgRating: document.getElementById('modalAvgRating'),
  modalReviewCount: document.getElementById('modalReviewCount'),
  modalReleaseYear: document.getElementById('modalReleaseYear'),
  modalRatingBars: document.getElementById('modalRatingBars'),
  modalFindSimilarBtn: document.getElementById('modalFindSimilarBtn'),

  // Toast
  toastPopup: document.getElementById('toastPopup'),
  toastText: document.getElementById('toastText'),
};

let searchDebounceTimer = null;
let toastTimeout = null;
let currentModalMovieId = null;

// --------------------------------------------------------------------------
// 1. Toast & Utility Helpers
// --------------------------------------------------------------------------
function showToast(message, type = 'success') {
  clearTimeout(toastTimeout);
  DOM.toastText.textContent = message;
  DOM.toastPopup.className = `toast-popup show ${type === 'error' ? 'toast-error' : ''}`;
  toastTimeout = setTimeout(() => {
    DOM.toastPopup.className = 'toast-popup';
  }, 3200);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

async function apiFetch(endpoint, options = {}) {
  try {
    const res = await fetch(endpoint, options);
    if (!res.ok) {
      const errorJson = await res.json().catch(() => ({}));
      throw new Error(errorJson.message || `Request failed with status ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

// --------------------------------------------------------------------------
// 2. Navigation & Routing (SPA)
// --------------------------------------------------------------------------
function navigateToSection(sectionId) {
  AppState.currentSection = sectionId;

  // Update URL hash without scroll jumps
  history.replaceState(null, '', `#${sectionId}`);

  // Highlight Sidebar Link
  DOM.navItems.forEach((link) => {
    if (link.dataset.section === sectionId) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  // Switch Active Section
  DOM.pageSections.forEach((section) => {
    if (section.id === `section-${sectionId}`) {
      section.classList.add('active');
    } else {
      section.classList.remove('active');
    }
  });

  // Update Breadcrumb
  const titleMap = {
    dashboard: 'Dashboard',
    movies: 'Explore Movies',
    recommendations: 'Recommendations',
    genres: 'Genre Analytics',
    ratings: 'Rating Insights',
    quality: 'Data Quality',
    about: 'About Project',
  };
  DOM.breadcrumbSection.textContent = titleMap[sectionId] || 'Dashboard';

  // Close Mobile Drawer if open
  DOM.sidebar.classList.remove('open');

  // Trigger Section Data Loading if necessary
  if (sectionId === 'movies' && AppState.movies.totalCount === 0) {
    fetchMoviesList();
  } else if (sectionId === 'genres') {
    fetchGenreAnalytics();
  } else if (sectionId === 'quality') {
    fetchDataQualityReport();
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Listen to Hash Changes
window.addEventListener('hashchange', () => {
  const hash = window.location.hash.replace('#', '') || 'dashboard';
  navigateToSection(hash);
});

// Setup Nav Click Listeners
DOM.navItems.forEach((item) => {
  item.addEventListener('click', (e) => {
    e.preventDefault();
    navigateToSection(item.dataset.section);
  });
});

DOM.mobileToggleBtn.addEventListener('click', () => {
  DOM.sidebar.classList.add('open');
});

DOM.mobileCloseBtn.addEventListener('click', () => {
  DOM.sidebar.classList.remove('open');
});

DOM.heroExploreBtn.addEventListener('click', () => navigateToSection('movies'));
DOM.heroRecommendBtn.addEventListener('click', () => navigateToSection('recommendations'));

// --------------------------------------------------------------------------
// 3. Dashboard Data Loading
// --------------------------------------------------------------------------
async function fetchDashboardMetrics() {
  try {
    const res = await apiFetch('/api/dashboard');
    if (res.success && res.data) {
      const d = res.data;
      DOM.kpiTotalMovies.textContent = d.total_movies.toLocaleString();
      DOM.kpiTotalRatings.textContent = d.total_ratings.toLocaleString();
      DOM.kpiUniqueUsers.textContent = d.unique_users.toLocaleString();
      DOM.kpiTotalGenres.textContent = d.num_genres.toLocaleString();
      DOM.kpiOverallRating.textContent = `${d.overall_average_rating.toFixed(2)}★`;

      if (d.highest_rated_movie) {
        DOM.kpiHighestRatedTitle.textContent = d.highest_rated_movie.title;
        DOM.kpiHighestRatedScore.textContent = `${d.highest_rated_movie.average_rating}★ (${d.highest_rated_movie.rating_count} reviews)`;
      } else {
        DOM.kpiHighestRatedTitle.textContent = 'None';
        DOM.kpiHighestRatedScore.textContent = 'No ratings yet';
      }
    }
  } catch (err) {
    showToast('Failed to load dashboard metrics', 'error');
  }
}

async function fetchFeaturedLists() {
  try {
    // Top Rated
    const topRes = await apiFetch('/api/analytics/top-movies?limit=4&min_ratings=5');
    if (topRes.success && topRes.data) {
      DOM.dashboardTopRatedList.innerHTML = topRes.data
        .map(
          (m, idx) => `
          <div class="featured-item" data-id="${m.movieId}">
            <div class="featured-item-left">
              <span class="featured-rank">#${idx + 1}</span>
              <div>
                <div class="featured-item-title">${escapeHtml(m.title)}</div>
                <div class="featured-item-genres">${escapeHtml(m.genres)}</div>
              </div>
            </div>
            <div class="featured-item-right">
              <span class="rating-badge">${m.average_rating.toFixed(1)}★</span>
              <span class="votes-badge">${m.rating_count} reviews</span>
            </div>
          </div>
        `
        )
        .join('');

      DOM.dashboardTopRatedList.querySelectorAll('.featured-item').forEach((item) => {
        item.addEventListener('click', () => openMovieDetailModal(item.dataset.id));
      });
    }

    // Popular
    const popRes = await apiFetch('/api/movies?sort=popularity&order=desc&page_size=4');
    if (popRes.success && popRes.data && popRes.data.items) {
      DOM.dashboardPopularList.innerHTML = popRes.data.items
        .map(
          (m, idx) => `
          <div class="featured-item" data-id="${m.movieId}">
            <div class="featured-item-left">
              <span class="featured-rank">#${idx + 1}</span>
              <div>
                <div class="featured-item-title">${escapeHtml(m.title)}</div>
                <div class="featured-item-genres">${escapeHtml(m.genres)}</div>
              </div>
            </div>
            <div class="featured-item-right">
              <span class="rating-badge">${m.average_rating.toFixed(1)}★</span>
              <span class="votes-badge">${m.rating_count} reviews</span>
            </div>
          </div>
        `
        )
        .join('');

      DOM.dashboardPopularList.querySelectorAll('.featured-item').forEach((item) => {
        item.addEventListener('click', () => openMovieDetailModal(item.dataset.id));
      });
    }
  } catch (err) {
    console.error('Featured lists error:', err);
  }
}

// --------------------------------------------------------------------------
// 4. Movie Explorer & Filtering
// --------------------------------------------------------------------------
async function fetchMoviesList() {
  DOM.moviesGrid.innerHTML = `
    <div class="skeleton-row" style="height: 140px;"></div>
    <div class="skeleton-row" style="height: 140px;"></div>
    <div class="skeleton-row" style="height: 140px;"></div>
  `;

  try {
    const params = new URLSearchParams({
      page: AppState.movies.page,
      page_size: AppState.movies.pageSize,
      sort: AppState.movies.sort,
      order: AppState.movies.order,
    });

    if (AppState.movies.search) params.append('search', AppState.movies.search);
    if (AppState.movies.genre && AppState.movies.genre !== 'all') params.append('genre', AppState.movies.genre);
    if (AppState.movies.minRating > 0) params.append('min_rating', AppState.movies.minRating);
    if (AppState.movies.minVotes > 0) params.append('min_votes', AppState.movies.minVotes);

    const res = await apiFetch(`/api/movies?${params.toString()}`);
    if (res.success && res.data) {
      const data = res.data;
      AppState.movies.totalCount = data.total_count;
      AppState.movies.totalPages = data.total_pages;

      DOM.explorerResultsCount.textContent = `Showing ${data.total_count} ${data.total_count === 1 ? 'movie' : 'movies'}`;
      DOM.paginationInfo.textContent = `Page ${data.page} of ${data.total_pages}`;
      DOM.prevPageBtn.disabled = data.page <= 1;
      DOM.nextPageBtn.disabled = data.page >= data.total_pages;

      renderMoviesGrid(data.items);
    }
  } catch (err) {
    DOM.moviesGrid.innerHTML = `
      <div class="empty-state">
        <i data-lucide="alert-circle" class="empty-icon text-rose"></i>
        <h4>Error loading movies</h4>
        <p>${err.message}</p>
        <button class="btn btn-secondary btn-sm mt-4" onclick="fetchMoviesList()">Retry</button>
      </div>
    `;
    lucide.createIcons();
  }
}

function renderMoviesGrid(movies) {
  if (!movies || movies.length === 0) {
    DOM.moviesGrid.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <i data-lucide="film" class="empty-icon"></i>
        <h4>No movies found</h4>
        <p>Try changing your search query or removing active filters.</p>
        <button class="btn btn-secondary btn-sm mt-4" id="emptyClearBtn">Clear Filters</button>
      </div>
    `;
    const emptyClear = document.getElementById('emptyClearBtn');
    if (emptyClear) emptyClear.addEventListener('click', resetExplorerFilters);
    lucide.createIcons();
    return;
  }

  DOM.moviesGrid.innerHTML = movies
    .map((m) => {
      const genresHtml = (m.genre_list || [])
        .map((g) => `<span class="genre-tag">${escapeHtml(g)}</span>`)
        .join('');

      return `
      <article class="movie-card" data-id="${m.movieId}">
        <div class="movie-card-header">
          <h3 class="movie-card-title">${escapeHtml(m.title)}</h3>
          <div class="movie-card-genres">${genresHtml}</div>
        </div>

        <div class="movie-card-stats">
          <div class="rating-display">
            <svg class="star-icon" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            <span class="rating-num">${m.average_rating.toFixed(1)}</span>
          </div>
          <span class="votes-count">${m.rating_count} reviews</span>
        </div>

        <div class="movie-card-actions">
          <button class="btn-card btn-card-details" data-action="details" data-id="${m.movieId}">
            View Details
          </button>
          <button class="btn-card btn-card-similar" data-action="similar" data-id="${m.movieId}">
            Find Similar
          </button>
        </div>
      </article>
    `;
    })
    .join('');

  // Event handlers
  DOM.moviesGrid.querySelectorAll('.btn-card-details').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      openMovieDetailModal(btn.dataset.id);
    });
  });

  DOM.moviesGrid.querySelectorAll('.btn-card-similar').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      openRecommendationsForMovie(btn.dataset.id);
    });
  });
}

// Explorer Filter Handlers
DOM.filterSearch.addEventListener('input', () => {
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {
    AppState.movies.search = DOM.filterSearch.value.trim();
    AppState.movies.page = 1;
    fetchMoviesList();
  }, 240);
});

DOM.filterGenre.addEventListener('change', () => {
  AppState.movies.genre = DOM.filterGenre.value;
  AppState.movies.page = 1;
  fetchMoviesList();
});

DOM.filterMinRating.addEventListener('input', () => {
  const val = parseFloat(DOM.filterMinRating.value);
  DOM.minRatingLabel.textContent = `${val.toFixed(1)}★`;
  AppState.movies.minRating = val;
  AppState.movies.page = 1;
  fetchMoviesList();
});

DOM.filterMinVotes.addEventListener('input', () => {
  AppState.movies.minVotes = parseInt(DOM.filterMinVotes.value, 10) || 0;
  AppState.movies.page = 1;
  fetchMoviesList();
});

DOM.filterSort.addEventListener('change', () => {
  AppState.movies.sort = DOM.filterSort.value;
  AppState.movies.page = 1;
  fetchMoviesList();
});

DOM.clearFiltersBtn.addEventListener('click', resetExplorerFilters);

function resetExplorerFilters() {
  DOM.filterSearch.value = '';
  DOM.filterGenre.value = 'all';
  DOM.filterMinRating.value = '0';
  DOM.minRatingLabel.textContent = '0.0★';
  DOM.filterMinVotes.value = '';
  DOM.filterSort.value = 'rating';

  AppState.movies.search = '';
  AppState.movies.genre = 'all';
  AppState.movies.minRating = 0;
  AppState.movies.minVotes = 0;
  AppState.movies.sort = 'rating';
  AppState.movies.order = 'desc';
  AppState.movies.page = 1;

  fetchMoviesList();
  showToast('Filters reset to default');
}

DOM.prevPageBtn.addEventListener('click', () => {
  if (AppState.movies.page > 1) {
    AppState.movies.page--;
    fetchMoviesList();
  }
});

DOM.nextPageBtn.addEventListener('click', () => {
  if (AppState.movies.page < AppState.movies.totalPages) {
    AppState.movies.page++;
    fetchMoviesList();
  }
});

// --------------------------------------------------------------------------
// 5. Movie Details Modal
// --------------------------------------------------------------------------
async function openMovieDetailModal(movieId) {
  currentModalMovieId = movieId;
  DOM.movieDetailModal.style.display = 'flex';
  DOM.modalMovieTitle.textContent = 'Loading...';
  DOM.modalMovieMeta.textContent = '';
  DOM.modalAvgRating.textContent = '—';
  DOM.modalReviewCount.textContent = '—';
  DOM.modalReleaseYear.textContent = '—';
  DOM.modalRatingBars.innerHTML = '<div class="skeleton-row" style="height: 60px;"></div>';

  try {
    const [movieRes, distRes] = await Promise.all([
      apiFetch(`/api/movies/${movieId}`),
      apiFetch(`/api/movies/${movieId}/distribution`),
    ]);

    if (movieRes.success && movieRes.data) {
      const m = movieRes.data;
      DOM.modalMovieTitle.textContent = m.title;
      DOM.modalMovieMeta.textContent = m.genres || 'Unknown';
      DOM.modalAvgRating.textContent = `${m.average_rating.toFixed(1)}★`;
      DOM.modalReviewCount.textContent = `${m.rating_count} reviews`;
      DOM.modalReleaseYear.textContent = m.release_year ? `${m.release_year}` : 'N/A';
    }

    if (distRes.success && distRes.data) {
      renderModalDistributionBars(distRes.data);
    }
  } catch (err) {
    DOM.modalMovieTitle.textContent = 'Error loading details';
    showToast('Failed to load movie details', 'error');
  }
}

function renderModalDistributionBars(distData) {
  const counts = distData.counts || {};
  const total = distData.total || 0;
  const ratingKeys = ['5.0', '4.5', '4.0', '3.5', '3.0', '2.5', '2.0', '1.5', '1.0', '0.5'];

  if (total === 0) {
    DOM.modalRatingBars.innerHTML = `<p style="font-size: 12px; color: var(--text-muted);">No ratings recorded for this movie yet.</p>`;
    return;
  }

  DOM.modalRatingBars.innerHTML = ratingKeys
    .map((r) => {
      const count = counts[r] || 0;
      const pct = total > 0 ? ((count / total) * 100).toFixed(0) : 0;
      return `
      <div class="dist-bar-row">
        <span class="dist-bar-label">${r}★</span>
        <div class="dist-bar-track">
          <div class="dist-bar-fill" style="width: ${pct}%;"></div>
        </div>
        <span class="dist-bar-count">${count}</span>
      </div>
    `;
    })
    .join('');
}

function closeMovieDetailModal() {
  DOM.movieDetailModal.style.display = 'none';
  currentModalMovieId = null;
}

DOM.modalCloseBtn.addEventListener('click', closeMovieDetailModal);
DOM.movieDetailModal.addEventListener('click', (e) => {
  if (e.target === DOM.movieDetailModal) closeMovieDetailModal();
});
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && DOM.movieDetailModal.style.display !== 'none') {
    closeMovieDetailModal();
  }
});

DOM.modalFindSimilarBtn.addEventListener('click', () => {
  if (currentModalMovieId) {
    closeMovieDetailModal();
    openRecommendationsForMovie(currentModalMovieId);
  }
});

// --------------------------------------------------------------------------
// 6. Recommendation Engine Interaction
// --------------------------------------------------------------------------
function openRecommendationsForMovie(movieId) {
  navigateToSection('recommendations');
  DOM.recMovieSelect.value = movieId;
  DOM.recMovieSelect.dispatchEvent(new Event('change'));
  generateRecommendations();
}

async function populateMovieSelector() {
  try {
    const res = await apiFetch('/api/movies?page_size=200&sort=title&order=asc');
    if (res.success && res.data && res.data.items) {
      AppState.allMoviesCatalog = res.data.items;
      DOM.recMovieSelect.innerHTML = `
        <option value="" disabled selected>Choose a movie from catalog...</option>
        ${AppState.allMoviesCatalog
          .map((m) => `<option value="${m.movieId}">${escapeHtml(m.title)}</option>`)
          .join('')}
      `;
    }
  } catch (err) {
    console.error('Populate movie selector error:', err);
  }
}

DOM.recMovieSelect.addEventListener('change', () => {
  const mid = parseInt(DOM.recMovieSelect.value, 10);
  const movie = AppState.allMoviesCatalog.find((m) => m.movieId === mid);
  if (movie) {
    DOM.targetTitle.textContent = movie.title;
    DOM.targetGenres.textContent = movie.genres || 'Unknown';
    DOM.targetRating.textContent = `${movie.average_rating.toFixed(1)}★`;
    DOM.targetVotes.textContent = `${movie.rating_count} reviews`;
    DOM.targetMoviePreview.style.display = 'block';
  }
});

DOM.generateRecsBtn.addEventListener('click', generateRecommendations);

async function generateRecommendations() {
  const movieId = DOM.recMovieSelect.value;
  const limit = DOM.recLimitSelect.value || 5;

  if (!movieId) {
    showToast('Please select a target movie first', 'error');
    return;
  }

  DOM.recommendationsResults.innerHTML = `
    <div class="skeleton-row" style="height: 90px; margin-bottom: 12px;"></div>
    <div class="skeleton-row" style="height: 90px; margin-bottom: 12px;"></div>
    <div class="skeleton-row" style="height: 90px;"></div>
  `;

  try {
    const res = await apiFetch(`/api/recommendations/${movieId}?limit=${limit}`);
    if (res.success && res.data) {
      renderRecommendations(res.data);
      showToast(`Computed ${res.data.length} recommendations`);
    }
  } catch (err) {
    DOM.recommendationsResults.innerHTML = `
      <div class="empty-state">
        <i data-lucide="alert-triangle" class="empty-icon text-rose"></i>
        <h4>Failed to generate recommendations</h4>
        <p>${err.message}</p>
      </div>
    `;
    lucide.createIcons();
  }
}

function renderRecommendations(items) {
  if (!items || items.length === 0) {
    DOM.recommendationsResults.innerHTML = `
      <div class="empty-state">
        <i data-lucide="film" class="empty-icon"></i>
        <h4>No similar matches found</h4>
        <p>Try selecting another film with richer genre classifications.</p>
      </div>
    `;
    lucide.createIcons();
    return;
  }

  DOM.recommendationsResults.innerHTML = items
    .map((r, idx) => {
      const genresHtml = (r.genre_list || [])
        .map((g) => `<span class="genre-tag">${escapeHtml(g)}</span>`)
        .join('');

      const similarityPct = (r.similarity_score * 100).toFixed(0);

      return `
      <article class="rec-card">
        <div class="rec-card-left">
          <h4 class="rec-card-title">#${idx + 1} ${escapeHtml(r.title)}</h4>
          <div class="rec-card-genres">${genresHtml}</div>
          <div class="rec-card-explanation">
            <strong>Why Recommended:</strong> ${escapeHtml(r.explanation)}
          </div>
        </div>

        <div class="rec-card-right">
          <span class="rec-similarity-badge" title="Genre Cosine Similarity">
            ${similarityPct}% Match
          </span>
          <span class="rec-wr-badge">Weighted: ${r.weighted_rating.toFixed(2)}★ (${r.rating_count} reviews)</span>
          <button class="btn btn-secondary btn-sm mt-2" onclick="openMovieDetailModal(${r.movieId})">
            Details
          </button>
        </div>
      </article>
    `;
    })
    .join('');
}

// --------------------------------------------------------------------------
// 7. Genre Analytics & Ratings Charts
// --------------------------------------------------------------------------
async function fetchGenreAnalytics() {
  try {
    const res = await apiFetch('/api/analytics/genres');
    if (res.success && res.data) {
      DOM.genreTableBody.innerHTML = res.data
        .map(
          (g) => `
        <tr>
          <td><strong>${escapeHtml(g.genre)}</strong></td>
          <td>${g.movie_count} films</td>
          <td><span class="rating-badge">${g.average_rating.toFixed(2)}★</span></td>
          <td>${g.total_ratings.toLocaleString()} reviews</td>
        </tr>
      `
        )
        .join('');

      // Populate genres dropdown in explorer if not already populated
      if (DOM.filterGenre.options.length <= 1) {
        res.data.forEach((g) => {
          const opt = document.createElement('option');
          opt.value = g.genre;
          opt.textContent = `${g.genre} (${g.movie_count})`;
          DOM.filterGenre.appendChild(opt);
        });
      }
    }
  } catch (err) {
    console.error('Fetch genre analytics error:', err);
  }
}

function refreshChartsImages() {
  const ts = Date.now();
  if (DOM.genreChartImg) DOM.genreChartImg.src = `/api/charts/genres?t=${ts}`;
  if (DOM.ratingDistChartImg) DOM.ratingDistChartImg.src = `/api/charts/ratings?t=${ts}`;
  if (DOM.popularityChartImg) DOM.popularityChartImg.src = `/api/charts/popularity?t=${ts}`;
  if (DOM.heatmapChartImg) DOM.heatmapChartImg.src = `/api/charts/heatmap?t=${ts}`;
  if (DOM.trendsChartImg) DOM.trendsChartImg.src = `/api/charts/trends?t=${ts}`;
}

// --------------------------------------------------------------------------
// 8. Data Quality Report & Dataset Upload / Reset
// --------------------------------------------------------------------------
async function fetchDataQualityReport() {
  try {
    const res = await apiFetch('/api/data-quality');
    if (res.success && res.data) {
      const q = res.data;
      DOM.qSource.textContent = q.source || 'Sample Dataset';
      DOM.sidebarDatasetName.textContent = q.source || 'Sample Dataset';
      DOM.qMoviesRetained.textContent = `${q.movies_valid} / ${q.movies_loaded}`;
      DOM.qMoviesDups.textContent = `${q.movie_duplicates_removed} duplicate records removed`;
      DOM.qRatingsRetained.textContent = `${q.ratings_valid} / ${q.ratings_loaded}`;
      DOM.qRatingsDups.textContent = `${q.ratings_duplicates_removed} duplicate user pairs removed`;
      DOM.qRatingsInvalid.textContent = `${q.ratings_invalid_range_removed + (q.ratings_unknown_movie_removed || 0)}`;

      if (q.cleaning_operations) {
        DOM.qualityLogList.innerHTML = q.cleaning_operations
          .map(
            (op) => `
          <li class="quality-log-item">
            <i data-lucide="check-circle-2"></i>
            <span>${escapeHtml(op)}</span>
          </li>
        `
          )
          .join('');
        lucide.createIcons();
      }
    }
  } catch (err) {
    showToast('Failed to load quality report', 'error');
  }
}

DOM.resetSampleDataBtn.addEventListener('click', async () => {
  if (!confirm('Reset dataset to the bundled sample data?')) return;
  try {
    const res = await apiFetch('/api/reset-data', { method: 'POST' });
    if (res.success) {
      showToast('Dataset reset to sample data successfully');
      refreshAllData();
    }
  } catch (err) {
    showToast(`Reset failed: ${err.message}`, 'error');
  }
});

DOM.uploadDatasetForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const moviesInput = document.getElementById('uploadMoviesFile');
  const ratingsInput = document.getElementById('uploadRatingsFile');

  if (!moviesInput.files[0] || !ratingsInput.files[0]) {
    showToast('Please select both movies.csv and ratings.csv', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('movies', moviesInput.files[0]);
  formData.append('ratings', ratingsInput.files[0]);

  const submitBtn = document.getElementById('uploadSubmitBtn');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Validating and loading...';

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData,
    });
    const result = await res.json();

    if (result.success) {
      showToast('Custom dataset loaded successfully!');
      DOM.uploadDatasetForm.reset();
      refreshAllData();
    } else {
      showToast(result.message || 'Dataset validation failed', 'error');
    }
  } catch (err) {
    showToast(`Upload error: ${err.message}`, 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i data-lucide="upload"></i> Validate & Load Custom Dataset';
    lucide.createIcons();
  }
});

// --------------------------------------------------------------------------
// 9. Global Search, Export & Full App Refresh
// --------------------------------------------------------------------------
window.addEventListener('keydown', (e) => {
  if (e.key === '/' && document.activeElement !== DOM.globalSearchInput && document.activeElement.tagName !== 'INPUT') {
    e.preventDefault();
    DOM.globalSearchInput.focus();
  }
});

DOM.globalSearchInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    const term = DOM.globalSearchInput.value.trim();
    DOM.filterSearch.value = term;
    AppState.movies.search = term;
    AppState.movies.page = 1;
    navigateToSection('movies');
    fetchMoviesList();
  }
});

// Export dropdown toggle
DOM.exportMenuBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  DOM.exportMenu.classList.toggle('show');
});

document.addEventListener('click', () => {
  DOM.exportMenu.classList.remove('show');
});

DOM.refreshDataBtn.addEventListener('click', () => {
  refreshAllData();
  showToast('Dataset and visualizations refreshed');
});

function refreshAllData() {
  fetchDashboardMetrics();
  fetchFeaturedLists();
  fetchMoviesList();
  fetchGenreAnalytics();
  fetchDataQualityReport();
  populateMovieSelector();
  refreshChartsImages();
}

// --------------------------------------------------------------------------
// 10. Initialization
// --------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();

  // Initial Section from Hash
  const initialHash = window.location.hash.replace('#', '') || 'dashboard';
  navigateToSection(initialHash);

  // Initial Data Calls
  fetchDashboardMetrics();
  fetchFeaturedLists();
  populateMovieSelector();
  fetchGenreAnalytics();
  fetchDataQualityReport();
});
