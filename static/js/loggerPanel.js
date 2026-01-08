/**
 * Logger Panel Module - ES6
 * Manages the left slide-over logger panel
 */

class LoggerPanel {
    constructor() {
        this.panel = document.getElementById('loggerPanel');
        this.content = document.getElementById('loggerMessages');
        this.autoScroll = true;
        this.messages = [];
        this.socket = null;
        this._socketRetryTimer = null;
        this._socketRetryAttempts = 0;
        this._maxSocketRetryAttempts = 50; // ~10s at 200ms

        this.init();
    }

    init() {
        // Logger toggle button
        document.getElementById('loggerToggle')?.addEventListener('click', () => {
            this.toggle();
        });

        // Close button
        document.getElementById('loggerClose')?.addEventListener('click', () => {
            this.close();
        });

        // Clear logs button
        document.getElementById('clearLogs')?.addEventListener('click', () => {
            this.clear();
        });

        // Pause auto-scroll button
        const pauseBtn = document.getElementById('pauseAutoScroll');
        pauseBtn?.addEventListener('click', () => {
            this.toggleAutoScroll();
        });

        // Detect manual scroll
        const loggerContent = document.getElementById('loggerContent');
        loggerContent?.addEventListener('scroll', () => {
            const isAtBottom = loggerContent.scrollHeight - loggerContent.scrollTop <= loggerContent.clientHeight + 50;
            if (!isAtBottom && this.autoScroll) {
                this.autoScroll = false;
                this.updatePauseButton();
            }
        });

        // Hydrate and subscribe to backend socket logs
        this.hydrateFromSession();
        this.setupSocket();
    }

    scheduleSocketRetry() {
        if (this._socketRetryTimer) return;
        if (this._socketRetryAttempts >= this._maxSocketRetryAttempts) return;

        this._socketRetryTimer = setInterval(() => {
            this._socketRetryAttempts += 1;
            this._socketRetryTimer = null;
            this.setupSocket();
        }, 200);
    }

    setupSocket() {
        if (this.socket) return;

        // Reuse global socket if available; otherwise create a lightweight connection.
        // Note: this file is loaded as an ES module (type="module"), so Socket.IO's `io`
        // is typically available as `window.io` / `globalThis.io`, not as an identifier.
        const g = (typeof globalThis !== 'undefined') ? globalThis : window;
        const existingSocket = g.socket || (g.window && g.window.socket);
        const ioFactory = g.io || (g.window && g.window.io);

        this.socket = existingSocket || (typeof ioFactory === 'function' ? ioFactory() : null);

        if (!this.socket) {
            this.scheduleSocketRetry();
            return;
        }

        if (this._socketRetryTimer) {
            clearInterval(this._socketRetryTimer);
            this._socketRetryTimer = null;
        }

        this.socket.on('log', (data) => {
            const message = data?.message || '';
            const rawTs = data?.ts || data?.timestamp;
            const timestamp = rawTs
                ? new Date(rawTs).toLocaleTimeString()
                : new Date().toLocaleTimeString();

            const level = (data?.level || '').toUpperCase();
            const levelToType = {
                ERROR: 'error',
                WARNING: 'warning',
                INFO: 'info',
                DEBUG: 'info'
            };
            const type = levelToType[level] || this.detectType(message);
            this.log({ message, timestamp, type }, { persist: true });
        });

        this.socket.on('notification', (data) => {
            const message = data?.message || '';
            this.log({
                message,
                timestamp: data?.timestamp
                    ? new Date(data.timestamp).toLocaleTimeString()
                    : new Date().toLocaleTimeString(),
                type: 'info'
            }, { persist: false });
        });
    }

    hydrateFromSession() {
        try {
            const saved = sessionStorage.getItem('loggerPanelMessages');
            if (!saved) return;
            const parsed = JSON.parse(saved);
            if (!Array.isArray(parsed)) return;
            parsed.forEach(entry => this.renderMessage(entry, { skipPersist: true }));
            this.messages = parsed;
            this.scrollToBottom();
        } catch (err) {
            console.warn('Failed to restore logger panel history', err);
        }
    }

    detectType(message) {
        const upper = (message || '').toUpperCase();
        if (upper.includes('ERROR')) return 'error';
        if (upper.includes('WARN')) return 'warning';
        if (upper.includes('SUCCESS')) return 'success';
        return 'info';
    }

    toggle() {
        const isOpen = !this.panel.classList.contains('-translate-x-full');
        if (isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    open() {
        this.panel.classList.remove('-translate-x-full');
        this.panel.classList.add('slide-in-left');
    }

    close() {
        this.panel.classList.add('-translate-x-full');
        this.panel.classList.remove('slide-in-left');
    }

    toggleAutoScroll() {
        this.autoScroll = !this.autoScroll;
        this.updatePauseButton();
        if (this.autoScroll) {
            this.scrollToBottom();
        }
    }

    updatePauseButton() {
        const pauseBtn = document.getElementById('pauseAutoScroll');
        if (pauseBtn) {
            const icon = pauseBtn.querySelector('i');
            if (this.autoScroll) {
                icon.className = 'fas fa-pause mr-2';
                pauseBtn.innerHTML = '<i class="fas fa-pause mr-2"></i>Pause Auto-Scroll';
            } else {
                icon.className = 'fas fa-play mr-2';
                pauseBtn.innerHTML = '<i class="fas fa-play mr-2"></i>Resume Auto-Scroll';
            }
        }
    }

    log(entry, { persist = true } = {}) {
        this.messages.push(entry);
        this.renderMessage(entry);

        if (persist) this.persist();
        if (this.autoScroll) this.scrollToBottom();
    }

    renderMessage(entry, { skipPersist = false } = {}) {
        const messageEl = document.createElement('div');
        messageEl.className = 'flex items-start space-x-2 text-xs';

        const typeIcons = {
            info: '<i class="fas fa-info-circle text-blue-500"></i>',
            success: '<i class="fas fa-check-circle text-green-500"></i>',
            warning: '<i class="fas fa-exclamation-triangle text-yellow-500"></i>',
            error: '<i class="fas fa-times-circle text-red-500"></i>'
        };

        messageEl.innerHTML = `
            <span class="text-gray-500 dark:text-gray-400">[${entry.timestamp}]</span>
            ${typeIcons[entry.type] || typeIcons.info}
            <span class="flex-1">${entry.message}</span>
        `;

        this.content.appendChild(messageEl);
        if (!skipPersist) this.persist();
    }

    clear() {
        this.messages = [];
        this.content.innerHTML = '';
        this.log({
            message: 'Logger cleared',
            timestamp: new Date().toLocaleTimeString(),
            type: 'info'
        });
    }

    persist() {
        try {
            sessionStorage.setItem('loggerPanelMessages', JSON.stringify(this.messages.slice(-200)));
        } catch (err) {
            console.warn('Failed to persist logger panel history', err);
        }
    }

    scrollToBottom() {
        const loggerContent = document.getElementById('loggerContent');
        if (loggerContent) {
            loggerContent.scrollTop = loggerContent.scrollHeight;
        }
    }
}

// Initialize and export
const loggerPanel = new LoggerPanel();

// Make it available globally for backward compatibility
window.loggerPanel = loggerPanel;

export default loggerPanel;
