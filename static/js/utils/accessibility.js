/**
 * Accessibility Utility Module
 * Provides ARIA helpers and screen reader support for dynamic UI updates
 */

class AccessibilityManager {
    constructor() {
        this.announceTimeout = null;
    }

    /**
     * Announce a message to screen readers using aria-live region
     * @param {string} message - The message to announce
     * @param {string} priority - 'polite' or 'assertive'
     */
    announce(message, priority = 'polite') {
        // Clear any pending announcement
        if (this.announceTimeout) {
            clearTimeout(this.announceTimeout);
        }

        // Get or create the live region
        let liveRegion = document.getElementById('aria-live-region');

        if (!liveRegion) {
            liveRegion = this._createLiveRegion(priority);
        } else {
            // Update priority if needed
            liveRegion.setAttribute('aria-live', priority);
        }

        // Set the message
        liveRegion.textContent = message;

        // Clear after a delay to allow screen readers to finish
        this.announceTimeout = setTimeout(() => {
            if (liveRegion) {
                liveRegion.textContent = '';
            }
        }, 1000);
    }

    /**
     * Create a live region for screen reader announcements
     * @private
     */
    _createLiveRegion(priority) {
        const liveRegion = document.createElement('div');
        liveRegion.id = 'aria-live-region';
        liveRegion.setAttribute('aria-live', priority);
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'sr-only';
        liveRegion.style.position = 'absolute';
        liveRegion.style.width = '1px';
        liveRegion.style.height = '1px';
        liveRegion.style.padding = '0';
        liveRegion.style.margin = '-1px';
        liveRegion.style.overflow = 'hidden';
        liveRegion.style.clip = 'rect(0, 0, 0, 0)';
        liveRegion.style.whiteSpace = 'nowrap';
        liveRegion.style.border = '0';

        document.body.appendChild(liveRegion);
        return liveRegion;
    }

    /**
     * Setup a region to announce log messages to screen readers
     * @param {HTMLElement} container - The container element
     */
    setupLogRegion(container) {
        if (!container) return;

        container.setAttribute('role', 'log');
        container.setAttribute('aria-live', 'polite');
        container.setAttribute('aria-atomic', 'false');
        container.setAttribute('aria-label', 'Application logs');
    }

    /**
     * Announce a log entry to screen readers
     * @param {Object} entry - Log entry with message, type, timestamp
     */
    announceLog(entry) {
        const typeLabels = {
            info: 'Info',
            success: 'Success',
            warning: 'Warning',
            error: 'Error'
        };

        const typeLabel = typeLabels[entry.type] || 'Message';
        this.announce(`${typeLabel}: ${entry.message}`, 'polite');
    }

    /**
     * Announce toast notification to screen readers
     * @param {string} message - Toast message
     * @param {string} type - Toast type
     */
    announceToast(message, type) {
        const typeLabels = {
            info: 'Information',
            success: 'Success',
            warning: 'Warning',
            error: 'Error'
        };

        const typeLabel = typeLabels[type] || 'Notification';
        this.announce(`${typeLabel}: ${message}`, 'polite');
    }

    /**
     * Announce status change (e.g., button state, progress)
     * @param {string} status - The new status
     */
    announceStatus(status) {
        this.announce(`Status: ${status}`, 'polite');
    }

    /**
     * Announce progress update
     * @param {number} current - Current step/progress
     * @param {number} total - Total steps/progress
     * @param {string} label - Optional label for the progress
     */
    announceProgress(current, total, label = 'Progress') {
        const percentage = Math.round((current / total) * 100);
        this.announce(`${label}: ${current} of ${total} complete, ${percentage}%`, 'polite');
    }

    /**
     * Setup keyboard navigation for a component
     * @param {HTMLElement} container - The container element
     * @param {Object} options - Navigation options
     */
    setupKeyboardNav(container, options = {}) {
        const {
            onEnter = null,
            onEscape = null,
            arrowNavigation = false,
            focusSelector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        } = options;

        container.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && onEnter) {
                onEnter(e);
            }

            if (e.key === 'Escape' && onEscape) {
                onEscape(e);
            }

            if (arrowNavigation) {
                this._handleArrowNavigation(e, container, focusSelector);
            }
        });
    }

    /**
     * Handle arrow key navigation within a container
     * @private
     */
    _handleArrowNavigation(e, container, focusSelector) {
        const focusableElements = container.querySelectorAll(focusSelector);
        const currentIndex = Array.from(focusableElements).indexOf(document.activeElement);

        if (currentIndex === -1) return;

        let nextIndex = currentIndex;

        if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
            nextIndex = (currentIndex + 1) % focusableElements.length;
        } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
            nextIndex = (currentIndex - 1 + focusableElements.length) % focusableElements.length;
        }

        if (nextIndex !== currentIndex) {
            e.preventDefault();
            focusableElements[nextIndex].focus();
        }
    }

    /**
     * Get color-blind friendly status indicator
     * @param {string} status - Status value
     * @returns {Object} - { icon, label, className }
     */
    getStatusIndicator(status) {
        const statusMap = {
            'matched': {
                icon: 'fa-check-circle',
                label: 'Matched',
                className: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
            },
            'unmatched': {
                icon: 'fa-times-circle',
                label: 'Unmatched',
                className: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
            },
            'pending': {
                icon: 'fa-clock',
                label: 'Pending',
                className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
            },
            'partially matched': {
                icon: 'fa-exclamation-circle',
                label: 'Partially Matched',
                className: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
            },
            'deployed': {
                icon: 'fa-cloud-upload-alt',
                label: 'Deployed',
                className: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
            }
        };

        return statusMap[status] || statusMap['pending'];
    }

    /**
     * Create an accessible status badge
     * @param {string} status - Status value
     * @returns {string} - HTML string for the badge
     */
    createStatusBadge(status) {
        const indicator = this.getStatusIndicator(status);
        return `
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${indicator.className}"
                  role="status"
                  aria-label="${indicator.label}">
                <i class="fas ${indicator.icon} mr-1" aria-hidden="true"></i>
                ${indicator.label}
            </span>
        `;
    }
}

// Create singleton instance
const accessibilityManager = new AccessibilityManager();

// Export for ES6 modules
export default accessibilityManager;

// Also attach to window for backward compatibility
if (typeof window !== 'undefined') {
    window.accessibilityManager = accessibilityManager;
    window.announceToScreenReader = (msg, priority) => accessibilityManager.announce(msg, priority);
}
