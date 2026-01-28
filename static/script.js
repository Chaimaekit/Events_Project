let allEvents = [];
let currentPage = 1;
let totalPages = 1;
let currentView = 'grid';
let currentUser = 'guest';
let favorites = new Set();

const state = {
    search: '',
    city: '',
    category: '',
    date: '',
    upcoming: false,
    sort: 'date_desc'
};

const filterToggle = document.getElementById('filter-toggle');
const closeFilters = document.getElementById('close-filters');
const filtersPanel = document.getElementById('filters-panel');
const quickSearch = document.getElementById('quick-search');
const citySelect = document.getElementById('city-select');
const categorySelect = document.getElementById('category-select');
const dateInput = document.getElementById('date-input');
const sortSelect = document.getElementById('sort-select');
const applyFiltersBtn = document.getElementById('apply-filters');
const resetFiltersBtn = document.getElementById('reset-filters');
const eventsGrid = document.getElementById('events-grid');
const loadingDiv = document.getElementById('loading');
const emptyState = document.getElementById('empty-state');
const pagination = document.getElementById('pagination');
const pageInfo = document.getElementById('page-info');
const prevPage = document.getElementById('prev-page');
const nextPage = document.getElementById('next-page');
const viewToggle = document.getElementById('view-toggle');
const calendarBtn = document.getElementById('calendar-btn');
const favoritesBtn = document.getElementById('favorites-btn');
const statsBar = document.getElementById('stats-bar');
const eventModal = document.getElementById('event-modal');
const modalClose = document.getElementById('modal-close');
const shareModal = document.getElementById('share-modal');
const shareClose = document.getElementById('share-close');
const copyLinkBtn = document.getElementById('copy-link');
const calendarView = document.getElementById('calendar-view');


document.addEventListener('DOMContentLoaded', () => {
    loadFilterOptions();
    loadStats();
    loadFavorites();
    performSearch();
    setupEventListeners();
});


function setupEventListeners() {
    filterToggle.addEventListener('click', toggleFilters);
    closeFilters.addEventListener('click', toggleFilters);
    applyFiltersBtn.addEventListener('click', applyFilters);
    resetFiltersBtn.addEventListener('click', resetFilters);
    prevPage.addEventListener('click', () => goToPage(currentPage - 1));
    nextPage.addEventListener('click', () => goToPage(currentPage + 1));
    viewToggle.addEventListener('click', toggleView);
    calendarBtn.addEventListener('click', showCalendar);
    favoritesBtn.addEventListener('click', showFavorites);
    modalClose.addEventListener('click', closeModal);
    shareClose.addEventListener('click', closeShareModal);
    copyLinkBtn.addEventListener('click', copyShareLink);

    quickSearch.addEventListener('input', debounce(() => {
        state.search = quickSearch.value;
        currentPage = 1;
        performSearch();
    }, 300));

    sortSelect.addEventListener('change', (e) => {
        state.sort = e.target.value;
        currentPage = 1;
        performSearch();
    });

    const upcomingCheckbox = document.getElementById('upcoming-checkbox');
    if (upcomingCheckbox) {
        upcomingCheckbox.addEventListener('change', (e) => {
            state.upcoming = e.target.checked;
            currentPage = 1;
            performSearch();
        });
    }

    window.addEventListener('click', (e) => {
        if (e.target === eventModal) closeModal();
        if (e.target === shareModal) closeShareModal();
    });
}

function toggleFilters() {
    filtersPanel.classList.toggle('active');
}

function toggleView() {
    currentView = currentView === 'grid' ? 'list' : 'grid';
    viewToggle.textContent = currentView === 'grid' ? '📝 List' : '🔲 Grid';
    eventsGrid.classList.toggle('list-view');
}


