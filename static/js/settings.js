/**
 * Settings Module - ES6
 * Manages application settings and configuration
 */

class Settings {
    constructor() {
        this.currentSettings = {};
        this.siems = [];
        this.llmEndpoints = [];
        this.llmEndpointMap = {};
        this.newLlmEndpoints = {};
        this.selectedLlmEndpoint = null;
        this.section = document.getElementById('settings-section');

        if (!this.section) return;

        this.cacheElements();
        this.bindEvents();
        this.loadSettings();
    }

    cacheElements() {
        this.elements = {
            darkModeToggle: document.getElementById('darkModeToggle'),
            ingestOn: document.getElementById('ingestOn'),
            ingestAlgoVersion: document.getElementById('ingestAlgoVersion'),
            ingestFrequency: document.getElementById('ingestFrequency'),
            similarityCheck: document.getElementById('similarityCheck'),
            similarityThreshold: document.getElementById('similarityThreshold'),
            activeSiem: document.getElementById('activeSiem'),
            activeLlmEndpoint: document.getElementById('activeLlmEndpoint'),
            activeLlm: document.getElementById('activeLlm'),
            fixCount: document.getElementById('fixCount'),
            siemSelect: document.getElementById('siem'),
            searchIndex: document.getElementById('searchIndex'),
            searchEntryCount: document.getElementById('searchEntryCount'),
            searchQuery: document.getElementById('searchQuery'),
            llmUrl: document.getElementById('llmUrl'),
            modelsContainer: document.getElementById('models'),
            newModelInput: document.getElementById('newModelInput'),
            addModelBtn: document.getElementById('addModelBtn'),
            saveBtn: document.getElementById('saveSettingsBtn'),
            connectionLogger: document.getElementById('connectionTestLogger'),
            queryLogger: document.getElementById('searchQueryLogger'),
            testConnectionBtn: document.getElementById('testConnectionBtn'),
            testQueryBtn: document.getElementById('testQueryBtn'),
            llmEndpointTabs: document.getElementById('llmEndpointTabs')
        };
    }

