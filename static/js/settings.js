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

        this.addSiemTestPassed = false;

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
            llmName: document.getElementById('llmName'),
            llmUrl: document.getElementById('llmUrl'),
            llmApiKey: document.getElementById('llmApiKey'),
            modelsContainer: document.getElementById('models'),
            newModelInput: document.getElementById('newModelInput'),
            addModelBtn: document.getElementById('addModelBtn'),
            deleteLlmEndpointBtn: document.getElementById('deleteLlmEndpointBtn'),
            saveBtn: document.getElementById('saveSettingsBtn'),
            connectionLogger: document.getElementById('connectionTestLogger'),
            queryLogger: document.getElementById('searchQueryLogger'),
            modelLogger: document.getElementById('testModelLogger'),
            testConnectionBtn: document.getElementById('testConnectionBtn'),
            testQueryBtn: document.getElementById('testQueryBtn'),
            llmEndpointTabs: document.getElementById('llmEndpointTabs'),

            // Add SIEM modal
            addSiemBtn: document.getElementById('addSiemBtn'),
            addSiemModal: document.getElementById('addSiemModal'),
            addSiemClose: document.getElementById('addSiemClose'),
            addSiemType: document.getElementById('addSiemType'),
            addElasticFields: document.getElementById('addElasticFields'),
            addSplunkFields: document.getElementById('addSplunkFields'),
            addSiemAlert: document.getElementById('addSiemAlert'),
            addSiemTestBtn: document.getElementById('addSiemTestBtn'),
            addSiemSaveBtn: document.getElementById('addSiemSaveBtn')
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

        this.elements.llmName?.addEventListener('input', (e) => this.updateSelectedEndpointName(e.target.value));
        this.elements.llmUrl?.addEventListener('input', (e) => this.updateSelectedEndpointUrl(e.target.value));
        this.elements.llmApiKey?.addEventListener('input', (e) => this.updateSelectedEndpointApiKey(e.target.value));

        this.elements.deleteLlmEndpointBtn?.addEventListener('click', () => this.deleteSelectedEndpoint());

        this.elements.saveBtn?.addEventListener('click', () => this.saveSettings());
        this.elements.testConnectionBtn?.addEventListener('click', () => this.testSiemConnection());
        this.elements.testQueryBtn?.addEventListener('click', () => this.testSiemQuery());

        this.elements.addSiemBtn?.addEventListener('click', () => this.openAddSiemModal());
        this.elements.addSiemClose?.addEventListener('click', () => this.closeAddSiemModal());
        this.elements.addSiemType?.addEventListener('change', () => this.onAddSiemTypeChange());
        this.elements.addSiemTestBtn?.addEventListener('click', () => this.testAddSiemConnection());
        this.elements.addSiemSaveBtn?.addEventListener('click', () => this.saveAddSiem());

        // Reset test state whenever add-SIEM fields change
        const addFields = [
            'addElasticHost', 'addElasticApiKey', 'addElasticKibanaUrl', 'addElasticUser', 'addElasticPassword',
            'addElasticSearchIndex', 'addElasticPipelineId', 'addElasticCertPath',
            'addSplunkHost', 'addSplunkPort', 'addSplunkUser', 'addSplunkPassword',
            'addSplunkSearchIndex', 'addSplunkSearchQuery', 'addSplunkSearchEntryCount'
        ];
        addFields.forEach((id) => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('input', () => this.resetAddSiemTestState());
        });

        this.elements.addSiemModal?.addEventListener('click', (e) => {
            const isBackdrop = e.target === this.elements.addSiemModal
                || (e.target?.classList && e.target.classList.contains('bg-opacity-50'));
            if (isBackdrop) this.closeAddSiemModal();
        });

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

            // Backend returns `{ globalSettings, siems, llmEndpoints }`.
            this.currentSettings = data.globalSettings || data.settings || {};
            this.siems = data.siems || [];

            // Normalize endpoints and models to a frontend-friendly shape
            this.llmEndpoints = (data.llmEndpoints || []).map((ep) => ({
                id: ep.id,
                name: ep.name || ep.id,
                url: ep.url || '',
                apiKey: ep.apiKey || ep.api_key || '',
                updatedAt: ep.updatedAt || ep.updated_at || null,
                models: (ep.models || []).map((m) => ({
                    id: m.id,
                    endpoint_id: ep.id,
                    model_name: m.modelName || m.model_name || m.model || m.model_name,
                    display_name: m.displayName || m.display_name || m.modelName || m.model_name,
                    provider: m.provider || ''
                }))
            }));

            this.llmEndpointMap = Object.fromEntries(
                this.llmEndpoints.map((ep) => [ep.id, { ...ep, models: [...(ep.models || [])] }])
            );

            // Snapshot original models so we can detect deletions on save
            this.originalModelsById = {};
            this.llmEndpoints.forEach((ep) => {
                (ep.models || []).forEach((m) => {
                    if (m && m.id) this.originalModelsById[m.id] = ep.id;
                });
            });

            // Normalize possible global setting key variants for active endpoint/model
            const gs = this.currentSettings || {};
            const activeEndpoint = gs.activeLlmEndpoint || gs.activeLlmEndpointId || gs.active_llm_endpoint || gs.activeLlm || gs.active_llm || null;
            const activeModel = gs.activeLlm || gs.active_llm || gs.activeLlmModelId || gs.active_llm_model_id || null;

            // Ensure the canonical keys exist on currentSettings
            if (activeEndpoint) this.currentSettings.activeLlmEndpoint = activeEndpoint;
            if (activeModel) this.currentSettings.activeLlm = activeModel;
            // If active endpoint value matches a name instead of id, resolve it to id
            if (this.currentSettings.activeLlmEndpoint && !this.llmEndpointMap[this.currentSettings.activeLlmEndpoint]) {
                const foundByName = this.llmEndpoints.find((e) => e.name === this.currentSettings.activeLlmEndpoint);
                if (foundByName) {
                    this.currentSettings.activeLlmEndpoint = foundByName.id;
                }
            }
            // If there is no explicit active endpoint but an active model is configured,
            // derive the endpoint from the model id so the UI can select the correct endpoint.
            if (!this.currentSettings.activeLlmEndpoint && this.currentSettings.activeLlm) {
                const modelId = this.currentSettings.activeLlm;
                for (const ep of this.llmEndpoints) {
                    if ((ep.models || []).some((m) => m.id === modelId)) {
                        this.currentSettings.activeLlmEndpoint = ep.id;
                        break;
                    }
                }
            }
            if (activeEndpoint && this.llmEndpointMap[activeEndpoint]) {
                this.selectedLlmEndpoint = activeEndpoint;
            } else if (!this.selectedLlmEndpoint && this.llmEndpoints.length) {
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

        this.updateAddSiemButtonVisibility();
    }

    updateAddSiemButtonVisibility() {
        if (!this.elements.addSiemBtn) return;

        // Keep the button visible so users can understand what's available,
        // but disable it when there is no eligible SIEM to add.
        const hasElastic = this.siems.some((s) => (s.id || '').toLowerCase() === 'elastic');
        const hasSplunk = this.siems.some((s) => (s.id || '').toLowerCase() === 'splunk');
        const canAdd = (hasElastic && !hasSplunk) || (!hasElastic && hasSplunk);

        this.elements.addSiemBtn.disabled = !canAdd;
        this.elements.addSiemBtn.classList.toggle('opacity-50', !canAdd);
        this.elements.addSiemBtn.classList.toggle('cursor-not-allowed', !canAdd);
        this.elements.addSiemBtn.title = canAdd
            ? 'Add the missing SIEM configuration'
            : 'Both SIEMs are already configured (or none exist yet)';
    }

    rebuildAddSiemTypeOptions() {
        if (!this.elements.addSiemType) return;

        const existing = new Set(this.siems.map((s) => (s.id || '').toLowerCase()));
        const allowed = [];
        if (!existing.has('elastic')) allowed.push({ value: 'elastic', label: 'Elastic' });
        if (!existing.has('splunk')) allowed.push({ value: 'splunk', label: 'Splunk' });

        // Rebuild select
        this.elements.addSiemType.innerHTML = '';
        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.textContent = allowed.length ? 'Select…' : 'No SIEMs to add';
        this.elements.addSiemType.appendChild(placeholder);
        allowed.forEach(({ value, label }) => {
            const opt = document.createElement('option');
            opt.value = value;
            opt.textContent = label;
            this.elements.addSiemType.appendChild(opt);
        });

        this.elements.addSiemType.disabled = allowed.length === 0;
    }

    getMissingSiemType() {
        const hasElastic = this.siems.some((s) => (s.id || '').toLowerCase() === 'elastic');
        const hasSplunk = this.siems.some((s) => (s.id || '').toLowerCase() === 'splunk');
        if (hasElastic && !hasSplunk) return 'splunk';
        if (!hasElastic && hasSplunk) return 'elastic';
        return null;
    }

    openAddSiemModal() {
        if (!this.elements.addSiemModal) return;

        this.rebuildAddSiemTypeOptions();

        const missing = this.getMissingSiemType();
        if (this.elements.addSiemType) {
            this.elements.addSiemType.value = missing || '';
        }
        this.onAddSiemTypeChange();
        this.resetAddSiemTestState();
        this.hideAddSiemAlert();

        if (this.elements.addSiemType?.disabled) {
            this.showAddSiemAlert('Both SIEMs are already configured.', 'error');
        }

        this.elements.addSiemModal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    closeAddSiemModal() {
        if (!this.elements.addSiemModal) return;
        this.elements.addSiemModal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
        this.hideAddSiemAlert();
    }

    onAddSiemTypeChange() {
        const type = (this.elements.addSiemType?.value || '').toLowerCase();
        this.elements.addElasticFields?.classList.toggle('hidden', type !== 'elastic');
        this.elements.addSplunkFields?.classList.toggle('hidden', type !== 'splunk');
        this.resetAddSiemTestState();
    }

    resetAddSiemTestState() {
        this.addSiemTestPassed = false;
        if (this.elements.addSiemSaveBtn) this.elements.addSiemSaveBtn.disabled = true;
    }

    showAddSiemAlert(message, type = 'error') {
        const el = this.elements.addSiemAlert;
        if (!el) return;
        el.classList.remove('hidden');
        el.textContent = message;
        el.className = 'text-sm mb-4 px-4 py-2 rounded-lg ' +
            (type === 'success'
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:bg-opacity-40 dark:text-green-200'
                : 'bg-red-100 text-red-800 dark:bg-red-900 dark:bg-opacity-40 dark:text-red-200');
    }

    hideAddSiemAlert() {
        const el = this.elements.addSiemAlert;
        if (!el) return;
        el.classList.add('hidden');
        el.textContent = '';
    }

    getAddSiemPayload() {
        const siemType = (this.elements.addSiemType?.value || '').toLowerCase();
        if (!siemType) return null;

        if (siemType === 'elastic') {
            return {
                siem_type: 'elastic',
                elastic: {
                    host: document.getElementById('addElasticHost')?.value?.trim() || '',
                    api_key: document.getElementById('addElasticApiKey')?.value?.trim() || '',
                    kibana_url: document.getElementById('addElasticKibanaUrl')?.value?.trim() || '',
                    user: document.getElementById('addElasticUser')?.value?.trim() || '',
                    password: document.getElementById('addElasticPassword')?.value || '',
                    search_index: document.getElementById('addElasticSearchIndex')?.value?.trim() || '',
                    pipeline_id: document.getElementById('addElasticPipelineId')?.value?.trim() || '',
                    cert_path: document.getElementById('addElasticCertPath')?.value?.trim() || ''
                }
            };
        }

        if (siemType === 'splunk') {
            return {
                siem_type: 'splunk',
                splunk: {
                    host: document.getElementById('addSplunkHost')?.value?.trim() || '',
                    port: document.getElementById('addSplunkPort')?.value?.trim() || '',
                    user: document.getElementById('addSplunkUser')?.value?.trim() || '',
                    password: document.getElementById('addSplunkPassword')?.value || '',
                    search_index: document.getElementById('addSplunkSearchIndex')?.value?.trim() || '',
                    search_query: document.getElementById('addSplunkSearchQuery')?.value?.trim() || '',
                    search_entry_count: document.getElementById('addSplunkSearchEntryCount')?.value || ''
                }
            };
        }

        return null;
    }

    async testAddSiemConnection() {
        this.hideAddSiemAlert();
        this.resetAddSiemTestState();

        const payload = this.getAddSiemPayload();
        if (!payload) {
            this.showAddSiemAlert('Please select a SIEM type.', 'error');
            return;
        }

        try {
            const response = await fetch('/api/settings/siem/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                this.showAddSiemAlert(data.error || 'Connection test failed.', 'error');
                return;
            }

            this.addSiemTestPassed = true;
            if (this.elements.addSiemSaveBtn) this.elements.addSiemSaveBtn.disabled = false;
            this.showAddSiemAlert('Connection successful.', 'success');
        } catch (error) {
            this.showAddSiemAlert('Connection test failed. Please check settings and try again.', 'error');
        }
    }

    async saveAddSiem() {
        if (!this.addSiemTestPassed) {
            this.showAddSiemAlert('Please test the connection before saving.', 'error');
            return;
        }

        const payload = this.getAddSiemPayload();
        if (!payload) {
            this.showAddSiemAlert('Please select a SIEM type.', 'error');
            return;
        }

        try {
            const response = await fetch('/api/settings/siem', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                this.showAddSiemAlert(data.error || 'Failed to save SIEM settings.', 'error');
                return;
            }

            await this.loadSettings();
            this.closeAddSiemModal();
            this.toast('SIEM added successfully', 'success');
        } catch (error) {
            this.showAddSiemAlert('Failed to save SIEM settings.', 'error');
        }
    }

    renderLlmControls() {
        const options = this.llmEndpoints.map((e) => ({ value: e.id, label: e.name || e.id }));
        this.populateSelect(
            this.elements.activeLlmEndpoint,
            options,
            this.currentSettings.activeLlmEndpoint,
            'Select endpoint...'
        );
        // Ensure the select DOM reflects the active endpoint before populating models
        if (this.currentSettings.activeLlmEndpoint) {
            try { this.elements.activeLlmEndpoint.value = this.currentSettings.activeLlmEndpoint; } catch (e) { }
        }
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
        // When requested, prefer the current settings values (useful during initial load)
        const endpointId = useCurrentValue
            ? (this.currentSettings?.activeLlmEndpoint || this.elements.activeLlmEndpoint?.value)
            : this.elements.activeLlmEndpoint?.value;
        // Ensure DOM select reflects chosen endpointId
        if (this.elements.activeLlmEndpoint && endpointId !== undefined && endpointId !== null) {
            try { this.elements.activeLlmEndpoint.value = endpointId; } catch (e) { }
        }
        // If endpointId is a name, resolve to id
        let resolvedEndpointId = endpointId;
        if (resolvedEndpointId && !this.llmEndpointMap[resolvedEndpointId]) {
            const found = this.llmEndpoints.find((e) => e.name === resolvedEndpointId || e.id === resolvedEndpointId);
            if (found) resolvedEndpointId = found.id;
        }

        const endpoint = this.llmEndpointMap[resolvedEndpointId];
        const models = endpoint?.models || [];

        let selectedModelId = useCurrentValue
            ? (this.currentSettings?.activeLlm || this.currentSettings?.activeLlmModelId)
            : this.elements.activeLlm?.value;

        // If selectedModelId refers to a model_name or display_name, resolve to model.id
        if (selectedModelId && !models.find((m) => m.id === selectedModelId)) {
            const matched = models.find((m) => m.model_name === selectedModelId || m.display_name === selectedModelId);
            if (matched) {
                selectedModelId = matched.id;
            } else {
                // fallback to first model's id or empty
                selectedModelId = models[0]?.id || '';
            }
        }

        this.populateSelect(
            this.elements.activeLlm,
            models.map((m) => ({ value: m.id, label: m.display_name || m.model_name })),
            selectedModelId,
            'Select model...'
        );
        // If using current value, ensure DOM select reflects chosen model
        if (useCurrentValue && this.elements.activeLlm && selectedModelId) {
            try { this.elements.activeLlm.value = selectedModelId; } catch (e) { }
        }
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

        this.setValue(this.elements.llmName, ep.name || ep.id || '');
        this.setValue(this.elements.llmUrl, ep.url || '');
        this.setValue(this.elements.llmApiKey, ep.apiKey || '');
        this.renderModelList(ep.models || []);
        this.refreshActiveModelOptionsIfNeeded();
    }

    markEndpointChanged(endpointId) {
        if (!endpointId) return;
        const ep = this.llmEndpointMap[endpointId];
        if (!ep) return;
        this.newLlmEndpoints[endpointId] = {
            id: endpointId,
            name: ep.name || endpointId,
            url: ep.url || '',
            apiKey: ep.apiKey || '',
            models: ep.models || []
        };
    }

    updateSelectedEndpointName(value) {
        if (!this.selectedLlmEndpoint) return;
        const ep = this.llmEndpointMap[this.selectedLlmEndpoint];
        if (ep) {
            ep.name = value;
            this.markEndpointChanged(this.selectedLlmEndpoint);
            this.renderLlmTabs();
        }
    }

    updateSelectedEndpointUrl(value) {
        if (!this.selectedLlmEndpoint) return;
        const ep = this.llmEndpointMap[this.selectedLlmEndpoint];
        if (ep) {
            ep.url = value;
            this.markEndpointChanged(this.selectedLlmEndpoint);
        }
    }

    updateSelectedEndpointApiKey(value) {
        if (!this.selectedLlmEndpoint) return;
        const ep = this.llmEndpointMap[this.selectedLlmEndpoint];
        if (ep) {
            ep.apiKey = value;
            this.markEndpointChanged(this.selectedLlmEndpoint);
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
                <span class="truncate text-gray-900 dark:text-white">${model.display_name || model.model_name}</span>
                <div class="flex items-center gap-3">
                    <button type="button" class="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300" title="Test model connection">
                        <i class="fas fa-plug"></i>
                    </button>
                    <button type="button" class="text-red-500 hover:text-red-600" title="Remove model">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            const [testBtn, deleteBtn] = row.querySelectorAll('button');

            testBtn?.addEventListener('click', () => this.testLlmConnection(model, testBtn));
            deleteBtn?.addEventListener('click', () => this.removeModel(index));

            container.appendChild(row);
        });
    }

    async testLlmConnection(model, buttonEl = null) {
        if (!this.elements.modelLogger) return;

        const endpointId = this.selectedLlmEndpoint;
        const endpoint = this.llmEndpointMap[endpointId];
        const url = endpoint?.url || this.elements.llmUrl?.value || '';
        const apiKey = endpoint?.apiKey || this.elements.llmApiKey?.value || '';

        const modelId = typeof model === 'string' ? null : model?.id;
        if (!modelId) {
            this.elements.modelLogger.innerHTML = '<span class="text-red-500">Save settings before testing this model.</span>';
            return;
        }

        const pendingEndpoint = this.newLlmEndpoints?.[endpointId];
        const isPendingModel = Array.isArray(pendingEndpoint?.models)
            ? pendingEndpoint.models.some((m) => m?.id === modelId)
            : false;
        if (isPendingModel) {
            this.elements.modelLogger.innerHTML = '<span class="text-red-500">Save settings before testing newly added models.</span>';
            return;
        }

        if (!endpointId || !url) {
            this.elements.modelLogger.innerHTML = '<span class="text-red-500">Select an endpoint and provide an API URL first.</span>';
            return;
        }

        this.elements.modelLogger.innerHTML = '<span class="text-blue-500">Testing LLM connection...</span>';

        const originalHtml = buttonEl?.innerHTML;
        if (buttonEl) {
            buttonEl.disabled = true;
            buttonEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        }

        try {
            const payload = {
                task: 'test',
                endpoint_id: endpointId,
                model_id: modelId,
                // Optional overrides for unsaved endpoint edits
                url,
                api_key: apiKey
            };

            const response = await fetch('/api/test_llm_connection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                const errMsg = data?.error?.error || data?.error || 'LLM connection test failed';
                throw new Error(errMsg);
            }

            const status = data?.status_code || response.status;
            const responsePreview = data?.response || data?.result || data?.data || null;

            if (status >= 200 && status < 300) {
                this.elements.modelLogger.innerHTML = responsePreview
                    ? `<pre class="text-xs whitespace-pre-wrap text-green-600 dark:text-green-400">${typeof responsePreview === 'string' ? responsePreview : JSON.stringify(responsePreview, null, 2)}</pre>`
                    : '<span class="text-green-500">LLM connection test succeeded.</span>';
            } else {
                this.elements.modelLogger.innerHTML = '<span class="text-red-500">LLM connection test failed.</span>';
            }
        } catch (error) {
            this.elements.modelLogger.innerHTML = `<span class="text-red-500">${error.message}</span>`;
        } finally {
            if (buttonEl) {
                buttonEl.disabled = false;
                buttonEl.innerHTML = originalHtml;
            }
        }
    }

    addModel() {
        const value = this.elements.newModelInput?.value.trim();
        const ep = this.llmEndpointMap[this.selectedLlmEndpoint];
        if (!value || !ep) return;

        // Generate a stable ID tied to the endpoint (e.g. ollama-qwen3.0-coder)
        const endpointId = this.selectedLlmEndpoint;
        const safeName = value
            .trim()
            .toLowerCase()
            .replace(/\s+/g, '-')
            .replace(/[^a-z0-9._-]/g, '');
        const id = `${endpointId}-${safeName || `model_${Date.now()}`}`;

        if (ep.models.find((m) => m.model_name === value)) {
            this.toast('Model already exists for this endpoint', 'warning');
            return;
        }

        ep.models.push({
            id,
            endpoint_id: endpointId,
            model_name: value,
            display_name: value,
            provider: ep.name || ''
        });
        this.markEndpointChanged(this.selectedLlmEndpoint);
        this.elements.newModelInput.value = '';
        this.renderModelList(ep.models);
        this.refreshActiveModelOptionsIfNeeded();
    }

    removeModel(index) {
        const ep = this.llmEndpointMap[this.selectedLlmEndpoint];
        ep.models.splice(index, 1);
        this.markEndpointChanged(this.selectedLlmEndpoint);
        this.renderModelList(ep.models);
        this.refreshActiveModelOptionsIfNeeded();
    }

    markEndpointChanged(endpointId) {
        if (!endpointId) return;
        const ep = this.llmEndpointMap[endpointId];
        if (!ep) return;
        this.newLlmEndpoints[endpointId] = {
            id: endpointId,
            name: ep.name || endpointId,
            url: ep.url || '',
            apiKey: ep.apiKey || '',
            models: ep.models.map((m) => ({ ...m })) // include full model object
        };
        // Keep llmEndpoints array in sync so deletions/changes are detected reliably
        const idx = this.llmEndpoints.findIndex((e) => e.id === endpointId);
        if (idx !== -1) {
            this.llmEndpoints[idx].models = ep.models.map((m) => ({ ...m }));
        } else {
            this.llmEndpoints.push({ id: endpointId, name: ep.name || endpointId, url: ep.url || '', apiKey: ep.apiKey || '', models: ep.models.map((m) => ({ ...m })) });
        }
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

        const endpoint = { id, name, url, apiKey: '', models: [] };
        this.llmEndpoints.push(endpoint);
        this.llmEndpointMap[id] = endpoint;
        this.markEndpointChanged(id);
        this.renderLlmControls();
        this.selectLlmEndpoint(id);
        this.toast(`Endpoint ${name} created`, 'success');
    }

    deleteSelectedEndpoint() {
        const id = this.selectedLlmEndpoint;
        if (!id) return;

        if (!confirm(`Delete endpoint "${this.llmEndpointMap[id]?.name || id}"?`)) {
            return;
        }

        // Mark for deletion in the save payload
        this.newLlmEndpoints[id] = null;

        // Remove locally
        delete this.llmEndpointMap[id];
        this.llmEndpoints = this.llmEndpoints.filter((ep) => ep.id !== id);

        // Update selection
        const nextId = this.llmEndpoints[0]?.id || null;
        this.selectedLlmEndpoint = nextId;

        // If active endpoint was deleted, clear active selections (user can set a new one)
        if (this.elements.activeLlmEndpoint?.value === id) {
            this.elements.activeLlmEndpoint.value = '';
            this.handleActiveEndpointChange();
        }

        this.renderLlmControls();
        if (nextId) {
            this.selectLlmEndpoint(nextId);
        } else {
            this.setValue(this.elements.llmName, '');
            this.setValue(this.elements.llmUrl, '');
            this.setValue(this.elements.llmApiKey, '');
            this.renderModelList([]);
        }
        this.toast('Endpoint deleted (pending save)', 'info');
    }

    async saveSettings() {
        const payload = {
            ingestOn: this.elements.ingestOn?.checked ?? false,
            ingestAlgoVersion: this.elements.ingestAlgoVersion?.value || 'v1',
            ingestFrequency: Number(this.elements.ingestFrequency?.value) || 0,
            similarityCheck: this.elements.similarityCheck?.checked ?? false,
            similarityThreshold: Number(this.elements.similarityThreshold?.value) || 0,
            activeSiem: this.elements.activeSiem?.value || '',
            activeLlmEndpoint: this.elements.activeLlmEndpoint?.value || '',
            activeLlmModelId: this.elements.activeLlm?.value || '',
            fixCount: Number(this.elements.fixCount?.value) || 0
        };

        if (this.elements.siemSelect?.value) {
            payload.siem = this.elements.siemSelect.value;
            payload.searchIndex = this.elements.searchIndex?.value || '';
            payload.searchEntryCount = Number(this.elements.searchEntryCount?.value) || 0;
            payload.searchQuery = this.elements.searchQuery?.value || '';
        }

        // Always prepare llmModels map so we can include creations, updates and deletions
        const llmModels = {};

        // Include creations/updates from any endpoint changes the user made
        if (Object.keys(this.newLlmEndpoints).length) {
            payload.llmEndpoints = this.newLlmEndpoints; // full object payload

            Object.entries(this.newLlmEndpoints).forEach(([epId, epData]) => {
                if (!epData || !epData.models) return;
                epData.models.forEach((m) => {
                    // Ensure model has an id
                    const modelId = m.id || `model_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
                    // Normalize fields expected by backend
                    llmModels[modelId] = {
                        model_name: m.model_name || m.modelName || m.model || m.display_name || modelId,
                        display_name: m.display_name || m.displayName || m.model_name || m.modelName || modelId,
                        endpoint_id: epId,
                        provider: m.provider || ''
                    };
                });
            });
        }

        // Detect deletions: any model that existed originally but is no longer present in current endpoints
        const currentModelIds = new Set();
        this.llmEndpoints.forEach((ep) => {
            (ep.models || []).forEach((m) => { if (m && m.id) currentModelIds.add(m.id); });
        });

        (Object.keys(this.originalModelsById || {})).forEach((mid) => {
            if (!currentModelIds.has(mid)) {
                // mark for deletion (backend accepts null or {_delete: true})
                llmModels[mid] = null;
            }
        });

        if (Object.keys(llmModels).length) {
            payload.llmModels = llmModels;
        }

        this.setSavingState(true);

        try {
            const response = await fetch('/api/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();

            if (!response.ok) throw new Error(data.error || 'Failed to save settings');

            this.toast('Settings saved successfully', 'success');
            this.newLlmEndpoints = {};
            await this.loadSettings();
        } catch (error) {
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
