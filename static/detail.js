// Akiya Scout - Property Detail Page
let map = null;
let marker = null;

document.addEventListener('DOMContentLoaded', () => {
    const pathParts = window.location.pathname.split('/');
    const propertyId = pathParts[pathParts.length - 1];
    
    if (propertyId) {
        loadPropertyDetail(propertyId);
    }
});

async function loadPropertyDetail(propertyId) {
    try {
        const response = await fetch(`/api/properties/${propertyId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error || data.detail) {
            showError(data.error || data.detail);
            return;
        }
        
        displayPropertyDetail(data);
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
    }
}

function displayPropertyDetail(data) {
    const property = data.property;
    const valuation = data.valuation;
    
    document.getElementById('loading-state').classList.add('hidden');
    document.getElementById('property-detail').classList.remove('hidden');
    
    // Photo
    if (property.image_url) {
        document.getElementById('main-photo').src = property.image_url;
        document.getElementById('main-photo').alt = property.title || 'Property photo';
        document.getElementById('main-photo').classList.remove('hidden');
        document.getElementById('photo-placeholder').classList.add('hidden');
    } else {
        document.getElementById('main-photo').classList.add('hidden');
        document.getElementById('photo-placeholder').classList.remove('hidden');
    }
    
    // Title, price, location
    document.getElementById('property-title').textContent = property.title || 'Untitled Property';
    
    if (property.listing_type === 'RENTAL') {
        document.getElementById('listing-type-badge').textContent = 'For Rent';
        document.getElementById('listing-type-badge').className = 'property-badge badge-rental';
        document.getElementById('property-price').textContent = property.price ? `¥${formatNumber(property.price)}/month` : 'Price N/A';
    } else {
        document.getElementById('listing-type-badge').textContent = 'For Sale';
        document.getElementById('listing-type-badge').className = 'property-badge badge-sale';
        document.getElementById('property-price').textContent = property.price ? `¥${formatNumber(property.price)}` : 'Price N/A';
    }
    
    document.getElementById('property-location').textContent = 
        `${property.prefecture || 'Unknown'} · ${property.municipality || 'Unknown'}${property.area ? ' · ' + property.area : ''}`;
    
    // Property details grid
    displayPropertyDetails(property);
    
    // Score breakdown (SALE only)
    if (valuation) {
        displayScoreBreakdown(valuation);
        displayCostEstimates(property, valuation);
    } else {
        document.getElementById('score-section').style.display = 'none';
        document.getElementById('cost-section').style.display = 'none';
    }
    
    // Classification
    displayClassification(property, valuation);
    
    // Map
    initializeMap(property);
    
    // Source info
    displaySourceInfo(property);
    
    // Original listing
    if (property.source_url) {
        document.getElementById('original-listing').href = property.source_url;
    } else {
        document.getElementById('original-listing').style.display = 'none';
    }
}

function displayPropertyDetails(property) {
    const grid = document.getElementById('property-details-grid');
    const details = [
        { label: 'Land', value: property.land_size_m2 ? `${formatNumber(property.land_size_m2)} m²` : 'N/A' },
        { label: 'Building', value: property.building_size_m2 ? `${formatNumber(property.building_size_m2)} m²` : 'N/A' },
        { label: 'Built', value: property.build_year || 'N/A' },
        { label: 'Rooms', value: property.rooms || 'N/A' },
        { label: 'Structure', value: property.structure || 'N/A' },
        { label: 'Parking', value: property.parking || 'N/A' },
    ];
    
    grid.innerHTML = details.map(d => `
        <div class="detail-item">
            <div class="detail-item-label">${d.label}</div>
            <div class="detail-item-value">${d.value}</div>
        </div>
    `).join('');
}

function displayScoreBreakdown(valuation) {
    document.getElementById('total-score-value').textContent = Math.round(valuation.akiya_score);
    
    const breakdownList = document.getElementById('breakdown-list');
    breakdownList.innerHTML = valuation.breakdown.map(item => `
        <div class="breakdown-item">
            <div>
                <div class="breakdown-category">${item.category}</div>
                <div class="breakdown-explanation">${item.explanation}</div>
            </div>
            <div class="breakdown-score">${Math.round(item.score)}/${item.max_score}</div>
        </div>
    `).join('');
}

function displayCostEstimates(property, valuation) {
    const costEstimates = document.getElementById('cost-estimates');
    
    costEstimates.innerHTML = `
        <div class="cost-estimate-item">
            <span class="cost-estimate-label">Purchase Price</span>
            <span class="cost-estimate-value">${property.price ? `¥${formatNumber(property.price)}` : 'N/A'}</span>
        </div>
        <div class="cost-estimate-item">
            <span class="cost-estimate-label">Estimated Renovation</span>
            <span class="cost-estimate-value">¥${formatNumber(valuation.estimated_renovation_cost)}</span>
        </div>
        <div class="cost-estimate-item">
            <span class="cost-estimate-label">Estimated Total</span>
            <span class="cost-estimate-value">¥${formatNumber(valuation.estimated_total_cost)}</span>
        </div>
        <div class="cost-estimate-disclaimer">${valuation.disclaimer}</div>
    `;
}

function displayClassification(property, valuation) {
    const goodPoints = [];
    const watchPoints = [];
    const unknownPoints = [];
    
    if (valuation) {
        valuation.breakdown.forEach(item => {
            const pct = item.max_score > 0 ? (item.score / item.max_score) * 100 : 0;
            if (pct >= 70) goodPoints.push(`${item.category}: ${item.explanation}`);
            else if (pct >= 40) watchPoints.push(`${item.category}: ${item.explanation}`);
            else unknownPoints.push(`${item.category}: ${item.explanation}`);
        });
    }
    
    if (property.price && property.listing_type === 'SALE' && property.price <= 3000000) {
        goodPoints.push(`Price: Affordable at ¥${formatNumber(property.price)}`);
    } else if (property.price && property.listing_type === 'SALE' && property.price > 10000000) {
        watchPoints.push(`Price: Higher at ¥${formatNumber(property.price)}`);
    } else if (!property.price) {
        unknownPoints.push('Price: Not specified');
    }
    
    if (property.land_size_m2 && property.land_size_m2 >= 300) {
        goodPoints.push(`Land: Large at ${formatNumber(property.land_size_m2)} m²`);
    } else if (property.land_size_m2 && property.land_size_m2 < 100) {
        watchPoints.push(`Land: Small at ${formatNumber(property.land_size_m2)} m²`);
    } else if (!property.land_size_m2) {
        unknownPoints.push('Land: Not specified');
    }
    
    if (property.build_year) {
        const age = 2026 - property.build_year;
        if (age <= 20) goodPoints.push(`Age: Relatively new (${age} years)`);
        else if (age > 50) watchPoints.push(`Age: Old (${age} years)`);
    } else {
        unknownPoints.push('Build year: Not specified');
    }
    
    document.getElementById('good-points').innerHTML = goodPoints.map(p => `<li>${p}</li>`).join('');
    document.getElementById('watch-points').innerHTML = watchPoints.map(p => `<li>${p}</li>`).join('');
    document.getElementById('unknown-points').innerHTML = unknownPoints.map(p => `<li>${p}</li>`).join('');
    
    if (goodPoints.length === 0) document.getElementById('good-section').style.display = 'none';
    if (watchPoints.length === 0) document.getElementById('watch-section').style.display = 'none';
    if (unknownPoints.length === 0) document.getElementById('unknown-section').style.display = 'none';
}

function initializeMap(property) {
    const mapElement = document.getElementById('map');
    const mapUnavailable = document.getElementById('map-unavailable');
    
    if (property.latitude && property.longitude) {
        mapElement.style.display = 'block';
        mapUnavailable.classList.add('hidden');
        
        if (map === null) {
            map = L.map('map').setView([property.latitude, property.longitude], 15);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors'
            }).addTo(map);
        } else {
            map.setView([property.latitude, property.longitude], 15);
        }
        
        if (marker) map.removeLayer(marker);
        marker = L.marker([property.latitude, property.longitude]).addTo(map);
        marker.bindPopup(property.title || 'Property').openPopup();
    } else {
        mapElement.style.display = 'none';
        mapUnavailable.classList.remove('hidden');
    }
}

function displaySourceInfo(property) {
    const sourceInfo = document.getElementById('source-info');
    const collected = property.collected_at ? new Date(property.collected_at).toLocaleString() : 'N/A';
    
    sourceInfo.innerHTML = `
        <div class="source-item">
            <span class="source-label">Source</span>
            <span class="source-value">${property.source_name || 'N/A'}</span>
        </div>
        <div class="source-item">
            <span class="source-label">Collected</span>
            <span class="source-value">${collected}</span>
        </div>
        <div class="source-item">
            <span class="source-label">Last Checked</span>
            <span class="source-value">${collected}</span>
        </div>
        <div class="source-disclaimer">
            Akiya Scout does not independently verify ownership, structural condition, legal status, or availability.
        </div>
    `;
}

function showError(message) {
    document.getElementById('loading-state').classList.add('hidden');
    document.getElementById('error-state').classList.remove('hidden');
    document.getElementById('error-message').textContent = message;
}

function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    return Number(num).toLocaleString('en-US', { maximumFractionDigits: 2 });
}