    bindEvents() {
        window.addEventListener('sectionChanged', (e) => {
            if (e.detail?.section === 'settings') {
                this.loadSettings();
            }
        });

        if (this.elements.darkModeToggle && typeof window.toggleDarkMode === 'function') {
            this.elements.darkModeToggle.checked = window.AppState?.darkMode ?? false;
            this.elements.darkModeToggle.addEventListener('change', () => window.toggleDarkMode());
        }

        this.elements.siemSelect?.addEventListener('change', () => this.handleSiemChange());
        this.elements.activeLlmEndpoint?.addEventListener('change', () => this.handleActiveEndpointChange());
        this.elements.addModelBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            this.addModel();
        });

        this.elements.llmUrl?.addEventListener('input', (e) => this.updateSelectedEndpointUrl(e.target.value));

        this.elements.saveBtn?.addEventListener('click', () => this.saveSettings());
        this.elements.testConnectionBtn?.addEventListener('click', () => this.testSiemConnection());
        this.elements.testQueryBtn?.addEventListener('click', () => this.testSiemQuery());

        ['searchIndex', 'searchEntryCount', 'searchQuery'].forEach((field) => {
            this.elements[field]?.addEventListener('input', () => this.persistSiemField(field));
        });
    }

    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to load settings');
            }

            this.currentSettings = data.settings || {};
            this.siems = data.siems || [];
            this.llmEndpoints = data.llmEndpoints || [];
            this.llmEndpointMap = Object.fromEntries(
                this.llmEndpoints.map((ep) => [ep.id, { ...ep, models: [...(ep.models || [])] }])
            );

            if (!this.selectedLlmEndpoint && this.llmEndpoints.length) {
                this.selectedLlmEndpoint = this.llmEndpoints[0].id;
            }

            if (this.selectedLlmEndpoint && !this.llmEndpointMap[this.selectedLlmEndpoint]) {
                this.selectedLlmEndpoint = this.llmEndpoints[0]?.id || null;
            }

            this.populateSettingsForm();
        } catch (error) {
            console.error('Error loading settings:', error);
            this.toast(error.message || 'Unable to load settings', 'error');
        }
    }

    populateSettingsForm() {
        const settings = this.currentSettings;

        this.setCheckbox(this.elements.ingestOn, settings.ingestOn);
        this.setCheckbox(this.elements.similarityCheck, settings.similarityCheck);
        this.setValue(this.elements.ingestAlgoVersion, settings.ingestAlgoVersion || 'v1');
        this.setValue(this.elements.ingestFrequency, settings.ingestFrequency ?? 15);
        this.setValue(this.elements.similarityThreshold, settings.similarityThreshold ?? 0.8);
        this.setValue(this.elements.fixCount, settings.fixCount ?? 3);

        this.renderSiemControls();
        this.renderLlmControls();
    }

    renderSiemControls() {
        const options = this.siems.map((s) => ({ value: s.id, label: s.name || s.id }));
        this.populateSelect(this.elements.activeSiem, options, this.currentSettings.activeSiem, 'Select SIEM...');
        this.populateSelect(
            this.elements.siemSelect,
            options,
            this.elements.siemSelect?.value || this.currentSettings.activeSiem,
            'Select SIEM...'
        );
        this.handleSiemChange();
    }

    renderLlmControls() {
        const options = this.llmEndpoints.map((e) => ({ value: e.id, label: e.name || e.id }));
        this.populateSelect(
            this.elements.activeLlmEndpoint,
            options,
            this.currentSettings.activeLlmEndpoint,
            'Select endpoint...'
        );
        this.handleActiveEndpointChange(true);
        this.renderLlmTabs();
    }

    handleSiemChange() {
        const id = this.elements.siemSelect.value;
        const siem = this.siems.find((s) => s.id === id);
        if (!siem) return;

        this.elements.searchIndex.value = siem.searchIndex || '';
        this.elements.searchEntryCount.value = siem.searchEntryCount ?? '';
        this.elements.searchQuery.value = siem.searchQuery || '';
    }

    persistSiemField(field) {
        const siemId = this.elements.siemSelect?.value;
        if (!siemId) return;
        const siem = this.siems.find((entry) => entry.id === siemId);
        if (!siem) return;

        if (field === 'searchEntryCount') {
            siem[field] = Number(this.elements[field].value) || 0;
        } else {
            siem[field] = this.elements[field].value;
        }
    }

    handleActiveEndpointChange(useCurrentValue = false) {
        const endpointId = this.elements.activeLlmEndpoint?.value;
        const endpoint = this.llmEndpointMap[endpointId];
        const models = endpoint?.models || [];

        let selected = useCurrentValue ? this.currentSettings.activeLlm : this.elements.activeLlm?.value;
        if (!models.includes(selected)) {
            selected = models[0] || '';
        }

        this.populateSelect(
            this.elements.activeLlm,
            models.map((m) => ({ value: m, label: m })),
            selected,
            'Select model...'
        );
    }

    renderLlmTabs() {
        const container = this.elements.llmEndpointTabs;
        if (!container) return;
        container.innerHTML = '';

        this.llmEndpoints.forEach((ep) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `px-4 py-2 rounded-lg text-sm border ${ep.id === this.selectedLlmEndpoint
                    ? 'bg-blue-500 text-white border-blue-500'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-transparent'
                }`;
            btn.textContent = ep.name || ep.id;
            btn.addEventListener('click', () => {
                this.selectLlmEndpoint(ep.id);
                this.renderLlmTabs();
            });
            container.appendChild(btn);
        });

        const addBtn = document.createElement('button');
        addBtn.type = 'button';
        addBtn.className = 'px-4 py-2 rounded-lg text-sm border border-dashed border-gray-400 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700';
        addBtn.innerHTML = '<i class="fas fa-plus mr-1"></i>Add Endpoint';
        addBtn.addEventListener('click', () => this.promptNewEndpoint());
        container.appendChild(addBtn);

        if (!this.selectedLlmEndpoint && this.llmEndpoints.length) {
            this.selectLlmEndpoint(this.llmEndpoints[0].id);
        } else if (this.selectedLlmEndpoint) {
            this.selectLlmEndpoint(this.selectedLlmEndpoint);
        }
    }

    selectLlmEndpoint(id) {
        this.selectedLlmEndpoint = id;
        const ep = this.llmEndpointMap[id];
        if (!ep) return;

        this.setValue(this.elements.llmUrl, ep.url || '');
        this.renderModelList(ep.models || []);
        this.refreshActiveModelOptionsIfNeeded();
    }

    updateSelectedEndpointUrl(value) {
        if (!this.selectedLlmEndpoint) return;
        const ep = this.llmEndpointMap[this.selectedLlmEndpoint];
        if (ep) {
            ep.url = value;
        }
    }

    renderModelList(models) {
        const container = this.elements.modelsContainer;
        if (!container) return;
        container.innerHTML = '';

        if (!models.length) {
            container.innerHTML = '<p class="text-sm text-gray-500">No models configured.</p>';
            return;
        }

        models.forEach((model, index) => {
            const row = document.createElement('div');
            row.className = 'flex items-center justify-between bg-gray-100 dark:bg-gray-700 rounded-lg px-3 py-2 text-sm';
            row.innerHTML = `
                <span>${model}</span>
                <button type="button" class="text-red-500 hover:text-red-600">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            row.querySelector('button')?.addEventListener('click', () => this.removeModel(index));
            container.appendChild(row);
        });
    }

    addModel() {
        const value = this.elements.newModelInput?.value.trim();
        const ep = this.llmEndpointMap[this.selectedLlmEndpoint];
        if (!value || !ep) return;

        if (ep.models.includes(value)) {
            this.toast('Model already exists for this endpoint', 'warning');
            return;
        }

        ep.models.push(value);
        this.elements.newModelInput.value = '';
        this.renderModelList(ep.models);
        this.refreshActiveModelOptionsIfNeeded();
    }

    removeModel(index) {
        const ep = this.llmEndpointMap[this.selectedLlmEndpoint];
        ep.models.splice(index, 1);
        this.renderModelList(ep.models);
        this.refreshActiveModelOptionsIfNeeded();
    }

    refreshActiveModelOptionsIfNeeded() {
        if (this.elements.activeLlmEndpoint?.value === this.selectedLlmEndpoint) {
            this.handleActiveEndpointChange();
        }
    }

    promptNewEndpoint() {
        const id = prompt('Enter endpoint ID (no spaces):');
        if (!id) return;
        if (this.llmEndpointMap[id]) {
            this.toast('Endpoint ID already exists', 'warning');
            return;
        }

        const name = prompt('Enter endpoint display name:', id) || id;
        const url = prompt('Enter endpoint API URL:', '') || '';

        const endpoint = { id, name, url, models: [] };
        this.llmEndpoints.push(endpoint);
        this.llmEndpointMap[id] = endpoint;
        this.newLlmEndpoints[id] = { ...endpoint };
        this.renderLlmControls();
        this.selectLlmEndpoint(id);
        this.toast(`Endpoint ${name} created`, 'success');
    }

    async saveSettings() {
        if (!this.elements.saveBtn) return;

        const payload = {
            ingestOn: this.elements.ingestOn?.checked ?? false,
            ingestAlgoVersion: this.elements.ingestAlgoVersion?.value || 'v1',
            ingestFrequency: Number(this.elements.ingestFrequency?.value) || 0,
            similarityCheck: this.elements.similarityCheck?.checked ?? false,
            similarityThreshold: Number(this.elements.similarityThreshold?.value) || 0,
            activeSiem: this.elements.activeSiem?.value || '',
            activeLlmEndpoint: this.elements.activeLlmEndpoint?.value || '',
            activeLlm: this.elements.activeLlm?.value || '',
            fixCount: Number(this.elements.fixCount?.value) || 0
        };

        if (this.elements.siemSelect?.value) {
            payload.siem = this.elements.siemSelect.value;
            payload.searchIndex = this.elements.searchIndex?.value || '';
            payload.searchEntryCount = Number(this.elements.searchEntryCount?.value) || 0;
            payload.searchQuery = this.elements.searchQuery?.value || '';
        }

        if (this.selectedLlmEndpoint) {
            const endpoint = this.llmEndpointMap[this.selectedLlmEndpoint];
            payload.llmEndpoint = this.selectedLlmEndpoint;
            payload.llmUrl = endpoint?.url || '';
            payload.models = endpoint?.models || [];
        }

        if (Object.keys(this.newLlmEndpoints).length) {
            payload.llmEndpoints = this.newLlmEndpoints;
        }

        this.setSavingState(true);

        try {
            const response = await fetch('/api/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to save settings');
            }

            this.toast('Settings saved successfully', 'success');
            this.newLlmEndpoints = {};
            await this.loadSettings();
        } catch (error) {
            console.error('Error saving settings:', error);
            this.toast(error.message || 'Unable to save settings', 'error');
        } finally {
            this.setSavingState(false);
        }
    }

    async testSiemConnection() {
        if (!this.elements.connectionLogger) return;
        this.elements.connectionLogger.innerHTML = '<span class="text-blue-500">Testing SIEM connection...</span>';

        try {
            const response = await fetch('/api/test_siem_connection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ siem: this.elements.siemSelect?.value || 'all' })
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error?.message || data.error || 'Connection test failed');
            }

            this.elements.connectionLogger.innerHTML = `<pre class="text-xs whitespace-pre-wrap">${this.formatConnectionResult(data)}</pre>`;
        } catch (error) {
            this.elements.connectionLogger.innerHTML = `<span class="text-red-500">${error.message}</span>`;
        }
    }

    async testSiemQuery() {
        if (!this.elements.queryLogger) return;
        this.elements.queryLogger.innerHTML = '<span class="text-blue-500">Running query test...</span>';

        try {
            const payload = {
                siem: this.elements.siemSelect?.value || '',
                searchQuery: this.elements.searchQuery?.value || '',
                searchIndex: this.elements.searchIndex?.value || '',
                entriesCount: Number(this.elements.searchEntryCount?.value) || 10
            };

            const response = await fetch('/api/test_query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();

            if (!response.ok || data.status_code !== 200) {
                throw new Error(data.error || 'Query test failed');
            }

            this.elements.queryLogger.innerHTML = '<span class="text-green-500">Query executed successfully.</span>';
        } catch (error) {
            this.elements.queryLogger.innerHTML = `<span class="text-red-500">${error.message}</span>`;
        }
    }

    formatConnectionResult(result) {
        if (result.status && result.message) {
            return `${result.status.toUpperCase()}: ${result.message}`;
        }

        return Object.entries(result)
            .map(([key, value]) => `${key.toUpperCase()}: ${value.status} - ${value.message}`)
            .join('\n');
    }

    populateSelect(select, options, selected, placeholder) {
        if (!select) return;
        select.innerHTML = '';

        if (placeholder) {
            const placeholderOption = document.createElement('option');
            placeholderOption.value = '';
            placeholderOption.textContent = placeholder;
            select.appendChild(placeholderOption);
        }

        options.forEach(({ value, label }) => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = label;
            select.appendChild(option);
        });

        select.value = selected ?? '';
    }

    setCheckbox(element, value) {
        if (element) {
            element.checked = Boolean(value);
        }
    }

    setValue(element, value) {
        if (element !== null && element !== undefined) {
            element.value = value ?? '';
        }
    }

    setSavingState(isSaving) {
        if (!this.elements.saveBtn) return;
        this.elements.saveBtn.disabled = isSaving;
        this.elements.saveBtn.innerHTML = isSaving
            ? '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...'
            : '<i class="fas fa-save mr-2"></i>Save Settings';
    }

    toast(message, type = 'info') {
        if (typeof window.showToast === 'function') {
            window.showToast(message, type);
        } else {
            console[type === 'error' ? 'error' : 'log'](message);
        }
    }
}

// Init
const settings = new Settings();
window.settings = settings;
export default settings;
