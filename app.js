// The Rewatchables AU - Main Application

class RewatchablesApp {
    constructor() {
        this.episodes = [];
        this.filteredEpisodes = [];
        this.streamingServices = {};
        this.viewMode = 'list'; // 'grid' or 'list'
        this.filters = {
            search: '',
            streaming: [],
            genre: '',
            sort: 'episodeDate-desc'
        };

        this.init();
    }

    async init() {
        await this.loadData();
        this.setupEventListeners();
        this.setupStreamingDropdown();
        this.updateViewToggle();
        this.render();
    }

    async loadData() {
        try {
            const [episodesRes, servicesRes] = await Promise.all([
                fetch('src/data/episodes.json'),
                fetch('src/data/streaming-services.json')
            ]);

            const episodesData = await episodesRes.json();
            const servicesData = await servicesRes.json();

            this.episodes = episodesData.episodes;
            this.streamingServices = servicesData.services;
            this.filteredEpisodes = [...this.episodes];

            document.getElementById('loading').classList.add('hidden');
        } catch (error) {
            console.error('Error loading data:', error);
            document.getElementById('loading').innerHTML = `
                <p class="text-red-400">Error loading episodes. Please refresh the page.</p>
            `;
        }
    }

    setupEventListeners() {
        // Search input
        const searchInput = document.getElementById('search-input');
        searchInput.addEventListener('input', (e) => {
            this.filters.search = e.target.value.toLowerCase();
            this.applyFilters();
        });

        // Genre filter
        const genreFilter = document.getElementById('genre-filter');
        genreFilter.addEventListener('change', (e) => {
            this.filters.genre = e.target.value;
            this.applyFilters();
        });

        // Sort select
        const sortSelect = document.getElementById('sort-select');
        sortSelect.addEventListener('change', (e) => {
            this.filters.sort = e.target.value;
            this.applyFilters();
        });

        // View toggle
        const viewGrid = document.getElementById('view-grid');
        const viewList = document.getElementById('view-list');

        viewGrid?.addEventListener('click', () => {
            this.viewMode = 'grid';
            this.updateViewToggle();
            this.render();
        });

        viewList?.addEventListener('click', () => {
            this.viewMode = 'list';
            this.updateViewToggle();
            this.render();
        });

        // Clear/Reset filters
        document.getElementById('clear-filters')?.addEventListener('click', () => this.resetFilters());
        document.getElementById('reset-filters')?.addEventListener('click', () => this.resetFilters());
    }

    setupStreamingDropdown() {
        const trigger = document.getElementById('streaming-trigger');
        const panel = document.getElementById('streaming-panel');
        const checkboxes = document.querySelectorAll('.streaming-checkbox');

        // Toggle panel on button click
        trigger.addEventListener('click', () => {
            panel.classList.toggle('hidden');
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            const dropdown = document.getElementById('streaming-dropdown');
            if (!dropdown.contains(e.target)) {
                panel.classList.add('hidden');
            }
        });

        // Handle checkbox changes
        checkboxes.forEach(cb => {
            cb.addEventListener('change', () => {
                this.filters.streaming = Array.from(checkboxes)
                    .filter(c => c.checked)
                    .map(c => c.value);
                this.updateStreamingTriggerText();
                this.applyFilters();
            });
        });
    }

    updateStreamingTriggerText() {
        const textEl = document.getElementById('streaming-trigger-text');
        const selected = this.filters.streaming;

        if (selected.length === 0) {
            textEl.textContent = 'All Streaming';
        } else {
            const nameMap = {
                netflix: 'Netflix',
                stan: 'Stan',
                primeVideo: 'Prime Video',
                disneyPlus: 'Disney+',
                binge: 'Binge',
                paramount: 'Paramount+',
                appleTv: 'Apple TV+',
                hboMax: 'HBO Max',
                rentBuy: 'Rent/Buy Only'
            };
            if (selected.length <= 2) {
                textEl.textContent = selected.map(s => nameMap[s]).join(', ');
            } else {
                textEl.textContent = `${selected.length} services`;
            }
        }
    }

    updateViewToggle() {
        const viewGrid = document.getElementById('view-grid');
        const viewList = document.getElementById('view-list');
        const grid = document.getElementById('episodes-grid');

        if (this.viewMode === 'grid') {
            viewGrid.classList.add('bg-cinema-navy', 'text-cinema-white');
            viewGrid.classList.remove('bg-cinema-white', 'text-cinema-navy');
            viewList.classList.add('bg-cinema-white', 'text-cinema-navy');
            viewList.classList.remove('bg-cinema-navy', 'text-cinema-white');
            grid.classList.remove('list-view');
            grid.classList.add('grid', 'grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3', 'gap-6');
        } else {
            viewList.classList.add('bg-cinema-navy', 'text-cinema-white');
            viewList.classList.remove('bg-cinema-white', 'text-cinema-navy');
            viewGrid.classList.add('bg-cinema-white', 'text-cinema-navy');
            viewGrid.classList.remove('bg-cinema-navy', 'text-cinema-white');
            grid.classList.add('list-view');
            grid.classList.remove('grid', 'grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3');
            grid.classList.add('flex', 'flex-col', 'gap-2');
        }
    }

