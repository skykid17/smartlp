/**
 * Config Hub Module - ES6
 * Manages the right slide-over configuration panel
 */

class ConfigHub {
    constructor() {
        this.panel = document.getElementById('configHub');
        this.content = document.getElementById('configHubContent');
        this.selectedEntries = [];
        
        this.init();
    }

    init() {
        // Close button
        document.getElementById('configHubClose')?.addEventListener('click', () => {
            this.close();
        });
    }

    open() {
        this.panel.classList.remove('translate-x-full');
        this.panel.classList.add('slide-in-right');
        this.loadContent();
    }

    close() {
        this.panel.classList.add('translate-x-full');
        this.panel.classList.remove('slide-in-right');
    }

    toggle() {
        const isOpen = !this.panel.classList.contains('translate-x-full');
        if (isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    loadContent() {
        // Load configuration options
        this.content.innerHTML = `
            <div class="space-y-4">
                <div class="border-b border-gray-200 dark:border-gray-700 pb-4">
                    <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-2">Selected Entries</h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                        <span id="selectedCount">${this.selectedEntries.length}</span> entries selected
                    </p>
                </div>

                <div class="space-y-2" id="configEntries">
                    ${this.selectedEntries.length === 0 ? 
                        '<p class="text-sm text-gray-500 dark:text-gray-400">No entries selected</p>' :
                        this.renderEntries()
                    }
                </div>

                ${this.selectedEntries.length > 0 ? `
                    <div class="space-y-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                        <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-2">Actions</h3>
                        <button onclick="window.configHub.validateAndGenerate()" class="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors duration-200">
                            <i class="fas fa-cog mr-2"></i>Generate Config
                        </button>
                        <button onclick="window.configHub.clearSelection()" class="w-full px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-white rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors duration-200">
                            <i class="fas fa-times mr-2"></i>Clear Selection
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderEntries() {
        return this.selectedEntries.map(entry => `
            <div class="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-semibold text-gray-700 dark:text-gray-300">ID: ${entry.id}</span>
                    <button onclick="window.configHub.removeEntry('${entry.id}')" class="text-red-500 hover:text-red-600">
                        <i class="fas fa-trash text-xs"></i>
                    </button>
                </div>
                <div class="space-y-1 text-xs">
                    <div class="text-gray-600 dark:text-gray-400">
                        <span class="font-medium">Index:</span> ${entry.index || 'N/A'}
                    </div>
                    <div class="text-gray-600 dark:text-gray-400">
                        <span class="font-medium">Source Type:</span> ${entry.source_type || 'N/A'}
                    </div>
                    <div class="text-gray-600 dark:text-gray-400 truncate">
                        <span class="font-medium">Log:</span> ${entry.log.substring(0, 50)}...
                    </div>
                </div>
            </div>
        `).join('');
    }

    setSelectedEntries(entries) {
        this.selectedEntries = entries;
        if (this.isOpen()) {
            this.loadContent();
        }
    }

    addEntry(entry) {
        if (!this.selectedEntries.find(e => e.id === entry.id)) {
            this.selectedEntries.push(entry);
            if (this.isOpen()) {
                this.loadContent();
            }
        }
    }

    removeEntry(entryId) {
        this.selectedEntries = this.selectedEntries.filter(e => e.id !== entryId);
        this.loadContent();
        
        // Dispatch event for table to update
        window.dispatchEvent(new CustomEvent('configEntryRemoved', { 
            detail: { entryId } 
        }));
    }

    clearSelection() {
        this.selectedEntries = [];
        this.loadContent();
        
        // Dispatch event for table to update
        window.dispatchEvent(new Event('configSelectionCleared'));
    }

    async validateAndGenerate() {
        if (this.selectedEntries.length === 0) {
            window.showToast('No entries selected', 'warning');
            return;
        }

        try {
            // Validate entries have required fields
            const invalidEntries = this.selectedEntries.filter(e => !e.index || !e.source_type);
            if (invalidEntries.length > 0) {
                window.showToast('Some entries are missing required fields (index, source_type)', 'warning');
                return;
            }

            // Call API to generate config
            const response = await fetch('/api/smartlp/config/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    entries: this.selectedEntries.map(e => e.id)
                })
            });

            const data = await response.json();

            if (data.config) {
                this.showConfigModal(data.config);
            } else {
                window.showToast('Failed to generate configuration', 'error');
            }
        } catch (error) {
            console.error('Config generation error:', error);
            window.showToast('Error generating configuration', 'error');
        }
    }

    showConfigModal(config) {
        // Create and show modal with config
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
        modal.innerHTML = `
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[80vh] flex flex-col">
                <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                    <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Generated Configuration</h2>
                    <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                        <i class="fas fa-times text-xl"></i>
                    </button>
                </div>
                <div class="flex-1 overflow-y-auto p-4">
                    <pre class="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm"><code>${this.escapeHtml(config)}</code></pre>
                </div>
                <div class="flex justify-end space-x-2 p-4 border-t border-gray-200 dark:border-gray-700">
                    <button onclick="this.closest('.fixed').remove()" class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-white rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors duration-200">Close</button>
                    <button onclick="window.configHub.deployConfig()" class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors duration-200">
                        <i class="fas fa-rocket mr-2"></i>Deploy
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    async deployConfig() {
        try {
            window.showToast('Deploying configuration...', 'info');
            
            const response = await fetch('/api/smartlp/config/deploy', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    entries: this.selectedEntries.map(e => e.id)
                })
            });

            const data = await response.json();

            if (data.success) {
                window.showToast('Configuration deployed successfully', 'success');
                this.clearSelection();
                this.close();
            } else {
                window.showToast('Deployment failed: ' + (data.message || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Deployment error:', error);
            window.showToast('Error deploying configuration', 'error');
        }
    }

    isOpen() {
        return !this.panel.classList.contains('translate-x-full');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize
const configHub = new ConfigHub();

// Make available globally
window.configHub = configHub;

export default configHub;
