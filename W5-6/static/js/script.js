/**
 * Touchline Analytics — Football Analytics & Player Comparison Lab Client Script.
 * Vanilla JavaScript (ES6+), Fetch API, Chart.js 4 Integration, Hash Routing,
 * Multi-player Comparisons & Normalized Radar Graphics.
 */

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  // State Management
  const state = {
    currentSection: 'section-overview',
    activeSeason: '2023-2024',
    activeLeague: '',
    searchDebounceTimer: null,
    playerFilters: {
      search: '',
      position: '',
      league: '',
      club: '',
      min_minutes: 0,
      min_rating: 0.0,
      sort_by: 'goals',
      sort_order: 'desc',
      page: 1,
      page_size: 15,
    },
    comparedPlayerIds: [1, 4], // Sensible initial comparison selection
    chartInstances: {},
  };

  // ------------------------------------------------------------------------
  // Reusable API Fetch Helper
  // ------------------------------------------------------------------------
  async function fetchAPI(endpoint, options = {}) {
    try {
      const response = await fetch(endpoint, options);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.message || `HTTP error ${response.status}`);
      }
      return data;
    } catch (err) {
      console.error(`API Request Failed [${endpoint}]:`, err);
      throw err;
    }
  }

  // ------------------------------------------------------------------------
  // Toast Notification System
  // ------------------------------------------------------------------------
  function showToast(message, isError = false) {
    const toast = document.getElementById('toastPopup');
    const toastText = document.getElementById('toastText');
    const toastIcon = document.getElementById('toastIcon');
    const toastIconWrap = document.getElementById('toastIconWrap');

    if (!toast) return;

    toastText.textContent = message;
    if (isError) {
      toastIconWrap.style.background = 'rgba(244, 63, 94, 0.2)';
      toastIconWrap.style.color = '#f43f5e';
      toastIcon.setAttribute('data-lucide', 'alert-circle');
    } else {
      toastIconWrap.style.background = 'rgba(16, 185, 129, 0.2)';
      toastIconWrap.style.color = '#10b981';
      toastIcon.setAttribute('data-lucide', 'check');
    }

    if (window.lucide) lucide.createIcons();

    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 3500);
  }

  // ------------------------------------------------------------------------
  // Safe Chart.js Creation / Re-creation
  // ------------------------------------------------------------------------
  function createOrUpdateChart(canvasId, config) {
    if (state.chartInstances[canvasId]) {
      state.chartInstances[canvasId].destroy();
    }
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    // Apply global clean light analytics font & color defaults
    Chart.defaults.color = '#475569';
    Chart.defaults.font.family = "'Plus Jakarta Sans', system-ui, -apple-system, sans-serif";

    state.chartInstances[canvasId] = new Chart(ctx, config);
    return state.chartInstances[canvasId];
  }

  // ------------------------------------------------------------------------
  // Section & Hash Navigation
  // ------------------------------------------------------------------------
  function navigateTo(sectionId) {
    state.currentSection = sectionId;

    document.querySelectorAll('.page-section').forEach(sec => {
      sec.classList.remove('active');
    });

    const activeSec = document.getElementById(sectionId);
    if (activeSec) {
      activeSec.classList.add('active');
    }

    document.querySelectorAll('.sidebar-nav .nav-item').forEach(link => {
      link.classList.toggle('active', link.dataset.section === sectionId);
    });

    // Update Topbar Breadcrumbs
    const titles = {
      'section-overview': { title: 'Overview', sub: 'Football Intelligence Dashboard' },
      'section-players': { title: 'Player Explorer', sub: 'Filterable Squad Statistics' },
      'section-compare': { title: 'Compare Players', sub: 'Multi-player Radar & Benchmarks' },
      'section-analytics': { title: 'Performance Lab', sub: 'In-Depth Positional & Age Curves' },
      'section-matches': { title: 'Match Insights', sub: 'Fixture Statistics & Scorelines' },
    };

    const meta = titles[sectionId] || { title: 'Touchline Analytics', sub: 'Football Analytics Lab' };
    document.getElementById('pageTitle').textContent = meta.title;
    document.getElementById('pageSubtitle').textContent = meta.sub;

    // Close mobile drawer if open
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.remove('open');

    // Section-specific triggers
    if (sectionId === 'section-overview') loadDashboard();
    else if (sectionId === 'section-players') loadPlayers();
    else if (sectionId === 'section-compare') loadComparison();
    else if (sectionId === 'section-analytics') loadAnalytics();
    else if (sectionId === 'section-matches') loadMatches();

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function handleHashChange() {
    const hash = window.location.hash.replace('#', '') || 'overview';
    const sectionMap = {
      overview: 'section-overview',
      players: 'section-players',
      compare: 'section-compare',
      analytics: 'section-analytics',
      matches: 'section-matches',
    };
    const targetSection = sectionMap[hash] || 'section-overview';
    if (!sectionMap[hash]) {
      window.location.hash = '#overview';
    }
    navigateTo(targetSection);
  }

  // ------------------------------------------------------------------------
  // Overview Dashboard Loader
  // ------------------------------------------------------------------------
  async function loadDashboard() {
    try {
      const season = state.activeSeason ? `season=${encodeURIComponent(state.activeSeason)}` : '';
      const league = state.activeLeague ? `league=${encodeURIComponent(state.activeLeague)}` : '';
      const query = [season, league].filter(Boolean).join('&');
      const url = `/api/dashboard${query ? '?' + query : ''}`;

      const res = await fetchAPI(url);
      if (!res.success) return;

      const data = res.data;
      const kpis = data.kpis;

      // Populate KPIs
      document.getElementById('kpiTotalPlayers').textContent = (kpis.total_players || 0).toLocaleString();
      document.getElementById('kpiTotalClubs').textContent = (kpis.total_clubs || 0).toLocaleString();
      document.getElementById('kpiTotalCompetitions').textContent = (kpis.total_competitions || 0).toLocaleString();
      document.getElementById('kpiTotalGoals').textContent = (kpis.total_goals || 0).toLocaleString();
      document.getElementById('kpiAvgRating').textContent = `${(kpis.average_rating || 0).toFixed(2)}★`;
      document.getElementById('kpiTotalMatches').textContent = (kpis.total_matches || 0).toLocaleString();

      // Chart 1: Position Goals & Assists
      if (data.position_chart) {
        const labels = data.position_chart.map(p => p.position);
        createOrUpdateChart('positionChart', {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [
              {
                label: 'Goals',
                data: data.position_chart.map(p => p.goals),
                backgroundColor: '#10b981',
                borderRadius: 4,
              },
              {
                label: 'Assists',
                data: data.position_chart.map(p => p.assists),
                backgroundColor: '#84cc16',
                borderRadius: 4,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'top' } },
            scales: {
              x: { grid: { color: 'rgba(0, 0, 0, 0.05)' } },
              y: { grid: { color: 'rgba(0, 0, 0, 0.05)' } },
            },
          },
        });
      }

      // Chart 2: Rating Distribution
      if (data.rating_distribution) {
        createOrUpdateChart('ratingDistChart', {
          type: 'bar',
          data: {
            labels: data.rating_distribution.map(b => b.range),
            datasets: [{
              label: 'Players in Rating Band',
              data: data.rating_distribution.map(b => b.count),
              backgroundColor: '#10b981',
              borderRadius: 4,
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { grid: { display: false } },
              y: { grid: { color: 'rgba(0, 0, 0, 0.05)' } },
            },
          },
        });
      }

      // Chart 3: Match Trends
      if (data.match_trends) {
        createOrUpdateChart('matchTrendsChart', {
          type: 'line',
          data: {
            labels: data.match_trends.map(t => t.period),
            datasets: [{
              label: 'Total Goals',
              data: data.match_trends.map(t => t.goals),
              borderColor: '#06b6d4',
              backgroundColor: 'rgba(6, 182, 212, 0.1)',
              fill: true,
              tension: 0.3,
              pointBackgroundColor: '#06b6d4',
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { grid: { display: false } },
              y: { grid: { color: 'rgba(0, 0, 0, 0.05)' } },
            },
          },
        });
      }

      // Chart 4: League Comparison
      if (data.league_comparison) {
        createOrUpdateChart('leagueCompChart', {
          type: 'bar',
          data: {
            labels: data.league_comparison.map(l => l.league),
            datasets: [
              {
                label: 'Total Goals',
                data: data.league_comparison.map(l => l.total_goals),
                backgroundColor: '#f59e0b',
                borderRadius: 4,
              },
              {
                label: 'Total Assists',
                data: data.league_comparison.map(l => l.total_assists),
                backgroundColor: '#06b6d4',
                borderRadius: 4,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'top' } },
            scales: {
              x: { grid: { display: false } },
              y: { grid: { color: 'rgba(0, 0, 0, 0.05)' } },
            },
          },
        });
      }

      // Top Performers Table
      const topBody = document.getElementById('topPerformersBody');
      if (topBody && data.top_performers) {
        topBody.innerHTML = '';
        data.top_performers.forEach(p => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td class="font-bold text-muted">${p.rank}</td>
            <td>
              <a href="javascript:void(0)" class="player-link font-bold text-emerald" data-id="${p.player_id}">
                ${p.player_name}
              </a>
            </td>
            <td>${p.club}</td>
            <td>${p.league}</td>
            <td><span class="pos-badge pos-${getPosClass(p.position)}">${p.position.slice(0,2).toUpperCase()}</span></td>
            <td class="font-bold">${p.goals}</td>
            <td>${p.assists}</td>
            <td class="text-emerald font-bold">${p.goals_per_90 !== null ? p.goals_per_90.toFixed(2) : '—'}</td>
            <td class="text-amber font-bold">${p.rating.toFixed(2)}★</td>
            <td>
              <button class="btn btn-secondary btn-sm compare-btn" data-id="${p.player_id}">
                <i data-lucide="git-compare"></i> Compare
              </button>
            </td>
          `;
          topBody.appendChild(tr);
        });
      }

      if (window.lucide) lucide.createIcons();
    } catch (e) {
      console.error('Failed to load dashboard:', e);
    }
  }

  function getPosClass(pos) {
    if (pos === 'Goalkeeper') return 'gk';
    if (pos === 'Defender') return 'df';
    if (pos === 'Midfielder') return 'mf';
    return 'fw';
  }

  // ------------------------------------------------------------------------
  // Player Explorer Loader
  // ------------------------------------------------------------------------
  async function loadPlayers() {
    try {
      const p = state.playerFilters;
      const query = new URLSearchParams({
        search: p.search,
        position: p.position,
        league: p.league,
        club: p.club,
        min_minutes: p.min_minutes > 0 ? p.min_minutes : '',
        min_rating: p.min_rating > 0 ? p.min_rating : '',
        sort_by: p.sort_by,
        sort_order: p.sort_order,
        page: p.page,
        page_size: p.page_size,
      });

      const res = await fetchAPI(`/api/players?${query.toString()}`);
      if (!res.success) return;

      const data = res.data;
      const tbody = document.getElementById('playersTableBody');
      const emptyState = document.getElementById('playersEmptyState');
      const countText = document.getElementById('resultsCountText');
      const pagInfo = document.getElementById('paginationInfo');
      const prevBtn = document.getElementById('prevPageBtn');
      const nextBtn = document.getElementById('nextPageBtn');

      countText.textContent = `Showing ${data.players.length} of ${data.total_count} matching players`;
      pagInfo.textContent = `Page ${data.page} of ${Math.max(1, data.total_pages)}`;
      prevBtn.disabled = data.page <= 1;
      nextBtn.disabled = data.page >= data.total_pages;

      if (!data.players.length) {
        tbody.innerHTML = '';
        emptyState.style.display = 'block';
        return;
      }

      emptyState.style.display = 'none';
      tbody.innerHTML = '';

      data.players.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>
            <a href="javascript:void(0)" class="player-link font-bold text-emerald" data-id="${p.player_id}">
              ${p.player_name}
            </a>
          </td>
          <td>${p.club}</td>
          <td>${p.league}</td>
          <td><span class="pos-badge pos-${getPosClass(p.position)}">${p.position.slice(0,2).toUpperCase()}</span></td>
          <td>${p.age}</td>
          <td>${p.appearances}</td>
          <td>${p.minutes_played.toLocaleString()}</td>
          <td class="font-bold">${p.goals}</td>
          <td>${p.assists}</td>
          <td class="text-emerald font-bold">${p.goals_per_90 !== null ? p.goals_per_90.toFixed(2) : '—'}</td>
          <td>${p.xg.toFixed(2)}</td>
          <td>${p.pass_completion_pct !== null ? p.pass_completion_pct.toFixed(1) + '%' : '—'}</td>
          <td class="text-amber font-bold">${p.rating.toFixed(2)}★</td>
          <td>
            <div style="display: flex; gap: 6px;">
              <button class="btn btn-secondary btn-sm details-btn" data-id="${p.player_id}" title="View detail profile">
                <i data-lucide="eye"></i>
              </button>
              <button class="btn btn-secondary btn-sm compare-btn" data-id="${p.player_id}" title="Add to comparison">
                <i data-lucide="git-compare"></i>
              </button>
            </div>
          </td>
        `;
        tbody.appendChild(tr);
      });

      if (window.lucide) lucide.createIcons();
    } catch (e) {
      console.error('Failed to load players:', e);
    }
  }

  // ------------------------------------------------------------------------
  // Player Detail Modal
  // ------------------------------------------------------------------------
  async function openPlayerModal(playerId) {
    try {
      const res = await fetchAPI(`/api/players/${playerId}`);
      if (!res.success) return;

      const p = res.data;
      document.getElementById('modalAvatar').textContent = (p.player_name.split(' ').map(n=>n[0]).join('')).slice(0,2).toUpperCase();
      document.getElementById('modalPlayerName').textContent = p.player_name;
      document.getElementById('modalClub').textContent = p.club;
      document.getElementById('modalLeague').textContent = p.league;
      
      const posBadge = document.getElementById('modalPosBadge');
      posBadge.className = `pos-badge pos-${getPosClass(p.position)}`;
      posBadge.textContent = p.position;

      document.getElementById('modalApps').textContent = p.appearances;
      document.getElementById('modalMins').textContent = p.minutes_played.toLocaleString();
      document.getElementById('modalRating').textContent = `${p.rating.toFixed(2)}★`;
      document.getElementById('modalG90').textContent = p.goals_per_90 !== null ? p.goals_per_90.toFixed(2) : 'N/A';

      document.getElementById('modalGoalsXg').textContent = `${p.goals} / ${p.xg.toFixed(2)}`;
      document.getElementById('modalAssistsXa').textContent = `${p.assists} / ${p.xa.toFixed(2)}`;
      document.getElementById('modalPassPct').textContent = p.pass_completion_pct !== null ? `${p.pass_completion_pct.toFixed(1)}%` : 'N/A';
      document.getElementById('modalShotAcc').textContent = p.shot_accuracy_pct !== null ? `${p.shot_accuracy_pct.toFixed(1)}%` : 'N/A';
      document.getElementById('modalKeyPasses').textContent = p.key_passes;
      document.getElementById('modalDefActions').textContent = p.defensive_actions_per_90 !== null ? p.defensive_actions_per_90.toFixed(2) : 'N/A';

      const compareBtn = document.getElementById('modalCompareAddBtn');
      compareBtn.setAttribute('data-id', p.player_id);

      document.getElementById('playerModal').style.display = 'flex';
    } catch (e) {
      showToast('Could not load player profile', true);
    }
  }

  function closePlayerModal() {
    document.getElementById('playerModal').style.display = 'none';
  }

  // ------------------------------------------------------------------------
  // Compare Players Section
  // ------------------------------------------------------------------------
  async function loadComparison() {
    const chipsContainer = document.getElementById('compareChipsContainer');
    const resultsArea = document.getElementById('compareResultsArea');
    const emptyState = document.getElementById('compareEmptyState');

    if (state.comparedPlayerIds.length < 2) {
      resultsArea.style.display = 'none';
      emptyState.style.display = 'block';
      renderCompareChips();
      return;
    }

    try {
      const idsQuery = state.comparedPlayerIds.join(',');
      const res = await fetchAPI(`/api/compare?ids=${idsQuery}`);
      if (!res.success) {
        showToast(res.message, true);
        return;
      }

      emptyState.style.display = 'none';
      resultsArea.style.display = 'block';

      const data = res;
      renderCompareChips(data.players);

      // Render Radar Chart
      const radar = data.radar;
      createOrUpdateChart('comparisonRadarChart', {
        type: 'radar',
        data: {
          labels: radar.labels,
          datasets: radar.datasets.map(ds => ({
            label: ds.label,
            data: ds.data,
            backgroundColor: ds.backgroundColor,
            borderColor: ds.borderColor,
            pointBackgroundColor: ds.pointBackgroundColor,
            borderWidth: 2,
          })),
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            r: {
              angleLines: { color: 'rgba(0, 0, 0, 0.08)' },
              grid: { color: 'rgba(0, 0, 0, 0.08)' },
              pointLabels: { color: '#334155', font: { size: 11, weight: '600' } },
              ticks: { display: false, min: 0, max: 100 },
            },
          },
          plugins: {
            legend: { position: 'top' },
          },
        },
      });

      // Render Grouped Bar Chart: Goals & Assists
      createOrUpdateChart('comparisonBarChart', {
        type: 'bar',
        data: {
          labels: data.players.map(p => p.player_name),
          datasets: [
            {
              label: 'Total Goals',
              data: data.players.map(p => p.goals),
              backgroundColor: '#10b981',
              borderRadius: 4,
            },
            {
              label: 'Total Assists',
              data: data.players.map(p => p.assists),
              backgroundColor: '#84cc16',
              borderRadius: 4,
            },
            {
              label: 'Goal Contributions (G+A)',
              data: data.players.map(p => p.goal_contributions),
              backgroundColor: '#06b6d4',
              borderRadius: 4,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'top' } },
          scales: {
            x: { grid: { display: false } },
            y: { grid: { color: 'rgba(0, 0, 0, 0.05)' } },
          },
        },
      });

      // Render Comparison Verdict
      const verdictList = document.getElementById('verdictPointsList');
      verdictList.innerHTML = '';
      data.verdict.summary_points.forEach(pt => {
        const item = document.createElement('div');
        item.className = 'verdict-point-item';
        item.innerHTML = `<i data-lucide="check-circle" style="color:#10b981; flex-shrink:0;"></i> <span>${pt}</span>`;
        verdictList.appendChild(item);
      });

      const warningsBox = document.getElementById('verdictWarningsBox');
      if (data.verdict.warnings.length) {
        warningsBox.style.display = 'block';
        warningsBox.innerHTML = data.verdict.warnings.map(w => `<p>• ${w}</p>`).join('');
      } else {
        warningsBox.style.display = 'none';
      }

      // Render Aligned Comparison Table
      renderComparisonTable(data.players, data.leaders);

      if (window.lucide) lucide.createIcons();
    } catch (e) {
      console.error('Failed to load comparison:', e);
    }
  }

  function renderCompareChips(players = []) {
    const container = document.getElementById('compareChipsContainer');
    if (!container) return;
    container.innerHTML = '';

    state.comparedPlayerIds.forEach(id => {
      const p = players.find(x => x.player_id === id);
      const name = p ? p.player_name : `Player #${id}`;
      const chip = document.createElement('div');
      chip.className = 'compare-chip';
      chip.innerHTML = `
        <span>${name}</span>
        <button class="chip-remove-btn" data-id="${id}" title="Remove player">
          <i data-lucide="x"></i>
        </button>
      `;
      container.appendChild(chip);
    });

    if (window.lucide) lucide.createIcons();
  }

  function renderComparisonTable(players, leaders) {
    const theadRow = document.getElementById('comparisonTableHeaderRow');
    const tbody = document.getElementById('comparisonTableBody');
    if (!theadRow || !tbody) return;

    theadRow.innerHTML = '<th>Metric</th>' + players.map(p => `<th>${p.player_name}</th>`).join('');

    const rows = [
      { key: 'club', label: 'Club', fmt: v => v },
      { key: 'league', label: 'League', fmt: v => v },
      { key: 'position', label: 'Position', fmt: v => v },
      { key: 'age', label: 'Age', fmt: v => `${v} yrs` },
      { key: 'minutes_played', label: 'Minutes Played', fmt: v => v.toLocaleString() },
      { key: 'goals', label: 'Total Goals', leaderKey: 'goals', fmt: v => v },
      { key: 'assists', label: 'Total Assists', leaderKey: 'assists', fmt: v => v },
      { key: 'goals_per_90', label: 'Goals / 90', leaderKey: 'goals_per_90', fmt: v => v !== null ? v.toFixed(2) : 'N/A' },
      { key: 'xg', label: 'Expected Goals (xG)', fmt: v => v.toFixed(2) },
      { key: 'xa', label: 'Expected Assists (xA)', fmt: v => v.toFixed(2) },
      { key: 'pass_completion_pct', label: 'Pass Completion %', leaderKey: 'pass_completion_pct', fmt: v => v !== null ? `${v.toFixed(1)}%` : 'N/A' },
      { key: 'shot_accuracy_pct', label: 'Shot Accuracy %', leaderKey: 'shot_accuracy_pct', fmt: v => v !== null ? `${v.toFixed(1)}%` : 'N/A' },
      { key: 'defensive_actions_per_90', label: 'Def Actions / 90', leaderKey: 'defensive_actions_per_90', fmt: v => v !== null ? v.toFixed(2) : 'N/A' },
      { key: 'rating', label: 'Performance Rating', leaderKey: 'rating', fmt: v => `${v.toFixed(2)}★` },
    ];

    tbody.innerHTML = '';
    rows.forEach(r => {
      const tr = document.createElement('tr');
      let cells = `<td class="font-bold text-muted">${r.label}</td>`;

      players.forEach(p => {
        const val = p[r.key];
        const isLeader = r.leaderKey && leaders[r.leaderKey] && leaders[r.leaderKey].leader === p.player_name;
        const cellClass = isLeader ? 'leader-cell' : '';
        cells += `<td class="${cellClass}">${r.fmt(val)}</td>`;
      });

      tr.innerHTML = cells;
      tbody.appendChild(tr);
    });
  }

  // ------------------------------------------------------------------------
  // Performance Analytics Lab
  // ------------------------------------------------------------------------
  async function loadAnalytics() {
    try {
      // 1. Positions table
      const posRes = await fetchAPI('/api/analytics/positions');
      if (posRes.success) {
        const posBody = document.getElementById('positionsTableBody');
        posBody.innerHTML = posRes.data.map(p => `
          <tr>
            <td class="font-bold">${p.position}</td>
            <td>${p.player_count}</td>
            <td class="font-bold">${p.total_goals}</td>
            <td>${p.total_assists}</td>
            <td class="text-emerald font-bold">${p.avg_goals_per_90.toFixed(2)}</td>
            <td class="text-amber font-bold">${p.avg_rating.toFixed(2)}★</td>
            <td>${p.avg_minutes.toFixed(0)}</td>
            <td>${p.avg_pass_comp.toFixed(1)}%</td>
          </tr>
        `).join('');
      }

      // 2. Clubs table
      const clubsRes = await fetchAPI('/api/analytics/clubs');
      if (clubsRes.success) {
        const clubsBody = document.getElementById('clubsTableBody');
        clubsBody.innerHTML = clubsRes.data.map(c => `
          <tr>
            <td class="font-bold">${c.club}</td>
            <td>${c.league}</td>
            <td>${c.player_count}</td>
            <td class="font-bold">${c.total_goals}</td>
            <td>${c.total_assists}</td>
            <td>${c.total_shots}</td>
            <td>${c.total_xg.toFixed(2)}</td>
            <td class="text-amber font-bold">${c.avg_rating.toFixed(2)}★</td>
          </tr>
        `).join('');
      }

    } catch (e) {
      console.error('Failed to load analytics:', e);
    }
  }

  // ------------------------------------------------------------------------
  // Match Insights Loader
  // ------------------------------------------------------------------------
  async function loadMatches() {
    try {
      const res = await fetchAPI('/api/analytics/matches');
      if (!res.success) return;

      const data = res.data;
      document.getElementById('kpiMatchesTotal').textContent = data.total_matches.toLocaleString();
      document.getElementById('kpiMatchesAvgGoals').textContent = data.avg_goals.toFixed(2);
      document.getElementById('kpiMatchesHomeWins').textContent = data.home_wins.toLocaleString();
      document.getElementById('kpiMatchesAwayWins').textContent = data.away_wins.toLocaleString();

      const tbody = document.getElementById('matchesTableBody');
      tbody.innerHTML = data.matches.map(m => {
        let resClass = 'badge-subtle';
        if (m.result === 'Home Win') resClass = 'pos-mf';
        else if (m.result === 'Away Win') resClass = 'pos-fw';
        else resClass = 'pos-gk';

        return `
          <tr>
            <td>${m.date_str}</td>
            <td>${m.league}</td>
            <td class="font-bold">${m.home_team}</td>
            <td class="font-bold text-center" style="font-size:14px;">${m.home_goals} - ${m.away_goals}</td>
            <td class="font-bold">${m.away_team}</td>
            <td><span class="pos-badge ${resClass}">${m.result}</span></td>
          </tr>
        `;
      }).join('');
    } catch (e) {
      console.error('Failed to load matches:', e);
    }
  }

  // ------------------------------------------------------------------------
  // Data Quality Loader
  // ------------------------------------------------------------------------
  async function loadDataQuality() {
    try {
      const res = await fetchAPI('/api/data-quality');
      if (!res.success) return;

      const data = res.data;
      document.getElementById('qualityCompleteness').textContent = `${data.completeness_score}%`;
      document.getElementById('qualityPlayersCount').textContent = data.players.valid_rows.toLocaleString();
      document.getElementById('qualityMatchesCount').textContent = data.matches.valid_rows.toLocaleString();

      const issues = (data.players.issues || []).concat(data.matches.issues || []);
      document.getElementById('qualityIssuesCount').textContent = issues.length;

      const tbody = document.getElementById('qualityTableBody');
      if (!issues.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">All loaded records conform 100% to schema rules. Zero issues found.</td></tr>';
        return;
      }

      tbody.innerHTML = issues.map((iss, i) => `
        <tr>
          <td><span class="badge badge-subtle">${iss.column === 'match_date' ? 'Matches' : 'Players'}</span></td>
          <td class="font-bold text-muted">${iss.column}</td>
          <td class="text-amber font-semibold">${iss.issue_type}</td>
          <td>${iss.count}</td>
          <td class="text-emerald">${iss.action}</td>
        </tr>
      `).join('');
    } catch (e) {
      console.error('Failed to load data quality:', e);
    }
  }

  // ------------------------------------------------------------------------
  // Populate Player Selectors & Filter Options
  // ------------------------------------------------------------------------
  async function initFilters() {
    try {
      const res = await fetchAPI('/api/filters');
      if (!res.success) return;

      const f = res.data;
      const clubSelect = document.getElementById('filterClub');
      clubSelect.innerHTML = '<option value="">All Clubs</option>' + f.clubs.map(c => `<option value="${c}">${c}</option>`).join('');

      // Populate comparison selector with all catalog players
      const compSelect = document.getElementById('comparePlayerSelect');
      const allPlayersRes = await fetchAPI('/api/players?page_size=200');
      if (allPlayersRes.success) {
        compSelect.innerHTML = '<option value="">Select a player to compare...</option>' +
          allPlayersRes.data.players.map(p => `<option value="${p.player_id}">${p.player_name} (${p.club} - ${p.position})</option>`).join('');
      }
    } catch (e) {
      console.error('Failed to init filters:', e);
    }
  }

  // ------------------------------------------------------------------------
  // Event Bindings
  // ------------------------------------------------------------------------
  function setupEventListeners() {
    // Hash Routing
    window.addEventListener('hashchange', handleHashChange);

    // Nav Item Click
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(link => {
      link.addEventListener('click', e => {
        e.preventDefault();
        window.location.hash = link.getAttribute('href');
      });
    });

    // Mobile Sidebar Toggle
    document.getElementById('mobileToggleBtn')?.addEventListener('click', () => {
      document.getElementById('sidebar')?.classList.toggle('open');
    });
    document.getElementById('mobileCloseBtn')?.addEventListener('click', () => {
      document.getElementById('sidebar')?.classList.remove('open');
    });

    // Hero Action Buttons
    document.getElementById('heroExploreBtn')?.addEventListener('click', () => { window.location.hash = '#players'; });
    document.getElementById('heroCompareBtn')?.addEventListener('click', () => { window.location.hash = '#compare'; });
    document.getElementById('heroAnalyticsBtn')?.addEventListener('click', () => { window.location.hash = '#analytics'; });
    document.getElementById('viewAllPlayersBtn')?.addEventListener('click', () => { window.location.hash = '#players'; });

    // Global Refresh
    document.getElementById('refreshBtn')?.addEventListener('click', () => {
      loadDashboard();
      showToast('Live analytics refreshed');
    });

    // Global Search Keybinding
    window.addEventListener('keydown', e => {
      if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
        e.preventDefault();
        document.getElementById('globalSearchInput')?.focus();
      }
    });

    // Global Search Input
    document.getElementById('globalSearchInput')?.addEventListener('input', e => {
      clearTimeout(state.searchDebounceTimer);
      state.searchDebounceTimer = setTimeout(() => {
        state.playerFilters.search = e.target.value.trim();
        state.playerFilters.page = 1;
        window.location.hash = '#players';
        loadPlayers();
      }, 300);
    });

    // Topbar Season & League Selectors
    document.getElementById('globalSeasonSelect')?.addEventListener('change', e => {
      state.activeSeason = e.target.value;
      loadDashboard();
    });
    document.getElementById('globalLeagueSelect')?.addEventListener('change', e => {
      state.activeLeague = e.target.value;
      loadDashboard();
    });

    // Explorer Filters
    const filterSearch = document.getElementById('filterSearch');
    filterSearch?.addEventListener('input', e => {
      clearTimeout(state.searchDebounceTimer);
      state.searchDebounceTimer = setTimeout(() => {
        state.playerFilters.search = e.target.value.trim();
        state.playerFilters.page = 1;
        loadPlayers();
      }, 300);
    });

    document.getElementById('filterPosition')?.addEventListener('change', e => {
      state.playerFilters.position = e.target.value;
      state.playerFilters.page = 1;
      loadPlayers();
    });

    document.getElementById('filterLeague')?.addEventListener('change', e => {
      state.playerFilters.league = e.target.value;
      state.playerFilters.page = 1;
      loadPlayers();
    });

    document.getElementById('filterClub')?.addEventListener('change', e => {
      state.playerFilters.club = e.target.value;
      state.playerFilters.page = 1;
      loadPlayers();
    });

    const filterMinutes = document.getElementById('filterMinutes');
    filterMinutes?.addEventListener('input', e => {
      document.getElementById('minutesVal').textContent = e.target.value;
      state.playerFilters.min_minutes = Number(e.target.value);
      state.playerFilters.page = 1;
      loadPlayers();
    });

    const filterRating = document.getElementById('filterRating');
    filterRating?.addEventListener('input', e => {
      document.getElementById('ratingVal').textContent = `${Number(e.target.value).toFixed(1)}★`;
      state.playerFilters.min_rating = Number(e.target.value);
      state.playerFilters.page = 1;
      loadPlayers();
    });

    document.getElementById('filterSortBy')?.addEventListener('change', e => {
      state.playerFilters.sort_by = e.target.value;
      loadPlayers();
    });

    document.getElementById('sortDescBtn')?.addEventListener('click', () => {
      document.getElementById('sortDescBtn').classList.add('active');
      document.getElementById('sortAscBtn').classList.remove('active');
      state.playerFilters.sort_order = 'desc';
      loadPlayers();
    });

    document.getElementById('sortAscBtn')?.addEventListener('click', () => {
      document.getElementById('sortAscBtn').classList.add('active');
      document.getElementById('sortDescBtn').classList.remove('active');
      state.playerFilters.sort_order = 'asc';
      loadPlayers();
    });

    document.getElementById('resetFiltersBtn')?.addEventListener('click', () => {
      state.playerFilters = {
        search: '',
        position: '',
        league: '',
        club: '',
        min_minutes: 0,
        min_rating: 0.0,
        sort_by: 'goals',
        sort_order: 'desc',
        page: 1,
        page_size: 15,
      };
      if (filterSearch) filterSearch.value = '';
      document.getElementById('filterPosition').value = '';
      document.getElementById('filterLeague').value = '';
      document.getElementById('filterClub').value = '';
      if (filterMinutes) { filterMinutes.value = 0; document.getElementById('minutesVal').textContent = '0'; }
      if (filterRating) { filterRating.value = 0; document.getElementById('ratingVal').textContent = '0.0★'; }
      loadPlayers();
      showToast('Filters cleared');
    });

    document.getElementById('emptyClearBtn')?.addEventListener('click', () => {
      document.getElementById('resetFiltersBtn')?.click();
    });

    // Pagination Buttons
    document.getElementById('prevPageBtn')?.addEventListener('click', () => {
      if (state.playerFilters.page > 1) {
        state.playerFilters.page -= 1;
        loadPlayers();
      }
    });

    document.getElementById('nextPageBtn')?.addEventListener('click', () => {
      state.playerFilters.page += 1;
      loadPlayers();
    });

    // Delegate Table Click Events (Player Details & Compare)
    document.addEventListener('click', e => {
      const link = e.target.closest('.player-link');
      if (link) {
        openPlayerModal(Number(link.dataset.id));
        return;
      }

      const detBtn = e.target.closest('.details-btn');
      if (detBtn) {
        openPlayerModal(Number(detBtn.dataset.id));
        return;
      }

      const compBtn = e.target.closest('.compare-btn');
      if (compBtn) {
        const pid = Number(compBtn.dataset.id);
        if (!state.comparedPlayerIds.includes(pid)) {
          if (state.comparedPlayerIds.length >= 4) {
            state.comparedPlayerIds.shift(); // Remove oldest to maintain max 4
          }
          state.comparedPlayerIds.push(pid);
          showToast('Player added to comparison');
        }
        window.location.hash = '#compare';
        loadComparison();
      }
    });

    // Modal Close
    document.getElementById('modalCloseBtn')?.addEventListener('click', closePlayerModal);
    document.getElementById('playerModal')?.addEventListener('click', e => {
      if (e.target.id === 'playerModal') closePlayerModal();
    });
    window.addEventListener('keydown', e => {
      if (e.key === 'Escape') closePlayerModal();
    });

    // Modal Add Compare Button
    document.getElementById('modalCompareAddBtn')?.addEventListener('click', () => {
      const pid = Number(document.getElementById('modalCompareAddBtn').dataset.id);
      if (pid && !state.comparedPlayerIds.includes(pid)) {
        if (state.comparedPlayerIds.length >= 4) state.comparedPlayerIds.shift();
        state.comparedPlayerIds.push(pid);
      }
      closePlayerModal();
      window.location.hash = '#compare';
      loadComparison();
    });

    // Compare Controls
    document.getElementById('addCompareBtn')?.addEventListener('click', () => {
      const select = document.getElementById('comparePlayerSelect');
      const pid = Number(select.value);
      if (!pid) {
        showToast('Please select a player to add', true);
        return;
      }
      if (state.comparedPlayerIds.includes(pid)) {
        showToast('Player is already in comparison', true);
        return;
      }
      if (state.comparedPlayerIds.length >= 4) {
        showToast('Maximum 4 players can be compared simultaneously', true);
        return;
      }
      state.comparedPlayerIds.push(pid);
      select.value = '';
      loadComparison();
      showToast('Player added to comparison');
    });

    document.getElementById('clearCompareBtn')?.addEventListener('click', () => {
      state.comparedPlayerIds = [];
      loadComparison();
      showToast('Comparison cleared');
    });

    // Remove Chip Delegate
    document.getElementById('compareChipsContainer')?.addEventListener('click', e => {
      const btn = e.target.closest('.chip-remove-btn');
      if (btn) {
        const pid = Number(btn.dataset.id);
        state.comparedPlayerIds = state.comparedPlayerIds.filter(id => id !== pid);
        loadComparison();
      }
    });

    // Subnav Tabs in Analytics Lab
    document.querySelectorAll('.subnav-tabs .tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.subnav-tabs .tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(btn.dataset.tab)?.classList.add('active');
      });
    });

    // Age Metric Select
    document.getElementById('ageMetricSelect')?.addEventListener('change', e => {
      const img = document.getElementById('chartImgAge');
      if (img) {
        img.src = `/api/charts/age?metric=${e.target.value}&t=${Date.now()}`;
      }
    });

    // Dataset Upload Forms
    document.getElementById('uploadPlayersForm')?.addEventListener('submit', async e => {
      e.preventDefault();
      const fileInput = document.getElementById('playersFileInput');
      if (!fileInput.files.length) return;

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);

      try {
        const res = await fetchAPI('/api/upload/players', { method: 'POST', body: formData });
        showToast(res.message);
        fileInput.value = '';
        loadDashboard();
      } catch (err) {
        showToast(err.message, true);
      }
    });

    document.getElementById('uploadMatchesForm')?.addEventListener('submit', async e => {
      e.preventDefault();
      const fileInput = document.getElementById('matchesFileInput');
      if (!fileInput.files.length) return;

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);

      try {
        const res = await fetchAPI('/api/upload/matches', { method: 'POST', body: formData });
        showToast(res.message);
        fileInput.value = '';
        loadDashboard();
      } catch (err) {
        showToast(err.message, true);
      }
    });

    // Reset Demo Data
    document.getElementById('resetDemoDataBtn')?.addEventListener('click', async () => {
      try {
        const res = await fetchAPI('/api/dataset/reset', { method: 'POST' });
        showToast(res.message);
        loadDashboard();
      } catch (err) {
        showToast(err.message, true);
      }
    });
  }

  // ------------------------------------------------------------------------
  // Initialize Application
  // ------------------------------------------------------------------------
  setupEventListeners();
  initFilters();
  handleHashChange();
});