    applyFilters() {
        let results = [...this.episodes];

        // Search filter
        if (this.filters.search) {
            const searchTerm = this.filters.search;
            results = results.filter(ep =>
                ep.title.toLowerCase().includes(searchTerm) ||
                ep.director.toLowerCase().includes(searchTerm) ||
                ep.hosts.some(h => h.toLowerCase().includes(searchTerm)) ||
                ep.guests.some(g => g.toLowerCase().includes(searchTerm)) ||
                ep.genres.some(g => g.toLowerCase().includes(searchTerm))
            );
        }

        // Streaming filter (multi-select, OR logic)
        if (this.filters.streaming.length > 0) {
            results = results.filter(ep => {
                return this.filters.streaming.some(service => {
                    if (service === 'rentBuy') {
                        const hasStreaming = Object.entries(ep.streaming)
                            .filter(([key]) => key !== 'rentBuy')
                            .some(([, value]) => value === true);
                        return !hasStreaming && ep.streaming.rentBuy.length > 0;
                    }
                    return ep.streaming[service] === true;
                });
            });
        }

        // Genre filter
        if (this.filters.genre) {
            results = results.filter(ep => ep.genres.includes(this.filters.genre));
        }

        // Sort
        results = this.sortEpisodes(results);

        this.filteredEpisodes = results;
        this.render();
        this.updateResultsCount();
    }

    sortEpisodes(episodes) {
        const [field, direction] = this.filters.sort.split('-');

        return episodes.sort((a, b) => {
            let valA, valB;

            switch (field) {
                case 'episodeDate':
                    valA = new Date(a.episodeDate);
                    valB = new Date(b.episodeDate);
                    break;
                case 'title':
                    valA = a.title.toLowerCase();
                    valB = b.title.toLowerCase();
                    break;
                case 'year':
                    valA = a.year;
                    valB = b.year;
                    break;
                default:
                    return 0;
            }

            if (direction === 'asc') {
                return valA > valB ? 1 : -1;
            } else {
                return valA < valB ? 1 : -1;
            }
        });
    }

    resetFilters() {
        this.filters = {
            search: '',
            streaming: [],
            genre: '',
            sort: 'episodeDate-desc'
        };

        document.getElementById('search-input').value = '';
        document.querySelectorAll('.streaming-checkbox').forEach(cb => cb.checked = false);
        this.updateStreamingTriggerText();
        document.getElementById('genre-filter').value = '';
        document.getElementById('sort-select').value = 'episodeDate-desc';

        this.applyFilters();
    }

    updateResultsCount() {
        const countEl = document.getElementById('results-count');
        const clearBtn = document.getElementById('clear-filters');
        const noResults = document.getElementById('no-results');
        const grid = document.getElementById('episodes-grid');

        const count = this.filteredEpisodes.length;
        const total = this.episodes.length;

        if (count === 0) {
            grid.classList.add('hidden');
            noResults.classList.remove('hidden');
        } else {
            grid.classList.remove('hidden');
            noResults.classList.add('hidden');
        }

        if (count === total) {
            countEl.textContent = `${total} episodes`;
            clearBtn.classList.add('hidden');
        } else {
            countEl.textContent = `Showing ${count} of ${total} episodes`;
            clearBtn.classList.remove('hidden');
        }
    }

    render() {
        const grid = document.getElementById('episodes-grid');

        if (this.viewMode === 'grid') {
            grid.className = 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6';
            grid.innerHTML = this.filteredEpisodes.map(ep => this.renderEpisodeCard(ep)).join('');
        } else {
            grid.className = 'flex flex-col gap-2';
            grid.innerHTML = this.filteredEpisodes.map(ep => this.renderEpisodeListItem(ep)).join('');
        }
    }

    renderEpisodeCard(episode) {
        const streamingBadges = this.renderStreamingBadges(episode.streaming);
        const isPick = episode.editorPick || false;

        const episodeDate = new Date(episode.episodeDate).toLocaleDateString('en-AU', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });

