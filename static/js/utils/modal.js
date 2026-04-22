/**
 * Modal Utility Module
 * Provides reusable confirm modal with focus trap for accessibility
 */

class ModalManager {
    constructor() {
        this.activeModal = null;
        this.previousFocus = null;
    }

    /**
     * Show a confirmation modal
     * @param {Object} options - Modal options
     * @param {string} options.title - Modal title
     * @param {string} options.body - Modal body content (can be HTML)
     * @param {string} options.confirmText - Text for confirm button (default: 'Confirm')
     * @param {string} options.cancelText - Text for cancel button (default: 'Cancel')
     * @param {string} options.confirmClass - CSS classes for confirm button
     * @param {string} options.cancelClass - CSS classes for cancel button
     * @returns {Promise<boolean>} - Resolves to true if confirmed, false if cancelled
     */
    async confirm(options = {}) {
        return new Promise((resolve) => {
            this._createConfirmModal(options, resolve);
        });
    }

    /**
     * Create the confirmation modal
     * @private
     */
    _createConfirmModal(options, callback) {
        const {
            title = 'Confirm Action',
            body = '',
            confirmText = 'Confirm',
            cancelText = 'Cancel',
            confirmClass = 'bg-blue-500 hover:bg-blue-600',
            cancelClass = 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
        } = options;

        // Store currently focused element for focus restoration
        this.previousFocus = document.activeElement;

        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('aria-labelledby', 'modalTitle');

        modal.innerHTML = `
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md max-h-[90vh] flex flex-col overflow-hidden"
                 tabindex="-1" id="confirmModalContent">
                <div class="p-6 border-b border-gray-200 dark:border-gray-700">
                    <h3 id="modalTitle" class="text-lg font-semibold text-gray-900 dark:text-white">${this._escapeHtml(title)}</h3>
                </div>
                <div class="p-6 overflow-y-auto flex-1">
                    <div class="text-sm text-gray-600 dark:text-gray-400">${body}</div>
                </div>
                <div class="flex justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
                    <button id="modalCancelBtn"
                            class="px-4 py-2 rounded-lg text-gray-800 dark:text-gray-100 transition-colors duration-200 ${cancelClass}">
                        ${this._escapeHtml(cancelText)}
                    </button>
                    <button id="modalConfirmBtn"
                            class="px-4 py-2 rounded-lg text-white transition-colors duration-200 ${confirmClass}">
                        ${this._escapeHtml(confirmText)}
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.activeModal = modal;

        // Setup focus trap
        this._setupFocusTrap(modal);

        // Setup button handlers
        const confirmBtn = modal.querySelector('#modalConfirmBtn');
        const cancelBtn = modal.querySelector('#modalCancelBtn');

        const closeModal = (result) => {
            this._closeModal(modal, result);
            callback(result);
        };

        confirmBtn?.addEventListener('click', () => closeModal(true));
        cancelBtn?.addEventListener('click', () => closeModal(false));

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(false);
            }
        });

        // Close on Escape key
        const escapeHandler = (e) => {
            if (e.key === 'Escape' && this.activeModal === modal) {
                document.removeEventListener('keydown', escapeHandler);
                closeModal(false);
            }
        };
        document.addEventListener('keydown', escapeHandler);

        // Focus the confirm button by default
        setTimeout(() => confirmBtn?.focus(), 100);
    }

    /**
     * Setup focus trap within modal
     * @private
     */
    _setupFocusTrap(modal) {
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        if (focusableElements.length === 0) return;

        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];

        modal.addEventListener('keydown', (e) => {
            if (e.key !== 'Tab') return;

            if (e.shiftKey) {
                // Shift + Tab
                if (document.activeElement === firstFocusable) {
                    e.preventDefault();
                    lastFocusable.focus();
                }
            } else {
                // Tab
                if (document.activeElement === lastFocusable) {
                    e.preventDefault();
                    firstFocusable.focus();
                }
            }
        });
    }

    /**
     * Close modal and restore focus
     * @private
     */
    _closeModal(modal, result) {
        if (this.activeModal === modal) {
            this.activeModal = null;
        }

        modal.remove();

        // Restore focus to previously focused element
        if (this.previousFocus && typeof this.previousFocus.focus === 'function') {
            this.previousFocus.focus();
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
const modalManager = new ModalManager();

// Export for ES6 modules
export default modalManager;

// Also attach to window for backward compatibility
if (typeof window !== 'undefined') {
    window.modalManager = modalManager;

    // Helper function for easy usage
    window.showConfirmModal = (options) => modalManager.confirm(options);
}
