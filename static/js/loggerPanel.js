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

    setupSocket() {
        if (this.socket) return;
        // Reuse global socket if available; otherwise create a lightweight connection
        this.socket = window.socket || (typeof io !== 'undefined' ? io() : null);
        if (!this.socket) return;

        this.socket.on('log', (data) => {
            const message = data?.message || '';
            const type = this.detectType(message);
            this.log(message, type, { persist: true });
        });

        this.socket.on('notification', (data) => {
            const message = data?.message || '';
            this.log(message, 'info', { persist: false });
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

    log(message, type = 'info', { persist = true } = {}) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = { timestamp, message, type };

        this.messages.push(logEntry);
        this.renderMessage(logEntry);

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

        const cleanedMessage = this.stripLeadingTimestamp(entry.message);

        messageEl.innerHTML = `
            <span class="text-gray-500 dark:text-gray-400">[${entry.timestamp}]</span>
            ${typeIcons[entry.type] || typeIcons.info}
            <span class="flex-1">${cleanedMessage}</span>
        `;

        this.content.appendChild(messageEl);
        if (!skipPersist) this.persist();
    }

    stripLeadingTimestamp(message = '') {
        if (typeof message !== 'string') return '';
        const patterns = [
            /^\d{1,2}\s[A-Za-z]{3}\s\d{2}:\d{2}:\d{2}:\s*/,
            /^\[?\d{2}:\d{2}:\d{2}]?\s*/
        ];

        for (const pattern of patterns) {
            if (pattern.test(message)) {
                return message.replace(pattern, '').trimStart();
            }
        }

        return message;
    }

    clear() {
        this.messages = [];
        this.content.innerHTML = '';
        this.log('Logger cleared', 'info');
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
