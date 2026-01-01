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
        this.statusSocket = null;
        this.statusPollInterval = null;

        this.init();
    }

    init() {
        // Only initialize if dashboard section exists
        if (!document.getElementById('dashboard-section')) return;

        // Search inputs
        document.getElementById('searchId')?.addEventListener('input', () => this.searchData());
        document.getElementById('searchLog')?.addEventListener('input', () => this.searchData());
        document.getElementById('searchRegex')?.addEventListener('input', () => this.searchData());
        document.getElementById('filterStatusSelect')?.addEventListener('change', () => this.searchData());

        // Action buttons
        document.getElementById('clearSearchButton')?.addEventListener('click', () => this.clearSearch());
        document.getElementById('refreshButton')?.addEventListener('click', () => this.searchData());
        document.getElementById('clearSelectionButton')?.addEventListener('click', () => this.clearSelection());
        document.getElementById('openParserButton')?.addEventListener('click', () => this.openParser());
        document.getElementById('deleteEntriesButton')?.addEventListener('click', () => this.deleteEntries());

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
        document.getElementById('entryModalClose')?.addEventListener('click', () => this.closeModal());
        document.getElementById('saveEntryChangesBtn')?.addEventListener('click', () => this.saveEntryChanges());
        document.getElementById('openParserFromModal')?.addEventListener('click', () => this.openParserFromModal());
        document.getElementById('deleteEntryFromModal')?.addEventListener('click', (e) => this.deleteEntryFromModal());

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

        // Initial load
        this.searchData();
        this.updateStatusPill();
    }

    async searchData() {
        const searchParams = {
            search_id: document.getElementById('searchId')?.value || '',
            search_log: document.getElementById('searchLog')?.value || '',
            search_regex: document.getElementById('searchRegex')?.value || '',
            filter_status: document.getElementById('filterStatusSelect')?.value || '',
            page: this.currentPage,
            per_page: this.entriesPerPage
        };

        try {
            const queryString = new URLSearchParams(searchParams).toString();
            const response = await fetch(`/api/smartlp/entries?${queryString}`);
            const data = await response.json();

            if (data.entries) {
                this.entries = data.entries;
                this.totalEntries = data.total;
                this.renderTable();
                this.updatePagination();
            }
        } catch (error) {
            console.error('Error fetching entries:', error);
            window.showToast('Error loading entries', 'error');
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
            row.onclick = () => this.showEntryDetails(entry);
            const statusBadge = this.getStatusBadge(entry.status.toLowerCase());

            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                    ${entry.id}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    ${new Date(entry.timestamp).toLocaleString()}
                </td>
                <td class="px-6 py-4 text-sm text-gray-900 dark:text-gray-100 truncate w-1/3 max-w-0" title="${this.escapeHtml(entry.log)}">
                    ${this.escapeHtml(entry.log.substring(0, 100))}${entry.log.length > 100 ? '...' : ''}
                </td>
                <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-400 truncate w-1/4 max-w-0" title="${this.escapeHtml(entry.regex || '')}">
                    ${this.escapeHtml((entry.regex || '').substring(0, 50))}${entry.regex && entry.regex.length > 50 ? '...' : ''}
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
            'partially-matched': { color: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200', icon: 'exclamation-circle' },
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
        document.getElementById('searchId').value = '';
        document.getElementById('searchLog').value = '';
        document.getElementById('searchRegex').value = '';
        document.getElementById('filterStatusSelect').value = '';
        this.currentPage = 1;
        this.searchData();
    }

    updateSelectionUI() {
        const count = this.selectedEntries.size;
        const buttons = ['clearSelectionButton', 'openParserButton', 'deleteEntriesButton'];

        buttons.forEach(btnId => {
            const btn = document.getElementById(btnId);
            if (btn) btn.disabled = count === 0;
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

        const statusEl = document.getElementById('modalStatus');
        statusEl.innerHTML = this.getStatusBadge(entry.status.toLowerCase());

        // Store current entry
        this.currentEntry = entry;

        modal.classList.remove('hidden');
    }

    closeModal() {
        document.getElementById('entryModal')?.classList.add('hidden');
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
}

// Initialize
const dashboard = new Dashboard();

// Make available globally
window.dashboard = dashboard;

export default dashboard;
