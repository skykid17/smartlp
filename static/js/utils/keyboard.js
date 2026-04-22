/**
 * Keyboard Utility Module
 * Reserved for future keyboard shortcuts implementation
 *
 * Planned shortcuts:
 * - Ctrl/Cmd + S: Save (when in Playground)
 * - Ctrl/Cmd + Enter: Generate regex
 * - Escape: Close modals
 * - Ctrl/Cmd + K: Quick search
 * - Ctrl/Cmd + ,: Open settings
 */

class KeyboardManager {
    constructor() {
        this.shortcuts = new Map();
        this.enabled = true;
    }

    /**
     * Register a keyboard shortcut
     * @param {string} key - Key combination (e.g., 'ctrl+s', 'escape')
     * @param {Function} handler - Callback function
     * @param {Object} options - Options
     * @param {string} options.description - Description for help display
     * @param {string} options.scope - Scope where shortcut is active ('global', 'playground', 'dashboard', etc.)
     */
    register(key, handler, options = {}) {
        const normalizedKey = this._normalizeKey(key);
        this.shortcuts.set(normalizedKey, {
            handler,
            description: options.description || '',
            scope: options.scope || 'global'
        });
    }

    /**
     * Unregister a keyboard shortcut
     * @param {string} key - Key combination to remove
     */
    unregister(key) {
        const normalizedKey = this._normalizeKey(key);
        this.shortcuts.delete(normalizedKey);
    }

    /**
     * Enable or disable keyboard shortcuts
     * @param {boolean} enabled - Whether shortcuts should be active
     */
    setEnabled(enabled) {
        this.enabled = enabled;
    }

    /**
     * Get all registered shortcuts for a scope
     * @param {string} scope - Scope to filter by
     * @returns {Array} - Array of shortcut objects
     */
    getShortcutsForScope(scope) {
        const result = [];
        for (const [key, data] of this.shortcuts) {
            if (data.scope === 'global' || data.scope === scope) {
                result.push({ key, ...data });
            }
        }
        return result;
    }

    /**
     * Normalize key combination string
     * @private
     */
    _normalizeKey(key) {
        return key.toLowerCase().trim();
    }

    /**
     * Parse keyboard event into normalized key string
     * @private
     */
    _eventToKey(e) {
        const parts = [];

        if (e.ctrlKey || e.metaKey) {
            parts.push('ctrl');
        }
        if (e.shiftKey) {
            parts.push('shift');
        }
        if (e.altKey) {
            parts.push('alt');
        }

        // Map special keys
        const keyMap = {
            'Escape': 'escape',
            'Enter': 'enter',
            'Tab': 'tab',
            'ArrowUp': 'up',
            'ArrowDown': 'down',
            'ArrowLeft': 'left',
            'ArrowRight': 'right',
            ' ': 'space',
            'Delete': 'delete',
            'Backspace': 'backspace'
        };

        const keyName = keyMap[e.key] || e.key.toLowerCase();
        parts.push(keyName);

        return parts.join('+');
    }

    /**
     * Initialize global keyboard listener
     */
    init() {
        document.addEventListener('keydown', (e) => {
            if (!this.enabled) return;

            // Ignore shortcuts when typing in inputs
            const target = e.target;
            if (target.tagName === 'INPUT' ||
                target.tagName === 'TEXTAREA' ||
                target.isContentEditable) {
                // Allow Escape to work even in inputs
                if (e.key !== 'Escape') return;
            }

            const keyCombo = this._eventToKey(e);
            const shortcut = this.shortcuts.get(keyCombo);

            if (shortcut) {
                // Check scope
                const currentScope = document.querySelector('[data-keyboard-scope]')?.dataset.keyboardScope || 'global';

                if (shortcut.scope === 'global' || shortcut.scope === currentScope) {
                    e.preventDefault();
                    shortcut.handler(e);
                }
            }
        });

        // Register Escape handler for closing modals
        this.register('escape', () => {
            // Close any open modals
            const openModal = document.querySelector('.fixed.inset-0:not(.hidden)');
            if (openModal) {
                const closeBtn = openModal.querySelector('button[id$="Close"]');
                closeBtn?.click();
            }
        }, {
            description: 'Close modal',
            scope: 'global'
        });
    }

    /**
     * Show keyboard shortcuts help
     * @returns {string} - HTML string listing shortcuts
     */
    getHelpHTML(scope = 'global') {
        const shortcuts = this.getShortcutsForScope(scope);

        if (shortcuts.length === 0) {
            return '<p class="text-sm text-gray-500">No shortcuts available</p>';
        }

        return `
            <div class="space-y-2">
                ${shortcuts.map(s => `
                    <div class="flex items-center justify-between text-sm">
                        <span class="text-gray-600 dark:text-gray-400">${s.description}</span>
                        <kbd class="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs font-mono">
                            ${this._formatKey(s.key)}
                        </kbd>
                    </div>
                `).join('')}
            </div>
        `;
    }

    /**
     * Format key combination for display
     * @private
     */
    _formatKey(key) {
        return key
            .split('+')
            .map(k => k.charAt(0).toUpperCase() + k.slice(1))
            .join(' + ');
    }
}

// Create singleton instance
const keyboardManager = new KeyboardManager();

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => keyboardManager.init());
} else {
    keyboardManager.init();
}

// Export for ES6 modules
export default keyboardManager;

// Also attach to window for backward compatibility
if (typeof window !== 'undefined') {
    window.keyboardManager = keyboardManager;
    window.registerKeyboardShortcut = (key, handler, options) => keyboardManager.register(key, handler, options);
}
