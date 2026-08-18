// Akiya Scout - Frontend Application
// Handles property search, filtering, and display

document.addEventListener('DOMContentLoaded', () => {
    console.log('Akiya Scout application initialized');
    
    // Set up event listeners
    document.getElementById('search-form').addEventListener('submit', handleSearch);
    document.getElementById('reset-btn').addEventListener('click', resetFilters);
    
    // Load initial properties
    searchProperties();
});

// Global state
let currentResults = [];

// Handle search form submission
async function handleSearch(event) {
    event.preventDefault();
    await searchProperties();
}

// Reset all filters
function resetFilters() {
    document.getElementById('search-form').reset();
    searchProperties();
}

// Fetch and display properties
async function searchProperties() {
    // Show loading state
    showState('loading');
    
    try {
        // Build query parameters
        const params = new URLSearchParams();
        
        const maxPrice = document.getElementById('max-price').value;
        const maxTotalCost = document.getElementById('max-total-cost').value;
        const prefecture = document.getElementById('prefecture').value;
        const municipality = document.getElementById('municipality').value;
        const minLand = document.getElementById('min-land').value;
        const minBuilding = document.getElementById('min-building').value;
        const minRooms = document.getElementById('min-rooms').value;
        const parking = document.getElementById('parking').value;
        
        if (maxPrice) params.append('max_price', maxPrice);
        if (maxTotalCost) params.append('max_total_cost', maxTotalCost);
        if (prefecture) params.append('prefecture', prefecture);
        if (municipality) params.append('municipality', municipality);
        if (minLand) params.append('min_land', minLand);
        if (minBuilding) params.append('min_building', minBuilding);
        if (minRooms) params.append('min_rooms', minRooms);
        if (parking) params.append('parking', parking);
        
        // Add sort parameter
        params.append('sort', 'price_asc');
        
        // Fetch properties
        const response = await fetch(`/api/properties?${params.toString()}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        currentResults = data.properties;
        
        // Update results count
        document.getElementById('results-count').textContent = `${data.total} properties found`;
        
        // Display results
        if (data.properties.length === 0) {
            showState('empty');
        } else {
            displayProperties(data.properties);
        }
        
    } catch (error) {
        console.error('Error fetching properties:', error);
        document.getElementById('error-message').textContent = error.message;
        showState('error');
    }
}

// Display properties in results grid
function displayProperties(properties) {
    const resultsGrid = document.getElementById('results-grid');
    resultsGrid.innerHTML = '';
    
    properties.forEach(property => {
        const card = createPropertyCard(property);
        resultsGrid.appendChild(card);
    });
    
    showState('results');
}

// Create property card element
function createPropertyCard(property) {
    const card = document.createElement('div');
    card.className = 'property-card';
    
    // Calculate score percentage for progress bar
    const scorePercent = property.akiya_score || 0;
    
    // Format price
    const price = property.price ? `¥${formatPrice(property.price)}` : 'Price not available';
    const totalCost = property.estimated_total_cost ? `¥${formatPrice(property.estimated_total_cost)}` : 'N/A';
    const renovationCost = property.estimated_renovation_cost ? `¥${formatPrice(property.estimated_renovation_cost)}` : 'N/A';
    
    card.innerHTML = `
        ${property.image_url ? `
        <img src="${property.image_url}" alt="${property.title}" class="property-image" onerror="this.style.display='none'">
        ` : ''}
        
        <div class="property-card-content">
            <span class="property-badge">Real Listing</span>
            
            <h3 class="property-title">${property.title || 'Untitled Property'}</h3>
            
            <div class="property-price">${price}</div>
            
            <div class="property-location">
                ${property.prefecture || 'Unknown'} / ${property.municipality || 'Unknown'}
            </div>
            
            <div class="property-details">
                ${property.land_size_m2 ? `
                <div class="detail-item">
                    <strong>Land:</strong> ${property.land_size_m2} m²
                </div>
                ` : ''}
                
                ${property.building_size_m2 ? `
                <div class="detail-item">
                    <strong>Building:</strong> ${property.building_size_m2} m²
                </div>
                ` : ''}
                
                ${property.build_year ? `
                <div class="detail-item">
                    <strong>Built:</strong> ${property.build_year}
                </div>
                ` : ''}
                
                ${property.rooms ? `
                <div class="detail-item">
                    <strong>Rooms:</strong> ${property.rooms}
                </div>
                ` : ''}
            </div>
            
            ${property.akiya_score ? `
            <div class="property-score">
                <div class="score-label">Akiya Score: ${property.akiya_score}/100</div>
                <div class="score-bar">
                    <div class="score-fill" style="width: ${scorePercent}%"></div>
                </div>
            </div>
            ` : ''}
            
            <div class="property-costs">
                <div class="cost-item">
                    <span>Estimated renovation:</span>
                    <strong>${renovationCost}</strong>
                </div>
                <div class="cost-item">
                    <span>Estimated total:</span>
                    <strong>${totalCost}</strong>
                </div>
            </div>
            
            <div class="property-actions">
                <button class="btn btn-primary" onclick="viewProperty('${property.source_url}')">
                    View Property
                </button>
                <button class="btn btn-link" onclick="viewProperty('${property.source_url}')">
                    Original Listing
                </button>
            </div>
        </div>
    `;
    
    return card;
}

// Open property link in new tab
function viewProperty(url) {
    if (url) {
        window.open(url, '_blank');
    }
}

// Show specific state (loading, error, empty, or results)
function showState(state) {
    const loadingState = document.getElementById('loading-state');
    const errorState = document.getElementById('error-state');
    const emptyState = document.getElementById('empty-state');
    const resultsGrid = document.getElementById('results-grid');
    
    // Hide all states
    loadingState.classList.add('hidden');
    errorState.classList.add('hidden');
    emptyState.classList.add('hidden');
    resultsGrid.classList.add('hidden');
    
    // Show the requested state
    switch(state) {
        case 'loading':
            loadingState.classList.remove('hidden');
            break;
        case 'error':
            errorState.classList.remove('hidden');
            break;
        case 'empty':
            emptyState.classList.remove('hidden');
            break;
        case 'results':
            resultsGrid.classList.remove('hidden');
            break;
    }
}

// Format price with commas
function formatPrice(price) {
    return price.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Format renovation cost range (placeholder for future implementation)
function formatCostRange(min, max) {
    return `¥${formatPrice(min)}–¥${formatPrice(max)}`;
}