        return `
            <article class="episode-card rounded-lg overflow-hidden">
                <!-- Poster/Header Area -->
                <div class="poster-gradient h-32 flex items-center justify-center relative">
                    <div class="text-center px-4">
                        <h2 class="text-xl font-bold text-cinema-white">${episode.title}</h2>
                        <p class="text-cinema-light text-sm">${episode.year}</p>
                    </div>
                </div>

                <!-- Content -->
                <div class="p-4">
                    <!-- Director -->
                    <p class="text-cinema-navy text-sm mb-2">
                        <span class="text-gray-500">Director:</span> ${episode.director}
                    </p>

                    <!-- Hosts -->
                    <p class="text-cinema-navy text-sm mb-3">
                        <span class="text-gray-500">Hosts:</span> ${episode.hosts.join(', ')}
                        ${episode.guests.length ? `<br><span class="text-gray-500">Guests:</span> ${episode.guests.join(', ')}` : ''}
                    </p>

                    <!-- Streaming Availability -->
                    <div class="mb-3">
                        <p class="text-gray-500 text-xs mb-2">Available on:</p>
                        <div class="flex flex-wrap gap-1">
                            ${streamingBadges}
                        </div>
                    </div>

                    <!-- Editor Pick & Date -->
                    <div class="flex items-center justify-between mb-3">
                        ${isPick ? '<span class="text-cinema-orange text-sm font-medium">★ Murph\'s Pick</span>' : '<span></span>'}
                        <span class="text-gray-500 text-xs">${episodeDate}</span>
                    </div>

                    <!-- Actions -->
                    <div class="flex gap-2">
                        ${episode.spotifyUrl ? `
                            <a href="${episode.spotifyUrl}"
                               target="_blank"
                               rel="noopener noreferrer"
                               class="spotify-btn flex-1 text-center py-2 rounded text-cinema-white text-sm font-medium">
                                Spotify
                            </a>
                        ` : ''}
                        ${episode.applePodcastsUrl ? `
                            <a href="${episode.applePodcastsUrl}"
                               target="_blank"
                               rel="noopener noreferrer"
                               class="apple-btn flex-1 text-center py-2 rounded text-cinema-white text-sm font-medium">
                                Apple
                            </a>
                        ` : ''}
                    </div>

                    <!-- Last Checked -->
                    <p class="text-gray-600 text-xs mt-3 text-right">
                        Streaming checked: ${new Date(episode.lastStreamingCheck).toLocaleDateString('en-AU')}
                    </p>
                </div>
            </article>
        `;
    }

    renderEpisodeListItem(episode) {
        const streamingBadges = this.renderStreamingBadges(episode.streaming);
        const isPick = episode.editorPick || false;

        const episodeDate = new Date(episode.episodeDate).toLocaleDateString('en-AU', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });

        return `
            <article class="episode-card rounded-lg p-4 flex flex-col sm:flex-row sm:items-center gap-4">
                <!-- Title & Info -->
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                        <h2 class="text-lg font-bold text-cinema-navy truncate">${episode.title}</h2>
                        <span class="text-gray-500 text-sm">(${episode.year})</span>
                    </div>
                    <p class="text-gray-600 text-xs">
                        <span class="text-gray-500">Dir:</span> ${episode.director}
                    </p>
                    <p class="text-gray-600 text-xs truncate">
                        <span class="text-gray-500">Hosts:</span> ${episode.hosts.join(', ')}
                    </p>
                </div>

                <!-- Streaming Badges -->
                <div class="flex flex-wrap gap-1 sm:justify-end sm:w-48">
                    ${streamingBadges}
                </div>

                <!-- Pick & Date -->
                <div class="flex items-center gap-4 sm:w-36 sm:justify-end">
                    ${isPick ? '<span class="text-cinema-orange text-sm font-medium">★ Pick</span>' : ''}
                    <span class="text-gray-500 text-xs">${episodeDate}</span>
                </div>

                <!-- Podcast Links -->
                <div class="flex gap-2">
                    ${episode.spotifyUrl ? `
                        <a href="${episode.spotifyUrl}"
                           target="_blank"
                           rel="noopener noreferrer"
                           class="spotify-btn px-3 py-2 rounded text-cinema-white text-sm font-medium whitespace-nowrap">
                            Spotify
                        </a>
                    ` : ''}
                    ${episode.applePodcastsUrl ? `
                        <a href="${episode.applePodcastsUrl}"
                           target="_blank"
                           rel="noopener noreferrer"
                           class="apple-btn px-3 py-2 rounded text-cinema-white text-sm font-medium whitespace-nowrap">
                            Apple
                        </a>
                    ` : ''}
                </div>
            </article>
        `;
    }

    renderStreamingBadges(streaming) {
        const badges = [];

        const serviceMap = {
            netflix: { name: 'Netflix', class: 'badge-netflix' },
            stan: { name: 'Stan', class: 'badge-stan' },
            primeVideo: { name: 'Prime', class: 'badge-prime' },
            disneyPlus: { name: 'Disney+', class: 'badge-disney' },
            binge: { name: 'Binge', class: 'badge-binge' },
            paramount: { name: 'Paramount+', class: 'badge-paramount' },
            appleTv: { name: 'Apple TV+', class: 'badge-apple' },
            hboMax: { name: 'HBO Max', class: 'badge-max' }
        };

        // Check each streaming service
        for (const [key, config] of Object.entries(serviceMap)) {
            if (streaming[key]) {
                badges.push(`<span class="streaming-badge ${config.class} text-cinema-white">${config.name}</span>`);
            }
        }

        // If no streaming, show rent/buy
        if (badges.length === 0 && streaming.rentBuy.length > 0) {
            badges.push(`<span class="streaming-badge badge-rent text-cinema-white">Rent/Buy</span>`);
        }

        // If nothing available
        if (badges.length === 0) {
            badges.push(`<span class="streaming-badge bg-gray-300 text-gray-600">Not Available</span>`);
        }

        return badges.join('');
    }

}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new RewatchablesApp();
});
