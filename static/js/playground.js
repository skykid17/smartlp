/**
 * Playground Module - ES6  
 * Manages the parser/playground page with regex testing
 */

class Playground {
    constructor() {
        this.currentEntry = null;
        this.init();
    }

    init() {
        // Only initialize if playground section exists
        if (!document.getElementById('playground-section')) return;

        // Listen for section changes
        window.addEventListener('sectionChanged', (e) => {
            if (e.detail.section === 'playground') {
                this.loadFromSession();
            }
        });

        // Initialize will be completed in next iteration
        console.log('Playground module initialized');
    }

    loadFromSession() {
        // Load entry data from session storage if coming from dashboard
        const entries = sessionStorage.getItem('parserEntries');
        if (entries) {
            this.loadEntries(JSON.parse(entries));
        }
    }

    async loadEntries(entryIds) {
        // Load entry details and populate parser
        console.log('Loading entries for parsing:', entryIds);
        // Implementation will be added in next iteration
    }
}

// Initialize
const playground = new Playground();

// Make available globally
window.playground = playground;

export default playground;
