/**
 * Playground Module - ES6
 * Migrated parser functionality with session-aware entry loading
 */

class Playground {
    constructor() {
        this.currentEntry = null;
        this.entriesQueue = [];
        this.currentEntryIndex = 0;
        this.dom = {};
        this.sectionEl = null;
        this.init();
    }

    init() {
        this.sectionEl = document.getElementById('playground-section');
        if (!this.sectionEl) return;

        this.cacheDom();
        this.bindEvents();
        this.restoreFromSession();
        this.loadEntryStatistics();
        this.setupSocketListeners();

        window.addEventListener('sectionChanged', (e) => {
            if (e.detail.section === 'playground') {
                this.loadFromSession();
            }
        });
    }

    setupSocketListeners() {
        if (typeof io !== 'undefined') {
            this.socket = io();
            this.socket.on('stats_update', () => this.loadEntryStatistics());
        }
    }

    cacheDom() {
        this.dom.regexDisplay = document.getElementById('regexDisplay');
        this.dom.logDisplay = document.getElementById('logDisplay');
        this.dom.matchDisplay = document.getElementById('matchDisplay');
        this.dom.captureGroupDisplay = document.getElementById('captureGroupDisplay');
        this.dom.matchLogger = document.getElementById('matchLogger');
        this.dom.logger = document.getElementById('logger');

        this.dom.reduceButton = document.getElementById('reduceButton');
        this.dom.generateButton = document.getElementById('generateButton');
        this.dom.fixButton = document.getElementById('fixButton');
        this.dom.pullEntryButton = document.getElementById('pullEntryButton');
        this.dom.clearEntryButton = document.getElementById('clearEntryButton');
        this.dom.saveButton = document.getElementById('saveToDBButton');
        this.dom.backButton = document.getElementById('backButton');

        this.dom.generateSpinner = document.getElementById('generateSpinner');
        this.dom.fixSpinner = document.getElementById('fixSpinner');
        this.dom.saveSpinner = document.getElementById('saveToDBSpinner');
    }

    bindEvents() {
        const events = {
            regexDisplay: ['input', () => this.findMatch()],
            reduceButton: ['click', () => this.reduceRegex()],
            generateButton: ['click', () => this.queryLLM('generate')],
            fixButton: ['click', () => this.queryLLM('fix')],
            pullEntryButton: ['click', () => this.pullEntry()],
            clearEntryButton: ['click', () => this.clearEntry()],
            saveButton: ['click', () => this.saveToDB()],
            backButton: ['click', () => window.navigateToSection?.('dashboard')]
        };

        Object.entries(events).forEach(([key, [event, handler]]) => {
            this.dom[key]?.addEventListener(event, handler);
        });
    }

    restoreFromSession() {
        const storedLog = this.getSessionItem('log');
        const storedRegex = this.getSessionItem('regex');
        const storedId = this.getSessionItem('id', '');

        if (storedLog || storedRegex) {
            this.setEntry({
                id: storedId || 'New Entry',
                log: storedLog,
                regex: storedRegex
            });
        }

        this.loadFromSession();
    }

    loadFromSession() {
        const entriesData = sessionStorage.getItem('parserEntryData');
        const entryIds = sessionStorage.getItem('parserEntries');

        if (entriesData) {
            try {
                const parsed = JSON.parse(entriesData) || [];
                if (Array.isArray(parsed) && parsed.length) {
                    this.loadEntries(parsed);
                    return;
                }
            } catch (err) {
                console.warn('Invalid parserEntryData in session', err);
            }
        }

        if (entryIds) {
            try {
                const ids = JSON.parse(entryIds) || [];
                if (Array.isArray(ids) && ids.length) {
                    this.loadEntries(ids);
                }
            } catch (err) {
                console.warn('Invalid parserEntries in session', err);
            }
        }
    }

    async loadEntries(entries) {
        if (!Array.isArray(entries) || entries.length === 0) return;

        // Accept either full entry objects or IDs
        const needsFetch = typeof entries[0] !== 'object';
        let loaded = [];

        if (needsFetch) {
            const results = await Promise.all(entries.map(id => this.fetchEntryById(id)));
            loaded = results.filter(Boolean);
        } else {
            loaded = entries.filter(Boolean);
        }

        if (!loaded.length) {
            this.setLogger('No entries found to load');
            return;
        }

        this.entriesQueue = loaded;
        this.currentEntryIndex = 0;
        this.setEntry(this.entriesQueue[0]);

        if (window.showToast) {
            window.showToast(`Loaded ${loaded.length} entr${loaded.length === 1 ? 'y' : 'ies'} for parsing`, 'success');
        }
    }

