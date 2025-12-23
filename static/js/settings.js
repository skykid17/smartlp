/**
 * Settings Module - ES6
 * Manages application settings and configuration
 */

class Settings {
    constructor() {
        this.currentSettings = {};
        this.init();
    }

    init() {
        // Only initialize if settings section exists
        if (!document.getElementById('settings-section')) return;

        // Listen for section changes
        window.addEventListener('sectionChanged', (e) => {
            if (e.detail.section === 'settings') {
                this.loadSettings();
            }
        });

        // Dark mode toggle
        const darkModeToggle = document.getElementById('darkModeToggle');
        if (darkModeToggle) {
            darkModeToggle.checked = window.AppState.darkMode;
            darkModeToggle.addEventListener('change', () => {
                window.toggleDarkMode();
            });
        }

        console.log('Settings module initialized');
    }

    async loadSettings() {
        // Load current settings from backend
        try {
            const response = await fetch('/api/settings');
            const data = await response.json();
            
            if (data.settings) {
                this.currentSettings = data.settings;
                this.populateSettingsForm();
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    populateSettingsForm() {
        // Populate settings form with current values
        console.log('Populating settings form', this.currentSettings);
        // Implementation will be completed in next iteration
    }

    async saveSettings() {
        // Save settings to backend
        console.log('Saving settings...');
        // Implementation will be completed in next iteration
    }
}

// Initialize
const settings = new Settings();

// Make available globally  
window.settings = settings;

export default settings;
