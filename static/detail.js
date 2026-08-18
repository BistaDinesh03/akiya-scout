// Akiya Scout - Property Detail Page
// Handles property detail display and map

let map = null;
let marker = null;

document.addEventListener('DOMContentLoaded', () => {
    // Get property ID from URL
    const pathParts = window.location.pathname.split('/');
    const propertyId = pathParts[pathParts.length - 1];
    
    if (propertyId) {
        loadPropertyDetail(propertyId);
    }
});

// Load property details from API
async function loadPropertyDetail(propertyId) {
    try {
        const response = await fetch(`/api/properties/${propertyId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        displayPropertyDetail(data);
        
    } catch (error) {
        console.error('Error loading property:', error);
        showError(error.message);
    }
}

// Display property details
function displayPropertyDetail(data) {
    const property = data.property;
    const valuation = data.valuation;
    
    // Hide loading, show detail
    document.getElementById('loading-state').classList.add('hidden');
    document.getElementById('property-detail').classList.remove('hidden');
    
    // Photos
    if (property.image_url) {
        document.getElementById('main-photo').src = property.image_url;
        document.getElementById('main-photo').alt = property.title || 'Property photo';
    } else {
        document.getElementById('photo-gallery').style.display = 'none';
    }
    
    // Title and price
    document.getElementById('property-title').textContent = property.title || 'Untitled Property';
    document.getElementById('property-price').textContent = property.price ? `¥${formatPrice(property.price)}` : 'Price not available';
    document.getElementById('property-location').textContent = `${property.prefecture || 'Unknown'} / ${property.municipality || 'Unknown'}${property.area ? ' / ' + property.area : ''}`;
    
    // Classification
    displayClassification(property, valuation);
    
    // Property details grid
    displayPropertyDetails(property);
    
    // Score breakdown
    displayScoreBreakdown(valuation);
    
    // Cost estimates
    displayCostEstimates(property, valuation);
    
    // Map
    initializeMap(property);
    
    // Source info
    displaySourceInfo(property);
    
    // Original listing link
    if (property.source_url) {
        document.getElementById('original-listing').href = property.source_url;
    } else {
        document.getElementById('original-listing').style.display = 'none';
    }
}

// Display GOOD / WATCH / UNKNOWN classification
function displayClassification(property, valuation) {
    const goodPoints = [];
    const watchPoints = [];
    const unknownPoints = [];
    
    // Analyze score breakdown
    valuation.breakdown.forEach(item => {
        const percentage = item.max_score > 0 ? (item.score / item.max_score) * 100 : 0;
        
        if (percentage >= 70) {
            goodPoints.push(`${item.category}: ${item.explanation}`);
        } else if (percentage >= 40) {
            watchPoints.push(`${item.category}: ${item.explanation}`);
        } else {
            unknownPoints.push(`${item.category}: ${item.explanation}`);
        }
    });
    
    // Price-specific classifications
    if (property.price && property.price <= 3000000) {
        goodPoints.push(`Price: Affordable at ¥${formatPrice(property.price)}`);
    } else if (property.price && property.price > 10000000) {
        watchPoints.push(`Price: Higher at ¥${formatPrice(property.price)}`);
    } else if (!property.price) {
        unknownPoints.push('Price: Not specified');
    }
    
    // Land size classifications
    if (property.land_size_m2 && property.land_size_m2 >= 300) {
        goodPoints.push(`Land: Large at ${property.land_size_m2} m²`);
    } else if (property.land_size_m2 && property.land_size_m2 < 100) {
        watchPoints.push(`Land: Small at ${property.land_size_m2} m²`);
    } else if (!property.land_size_m2) {
        unknownPoints.push('Land size: Not specified');
    }
    
    // Building age classifications
    if (property.build_year) {
        const buildingAge = 2026 - property.build_year;
        if (buildingAge <= 20) {
            goodPoints.push(`Age: Relatively new (${buildingAge} years)`);
        } else if (buildingAge > 50) {
            watchPoints.push(`Age: Old building (${buildingAge} years)`);
        }
    } else {
        unknownPoints.push('Build year: Not specified');
    }
    
    // Update UI
    document.getElementById('good-points').innerHTML = goodPoints.map(p => `<li>✓ ${p}</li>`).join('');
    document.getElementById('watch-points').innerHTML = watchPoints.map(p => `<li>⚠ ${p}</li>`).join('');
    document.getElementById('unknown-points').innerHTML = unknownPoints.map(p => `<li>? ${p}</li>`).join('');
    
    // Hide empty sections
    if (goodPoints.length === 0) document.getElementById('good-section').style.display = 'none';
    if (watchPoints.length === 0) document.getElementById('watch-section').style.display = 'none';
    if (unknownPoints.length === 0) document.getElementById('unknown-section').style.display = 'none';
}

// Display property details grid
function displayPropertyDetails(property) {
    const grid = document.getElementById('property-details-grid');
    const details = [
        { label: 'Land Size', value: property.land_size_m2 ? `${property.land_size_m2} m²` : 'N/A' },
        { label: 'Building Size', value: property.building_size_m2 ? `${property.building_size_m2} m²` : 'N/A' },
        { label: 'Build Year', value: property.build_year || 'N/A' },
        { label: 'Rooms', value: property.rooms || 'N/A' },
        { label: 'Structure', value: property.structure || 'N/A' },
        { label: 'Floors', value: property.floors || 'N/A' },
        { label: 'Parking', value: property.parking || 'N/A' },
        { label: 'Description', value: property.description || 'N/A' },
    ];
    
    grid.innerHTML = details.map(d => `
        <div class="detail-item">
            <div class="detail-item-label">${d.label}</div>
            <div class="detail-item-value">${d.value}</div>
        </div>
    `).join('');
}

// Display score breakdown
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

// Display cost estimates
function displayCostEstimates(property, valuation) {
    const costEstimates = document.getElementById('cost-estimates');
    
    const renovationCost = valuation.estimated_renovation_cost;
    const totalCost = valuation.estimated_total_cost;
    
    let costHtml = `
        <div class="cost-estimate-item">
            <span class="cost-estimate-label">Purchase Price</span>
            <span class="cost-estimate-value">${property.price ? `¥${formatPrice(property.price)}` : 'N/A'}</span>
        </div>
        <div class="cost-estimate-item">
            <span class="cost-estimate-label">Estimated Renovation</span>
            <span class="cost-estimate-value">¥${formatPrice(renovationCost)}</span>
        </div>
        <div class="cost-estimate-item">
            <span class="cost-estimate-label">Estimated Total Cost</span>
            <span class="cost-estimate-value">${totalCost ? `¥${formatPrice(totalCost)}` : 'N/A'}</span>
        </div>
        <div class="cost-estimate-item">
            <span class="cost-estimate-label">Disclaimer</span>
            <span class="cost-estimate-value" style="font-size: 0.875rem; color: var(--text-secondary);">${valuation.disclaimer}</span>
        </div>
    `;
    
    costEstimates.innerHTML = costHtml;
}

// Initialize map
function initializeMap(property) {
    const mapElement = document.getElementById('map');
    const mapUnavailable = document.getElementById('map-unavailable');
    
    // Only show map if coordinates exist
    if (property.latitude && property.longitude) {
        mapElement.style.display = 'block';
        mapUnavailable.classList.add('hidden');
        
        // Initialize Leaflet map
        if (map === null) {
            map = L.map('map').setView([property.latitude, property.longitude], 15);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);
        } else {
            map.setView([property.latitude, property.longitude], 15);
        }
        
        // Add marker
        if (marker) {
            map.removeLayer(marker);
        }
        
        marker = L.marker([property.latitude, property.longitude]).addTo(map);
        marker.bindPopup(property.title || 'Property location').openPopup();
        
    } else {
        // Show coordinates unavailable message
        mapElement.style.display = 'none';
        mapUnavailable.classList.remove('hidden');
    }
}

// Display source information
function displaySourceInfo(property) {
    const sourceInfo = document.getElementById('source-info');
    
    const collectedTime = property.collected_at ? new Date(property.collected_at).toLocaleString() : 'N/A';
    
    sourceInfo.innerHTML = `
        <div class="source-item">
            <span class="source-label">Source:</span>
            <span class="source-value">${property.source_name || 'N/A'}</span>
        </div>
        <div class="source-item">
            <span class="source-label">Source URL:</span>
            <span class="source-value">${property.source_url || 'N/A'}</span>
        </div>
        <div class="source-item">
            <span class="source-label">Collected:</span>
            <span class="source-value">${collectedTime}</span>
        </div>
    `;
}

// Show error state
function showError(message) {
    document.getElementById('loading-state').classList.add('hidden');
    document.getElementById('error-state').classList.remove('hidden');
    document.getElementById('error-message').textContent = message;
}

// Format price with commas
function formatPrice(price) {
    return price.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}