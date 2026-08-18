// Akiya Scout - Frontend Application
let currentListingType = 'SALE';
let currentResults = [];

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    searchProperties();
});

function setupEventListeners() {
    document.getElementById('search-form').addEventListener('submit', handleSearch);
    document.getElementById('reset-btn').addEventListener('click', resetFilters);
    
    // Listing type toggle
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentListingType = btn.dataset.type;
            searchProperties();
        });
    });
}

function handleSearch(event) {
    event.preventDefault();
    searchProperties();
}

function resetFilters() {
    document.getElementById('search-form').reset();
    currentListingType = 'SALE';
    document.querySelectorAll('.toggle-btn').forEach(b => {
        b.classList.remove('active');
        if (b.dataset.type === 'SALE') b.classList.add('active');
    });
    searchProperties();
}

async function searchProperties() {
    showState('loading');
    
    try {
        const params = new URLSearchParams();
        
        const maxPrice = document.getElementById('max-price').value;
        const prefecture = document.getElementById('prefecture').value;
        const municipality = document.getElementById('municipality').value;
        const minLand = document.getElementById('min-land').value;
        const minBuilding = document.getElementById('min-building').value;
        const minRooms = document.getElementById('min-rooms').value;
        const parking = document.getElementById('parking').value;
        const sort = document.getElementById('sort').value;
        
        if (maxPrice) params.append('max_price', maxPrice);
        if (prefecture) params.append('prefecture', prefecture);
        if (municipality) params.append('municipality', municipality);
        if (minLand) params.append('min_land', minLand);
        if (minBuilding) params.append('min_building', minBuilding);
        if (minRooms) params.append('min_rooms', minRooms);
        if (parking) params.append('parking', parking);
        if (sort) params.append('sort', sort);
        
        if (currentListingType !== 'ALL') {
            params.append('listing_type', currentListingType);
        }
        
        params.append('real_listings_only', 'true');
        
        const response = await fetch(`/api/properties?${params.toString()}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        document.getElementById('results-count').textContent = `${data.total} properties found`;
        
        if (data.properties.length === 0) {
            showState('empty');
            // Update empty message based on listing type
            const emptyMsg = document.querySelector('#empty-state p');
            if (currentListingType === 'SALE') {
                emptyMsg.textContent = 'No sale properties found. Try For Rent or All.';
            } else if (currentListingType === 'RENTAL') {
                emptyMsg.textContent = 'No rental properties found. Try For Sale or All.';
            } else {
                emptyMsg.textContent = 'No properties found. Try adjusting your filters.';
            }
        } else {
            displayProperties(data.properties);
        }
        
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('error-message').textContent = error.message;
        showState('error');
    }
}

function displayProperties(properties) {
    const grid = document.getElementById('results-grid');
    grid.innerHTML = '';
    
    properties.forEach(prop => {
        grid.appendChild(createPropertyCard(prop));
    });
    
    showState('results');
}

function createPropertyCard(prop) {
    const card = document.createElement('div');
    card.className = 'property-card';
    
    const listingType = prop.listing_type === 'RENTAL' ? 'For Rent' : 'For Sale';
    const priceDisplay = prop.listing_type === 'RENTAL' 
        ? `¥${formatNumber(prop.price)}/month`
        : `¥${formatNumber(prop.price)}`;
    
    const imageHtml = prop.image_url
        ? `<img src="${prop.image_url}" alt="${prop.title}" class="property-image" onerror="this.parentElement.innerHTML='<div class=\\'property-image-placeholder\\'>No property image available</div>'">`
        : `<div class="property-image-placeholder">No property image available</div>`;
    
    card.innerHTML = `
        <div class="property-image-container">${imageHtml}</div>
        <div class="property-card-body">
            <div class="property-badge-row">
                <span class="property-badge badge-real">Real Listing</span>
                <span class="property-badge ${prop.listing_type === 'RENTAL' ? 'badge-rental' : 'badge-sale'}">${listingType}</span>
            </div>
            <h3 class="property-title" title="${prop.title}">${prop.title || 'Untitled'}</h3>
            <div class="property-price">${priceDisplay}</div>
            <div class="property-location">${prop.prefecture || ''} · ${prop.municipality || ''}</div>
            
            <div class="property-specs">
                ${prop.land_size_m2 ? `<div class="spec-item"><strong>Land</strong> ${formatNumber(prop.land_size_m2)} m²</div>` : ''}
                ${prop.building_size_m2 ? `<div class="spec-item"><strong>Building</strong> ${formatNumber(prop.building_size_m2)} m²</div>` : ''}
                ${prop.build_year ? `<div class="spec-item"><strong>Built</strong> ${prop.build_year}</div>` : ''}
                ${prop.rooms ? `<div class="spec-item"><strong>Rooms</strong> ${prop.rooms}</div>` : ''}
            </div>
            
            ${prop.akiya_score ? `
            <div class="property-score">
                <div class="score-row">
                    <span class="score-label">Akiya Score</span>
                    <span class="score-value">${prop.akiya_score} / 100</span>
                </div>
                <div class="score-bar">
                    <div class="score-bar-fill" style="width: ${prop.akiya_score}%"></div>
                </div>
            </div>
            ` : ''}
            
            ${prop.estimated_total_cost ? `
            <div class="property-cost">
                <strong>Estimated total:</strong> ¥${formatNumber(prop.estimated_total_cost)}
            </div>
            ` : ''}
            
            <div class="property-actions">
                <a href="/property/${prop.id}" class="btn btn-primary">View Property</a>
                ${prop.source_url ? `<a href="${prop.source_url}" target="_blank" rel="noopener" class="btn btn-outline">Original Listing</a>` : ''}
            </div>
        </div>
    `;
    
    return card;
}

function showState(state) {
    document.getElementById('loading-state').classList.add('hidden');
    document.getElementById('error-state').classList.add('hidden');
    document.getElementById('empty-state').classList.add('hidden');
    document.getElementById('results-grid').classList.add('hidden');
    
    switch(state) {
        case 'loading':
            document.getElementById('loading-state').classList.remove('hidden');
            break;
        case 'error':
            document.getElementById('error-state').classList.remove('hidden');
            break;
        case 'empty':
            document.getElementById('empty-state').classList.remove('hidden');
            break;
        case 'results':
            document.getElementById('results-grid').classList.remove('hidden');
            break;
    }
}

function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    return Number(num).toLocaleString('en-US', { maximumFractionDigits: 2 });
}