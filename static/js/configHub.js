/**
 * Config Hub Module - ES6
 * Manages the right slide-over configuration panel
 */

class ConfigHub {
    constructor() {
        this.panel = document.getElementById('configHub');
        this.content = document.getElementById('configHubContent');
        this.selectedEntries = [];
        this.lastGeneratedConfig = null;

        this._saveTimeouts = new Map();
        this._saveQueue = new Map();
        this._inFlightSaves = new Map();

        this.init();
    }

    init() {
        document.getElementById('configHubClose')?.addEventListener('click', () => this.close());
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
        this.panel.classList.contains('translate-x-full') ? this.open() : this.close();
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
                <div class="space-y-2 text-xs">
                    <label class="block text-gray-600 dark:text-gray-400">
                        <span class="font-medium">Index:</span>
                        <input id="input-index-${entry.id}" oninput="window.configHub.onInlineEdit('${entry.id}','index', this.value)" value="${entry.index || ''}" class="mt-1 block w-full rounded-md border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm p-2" />
                    </label>
                    <label class="block text-gray-600 dark:text-gray-400">
                        <span class="font-medium">Source Type:</span>
                        <input id="input-source-${entry.id}" oninput="window.configHub.onInlineEdit('${entry.id}','source_type', this.value)" value="${entry.source_type || ''}" class="mt-1 block w-full rounded-md border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm p-2" />
                    </label>
                    <label class="block text-gray-600 dark:text-gray-400">
                        <span class="font-medium">Log:</span>
                        <textarea id="textarea-log-${entry.id}" oninput="window.configHub.onInlineEdit('${entry.id}','log', this.value)" class="mt-1 block w-full rounded-md border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm p-2" rows="3">${entry.log || ''}</textarea>
                    </label>
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
            // Ensure latest inline edits are persisted so generated config reflects them
            const savedOk = await this.flushAllPendingSaves();
            if (!savedOk) {
                window.showToast('Failed to save edits before generating config', 'error');
                return;
            }

            // Validate entries have required fields
            const invalidEntries = this.selectedEntries.filter(e => !e.index || !e.source_type);
            if (invalidEntries.length > 0) {
                window.showToast('Some entries are missing required fields (index, source_type)', 'warning');
                return;
            }

            // Call API to generate config
            const response = await fetch('/api/smartlp/generate_config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ids: this.selectedEntries.map(e => e.id)
                })
            });

            const data = await response.json();

            if (response.ok) {
                // Check if this is a Splunk dict response or Elastic string response
                if (data.props_conf !== undefined && data.transforms_conf !== undefined) {
                    // Splunk dictionary response
                    this.lastGeneratedConfig = {
                        props_conf: data.props_conf,
                        transforms_conf: data.transforms_conf,
                        siem: data.siem
                    };
                    this.showConfigModal(this.lastGeneratedConfig);
                } else {
                    // Elastic string response (backward compatibility)
                    const configText = data?.config ?? data?.settings;
                    if (configText) {
                        this.lastGeneratedConfig = configText;
                        this.showConfigModal(configText);
                    } else {
                        window.showToast('No configuration returned', 'error');
                    }
                }
            } else {
                window.showToast(data?.error || 'Failed to generate configuration', 'error');
            }
        } catch (error) {
            console.error('Config generation error:', error);
            window.showToast('Error generating configuration', 'error');
        }
    }

    showConfigModal(config) {
        // Create and show modal with config
        const modal = document.createElement('div');
        modal.id = 'generatedConfigModal';
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';

        // Check if config is a dictionary (Splunk) or string (Elastic)
        const isSplunk = typeof config === 'object' && config.props_conf !== undefined;

        if (isSplunk) {
            // Splunk tabbed interface
            modal.innerHTML = `
                <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[80vh] flex flex-col">
                    <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                        <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Generated Splunk Configuration</h2>
                        <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                    
                    <!-- Tabs -->
                    <div class="flex border-b border-gray-200 dark:border-gray-700">
                        <button id="propsTab" class="px-6 py-3 text-sm font-medium text-blue-600 border-b-2 border-blue-600 dark:text-blue-400 dark:border-blue-400" onclick="window.configHub.switchTab('props')">
                            props.conf
                            <span class="ml-2 text-xs text-gray-500 dark:text-gray-400">/etc/system/local/props.conf</span>
                        </button>
                        <button id="transformsTab" class="px-6 py-3 text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200" onclick="window.configHub.switchTab('transforms')">
                            transforms.conf
                            <span class="ml-2 text-xs text-gray-500 dark:text-gray-400">/etc/system/local/transforms.conf</span>
                        </button>
                    </div>
                    
                    <!-- Tab Content -->
                    <div class="flex-1 overflow-y-auto p-4">
                        <div id="propsContent" class="tab-content">
                            <textarea id="propsTextarea" class="bg-gray-900 text-gray-100 p-4 rounded-lg w-full overflow-x-auto text-sm font-mono" spellcheck="false" style="height:50vh; resize: vertical;" readonly></textarea>
                        </div>
                        <div id="transformsContent" class="tab-content hidden">
                            <textarea id="transformsTextarea" class="bg-gray-900 text-gray-100 p-4 rounded-lg w-full overflow-x-auto text-sm font-mono" spellcheck="false" style="height:50vh; resize: vertical;" readonly></textarea>
                        </div>
                    </div>
                    
                    <div class="flex justify-between items-center p-4 border-t border-gray-200 dark:border-gray-700">
                        <div class="flex space-x-2">
                            <button onclick="window.configHub.copyConfig()" class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-white rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors duration-200">
                                <i class="fas fa-copy mr-2"></i>Copy
                            </button>
                            <button onclick="window.configHub.downloadConfig()" class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-white rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors duration-200">
                                <i class="fas fa-download mr-2"></i>Download
                            </button>
                        </div>
                        <div class="flex space-x-2">
                            <button onclick="this.closest('.fixed').remove()" class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-white rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors duration-200">Close</button>
                            <button onclick="window.configHub.showDeployConfirm()" class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors duration-200">
                                <i class="fas fa-rocket mr-2"></i>Deploy to Splunk
                            </button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);

            // Populate textareas
            document.getElementById('propsTextarea').value = config.props_conf || '';
            document.getElementById('transformsTextarea').value = config.transforms_conf || '';

            // Store current tab
            this.currentTab = 'props';

        } else {
            // Elastic single text area interface (original)
            modal.innerHTML = `
                <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[80vh] flex flex-col">
                    <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                        <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Generated Configuration</h2>
                        <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                    <div class="flex-1 overflow-y-auto p-4">
                        <textarea id="generatedConfigTextarea" class="bg-gray-900 text-gray-100 p-4 rounded-lg w-full overflow-x-auto text-sm font-mono" spellcheck="false" style="height:60vh; resize: vertical;"></textarea>
                    </div>
                    <div class="flex justify-end space-x-2 p-4 border-t border-gray-200 dark:border-gray-700">
                        <button onclick="this.closest('.fixed').remove()" class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-white rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors duration-200">Close</button>
                        <button onclick="window.configHub.showDeployConfirm()" class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors duration-200">
                            <i class="fas fa-rocket mr-2"></i>Deploy
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);

            const textarea = modal.querySelector('#generatedConfigTextarea');
            textarea.value = config ?? '';
            textarea.addEventListener('input', () => {
                this.lastGeneratedConfig = textarea.value;
            });
        }
    }

    switchTab(tab) {
        // Update tab buttons
        const propsTab = document.getElementById('propsTab');
        const transformsTab = document.getElementById('transformsTab');
        const propsContent = document.getElementById('propsContent');
        const transformsContent = document.getElementById('transformsContent');

        if (tab === 'props') {
            propsTab.className = 'px-6 py-3 text-sm font-medium text-blue-600 border-b-2 border-blue-600 dark:text-blue-400 dark:border-blue-400';
            transformsTab.className = 'px-6 py-3 text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200';
            propsContent.classList.remove('hidden');
            transformsContent.classList.add('hidden');
            this.currentTab = 'props';
        } else {
            transformsTab.className = 'px-6 py-3 text-sm font-medium text-blue-600 border-b-2 border-blue-600 dark:text-blue-400 dark:border-blue-400';
            propsTab.className = 'px-6 py-3 text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200';
            transformsContent.classList.remove('hidden');
            propsContent.classList.add('hidden');
            this.currentTab = 'transforms';
        }
    }

    copyConfig() {
        // Copy current tab content for Splunk, or entire config for Elastic
        let textToCopy = '';
        if (typeof this.lastGeneratedConfig === 'object') {
            // Splunk - copy current tab
            const textarea = this.currentTab === 'props'
                ? document.getElementById('propsTextarea')
                : document.getElementById('transformsTextarea');
            textToCopy = textarea?.value || '';
        } else {
            // Elastic - copy entire config
            const textarea = document.getElementById('generatedConfigTextarea');
            textToCopy = textarea?.value || '';
        }

        navigator.clipboard.writeText(textToCopy).then(() => {
            window.showToast('Configuration copied to clipboard', 'success');
        }).catch(() => {
            window.showToast('Failed to copy configuration', 'error');
        });
    }

    downloadConfig() {
        // Download config files
        if (typeof this.lastGeneratedConfig === 'object') {
            // Splunk - download both files
            this.downloadFile('props.conf', this.lastGeneratedConfig.props_conf);
            this.downloadFile('transforms.conf', this.lastGeneratedConfig.transforms_conf);
            window.showToast('Configuration files downloaded', 'success');
        } else {
            // Elastic - download single file
            this.downloadFile('config.conf', this.lastGeneratedConfig);
            window.showToast('Configuration file downloaded', 'success');
        }
    }

    downloadFile(filename, content) {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    onInlineEdit(entryId, field, value) {
        const idx = this.selectedEntries.findIndex(e => e.id === entryId);
        if (idx === -1) return;
        // update value
        this.selectedEntries[idx][field] = value;

        // Persist inline edits to backend (debounced)
        this.queueEntrySave(entryId, { [field]: value });

        // dispatch update event so other parts of the app can react
        window.dispatchEvent(new CustomEvent('configEntryUpdated', {
            detail: { entry: this.selectedEntries[idx], field }
        }));
    }

    queueEntrySave(entryId, updates) {
        const existing = this._saveQueue.get(entryId) || {};
        this._saveQueue.set(entryId, { ...existing, ...updates });

        const existingTimer = this._saveTimeouts.get(entryId);
        if (existingTimer) {
            clearTimeout(existingTimer);
        }

        const timerId = setTimeout(() => {
            this.flushEntrySave(entryId);
        }, 400);

        this._saveTimeouts.set(entryId, timerId);
    }

    async flushEntrySave(entryId) {
        const timer = this._saveTimeouts.get(entryId);
        if (timer) {
            clearTimeout(timer);
            this._saveTimeouts.delete(entryId);
        }

        const updates = this._saveQueue.get(entryId);
        if (!updates || Object.keys(updates).length === 0) {
            return true;
        }
        this._saveQueue.delete(entryId);

        // Reuse in-flight request if one exists
        const inFlight = this._inFlightSaves.get(entryId);
        if (inFlight) {
            return inFlight;
        }

        const savePromise = (async () => {
            try {
                const response = await fetch(`/api/smartlp/entries/${encodeURIComponent(entryId)}`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(updates)
                });

                if (!response.ok) {
                    let errMsg = 'Failed to save entry edits';
                    try {
                        const data = await response.json();
                        errMsg = data?.message || data?.error || errMsg;
                    } catch {
                        // ignore
                    }
                    window.showToast(errMsg, 'error');
                    return false;
                }
                return true;
            } catch (e) {
                console.error('Entry save error:', e);
                window.showToast('Error saving entry edits', 'error');
                return false;
            } finally {
                this._inFlightSaves.delete(entryId);
            }
        })();

        this._inFlightSaves.set(entryId, savePromise);
        return savePromise;
    }

    async flushAllPendingSaves() {
        const entryIds = new Set([
            ...this._saveQueue.keys(),
            ...this._inFlightSaves.keys(),
            ...this._saveTimeouts.keys()
        ]);

        const results = [];
        for (const entryId of entryIds) {
            results.push(await this.flushEntrySave(entryId));
        }

        return results.every(Boolean);
    }

    showDeployConfirm() {
        const ok = window.confirm(
            'Confirm Deployment\n\nAre you sure you want to deploy the generated configuration for the selected entries? This action cannot be undone.'
        );
        if (!ok) return;
        this.deployConfig();
    }

    async deployConfig() {
        console.log('Deploying config for entries:', this.selectedEntries);
        try {
            if (!this.selectedEntries.length) {
                window.showToast('No entries selected', 'warning');
                return;
            }
            if (!this.lastGeneratedConfig) {
                window.showToast('Generate configuration first', 'warning');
                return;
            }

            window.showToast('Deploying configuration...', 'info');

            const response = await fetch('/api/smartlp/deploy_config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ids: this.selectedEntries.map(e => e.id),
                    config: this.lastGeneratedConfig
                })
            });

            const data = await response.json();
            if (response.ok) {
                window.showToast(data.message || 'Configuration deployed successfully', 'success');
                this.clearSelection();
                this.close();
            } else {
                window.showToast(data.error || 'Deployment failed', 'error');
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