    async fetchEntryById(id) {
        if (!id) return null;

        try {
            const query = new URLSearchParams({ search_id: id, page: 1, per_page: 1 }).toString();
            const response = await fetch(`/api/smartlp/entries?${query}`);
            const data = await response.json();
            return data.entries && data.entries.length ? data.entries[0] : null;
        } catch (error) {
            console.error('Failed to fetch entry', error);
            return null;
        }
    }

    setEntry(entry) {
        if (!entry) return;

        this.currentEntry = entry;

        if (this.dom.logDisplay) {
            this.dom.logDisplay.textContent = entry.log || '';
        }
        if (this.dom.regexDisplay) {
            this.dom.regexDisplay.value = entry.regex || '';
        }

        const timestamp = entry.timestamp ? ` (${new Date(entry.timestamp).toLocaleString()})` : '';
        this.setLogger(`Entry ${entry.id || 'New Entry'}${timestamp}`);

        this.setSessionItem('id', entry.id || '');
        this.setSessionItem('log', entry.log || '');
        this.setSessionItem('regex', entry.regex || '');

        this.findMatch();
    }

    setLogger(message) {
        if (this.dom.logger) {
            this.dom.logger.textContent = message; // Use textContent to overwrite, not append
        }
    }

    getSessionItem(key, defaultValue = '') {
        return window.getSessionItem?.(key, defaultValue) ?? sessionStorage.getItem(key) ?? defaultValue;
    }

    setSessionItem(key, value) {
        window.setSessionItem?.(key, value) ?? sessionStorage.setItem(key, value);
    }

    toggleSpinner(spinner, button, show) {
        if (spinner) spinner.classList.toggle('hidden', !show);
        if (button) button.disabled = !!show;
    }

    async pullEntry() {
        if (!this.dom.pullEntryButton) return;

        const originalHtml = this.dom.pullEntryButton.innerHTML;
        this.dom.pullEntryButton.disabled = true;
        this.dom.pullEntryButton.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Pulling...';

        try {
            this.setLogger('Searching for oldest unmatched entry...');
            const response = await fetch('/api/entries/oldest', { headers: { 'Content-Type': 'application/json' } });

            if (response.status === 404) {
                this.setLogger('No unmatched entries found in database');
                return;
            }

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            if (!data.id || !data.log) {
                throw new Error('Invalid entry data received from server');
            }

            this.setEntry({ id: data.id, log: data.log, regex: data.regex || '', timestamp: data.timestamp });
            this.setLogger(`Entry ${data.id} pulled successfully (${new Date(data.timestamp).toLocaleString()})`);
            setTimeout(() => this.loadEntryStatistics(), 500);
        } catch (error) {
            console.error('Error pulling entry:', error);
            this.setLogger(`Error pulling entry: ${error.message}`);
        } finally {
            this.dom.pullEntryButton.disabled = false;
            this.dom.pullEntryButton.innerHTML = originalHtml;
        }
    }

