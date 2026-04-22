/**
 * Toast Notification Utility Module
 * Manages toast notifications with queue limiting (max 3 visible)
 */

const MAX_VISIBLE_TOASTS = 3;
const TOAST_DURATION_MS = 5000;

class ToastManager {
    constructor() {
        this.queue = [];
        this.container = null;
    }

    init() {
        this.container = document.getElementById('toastContainer');
        if (!this.container) {
            console.warn('Toast container not found. Toasts will not be displayed.');
        }
    }

    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - The type: 'info', 'success', 'warning', 'error'
     */
    show(message, type = 'info') {
        const visibleToasts = this.container?.querySelectorAll('#toastContainer > div') || [];

        if (visibleToasts.length >= MAX_VISIBLE_TOASTS) {
            // Queue the toast for later
            this.queue.push({ message, type });
            return;
        }

        this._createToast(message, type);
    }

    /**
     * Create and display a toast element
     * @private
     */
    _createToast(message, type) {
        if (!this.container) return;

        const colors = {
            info: 'bg-blue-500',
            success: 'bg-green-500',
            warning: 'bg-yellow-500',
            error: 'bg-red-500'
        };

        const icons = {
            info: 'fa-info-circle',
            success: 'fa-check-circle',
            warning: 'fa-exclamation-triangle',
            error: 'fa-times-circle'
        };

        const toast = document.createElement('div');
        toast.className = `${colors[type] || colors.info} text-white px-6 py-3 rounded-lg shadow-lg flex items-center space-x-3 animate-slide-in-right`;
        toast.setAttribute('role', 'status');
        toast.setAttribute('aria-live', 'polite');
        toast.innerHTML = `
            <i class="fas ${icons[type] || icons.info}" aria-hidden="true"></i>
            <span>${this._escapeHtml(message)}</span>
            <button onclick="this.parentElement.remove(); window.toastManager?._dequeueNext()"
                    class="ml-4 text-white hover:text-gray-200"
                    aria-label="Dismiss notification">
                <i class="fas fa-times"></i>
            </button>
        `;

        this.container.appendChild(toast);

        // Auto-remove after duration
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
                this._dequeueNext();
            }
        }, TOAST_DURATION_MS);
    }

    /**
     * Dequeue the next toast from the queue
     * @private
     */
    _dequeueNext() {
        if (this.queue.length > 0) {
            const next = this.queue.shift();
            this._createToast(next.message, next.type);
        }
    }

    /**
     * Escape HTML to prevent XSS
     * @private
     */
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Create singleton instance
const toastManager = new ToastManager();

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => toastManager.init());
} else {
    toastManager.init();
}

// Export for ES6 modules
export default toastManager;

// Also attach to window for backward compatibility with inline handlers
if (typeof window !== 'undefined') {
    window.toastManager = toastManager;
}