async function loadFilterOptions() {
    try {
        const response = await fetch('/filters');
        const data = await response.json();

        if (data.cities) {
            data.cities.forEach(city => {
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                citySelect.appendChild(option);
            });
        }

        if (data.categories) {
            data.categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                categorySelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading filter options:', error);
    }
}


async function loadStats() {
    try {
        const response = await fetch('/stats');
        const data = await response.json();
        
        document.getElementById('stat-total').textContent = data.total_events;
        document.getElementById('stat-upcoming').textContent = data.upcoming_events;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}


async function performSearch() {
    showLoading();
    try {
        const params = new URLSearchParams({
            q: state.search,
            city: state.city,
            category: state.category,
            date: state.date,
            upcoming: state.upcoming,
            page: currentPage,
            size: 12,
            sort: state.sort
        });

        const response = await fetch(`/search?${params}`);
        const data = await response.json();

        allEvents = data.events || [];
        totalPages = data.pages || 1;
        
        renderEvents(allEvents);
        updatePagination();
        filtersPanel.classList.remove('active');
    } catch (error) {
        console.error('Search error:', error);
        showEmpty();
    }
}

function applyFilters() {
    state.city = citySelect.value;
    state.category = categorySelect.value;
    state.date = dateInput.value;
    currentPage = 1;
    performSearch();
}

function resetFilters() {
    quickSearch.value = '';
    citySelect.value = '';
    categorySelect.value = '';
    dateInput.value = '';
    sortSelect.value = 'date_desc';
    const upcomingCheckbox = document.getElementById('upcoming-checkbox');
    if (upcomingCheckbox) upcomingCheckbox.checked = false;
    state.search = '';
    state.city = '';
    state.category = '';
    state.date = '';
    state.upcoming = false;
    state.sort = 'date_desc';
    currentPage = 1;
    performSearch();
}

function renderEvents(events) {
    eventsGrid.innerHTML = '';

    if (events.length === 0) {
        hideLoading();
        showEmpty();
        return;
    }

    events.forEach((event, index) => {
        const card = createEventCard(event);
        card.style.animationDelay = `${index * 0.05}s`;
        eventsGrid.appendChild(card);
    });

    hideLoading();
    emptyState.style.display = 'none';
}

function createEventCard(event) {
    const card = document.createElement('div');
    card.className = 'event-card';
    
    const isFavorited = favorites.has(event.id);
    const imageUrl = event.img || 'https://images.unsplash.com/photo-1533900298318-6b8da08a523e?w=500&h=300&fit=crop';
    const title = event.name || 'Untitled Event';
    const description = event.description || 'No description available';
    const category = Array.isArray(event.category) ? event.category[0] : (typeof event.category === 'string' ? event.category : 'Event');
    const city = event.city || 'Location TBA';
    const place = event.place || 'TBA';
    
    let dateStr = '';
    if (event.date) {
        if (typeof event.date === 'string') {
            dateStr = event.date;
        } else if (event.date.startAt) {
            dateStr = event.date.startAt;
        } else if (event.date.customDate) {
            dateStr = event.date.customDate;
        }
    }
    const date = formatDate(dateStr);

    card.innerHTML = `
        <img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(title)}" class="event-image" 
             onerror="this.src='https://images.unsplash.com/photo-1533900298318-6b8da08a523e?w=500&h=300&fit=crop'">
        
        <div class="event-content">
            <div class="event-header">
                <div>
                    <div class="event-category">${escapeHtml(category)}</div>
                    <h3 class="event-title">${escapeHtml(title)}</h3>
                </div>
                <button class="favorite-btn ${isFavorited ? 'favorited' : ''}" onclick="toggleFavorite('${event.id}', this)">
                    ${isFavorited ? '❤️' : '🤍'}
                </button>
            </div>
            
            <p class="event-description">${escapeHtml(description.substring(0, 100))}${description.length > 100 ? '...' : ''}</p>
            
            <div class="event-meta">
                <span class="meta-item">📍 ${escapeHtml(city)} • ${escapeHtml(place)}</span>
                <span class="meta-item">📅 ${date}</span>
            </div>

            <div class="event-footer">
                <button class="btn-secondary" onclick="openEventModal('${event.id}')">View Details</button>
                <a href="${escapeHtml(event.url)}" target="_blank" class="btn-primary">Visit Event →</a>
            </div>
        </div>
    `;

    return card;
}


async function openEventModal(eventId) {
    try {
        const response = await fetch(`/event/${eventId}`);
        const event = await response.json();
        
        // Fetch transport information
        let transportHTML = '';
        try {
            const transportResponse = await fetch(`/transport/${eventId}`);
            const transportData = await transportResponse.json();
            if (transportData.bus_lines && transportData.bus_lines.length > 0) {
                transportData.bus_lines.forEach(bus => {
                    transportHTML += `
                        <div class="bus-line-item">
                            <span class="bus-line-badge">L${bus.ligne_nb}</span>
                            <div style="flex: 1;">
                                <p style="margin: 0; font-weight: 600; color: var(--text-primary);">${bus.start} → ${bus.end}</p>
                                <p style="margin: 0; font-size: 0.85rem; color: var(--text-secondary);">${bus.distance_km} km away</p>
                            </div>
                        </div>
                    `;
                });
                document.getElementById('transport-info').style.display = 'block';
                document.getElementById('transport-content').innerHTML = transportHTML;
            } else {
                document.getElementById('transport-info').style.display = 'none';
            }
        } catch (error) {
            console.warn('Error loading transport info:', error);
            document.getElementById('transport-info').style.display = 'none';
        }
        
        let dateStr = '';
        if (event.date) {
            if (typeof event.date === 'string') {
                dateStr = event.date;
            } else if (event.date.startAt) {
                dateStr = event.date.startAt;
            } else if (event.date.customDate) {
                dateStr = event.date.customDate;
            }
        }
        
        document.getElementById('modal-image').src = event.img || 'https://images.unsplash.com/photo-1533900298318-6b8da08a523e?w=800&h=400&fit=crop';
        document.getElementById('modal-title').textContent = event.name;
        document.getElementById('modal-description').textContent = event.description;
        document.getElementById('modal-location').textContent = `${event.city}, ${event.place}`;
        document.getElementById('modal-date').textContent = formatDate(dateStr);
        document.getElementById('modal-category').textContent = Array.isArray(event.category) ? event.category.join(', ') : (event.category || 'N/A');
        document.getElementById('modal-producer').textContent = event.producer || 'N/A';
        document.getElementById('modal-link').href = event.url;
        
        document.getElementById('modal-favorite').textContent = favorites.has(event.id) ? '❤️ Remove from Favorites' : '❤️ Add to Favorites';
        document.getElementById('modal-favorite').onclick = () => toggleFavorite(event.id);
        document.getElementById('modal-share').onclick = () => openShareModal(event.name, event.url);
        
        eventModal.style.display = 'flex';
    } catch (error) {
        console.error('Error loading event details:', error);
    }
}

function closeModal() {
    eventModal.style.display = 'none';
}


function toggleFavorite(eventId, button) {
    if (favorites.has(eventId)) {
        favorites.delete(eventId);
        if (button) button.textContent = '🤍';
        removeFavorite(eventId);
    } else {
        favorites.add(eventId);
        if (button) button.textContent = '❤️';
        addFavorite(eventId);
    }
    
    if (button) button.classList.toggle('favorited');
}

async function addFavorite(eventId) {
    try {
        await fetch(`/favorites/${eventId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
    } catch (error) {
        console.error('Error adding favorite:', error);
    }
}

async function removeFavorite(eventId) {
    try {
        await fetch(`/favorites/${eventId}`, { method: 'DELETE' });
    } catch (error) {
        console.error('Error removing favorite:', error);
    }
}

async function loadFavorites() {
    try {
        const response = await fetch(`/favorites?user_id=${currentUser}`);
        const data = await response.json();
        data.favorites?.forEach(event => favorites.add(event.id));
    } catch (error) {
        console.error('Error loading favorites:', error);
    }
}

async function showFavorites() {
    try {
        const response = await fetch(`/favorites?user_id=${currentUser}`);
        const data = await response.json();
        
        allEvents = data.favorites || [];
        currentPage = 1;
        totalPages = 1;
        renderEvents(allEvents);
        updatePagination();
        
        calendarView.style.display = 'none';
        eventsGrid.style.display = 'grid';
    } catch (error) {
        console.error('Error loading favorites:', error);
    }
}


async function showCalendar() {
    const now = new Date();
    const month = now.getMonth() + 1;
    const year = now.getFullYear();
    
    try {
        const response = await fetch(`/calendar?month=${month}&year=${year}`);
        const data = await response.json();
        
        renderCalendar(data);
        calendarView.style.display = 'block';
        eventsGrid.style.display = 'none';
        emptyState.style.display = 'none';
    } catch (error) {
        console.error('Error loading calendar:', error);
    }
}

function renderCalendar(data) {
    const monthYear = document.getElementById('month-year');
    const calendarGrid = document.getElementById('calendar-grid');
    
    monthYear.textContent = new Date(data.year, data.month - 1).toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric'
    });
    
    calendarGrid.innerHTML = '';
    
    for (const [date, events] of Object.entries(data.events)) {
        const dayCell = document.createElement('div');
        dayCell.className = 'calendar-day';
        dayCell.innerHTML = `
            <strong>${new Date(date).getDate()}</strong>
            <span class="event-count">${events.length} event${events.length !== 1 ? 's' : ''}</span>
        `;
        dayCell.onclick = () => showDayEvents(events, date);
        calendarGrid.appendChild(dayCell);
    }
}

function showDayEvents(events, date) {
    allEvents = events;
    currentPage = 1;
    totalPages = 1;
    renderEvents(events);
    calendarView.style.display = 'none';
    eventsGrid.style.display = 'grid';
}


let shareData = { title: '', url: '' };

function openShareModal(title, url) {
    shareData = { title, url };
    shareModal.style.display = 'flex';
}

function closeShareModal() {
    shareModal.style.display = 'none';
}

function shareOnSocial(platform) {
    const text = `Check out: ${shareData.title}`;
    const urls = {
        twitter: `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(shareData.url)}`,
        facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareData.url)}`,
        whatsapp: `https://wa.me/?text=${encodeURIComponent(text + ' ' + shareData.url)}`
    };
    
    if (urls[platform]) {
        window.open(urls[platform], '_blank');
    }
}

function copyShareLink() {
    navigator.clipboard.writeText(shareData.url);
    copyLinkBtn.textContent = '✓ Copied!';
    setTimeout(() => {
        copyLinkBtn.textContent = '🔗 Copy Link';
    }, 2000);
}


function updatePagination() {
    const paginationNumbers = document.getElementById('pagination-numbers');
    if (!paginationNumbers) {
        console.error('Pagination numbers element not found');
        return;
    }
    paginationNumbers.innerHTML = '';
    
    const maxVisible = 7;
    let startPage = 1;
    let endPage = totalPages;
    
    if (totalPages > maxVisible) {
        startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        endPage = Math.min(totalPages, startPage + maxVisible - 1);
        
        if (endPage - startPage + 1 < maxVisible) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }
    }
    
    prevPage.disabled = currentPage === 1;
    
    if (startPage > 1) {
        const firstBtn = createPageButton(1);
        paginationNumbers.appendChild(firstBtn);
        
        if (startPage > 2) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'pagination-ellipsis';
            ellipsis.textContent = '...';
            paginationNumbers.appendChild(ellipsis);
        }
    }
    for (let i = startPage; i <= endPage; i++) {
        const btn = createPageButton(i);
        paginationNumbers.appendChild(btn);
    }
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'pagination-ellipsis';
            ellipsis.textContent = '...';
            paginationNumbers.appendChild(ellipsis);
        }
        
        const lastBtn = createPageButton(totalPages);
        paginationNumbers.appendChild(lastBtn);
    }
    nextPage.disabled = currentPage === totalPages;
}

function createPageButton(pageNum) {
    const btn = document.createElement('button');
    btn.className = 'pagination-number';
    btn.textContent = pageNum;
    
    if (pageNum === currentPage) {
        btn.classList.add('active');
    }
    
    btn.onclick = () => goToPage(pageNum);
    return btn;
}

function goToPage(page) {
    if (page >= 1 && page <= totalPages) {
        currentPage = page;
        performSearch();
        window.scrollTo(0, 0);
    }
}


function showLoading() {
    loadingDiv.style.display = 'flex';
    eventsGrid.style.display = 'none';
    emptyState.style.display = 'none';
}

function hideLoading() {
    loadingDiv.style.display = 'none';
    eventsGrid.style.display = 'grid';
}

function showEmpty() {
    loadingDiv.style.display = 'none';
    eventsGrid.style.display = 'none';
    emptyState.style.display = 'flex';
}


function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func(...args), delay);
    };
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString.replace(' ', 'T'));
        if (isNaN(date.getTime())) {
            return dateString;
        }
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    } catch (e) {
        return dateString;
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