    async queryLLM(task) {
        const log = this.dom.logDisplay?.textContent || '';
        const regex = this.dom.regexDisplay?.value || '';

        if (!log) return this.setLogger('No log to analyze');
        if (task === 'fix' && !regex) return this.setLogger('No regex to fix');

        const spinnerMap = { fix: [this.dom.fixSpinner, this.dom.fixButton], generate: [this.dom.generateSpinner, this.dom.generateButton] };
        const [spinner, button] = spinnerMap[task];

        this.toggleSpinner(spinner, button, true);
        this.setLogger(task === 'generate' ? 'AI is generating regex...' : 'AI is fixing regex...');

        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task, regex, log })
            });

            if (!response.ok) throw new Error(`Server returned ${response.status}`);
            const data = await response.json();

            if (!data?.success || !data.regex) {
                const message = data?.error || data?.message || 'Regex update failed';
                this.setLogger(message);
                window.showToast?.(message, 'error');
                return;
            }

            if (this.dom.regexDisplay) this.dom.regexDisplay.value = data.regex;
            this.setLogger(data.logger || 'Regex updated');
            window.showToast?.(task === 'fix' ? 'Regex improved successfully' : 'Regex generated successfully', 'success');
            this.findMatch();
        } catch (error) {
            console.error(`Error during ${task}:`, error);
            this.setLogger(`Error: ${error.message}`);
        } finally {
            this.toggleSpinner(spinner, button, false);
        }
    }

    showAlert(message, type = 'success') {
        const alertEl = document.createElement('div');
        alertEl.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        // Ensure fixed positioning even if Bootstrap CSS isn't loaded.
        alertEl.style.position = 'fixed';
        alertEl.style.top = '20px';
        alertEl.style.right = '20px';
        alertEl.style.zIndex = '9999';
        alertEl.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.body.appendChild(alertEl);

        const bootstrapAlert = window.bootstrap?.Alert;
        if (bootstrapAlert) {
            const bsAlert = new bootstrapAlert(alertEl);
            setTimeout(() => {
                if (alertEl) {
                    bsAlert.close();
                    alertEl.addEventListener('closed.bs.alert', () => alertEl.remove());
                }
            }, 3000);
        } else {
            // Fallback cleanup if Bootstrap JS isn't available.
            setTimeout(() => alertEl.remove(), 3000);
        }
    }

    async saveToDB() {
        if (!this.currentEntry || !this.currentEntry.id) {
            this.setLogger('No entry to save');
            return;
        }

        this.toggleSpinner(this.dom.saveSpinner, this.dom.saveButton, true);

        try {
            const response = await fetch(`/api/smartlp/entries/${this.currentEntry.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    log: this.dom.logDisplay.textContent,
                    regex: this.dom.regexDisplay.value
                })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.message || 'Failed to save');

            // FIXED: Using window.showToast instead of bootstrap showAlert
            if (window.showToast) {
                window.showToast(`Entry ${this.currentEntry.id} saved successfully`, 'success');
            }
            this.setLogger(`Saved: ${this.currentEntry.id}`);

        } catch (error) {
            if (window.showToast) window.showToast(error.message, 'error');
        } finally {
            this.toggleSpinner(this.dom.saveSpinner, this.dom.saveButton, false);
        }
    }

    async findMatch() {
        const log = this.getSessionItem('log') || (this.dom.logDisplay ? this.dom.logDisplay.textContent : '');
        const regex = this.dom.regexDisplay ? this.dom.regexDisplay.value : '';

        if (!regex.trim()) {
            if (this.dom.matchDisplay) {
                this.dom.matchDisplay.innerHTML = '<p class="text-sm text-gray-500 dark:text-gray-400">No regex provided</p>';
            }
            if (this.dom.captureGroupDisplay) {
                this.dom.captureGroupDisplay.innerHTML = '<p class="text-sm text-gray-500 dark:text-gray-400">No capture groups</p>';
            }
            if (this.dom.matchLogger) this.dom.matchLogger.textContent = 'No Regex';
            if (this.dom.logDisplay) this.dom.logDisplay.textContent = log;
            return;
        }

        try {
            const response = await fetch('/api/find_match', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ log, regex })
            });
            const data = await response.json();

            if (this.dom.matchLogger) {
                this.dom.matchLogger.textContent = data.status;
                this.dom.matchLogger.className = data.status?.includes('Unmatched')
                    ? 'text-danger'
                    : data.status?.includes('Partially')
                        ? 'text-warning'
                        : data.status === 'Matched'
                            ? 'text-success'
                            : '';
            }

            const matches = [];
            if (data.full) {
                matches.push(['matched1', data.full]);
                if (Array.isArray(data.groups)) {
                    data.groups.forEach((g, i) => matches.push([g.name || `group${i + 1}`, g]));
                }
            }

            const fullMatchObj = matches.find(([k]) => k === 'matched1')?.[1] || null;
            const groupMatches = matches.filter(([k]) => k !== 'matched1');

            if (this.dom.matchDisplay) {
                this.dom.matchDisplay.innerHTML = fullMatchObj 
                    ? `<div class="text-gray-900 dark:text-white">${this.escapeHtml(fullMatchObj.value)}</div>` 
                    : '<p class="text-sm text-gray-500 dark:text-gray-400">No matches</p>';
            }
            if (this.dom.captureGroupDisplay) {
                const groupText = groupMatches
                    .map(([k, v]) => `${this.escapeHtml(k)}: ${this.escapeHtml(v?.value ?? '')}`)
                    .join('\n');
                
                this.dom.captureGroupDisplay.innerHTML = groupText 
                    ? `<pre class="text-gray-900 dark:text-white whitespace-pre-wrap">${groupText}</pre>`
                    : '<p class="text-sm text-gray-500 dark:text-gray-400">No capture groups</p>';
            }

            this.highlightLog(log, fullMatchObj, groupMatches);
        } catch (err) {
            console.error('findMatch() error:', err);
            if (this.dom.matchLogger) this.dom.matchLogger.textContent = 'Request Error';
        }
    }

    escapeHtml(text) {
        if (text == null) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    highlightLog(logText, fullMatch, groups) {
        if (!this.dom.logDisplay) return;

        const escapeHtml = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        const highlights = [];

        if (fullMatch && typeof fullMatch.start === 'number') {
            highlights.push({ start: fullMatch.start, end: fullMatch.end, color: 'rgba(255,255,0,0.3)' });
        }

        groups.forEach(([_, g]) => {
            if (!g || typeof g.start !== 'number' || typeof g.end !== 'number') return;
            highlights.push({ start: g.start, end: g.end, color: 'rgba(0,0,255,0.2)' });
        });

        highlights.sort((a, b) => a.start - b.start || a.end - b.end);

        const segments = [];
        let pointer = 0;
        while (pointer < logText.length) {
            const overlapping = highlights.filter(h => h.start <= pointer && h.end > pointer);
            let nextBoundary = logText.length;
            if (overlapping.length) {
                nextBoundary = Math.min(...overlapping.map(h => h.end));
            } else {
                const future = highlights.find(h => h.start > pointer);
                if (future) nextBoundary = future.start;
            }

            const segmentText = logText.slice(pointer, nextBoundary);
            segments.push({ text: segmentText, highlights: overlapping.slice() });
            pointer = nextBoundary;
        }

        const finalHtml = segments.map(seg => {
            let text = escapeHtml(seg.text);
            seg.highlights.forEach(h => {
                text = `<mark style="background:${h.color}">${text}</mark>`;
            });
            return text;
        }).join('');

        this.dom.logDisplay.innerHTML = finalHtml;
    }

    async reduceRegex() {
        if (!this.dom.regexDisplay || !this.dom.regexDisplay.value) {
            this.setLogger('No regex to reduce');
            return;
        }

        try {
            const response = await fetch('/api/reduce_regex', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ log: this.dom.logDisplay ? this.dom.logDisplay.textContent : '', regex: this.dom.regexDisplay.value })
            });
            const data = await response.json();
            this.dom.regexDisplay.value = data.regex;
            this.findMatch();
            this.setLogger('Regex reduced successfully');
        } catch (error) {
            console.error('reduceRegex() error:', error);
            this.setLogger('Error reducing regex');
        }
    }

    clearEntry() {
        if (this.dom.logDisplay) this.dom.logDisplay.textContent = '';
        if (this.dom.regexDisplay) this.dom.regexDisplay.value = '';
        if (this.dom.matchDisplay) {
            this.dom.matchDisplay.innerHTML = '<p class="text-sm text-gray-500 dark:text-gray-400">Matches will appear here...</p>';
        }
        if (this.dom.captureGroupDisplay) {
            this.dom.captureGroupDisplay.innerHTML = '<p class="text-sm text-gray-500 dark:text-gray-400">Capture groups will appear here...</p>';
        }
        if (this.dom.matchLogger) this.dom.matchLogger.textContent = '';

        ['id', 'log', 'regex', 'parserEntries', 'parserEntryData'].forEach(key => sessionStorage.removeItem(key));
        this.currentEntry = null;
        this.setLogger('Entry cleared');
    }

    async loadEntryStatistics() {
        const statsElement = document.getElementById('entryStats');
        if (!statsElement) return;

        try {
            const response = await fetch('/api/entries/stats', { headers: { 'Content-Type': 'application/json' } });
            if (!response.ok) throw new Error(`Failed to fetch statistics: ${response.status}`);

            const stats = await response.json();
            const totalEntries = stats.total_entries || 0;
            const unmatchedCount = stats.unmatched_count || 0;
            const matchedCount = stats.status_counts?.Matched || 0;
            const matchRate = totalEntries > 0 ? Math.round((matchedCount / totalEntries) * 100) : 0;

            statsElement.innerHTML = `
                <i class="fa fa-database"></i> ${totalEntries} total entries | 
                <i class="fa fa-exclamation-triangle text-warning"></i> ${unmatchedCount} unmatched | 
                <i class="fa fa-check-circle text-success"></i> ${matchedCount} matched (${matchRate}%)
            `;

            if (this.dom.pullEntryButton) {
                if (unmatchedCount > 0) {
                    this.dom.pullEntryButton.setAttribute('data-bs-title', `Pull oldest unmatched entry (${unmatchedCount} available)`);
                    this.dom.pullEntryButton.disabled = false;
                } else {
                    this.dom.pullEntryButton.setAttribute('data-bs-title', 'No unmatched entries available');
                    this.dom.pullEntryButton.disabled = true;
                }
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
            statsElement.innerHTML = '<i class="fa fa-exclamation-circle text-danger"></i> Unable to load statistics';
        }
    }
}

const playground = new Playground();
window.playground = playground;
export default playground;
