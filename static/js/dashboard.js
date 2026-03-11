/**
 * Dashboard Module - ES6
 * Manages the dashboard page with log entries, search, and filtering
 */

import loggerPanel from './loggerPanel.js';
import configHub from './configHub.js';

class Dashboard {
    constructor() {
        this.currentPage = 1;
        this.entriesPerPage = 15;
        this.totalEntries = 0;
        this.selectedEntries = new Set();
        this.entries = [];
        this.selectedDetectionRule = null;
        this.statusSocket = null;
        this.statusPollInterval = null;
        this.ingestProgressState = {};

        this.init();
    }

    init() {
        // Only initialize if dashboard section exists
        if (!document.getElementById('dashboard-section')) return;

        // Search inputs - debounced for better UX
        ['searchId', 'searchLog', 'searchRegex'].forEach(id => {
            document.getElementById(id)?.addEventListener('input', () => this.searchData());
        });
        document.getElementById('filterStatusSelect')?.addEventListener('change', () => this.searchData());

        // Action buttons
        const actions = {
            clearSearchButton: () => this.clearSearch(),
            refreshButton: () => this.searchData(),
            clearSelectionButton: () => this.clearSelection(),
            deleteEntriesButton: () => this.deleteEntries()
        };
        Object.entries(actions).forEach(([id, handler]) => {
            document.getElementById(id)?.addEventListener('click', handler);
        });

        // Pagination
        document.getElementById('prevPage')?.addEventListener('click', () => this.changePage(this.currentPage - 1));
        document.getElementById('nextPage')?.addEventListener('click', () => this.changePage(this.currentPage + 1));
        document.getElementById('goToPage')?.addEventListener('click', () => {
            const page = parseInt(document.getElementById('pageInput').value);
            if (page) this.changePage(page);
        });
        document.getElementById('rowsPerPage')?.addEventListener('change', (e) => {
            this.entriesPerPage = parseInt(e.target.value);
            this.currentPage = 1;
            this.searchData();
        });

        // Entry modal
        document.getElementById('entryModal')?.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeModal();
        });
        document.getElementById('entryModalClose')?.addEventListener('click', () => this.closeModal());
        document.getElementById('saveEntryChangesBtn')?.addEventListener('click', () => this.saveEntryChanges());
        document.getElementById('openParserButton')?.addEventListener('click', () => this.openParserFromModal());
        document.getElementById('deleteEntryFromModal')?.addEventListener('click', (e) => this.deleteEntryFromModal());
        document.getElementById('deployConfigFromModal')?.addEventListener('click', (e) => {
            if (!this.currentEntry) {
                window.showToast?.('No entry selected', 'error');
                return;
            }

            // Ensure Config Hub receives a selection when deploying from the modal.
            configHub.setSelectedEntries([this.currentEntry]);
            configHub.validateAndGenerate();
        });

        document.getElementById('deployRulePopup')?.addEventListener('click', (e) => {
            if (e.target === e.currentTarget || e.target.classList.contains('bg-opacity-50')) this.closeDeployRulePopup();
        });
        document.getElementById('deployRuleCancel')?.addEventListener('click', () => this.closeDeployRulePopup());
        document.getElementById('deployRuleConfirm')?.addEventListener('click', () => this.deployRuleFromPopup());

        // Listen for section changes
        window.addEventListener('sectionChanged', (e) => {
            if (e.detail.section === 'dashboard') {
                this.searchData();
            }
        });

        // Listen for config events
        window.addEventListener('configEntryRemoved', (e) => {
            this.selectedEntries.delete(e.detail.entryId);
            this.updateSelectionUI();
        });

        window.addEventListener('configSelectionCleared', () => {
            this.clearSelection();
        });

        // Setup copy buttons
        this.setupCopyButtons();

        // Setup manual ingestion modal
        this.setupIngestModal();

        // Initial load
        this.searchData();
        this.updateStatusPill();
    }

    async searchData() {
        const params = {
            search_id: document.getElementById('searchId')?.value || '',
            search_log: document.getElementById('searchLog')?.value || '',
            search_regex: document.getElementById('searchRegex')?.value || '',
            filter_status: document.getElementById('filterStatusSelect')?.value || '',
            page: this.currentPage,
            per_page: this.entriesPerPage
        };

        try {
            const response = await fetch(`/api/smartlp/entries?${new URLSearchParams(params)}`);
            const data = await response.json();

            if (data.entries) {
                this.entries = data.entries;
                this.totalEntries = data.total;
                this.renderTable();
                this.updatePagination();
            }
        } catch (error) {
            console.error('Error fetching entries:', error);
            window.showToast?.('Error loading entries', 'error');
        }
    }

    renderTable() {
        const tbody = document.getElementById('entryTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (this.entries.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                        <i class="fas fa-inbox text-4xl mb-2"></i>
                        <p>No entries found</p>
                    </td>
                </tr>
            `;
            return;
        }

        this.entries.forEach(entry => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors duration-150';
            row.addEventListener('click', () => {
                this.showEntryDetails(entry);
            });
            const statusBadge = this.getStatusBadge(entry.status.toLowerCase());

            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                    ${entry.id}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    ${new Date(entry.timestamp).toLocaleString('en-GB', {
                day: 'numeric',    // "2"
                month: 'short',    // "Jan"
                hour: '2-digit',   // "10"
                minute: '2-digit', // "34"
                hour12: false      // 24-hour format (Standard for SecOps)
            })}
                </td>
                <td class="px-6 py-4 text-sm text-gray-900 dark:text-gray-100 truncate w-1/3 max-w-0" title="${this.escapeHtml(entry.log)}">
                    ${this.escapeHtml(entry.log.substring(0, 100))}${entry.log.length > 100 ? '...' : ''}
                </td>
                <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-400 truncate w-1/4 max-w-0" title="${this.escapeHtml(entry.regex || '')}">
                    ${entry.regex
                    ? this.escapeHtml((entry.regex || '').substring(0, 50))
                    : `<a href="${entry.package_url}" target="_blank" class="badge badge-native" title="Package available">${this.escapeHtml(entry.package_name)}</a>`
                }${entry.regex && entry.regex.length > 50 ? '...' : ''}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm">
                    ${statusBadge}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-center" onclick="event.stopPropagation()">
                    <input type="checkbox" 
                        class="w-4 h-4 text-blue-600 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 cursor-pointer"
                        data-entry-id="${entry.id}"
                        ${this.selectedEntries.has(entry.id) ? 'checked' : ''}>
                </td>
            `;

            // Checkbox handler
            const checkbox = row.querySelector('input[type="checkbox"]');
            checkbox.addEventListener('change', (e) => {
                e.stopPropagation();
                if (checkbox.checked) {
                    this.selectedEntries.add(entry.id);
                } else {
                    this.selectedEntries.delete(entry.id);
                }
                this.updateSelectionUI();
            });

            tbody.appendChild(row);
        });

        document.getElementById('resultsCount').textContent = `${this.totalEntries} entries`;
    }

    getStatusBadge(status) {
        const statusMap = {
            'matched': { color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200', icon: 'check-circle' },
            'unmatched': { color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200', icon: 'times-circle' },
            'pending': { color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200', icon: 'clock' },
            'partially matched': { color: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200', icon: 'exclamation-circle' },
            'deployed': { color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200', icon: 'cloud-upload-alt' }
        };

        const statusInfo = statusMap[status] || statusMap['pending'];
        return `
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.color}">
                <i class="fas fa-${statusInfo.icon} mr-1"></i>
                ${status}
            </span>
        `;
    }

    updatePagination() {
        const totalPages = Math.ceil(this.totalEntries / this.entriesPerPage);
        const start = (this.currentPage - 1) * this.entriesPerPage + 1;
        const end = Math.min(this.currentPage * this.entriesPerPage, this.totalEntries);

        document.getElementById('pageInfo').textContent =
            `Showing ${start}-${end} of ${this.totalEntries} entries`;

        // Update prev/next buttons
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');

        if (prevBtn) prevBtn.disabled = this.currentPage === 1;
        if (nextBtn) nextBtn.disabled = this.currentPage >= totalPages;

        // Generate page buttons
        const paginationButtons = document.getElementById('pagination-buttons');
        if (paginationButtons) {
            paginationButtons.innerHTML = '';

            // Show at most 5 page buttons
            const startPage = Math.max(1, this.currentPage - 2);
            const endPage = Math.min(totalPages, startPage + 4);

            for (let i = startPage; i <= endPage; i++) {
                const btn = document.createElement('button');
                btn.textContent = i;
                btn.className = `px-3 py-1 rounded-lg text-sm ${i === this.currentPage
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                    }`;
                btn.onclick = () => this.changePage(i);
                paginationButtons.appendChild(btn);
            }
        }
    }

    changePage(page) {
        const totalPages = Math.ceil(this.totalEntries / this.entriesPerPage);
        if (page < 1 || page > totalPages) return;

        this.currentPage = page;
        this.searchData();
    }

    clearSearch() {
        ['searchId', 'searchLog', 'searchRegex', 'filterStatusSelect'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
        this.currentPage = 1;
        this.searchData();
    }

    updateSelectionUI() {
        const hasSelection = this.selectedEntries.size > 0;

        ['clearSelectionButton', 'deleteEntriesButton'].forEach(btnId => {
            const btn = document.getElementById(btnId);
            if (btn) btn.disabled = !hasSelection;
        });

        // Update config hub
        const selectedEntryData = this.entries.filter(e => this.selectedEntries.has(e.id));
        configHub.setSelectedEntries(selectedEntryData);
    }

    clearSelection() {
        this.selectedEntries.clear();
        document.querySelectorAll('input[type="checkbox"][data-entry-id]').forEach(cb => {
            cb.checked = false;
        });
        this.updateSelectionUI();
    }

    openParser() {
        if (this.selectedEntries.size === 0) return;

        const selectedIds = Array.from(this.selectedEntries);
        const selectedEntryData = this.entries.filter(e => this.selectedEntries.has(e.id));
        sessionStorage.setItem('parserEntries', JSON.stringify(selectedIds));
        sessionStorage.setItem('parserEntryData', JSON.stringify(selectedEntryData));

        // Navigate to playground
        window.navigateToSection('playground');
    }

    openParserFromModal() {
        if (!this.currentEntry) return;

        sessionStorage.setItem('parserEntries', JSON.stringify([this.currentEntry.id]));
        sessionStorage.setItem('parserEntryData', JSON.stringify([this.currentEntry]));

        this.closeModal();
        window.navigateToSection('playground');
    }

    async deleteEntryFromModal() {
        if (!this.currentEntry?.id) return;

        const entryId = this.currentEntry.id;
        if (!confirm(`Are you sure you want to delete entry ${entryId}?`)) {
            return;
        }

        const deleteBtn = document.getElementById('deleteEntryFromModal');
        if (deleteBtn) deleteBtn.disabled = true;

        try {
            const response = await fetch('/api/smartlp/entries/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids: [entryId] })
            });

            const data = await response.json().catch(() => ({}));

            if (response.ok && data.success) {
                window.showToast(`Deleted entry ${entryId}`, 'success');

                // Keep selection/config hub in sync
                this.selectedEntries.delete(entryId);
                this.updateSelectionUI();

                // If we just deleted the last entry on the page, step back a page when possible
                if (this.entries?.length === 1 && this.currentPage > 1) {
                    this.currentPage -= 1;
                }

                this.currentEntry = null;
                this.closeModal();
                this.searchData();
            } else {
                window.showToast(data.message || `Failed to delete entry ${entryId}`, 'error');
            }
        } catch (error) {
            console.error('Error deleting entry:', error);
            window.showToast('Error deleting entry', 'error');
        } finally {
            if (deleteBtn) deleteBtn.disabled = false;
        }
    }

    async deleteEntries() {
        if (this.selectedEntries.size === 0) return;

        if (!confirm(`Are you sure you want to delete ${this.selectedEntries.size} entries?`)) {
            return;
        }

        try {
            const response = await fetch('/api/smartlp/entries/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids: Array.from(this.selectedEntries) })
            });

            const data = await response.json();

            if (data.success) {
                window.showToast(`Deleted ${this.selectedEntries.size} entries`, 'success');
                this.clearSelection();
                this.searchData();
            } else {
                window.showToast('Failed to delete entries', 'error');
            }
        } catch (error) {
            console.error('Error deleting entries:', error);
            window.showToast('Error deleting entries', 'error');
        }
    }

    showEntryDetails(entry) {
        const modal = document.getElementById('entryModal');
        if (!modal) return;

        document.getElementById('modalId').textContent = entry.id;
        document.getElementById('modalTimestamp').textContent = new Date(entry.timestamp).toLocaleString();
        document.getElementById('modalIndex').value = entry.index || '';
        document.getElementById('modalSourceType').value = entry.source_type || '';
        document.getElementById('modalLogType').textContent = entry.log_type || 'N/A';
        document.getElementById('modalLog').textContent = entry.log;
        document.getElementById('modalRegex').textContent = entry.regex || 'N/A';

        const pkgLink = document.getElementById('modalPackageUrl');
        const pkgName = document.getElementById('modalPackageName');

        if (pkgLink && pkgName) {
            if (entry.package_url) {
                pkgLink.href = entry.package_url;
                pkgLink.classList.remove('pointer-events-none', 'text-gray-400');
                pkgName.textContent = entry.package_name || 'View Package';
            } else {
                pkgLink.removeAttribute('href');
                pkgLink.classList.add('pointer-events-none', 'text-gray-400');
                pkgName.textContent = 'N/A';
            }
        }

        const statusEl = document.getElementById('modalStatus');
        statusEl.innerHTML = this.getStatusBadge(entry.status.toLowerCase());

        // Detection rules (frontend-only rendering)
        this.renderDetectionRules(entry);

        // Store current entry
        this.currentEntry = entry;

        // Reset deploy popup inputs each time a new entry is opened
        this.resetDeployRulePopup();

        modal.classList.remove('hidden');
    }

    resetDeployRulePopup() {
        const popup = document.getElementById('deployRulePopup');
        if (popup) popup.classList.add('hidden');

        const severityEl = document.getElementById('deploySeverity');
        const riskEl = document.getElementById('deployRiskScore');
        const latestEl = document.getElementById('deployLatest');
        const earliestEl = document.getElementById('deployEarliest');

        if (severityEl) severityEl.value = '';
        if (riskEl) riskEl.value = '';
        if (latestEl) latestEl.value = '';
        if (earliestEl) earliestEl.value = '';
        // Clear any selected detection rule when resetting popup
        this.selectedDetectionRule = null;
    }

    openDeployRulePopup() {
        if (!this.currentEntry?.id) {
            window.showToast?.('No entry selected', 'error');
            return;
        }

        // Backend requires entry to be parsed/matched before deployment
        const status = (this.currentEntry?.status || '').toString().toLowerCase();
        if (status !== 'deployed') {
            window.showToast?.('Log must be parsed before deploying a rule', 'error');
            return;
        }

        const popup = document.getElementById('deployRulePopup');
        if (!popup) return;
        popup.classList.remove('hidden');
    }

    closeDeployRulePopup() {
        const popup = document.getElementById('deployRulePopup');
        if (!popup) return;
        popup.classList.add('hidden');
    }

    async deployRuleFromPopup() {
        const entryId = this.currentEntry?.id;
        if (!entryId) return;

        // Prepare confirm button handle early so we can re-enable on errors
        const confirmBtn = document.getElementById('deployRuleConfirm');

        // Determine which rule id to send to backend: prefer sigma_id, then id, then title
        const selected = this.selectedDetectionRule || null;
        const ruleIdToSend = selected?.sigma_id || selected?.id || selected?.title || null;
        if (!ruleIdToSend) {
            window.showToast?.('No detection rule selected to deploy', 'error');
            if (confirmBtn) confirmBtn.disabled = false;
            return;
        }

        const severity = (document.getElementById('deploySeverity')?.value || '').trim();
        const riskRaw = (document.getElementById('deployRiskScore')?.value || '').trim();
        const dispatch_latest_time = (document.getElementById('deployLatest')?.value || '').trim();
        const dispatch_earliest_time = (document.getElementById('deployEarliest')?.value || '').trim();

        if (!severity || !riskRaw || !dispatch_latest_time || !dispatch_earliest_time) {
            window.showToast?.('All fields are required', 'error');
            return;
        }

        const risk_score = Number(riskRaw);
        if (!Number.isFinite(risk_score) || risk_score < 0 || risk_score > 100) {
            window.showToast?.('Risk score must be between 0 and 100', 'error');
            return;
        }

        if (confirmBtn) confirmBtn.disabled = true;

        try {
            const response = await fetch('/api/smartlp/deploy_rule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: ruleIdToSend,
                    entry_id: entryId,
                    severity,
                    risk_score,
                    dispatch_latest_time,
                    dispatch_earliest_time
                })
            });

            const data = await response.json().catch(() => ({}));

            if (response.ok && data?.success) {
                window.showToast?.(data.message || 'Rule deployed', 'success');
                this.closeDeployRulePopup();
                this.closeModal();
                this.searchData();
            } else {
                const msg = data?.error || data?.message || 'Failed to deploy rule';
                window.showToast?.(msg, 'error');
            }
        } catch (error) {
            console.error('Error deploying rule:', error);
            window.showToast?.('Error deploying rule', 'error');
        } finally {
            if (confirmBtn) confirmBtn.disabled = false;
        }
    }

    renderDetectionRules(entry) {
        const emptyEl = document.getElementById('modalDetectionRulesEmpty');
        const listEl = document.getElementById('modalDetectionRulesList');
        if (!emptyEl || !listEl) return;

        // Clear previous content
        listEl.innerHTML = '';
        emptyEl.classList.add('hidden');

        const rules = Array.isArray(entry?.detection_rules) ? entry.detection_rules : [];
        const status = (entry?.detection_status || '').toLowerCase();

        if (status === 'none' || rules.length === 0) {
            emptyEl.classList.remove('hidden');
            return;
        }

        // Sort by confidence descending
        const sorted = [...rules].sort((a, b) => (b?.confidence ?? 0) - (a?.confidence ?? 0));

        sorted.forEach((rule, idx) => {
            const title = (rule?.title ?? '').toString();
            const confidence = Number(rule?.confidence ?? 0);
            const reason = (rule?.reason ?? '').toString();
            const siemRule = (rule?.siem_rule ?? '').toString();
            const deployed = Boolean(rule?.deployed ?? false);

            const pct = Number.isFinite(confidence) ? Math.round(confidence * 100) : 0;

            let badgeClass = 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
            if (confidence >= 0.85) {
                badgeClass = 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
            } else if (confidence >= 0.75) {
                badgeClass = 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
            }

            const card = document.createElement('div');
            card.className = 'border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800';

            // Header row: Sigma Title + confidence badge
            const headerRow = document.createElement('div');
            headerRow.className = 'flex items-start justify-between gap-4';

            const sigmaTitle = document.createElement('span');
            sigmaTitle.className = 'text-gray-900 dark:text-gray-100 font-semibold whitespace-pre-wrap break-words';
            sigmaTitle.textContent = title || 'N/A';

            const badge = document.createElement('span');
            badge.className = `px-2.5 py-0.5 rounded-full text-xs ${badgeClass}`;
            badge.textContent = `${pct}% Confidence`;

            headerRow.appendChild(sigmaTitle);
            headerRow.appendChild(badge);

            // Reason
            const reasonEl = document.createElement('p');
            reasonEl.className = 'mt-2 text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap break-words';
            reasonEl.textContent = reason || '';

            card.appendChild(headerRow);
            if (reason) card.appendChild(reasonEl);

            // Optional expandable SIEM rule + copy + deploy
            const hasSiemRule = Boolean(siemRule && siemRule.trim());
            if (hasSiemRule) {
                const controlsId = `modalSiemRule_${Date.now()}_${idx}`;

                const toggleBtn = document.createElement('button');
                toggleBtn.type = 'button';
                toggleBtn.className = 'mt-3 text-sm text-blue-600 dark:text-blue-400 hover:underline';
                toggleBtn.textContent = 'View Rule';
                toggleBtn.setAttribute('aria-expanded', 'false');
                toggleBtn.setAttribute('aria-controls', controlsId);

                const siemContainer = document.createElement('div');
                siemContainer.id = controlsId;
                siemContainer.className = 'mt-2 relative hidden';

                const pre = document.createElement('pre');
                pre.className = 'text-xs text-gray-900 dark:text-gray-100 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg p-3 whitespace-pre-wrap break-words overflow-x-auto';
                const code = document.createElement('code');
                code.textContent = siemRule;
                pre.appendChild(code);

                siemContainer.appendChild(pre);

                const copyBtn = document.createElement('button');
                copyBtn.type = 'button';
                copyBtn.className = 'absolute top-2 right-2 z-10 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 copy-btn';
                copyBtn.setAttribute('aria-label', 'Copy Rule');
                copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
                siemContainer.appendChild(copyBtn);

                const deployBtn = document.createElement('button');
                deployBtn.type = 'button';
                deployBtn.className = 'text-xs mt-4 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors duration-200';
                deployBtn.id = 'deployRuleFromModal';
                deployBtn.innerHTML = '<i class="fas fa-cloud-upload-alt mr-2"></i>Deploy Rule';
                deployBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    // Store which detection rule the user intends to deploy
                    try {
                        this.selectedDetectionRule = rule;
                    } catch (err) {
                        this.selectedDetectionRule = null;
                    }
                    this.openDeployRulePopup();
                });

                if (!deployed) {
                    siemContainer.appendChild(deployBtn);
                } else {
                    const deployedLabel = document.createElement('span');
                    deployedLabel.className = 'inline-flex items-center px-2.5 py-0.5 mt-4 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
                    deployedLabel.innerHTML = '<i class="fas fa-cloud-upload-alt mr-1"></i>deployed';
                    siemContainer.appendChild(deployedLabel);
                }

                toggleBtn.addEventListener('click', () => {
                    const isHidden = siemContainer.classList.contains('hidden');
                    siemContainer.classList.toggle('hidden', !isHidden);
                    toggleBtn.setAttribute('aria-expanded', String(isHidden));
                    toggleBtn.textContent = isHidden ? 'Hide Rule' : 'View Rule';
                });

                card.appendChild(toggleBtn);
                card.appendChild(siemContainer);
            }

            listEl.appendChild(card);
        });
    }

    closeModal() {
        document.getElementById('entryModal')?.classList.add('hidden');
        this.currentEntry = null;
        this.resetDeployRulePopup();
    }

    async saveEntryChanges() {
        if (!this.currentEntry) return;

        const updates = {
            index: document.getElementById('modalIndex').value,
            source_type: document.getElementById('modalSourceType').value
        };

        try {
            const response = await fetch(`/api/smartlp/entries/${this.currentEntry.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });

            const data = await response.json();

            if (response.ok) {
                window.showToast(data.message || 'Entry updated successfully', 'success');
                this.closeModal();
                this.searchData();
            } else {
                window.showToast(data.message || 'Failed to update entry', 'error');
            }
        } catch (error) {
            console.error('Error updating entry:', error);
            window.showToast('Error updating entry', 'error');
        }
    }

    setupCopyButtons() {
        document.addEventListener('click', (e) => {
            const copyBtn = e.target.closest('.copy-btn');
            if (!copyBtn) return;

            const codeEl = copyBtn.parentElement.querySelector('code');
            if (!codeEl) return;

            const text = codeEl.textContent;
            navigator.clipboard.writeText(text).then(() => {
                const originalIcon = copyBtn.innerHTML;
                copyBtn.innerHTML = '<i class="fas fa-check"></i>';
                setTimeout(() => {
                    copyBtn.innerHTML = originalIcon;
                }, 2000);
            });
        });
    }

    updateStatusPill() {
        const pill = document.getElementById('statusPill');
        if (!pill) return;

        const fetchAndUpdate = () => this.fetchStatusAndUpdate();

        fetchAndUpdate();
        if (this.statusPollInterval) {
            clearInterval(this.statusPollInterval);
        }
        this.statusPollInterval = setInterval(fetchAndUpdate, 15000);

        if (typeof io !== 'undefined' && !this.statusSocket) {
            this.statusSocket = io();
            this.statusSocket.on('status_update', (data) => {
                const statusKey = data?.status || 'idle';
                this.applyStatusToPill(statusKey, data);
            });
        }
    }

    async fetchStatusAndUpdate() {
        try {
            const response = await fetch('/api/smartlp/ingestion/status');
            if (!response.ok) throw new Error('Failed to fetch ingestion status');

            const payload = await response.json();
            const statusKey = this.getStatusKeyFromPayload(payload);
            this.applyStatusToPill(statusKey, payload);
        } catch (error) {
            console.error('Error fetching ingestion status:', error);
        }
    }

    getStatusKeyFromPayload(payload) {
        if (!payload) return 'idle';

        const normalizedEnabled = this.normalizeBoolean(
            payload.ingestion_enabled ?? payload.ingest_on ?? payload.ingestOn
        );

        return normalizedEnabled ? 'polling' : 'idle';
    }

    applyStatusToPill(statusKey = 'idle', payload = {}) {
        const pill = document.getElementById('statusPill');
        if (!pill) return;

        const statusMap = {
            polling: { color: 'bg-blue-100 dark:bg-blue-900', text: 'Polling', dot: 'bg-blue-500', pulse: true },
            syncing: { color: 'bg-green-100 dark:bg-green-900', text: 'Syncing', dot: 'bg-green-500', pulse: true },
            idle: { color: 'bg-gray-100 dark:bg-gray-700', text: 'Idle', dot: 'bg-gray-400', pulse: false }
        };

        const status = statusMap[statusKey] || statusMap.idle;
        const siemLabel = this.formatSiemLabel(payload?.active_siem);
        const displayText = statusKey === 'polling' && siemLabel
            ? `${status.text} ${siemLabel}`
            : status.text;

        pill.className = `px-4 py-2 rounded-full ${status.color} flex items-center space-x-2`;
        pill.innerHTML = `
            <span class="w-2 h-2 rounded-full ${status.dot} ${status.pulse ? 'pulse-soft' : ''}"></span>
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">${displayText}</span>
        `;
    }

    formatSiemLabel(value) {
        if (!value) return '';
        return value
            .split(/[_-]/)
            .filter(Boolean)
            .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
            .join(' ');
    }

    normalizeBoolean(value) {
        if (value === undefined || value === null) return false;
        if (typeof value === 'boolean') return value;
        if (typeof value === 'string') {
            return value.toLowerCase() === 'true';
        }
        return Boolean(value);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    setupIngestModal() {
        const addDataBtn = document.getElementById('addDataButton');
        const ingestModal = document.getElementById('ingestModal');
        const ingestModalClose = document.getElementById('ingestModalClose');
        const ingestCancelBtn = document.getElementById('ingestCancelBtn');
        const ingestSubmitBtn = document.getElementById('ingestSubmitBtn');
        const ingestTextarea = document.getElementById('ingestTextarea');

        addDataBtn?.addEventListener('click', () => {
            ingestModal?.classList.remove('hidden');
            this.resetIngestProgress();
        });

        ingestModal?.addEventListener('click', (e) => {
            if (e.target === ingestModal) ingestModal.classList.add('hidden');
        });

        ingestModalClose?.addEventListener('click', () => {
            ingestModal?.classList.add('hidden');
        });

        ingestCancelBtn?.addEventListener('click', () => {
            ingestModal?.classList.add('hidden');
        });

        ingestSubmitBtn?.addEventListener('click', () => this.submitManualIngestion());

        // Setup Socket.IO listener for ingestion progress
        if (typeof io !== 'undefined') {
            const socket = io();
            socket.on('ingest_progress', (data) => {
                this.updateIngestProgress(data);
            });
        }
    }

    resetIngestProgress() {
        const progressContainer = document.getElementById('ingestProgressContainer');
        progressContainer?.classList.add('hidden');

        const steps = ['dedup', 'classify', 'parser', 'regex', 'detection', 'save'];
        steps.forEach(step => {
            const icon = document.getElementById(`step-${step}-icon`);
            const status = document.getElementById(`step-${step}-status`);
            icon?.classList.remove('fa-spinner', 'fa-spin', 'fa-check', 'fa-times', 'text-blue-500', 'text-green-500', 'text-red-500');
            icon?.classList.add('fa-circle', 'text-gray-400');
            if (status) status.textContent = 'Pending';
        });

        this.ingestProgressState = {};
    }

    async submitManualIngestion() {
        const textarea = document.getElementById('ingestTextarea');
        const submitBtn = document.getElementById('ingestSubmitBtn');
        const progressContainer = document.getElementById('ingestProgressContainer');

        const rawInput = textarea?.value?.trim();
        if (!rawInput) {
            window.showToast?.('Please enter at least one log entry', 'warning');
            return;
        }

        const logs = rawInput.split('\n').filter(line => line.trim() !== '');
        if (logs.length === 0) {
            window.showToast?.('No valid log entries found', 'warning');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
        progressContainer?.classList.remove('hidden');

        try {
            const response = await fetch('/api/smartlp/ingest/manual', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ logs })
            });

            const result = await response.json();

            if (response.ok) {
                window.showToast?.(`Started ingestion of ${logs.length} log(s)`, 'success');
            } else {
                window.showToast?.(result.error || 'Ingestion failed', 'error');
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-upload"></i><span>Start Ingestion</span>';
            }
        } catch (error) {
            console.error('Manual ingestion error:', error);
            window.showToast?.('Failed to submit logs for ingestion', 'error');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-upload"></i><span>Start Ingestion</span>';
        }
    }

    updateIngestProgress(data) {
        const { stage, status, message, log_index, total_logs } = data;

        const stageMap = {
            'deduplication': 'dedup',
            'classification': 'classify',
            'parser_resolution': 'parser',
            'regex_generation': 'regex',
            'detection_mapping': 'detection',
            'saved': 'save'
        };

        const stepId = stageMap[stage];
        if (!stepId) return;

        const icon = document.getElementById(`step-${stepId}-icon`);
        const statusText = document.getElementById(`step-${stepId}-status`);

        if (!icon || !statusText) return;

        // Update icon based on status
        icon.classList.remove('fa-circle', 'fa-spinner', 'fa-spin', 'fa-check', 'fa-times', 'text-gray-400', 'text-blue-500', 'text-green-500', 'text-red-500');

        if (status === 'in_progress') {
            icon.classList.add('fa-spinner', 'fa-spin', 'text-blue-500');
            statusText.textContent = message || 'In Progress...';
        } else if (status === 'completed') {
            icon.classList.add('fa-check', 'text-green-500');
            statusText.textContent = message || 'Completed';
        } else if (status === 'failed') {
            icon.classList.add('fa-times', 'text-red-500');
            statusText.textContent = message || 'Failed';
        }

        // Store state for persistence
        this.ingestProgressState[stepId] = { status, message };

        // Check if all stages complete
        if (stage === 'saved' && status === 'completed') {
            setTimeout(() => {
                const submitBtn = document.getElementById('ingestSubmitBtn');
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-upload"></i><span>Start Ingestion</span>';

                window.showToast?.('Ingestion completed successfully', 'success');

                // Refresh dashboard
                this.searchData();

                // Close modal after a delay
                setTimeout(() => {
                    document.getElementById('ingestModal')?.classList.add('hidden');
                    document.getElementById('ingestTextarea').value = '';
                    this.resetIngestProgress();
                }, 2000);
            }, 500);
        }
    }
}

// Initialize
const dashboard = new Dashboard();

// Make available globally
window.dashboard = dashboard;

export default dashboard;
