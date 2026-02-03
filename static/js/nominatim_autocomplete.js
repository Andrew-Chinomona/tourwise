/**
 * Nominatim Autocomplete for Zimbabwe Locations
 * Free OpenStreetMap-based location search
 * No API key required - completely free!
 */
class NominatimAutocomplete {
    constructor(inputElement, suggestionsElement, options = {}) {
        this.input = inputElement;
        this.suggestions = suggestionsElement;
        this.options = {
            countryCode: 'ZW',  // Zimbabwe
            limit: 5,
            debounceMs: 300,
            minChars: 2,
            ...options
        };
        
        this.debounceTimer = null;
        this.selectedIndex = -1;
        this.results = [];
        
        this.init();
    }
    
    init() {
        this.input.addEventListener('input', () => this.handleInput());
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        document.addEventListener('click', (e) => this.handleClickOutside(e));
    }
    
    handleInput() {
        clearTimeout(this.debounceTimer);
        const query = this.input.value.trim();
        
        if (query.length < this.options.minChars) {
            this.hideSuggestions();
            return;
        }
        
        this.debounceTimer = setTimeout(() => {
            this.search(query);
        }, this.options.debounceMs);
    }
    
    async search(query) {
        const url = new URL('https://nominatim.openstreetmap.org/search');
        url.searchParams.set('q', query);
        url.searchParams.set('format', 'json');
        url.searchParams.set('countrycodes', this.options.countryCode);
        url.searchParams.set('addressdetails', '1');
        url.searchParams.set('limit', this.options.limit);
        
        try {
            const response = await fetch(url, {
                headers: {
                    'User-Agent': 'TourWise Property Listings'  // Required by Nominatim
                }
            });
            
            if (!response.ok) throw new Error('Search failed');
            
            this.results = await response.json();
            this.displaySuggestions();
        } catch (error) {
            console.error('Nominatim search error:', error);
            this.hideSuggestions();
        }
    }
    
    displaySuggestions() {
        if (this.results.length === 0) {
            this.hideSuggestions();
            return;
        }
        
        this.suggestions.innerHTML = '';
        this.selectedIndex = -1;
        
        this.results.forEach((result, index) => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            item.textContent = result.display_name;
            item.dataset.index = index;
            
            item.addEventListener('click', () => {
                this.selectResult(result);
            });
            
            this.suggestions.appendChild(item);
        });
        
        this.suggestions.style.display = 'block';
    }
    
    selectResult(result) {
        this.input.value = result.display_name;
        this.hideSuggestions();
        
        // Fire custom event with location data
        const event = new CustomEvent('location-selected', {
            detail: {
                lat: parseFloat(result.lat),
                lon: parseFloat(result.lon),
                address: result.address,
                displayName: result.display_name
            }
        });
        this.input.dispatchEvent(event);
    }
    
    handleKeydown(e) {
        if (!this.suggestions.style.display || this.suggestions.style.display === 'none') {
            return;
        }
        
        const items = this.suggestions.querySelectorAll('.suggestion-item');
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            this.selectedIndex = (this.selectedIndex + 1) % items.length;
            this.updateSelection(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            this.selectedIndex = (this.selectedIndex - 1 + items.length) % items.length;
            this.updateSelection(items);
        } else if (e.key === 'Enter' && this.selectedIndex >= 0) {
            e.preventDefault();
            this.selectResult(this.results[this.selectedIndex]);
        } else if (e.key === 'Escape') {
            this.hideSuggestions();
        }
    }
    
    updateSelection(items) {
        items.forEach((item, index) => {
            if (index === this.selectedIndex) {
                item.classList.add('active');
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.classList.remove('active');
            }
        });
    }
    
    handleClickOutside(e) {
        if (!this.input.contains(e.target) && !this.suggestions.contains(e.target)) {
            this.hideSuggestions();
        }
    }
    
    hideSuggestions() {
        this.suggestions.style.display = 'none';
        this.selectedIndex = -1;
    }
}

// Make it available globally
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NominatimAutocomplete;
}
