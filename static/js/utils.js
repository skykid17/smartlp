// Global variables and utility functions
let logger;
let entryModal;
let errorModal;

const socket = io(); // Connect to the WebSocket server

document.addEventListener("DOMContentLoaded", () => {
    logger = document.getElementById("logger");
    entryModal = document.getElementById("entryModal");
    errorModal = document.getElementById("errorModal");
    toastLive = document.getElementById('liveToast');
    const smartlpLogger = document.getElementById('smartlpLogger');
    const toast = new bootstrap.Toast(toastLive, { delay: 30000 });
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

    document.addEventListener('click', function (event) {
        const target = event.target.closest('.copy-btn');
        if (!target) return;

        const codeElement = target.parentElement.querySelector('code');
        if (!codeElement) return;

        const text = codeElement.innerText;

        // Check if the Clipboard API is available
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(() => {
                showCopied(target);
            }).catch(() => {
                copyTextToClipboard(text, target);
            });
        } else {
            // Use fallback
            copyTextToClipboard(text, target);
        }
    });

    socket.on('notification', (data) => {
        const notification = document.getElementById('ingestNotification');
        const timestamp = document.querySelector('.toast-timestamp');

        notification.textContent = data.message;
        if (timestamp) timestamp.textContent = new Date().toLocaleTimeString();

        toast.show();
    });
    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
    }); const savedLogs = sessionStorage.getItem('smartlpLogs');
    if (savedLogs) {
        logger.innerHTML = savedLogs;
    }    // Global modal backdrop cleanup to prevent multiple backdrop layers
    document.addEventListener('hidden.bs.modal', function (event) {
        // Small delay to ensure Bootstrap has finished cleanup
        setTimeout(() => {
            cleanupModalBackdrops();
        }, 50);
    });

    // Emergency cleanup handler - Ctrl+Shift+Escape to force cleanup all modals
    document.addEventListener('keydown', function (event) {
        if (event.ctrlKey && event.shiftKey && event.key === 'Escape') {
            console.log('Emergency modal cleanup triggered');
            forceCleanupAllModals();
            event.preventDefault();
        }
    });
});

socket.on('log', (data) => {
    const logEntry = document.createElement('div');
    logEntry.textContent = data.message;

    // Add styling based on log type
    if (data.message.includes('[INGESTION]')) {
        logEntry.className = 'text-primary fw-bold';
        logEntry.style.borderLeft = '3px solid #0d6efd';
        logEntry.style.paddingLeft = '8px';
        logEntry.style.marginBottom = '2px';
    } else if (data.message.includes('ERROR:')) {
        logEntry.className = 'text-danger';
        logEntry.style.borderLeft = '3px solid #dc3545';
        logEntry.style.paddingLeft = '8px';
        logEntry.style.marginBottom = '2px';
    } else if (data.message.includes('WARNING:')) {
        logEntry.className = 'text-warning';
        logEntry.style.borderLeft = '3px solid #ffc107';
        logEntry.style.paddingLeft = '8px';
        logEntry.style.marginBottom = '2px';
    } else {
        logEntry.style.marginBottom = '2px';
    }

    // Prepend new log
    logger.prepend(logEntry);

    // Limit the number of log entries displayed (keep last 100)
    while (logger.children.length > 100) {
        logger.removeChild(logger.lastChild);
    }

    // Save current logs to sessionStorage
    sessionStorage.setItem('smartlpLogs', logger.innerHTML);

    // Ensure vertical scroll
    logger.style.overflowY = 'auto';
});


function copyTextToClipboard(text, target) {
    // Create a temporary element
    const tempElement = document.createElement('div');

    // Position it absolutely to make it invisible but functional
    tempElement.style.position = 'absolute';
    tempElement.style.left = '-9999px';
    tempElement.style.top = '0';

    // Set the text content directly in the div for selection
    tempElement.textContent = text;
    document.body.appendChild(tempElement);

    // Create selection
    const range = document.createRange();
    range.selectNode(tempElement);

    // Clear any existing selections
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);

    let successful = false;
    try {
        successful = document.execCommand('copy');
        if (successful) {
            showCopied(target);
        } else {
            target.innerHTML = 'Copy failed';
        }
    } catch (err) {
        console.error('Copy failed:', err);
        target.innerHTML = 'Error copying';
    }

    // Clean up
    selection.removeAllRanges();
    document.body.removeChild(tempElement);

    return successful;
}

function showCopied(target) {
    const originalContent = target.innerHTML;
    target.innerHTML = 'Copied!';
    target.disabled = true;

    setTimeout(() => {
        target.innerHTML = originalContent;
        target.disabled = false;
    }, 2000);
}

// Add an event listener if the element exists
function addEventIfExists(element, event, handler) {
    if (element) element.addEventListener(event, handler);
}

// Fetch data from an API endpoint and handle the response
async function fetchAndHandle(url, options, onSuccess, errorMessage) {
    try {
        const response = await fetch(url, options);
        const data = await response.json();
        onSuccess(data);
    } catch (error) {
        console.error(errorMessage, error);
    }
}

// Display an error modal with the specified message
function showErrorModal(message) {
    // Clean up any existing backdrops before showing new modal
    cleanupModalBackdrops();

    document.getElementById("errorMessage").innerHTML = message;
    const errorModalInstance = new bootstrap.Modal(errorModal, {
        backdrop: true,
        keyboard: true
    });

    // Add event listener to clean up backdrop when modal is hidden
    errorModal.addEventListener('hidden.bs.modal', function () {
        cleanupModalBackdrops();
    }, { once: true }); // Use once to prevent multiple listeners

    errorModalInstance.show();
}

// Clean up any lingering modal backdrops
function cleanupModalBackdrops() {
    // Remove all modal backdrops
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
        backdrop.remove();
    });

    // Remove modal-open class from body if no modals are visible
    const visibleModals = document.querySelectorAll('.modal.show');
    if (visibleModals.length === 0) {
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }
}

// Force cleanup of all modal states - use this as a last resort
function forceCleanupAllModals() {
    // Hide all visible modals
    document.querySelectorAll('.modal.show').forEach(modal => {
        const modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
            modalInstance.hide();
        }
    });

    // Remove all modal backdrops
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
        backdrop.remove();
    });

    // Reset body state
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';

    // Remove any lingering modal classes
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.remove('show');
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
        modal.removeAttribute('aria-modal');
        modal.removeAttribute('role');
    });
}

// Get stored session data for a key, with optional default value
function getSessionItem(key, defaultValue = "") {
    return sessionStorage.getItem(key) || defaultValue;
}

// Store a value in session storage
function setSessionItem(key, value) {
    sessionStorage.setItem(key, value);
}

// --- Reusable Selection Module ---
// Usage: const selection = createSelectionModule({
//   tableBodyId: 'entryTableBody',
//   selectEnableSelector: '.selectEnable',
//   loggerId: 'logger',
//   configPanelSync: optionalSyncFunction
// });
//
// selection.ids, selection.visibleIds, selection.clearSelection(), etc.

function createSelectionModule({
    tableBodyId,
    selectEnableSelector,
    loggerId,
    configPanelSync,
    storagePrefix = 'selection', // Allow custom prefix for storage key
    idLabel = 'entries', // Allow custom label for logging (e.g., 'entries' or 'rules')
    checkboxSelector = 'input[type="checkbox"]' // Allow custom checkbox selector
}) {
    // Create unique session storage key based on prefix and table ID to avoid conflicts between modules
    const storageKey = `${storagePrefix}_${tableBodyId}`;
    let visibleIds = new Set();
    let selectEnableButtons = [];
    let logger = loggerId ? document.getElementById(loggerId) : null;

    // Helper functions for session storage management
    function getIds() {
        try {
            const stored = sessionStorage.getItem(storageKey);
            return stored ? JSON.parse(stored) : [];
        } catch (error) {
            console.warn(`Error reading selection from session storage:`, error);
            return [];
        }
    }
    function setIds(newIds) {
        try {
            sessionStorage.setItem(storageKey, JSON.stringify(newIds));
        } catch (error) {
            console.warn(`Error saving selection to session storage:`, error);
        }
    }
    function clearSelection() {
        // Clear all checkboxes and selected states before clearing the storage
        const tableBody = document.getElementById(tableBodyId);
        if (tableBody) {
            tableBody.querySelectorAll('tr.selected').forEach(row => {
                row.classList.remove('selected');
                const checkbox = row.querySelector(checkboxSelector);
                if (checkbox) checkbox.checked = false;
            });
        }
        setIds([]);
        updateSelectionUI();
    }
    function updateSelectionUI() {
        const ids = getIds();
        const hiddenIdCnt = ids.length - ids.filter(id => visibleIds.has(id)).length;
        const message = ids.length === 0
            ? `No ${idLabel} selected`
            : hiddenIdCnt > 0
                ? `Selected ${ids.length} ${idLabel} (${hiddenIdCnt} filtered out)`
                : `Selected ${ids.length} ${idLabel}`;

        if (logger) {
            if (logger.textContent === '' || logger.textContent.includes("elected")) {
                logger.textContent = message;
            } else {
                setTimeout(() => {
                    logger.textContent = message;
                }, 3000);
            }
        }
        if (!selectEnableButtons.length && selectEnableSelector) {
            selectEnableButtons = Array.from(document.querySelectorAll(selectEnableSelector));
        }
        selectEnableButtons.forEach(btn => {
            if (btn.id === 'openConfigPanel') {
                btn.toggleAttribute("disabled", false);
            } else {
                btn.toggleAttribute("disabled", ids.length === 0);
            }
        });
        const tableBody = document.getElementById(tableBodyId);
        if (tableBody) {
            // Update selected rows to match the stored IDs
            tableBody.querySelectorAll('tr.selected').forEach(row => {
                const checkbox = row.querySelector(checkboxSelector);
                const id = checkbox ? checkbox.value : row.querySelector('td:first-child')?.textContent;
                if (!ids.includes(id)) {
                    row.classList.remove('selected');
                    if (checkbox) checkbox.checked = false;
                }
            });
            // Update unselected rows that should be selected
            tableBody.querySelectorAll('tr:not(.selected)').forEach(row => {
                const checkbox = row.querySelector(checkboxSelector);
                const id = checkbox ? checkbox.value : row.querySelector('td:first-child')?.textContent;
                if (ids.includes(id)) {
                    row.classList.add('selected');
                    if (checkbox) checkbox.checked = true;
                }
            });
        }
        if (updateSelectionUI.syncTimeout) clearTimeout(updateSelectionUI.syncTimeout);
        updateSelectionUI.syncTimeout = setTimeout(() => {
            if (typeof configPanelSync === 'function') configPanelSync();
        }, 100);
    }
    function toggleRowSelection(row, entryId) {
        const ids = getIds();
        let newIds;
        const checkbox = row.querySelector(checkboxSelector);

        if (row.classList.contains('selected')) {
            // Row is currently selected, so remove the ID
            newIds = ids.filter(id => id !== entryId);
            row.classList.remove('selected');
            if (checkbox) checkbox.checked = false;
        } else {
            // Row is not selected, so add the ID if not already present
            newIds = ids.includes(entryId) ? ids : [...ids, entryId];
            row.classList.add('selected');
            if (checkbox) checkbox.checked = true;
        }
        setIds(newIds);
        updateSelectionUI();
    }
    function updateMainTableSelection() {
        const ids = getIds();
        const mainTableRows = document.querySelectorAll(`#${tableBodyId} tr`);
        mainTableRows.forEach(row => {
            const checkbox = row.querySelector(checkboxSelector);
            if (checkbox) {
                const entryId = checkbox.value;
                const shouldBeSelected = ids.includes(entryId);
                if (shouldBeSelected) {
                    row.classList.add('selected');
                    checkbox.checked = true;
                } else {
                    row.classList.remove('selected');
                    checkbox.checked = false;
                }
            }
        });
    }

    // Add method to remove specific IDs (for config panel remove buttons)
    function removeIds(idsToRemove) {
        const ids = getIds();
        const newIds = ids.filter(id => !idsToRemove.includes(id));
        setIds(newIds);
        updateSelectionUI();
    }

    // Add method to add specific IDs (for programmatic selection)
    function addIds(idsToAdd) {
        const ids = getIds();
        const newIds = [...new Set([...ids, ...idsToAdd])]; // Use Set to avoid duplicates
        setIds(newIds);
        updateSelectionUI();
    }

    function updateTableData(entries, options = {}) {
        const tableBody = document.getElementById(tableBodyId);
        if (!tableBody) return;

        tableBody.innerHTML = '';  // Clear existing rows
        visibleIds.clear();

        const {
            emptyStateColSpan = 6,
            emptyStateHtml = `
                <div class="py-4">
                    <i class="fa fa-search fa-2x mb-2 d-block"></i>
                    <h6>No entries found</h6>
                    <small>Try adjusting your search criteria or filters</small>
                </div>
            `,
            rowRenderer = null,
            afterUpdate = null
        } = options;

        if (entries.length === 0) {
            // Show empty state
            const row = tableBody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = emptyStateColSpan;
            cell.className = 'text-center py-4 text-muted';
            cell.innerHTML = emptyStateHtml;

            if (typeof afterUpdate === 'function') {
                afterUpdate(entries);
            }
            return;
        }

        entries.forEach(entry => {
            visibleIds.add(entry.id);
            const row = tableBody.insertRow();

            // Use custom renderer if provided, otherwise expect consumer to handle rendering
            if (typeof rowRenderer === 'function') {
                rowRenderer(row, entry);
            }

            // Check if this entry is globally selected
            const ids = getIds();
            if (ids.includes(entry.id)) {
                row.classList.add('selected');
                const checkbox = row.querySelector(checkboxSelector);
                if (checkbox) {
                    checkbox.checked = true;
                }
            }
        });

        if (typeof afterUpdate === 'function') {
            afterUpdate(entries);
        }

        // Update selection UI to reflect current visible vs selected state
        updateSelectionUI();
    }

    return {
        get ids() { return getIds(); },
        set ids(newIds) { setIds(newIds); },
        visibleIds,
        clearSelection,
        toggleRowSelection,
        updateMainTableSelection,
        updateSelectionUI,
        removeIds,
        addIds,
        updateTableData,
        storageKey // Expose storage key for debugging
    };
}

// --- Reusable Click-to-Select Setup ---
/**
 * Setup click-to-select functionality for table rows
 * @param {Object} selection - The selection module instance
 * @param {Object} options - Configuration options
 * @param {string} options.tableBodyId - ID of the table body element
 * @param {string} options.rowSelector - CSS selector for table rows (default: 'tr')
 * @param {string} options.checkboxSelector - CSS selector for checkboxes (default: 'input[type="checkbox"]')
 * @param {Function} options.onRowClick - Optional custom row click handler
 */
function setupClickToSelect(selection, options = {}) {
    const {
        tableBodyId = 'entryTableBody',
        rowSelector = 'tr',
        checkboxSelector = 'input[type="checkbox"]',
        onRowClick = null
    } = options;

    const tableBody = document.getElementById(tableBodyId);
    if (!tableBody) {
        console.warn(`Table body with ID '${tableBodyId}' not found`);
        return;
    }

    // Use event delegation to handle clicks on dynamically added rows
    tableBody.addEventListener('click', function (event) {
        const row = event.target.closest(rowSelector);
        if (!row) return;

        const checkbox = row.querySelector(checkboxSelector);
        if (!checkbox) return;

        // If checkbox was clicked directly, let it handle its own event
        if (event.target.matches(checkboxSelector)) {
            return;
        }

        // If click was on a button or other interactive element, ignore
        if (event.target.closest('button, a, .btn')) {
            return;
        }

        // Toggle checkbox and selection
        event.preventDefault();
        checkbox.checked = !checkbox.checked;

        // Trigger the selection toggle
        selection.toggleRowSelection(row, checkbox.value);

        // Call custom row click handler if provided
        if (typeof onRowClick === 'function') {
            onRowClick(row, checkbox.value, event);
        }
    });

    // Also setup checkbox change events
    tableBody.addEventListener('change', function (event) {
        if (event.target.matches(checkboxSelector)) {
            const row = event.target.closest(rowSelector);
            if (row) {
                selection.toggleRowSelection(row, event.target.value);
            }
        }
    });
}

// --- Reusable Config Panel Module ---
// Usage: const configPanel = createConfigPanelModule({
//   selection, // the selection module instance
//   configTableBodyId: 'configTableBody',
//   popupBoxId: 'popupBox',
//   selectionCountId: 'configSelectionCount',
//   previewId: 'configPreview',
//   openPanelBtnId: 'openConfigPanel',
//   validateAndConfigId: 'validateAndConfig',
//   loggerId: 'logger',
//   fetchConfigData: async (ids) => { ... },
//   validateConfig: async (rows) => { ... },
//   onPanelOpen: optional callback,
//   onPanelClose: optional callback
// });

function createConfigPanelModule({
    selection,
    configTableBodyId,
    popupBoxId,
    selectionCountId,
    previewId,
    openPanelBtnId,
    validateAndConfigId,
    loggerId,
    fetchConfigData, // async (ids) => [...]
    validateConfig,  // async (rows) => { valid, errors }
    onPanelOpen,
    onPanelClose,
    customRenderConfigTable // optional: custom rendering for config table
}) {
    const configTableBody = document.getElementById(configTableBodyId);
    const popup = document.getElementById(popupBoxId);
    const selectionCount = selectionCountId ? document.getElementById(selectionCountId) : null;
    const preview = previewId ? document.getElementById(previewId) : null;
    const logger = loggerId ? document.getElementById(loggerId) : null;
    const openPanelBtn = openPanelBtnId ? document.getElementById(openPanelBtnId) : null;
    const validateBtn = validateAndConfigId ? document.getElementById(validateAndConfigId) : null;

    // --- Open/Toggle Panel ---
    function togglePanel() {
        if (!popup) return;
        popup.classList.toggle("collapsed");
        if (!popup.classList.contains("collapsed")) {
            syncPanel();
            if (typeof onPanelOpen === 'function') onPanelOpen();
        } else {
            if (typeof onPanelClose === 'function') onPanelClose();
        }
    }
    if (openPanelBtn) {
        openPanelBtn.onclick = togglePanel;
    }

    // --- Sync Panel with Selection ---
    async function syncPanel() {
        if (!popup || !configTableBody) {
            return;
        }
        if (popup.classList.contains("collapsed")) return;
        if (syncPanel.isRunning) return;
        syncPanel.isRunning = true;
        try {
            const ids = selection.ids;
            if (!ids || ids.length === 0) {
                configTableBody.innerHTML = `<tr><td colspan="10" class="text-center">No entries selected</td></tr>`;
                if (selectionCount) selectionCount.textContent = '0';
                return;
            }
            if (selectionCount) selectionCount.textContent = ids.length;
            // Fetch config data for selected ids
            let configRows = [];
            if (typeof fetchConfigData === 'function') {
                try {
                    configRows = await fetchConfigData(ids);
                } catch (error) {
                    console.error('Config panel: Error fetching config data:', error);
                    configRows = [];
                }
            } else {
                // Default: just show IDs
                configRows = ids.map(id => ({ id }));
            }            // Custom render if provided
            if (typeof customRenderConfigTable === 'function') {
                // Pass the panel API methods to the custom render function
                customRenderConfigTable.call({
                    syncPanel,
                    removeFromConfig,
                    selection
                }, configRows, configTableBody);
            } else {
                // Default: just show IDs
                configTableBody.innerHTML = '';
                configRows.forEach(row => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td>${row.id}</td>` +
                        (row.timestamp !== undefined ? `<td>${new Date(row.timestamp).toLocaleString()}</td>` : '') +

                        (row.index !== undefined ? `<td>${row.index}</td>` : '') +
                        (row.source_type !== undefined ? `<td>${row.source_type}</td>` : '') +
                        (row.log !== undefined ? `<td>${row.log}</td>` : '') +
                        `<td><button class="btn btn-sm btn-outline-danger remove-config-btn" data-entry-id="${row.id}" title="Remove from config"><i class="fa fa-times"></i></button></td>`;
                    configTableBody.appendChild(tr);
                });
                // Attach remove handlers
                configTableBody.querySelectorAll('.remove-config-btn').forEach(btn => {
                    btn.addEventListener('click', function () {
                        removeFromConfig(this.dataset.entryId);
                    });
                });
            }
        } catch (error) {
            console.error('Config panel: Unexpected error:', error);
            if (configTableBody) {
                configTableBody.innerHTML = `<tr><td colspan="10" class="text-center text-danger">Error loading configuration data</td></tr>`;
            }
        } finally {
            syncPanel.isRunning = false;
        }
    }    // --- Remove Entry from Config Panel and Selection ---
    function removeFromConfig(entryId) {
        // Use the new session storage-based removeIds method
        selection.removeIds([entryId]);
        selection.updateMainTableSelection();
        // updateSelectionUI is already called by removeIds
        syncPanel();
    }

    // --- Set Config Preview (with line numbers) ---
    function setConfigPreviewWithLineNumbers(text) {
        if (!preview) return;
        const esc = (str) => str.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', '\'': '&#39;' }[c]));
        preview.innerHTML = text.split('\n').map(line => `<span>${esc(line)}</span>`).join('\n');
    }

    // --- Validate and Config (example: can be customized) ---
    async function validateAndConfig() {
        if (!configTableBody) return;
        const rows = configTableBody.querySelectorAll('tr');
        if (rows.length === 0) {
            if (logger) {
                logger.textContent = 'No entries to configure.';
                logger.className = 'alert alert-danger fs-6';
            }
            return;
        }
        // Custom validation logic
        let valid = true;
        let errors = [];
        if (typeof validateConfig === 'function') {
            const result = await validateConfig(rows);
            valid = result.valid;
            errors = result.errors;
        }
        if (!valid) {
            if (logger) {
                logger.textContent = errors.join(', ');
                logger.className = 'alert alert-danger fs-6';
            }
            return;
        }
        setTimeout(() => {
            if (logger) logger.textContent = '';
        }, 2000);
    }
    if (validateBtn) {
        validateBtn.onclick = validateAndConfig;
    }

    // --- Expose API ---
    return {
        togglePanel,
        syncPanel,
        removeFromConfig,
        setConfigPreviewWithLineNumbers,
        validateAndConfig
    };
}

// ========================================
// Shared API Utility Functions
// ========================================

/**
 * Generic API request function with error handling
 * @param {string} url - The API endpoint URL
 * @param {Object} options - Fetch options (method, body, headers, etc.)
 * @returns {Promise<any>} - The parsed JSON response
 */
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API request error for ${url}:`, error);
        throw error;
    }
}

/**
 * Fetch entries from the SmartLP API
 * @param {Object} params - Query parameters for the entries endpoint
 * @returns {Promise<Object>} - The entries data
 */
async function fetchEntries(params = {}) {
    const searchParams = new URLSearchParams(params);
    return await apiRequest(`/api/entries?${searchParams}`, { method: 'GET' });
}

/**
 * Update an entry via the SmartLP API
 * @param {string} entryId - The ID of the entry to update
 * @param {Object} data - The data to update
 * @returns {Promise<Object>} - The updated entry data
 */
async function updateEntry(entryId, data) {
    return await apiRequest(`/api/entries/${entryId}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

/**
 * Delete an entry via the SmartLP API
 * @param {string} entryId - The ID of the entry to delete
 * @returns {Promise<Object>} - The deletion response
 */
async function deleteEntry(entryId) {
    return await apiRequest(`/api/entries/${entryId}`, { method: 'DELETE' });
}

/**
 * Check if entries are deployable
 * @param {Array<string>} ids - Array of entry IDs to check
 * @returns {Promise<Object>} - The deployable status data
 */
async function checkDeployableStatus(ids) {
    return await apiRequest('/api/check_deployable', {
        method: 'POST',
        body: JSON.stringify({ ids })
    });
}

/**
 * Generate SmartLP configuration
 * @param {Array<string>} ids - Array of entry IDs for config generation
 * @returns {Promise<Object>} - The generated configuration
 */
async function generateSmartLPConfig(ids) {
    return await apiRequest('/api/smartlp/generate_config', {
        method: 'POST',
        body: JSON.stringify({ ids })
    });
}

/**
 * Generate SmartUC configuration
 * @param {Array<string>} ids - Array of entry IDs for config generation
 * @param {string} siem - The target SIEM platform
 * @returns {Promise<Object>} - The generated configuration
 */
async function generateSmartUCConfig(ids, siem) {
    return await apiRequest('/api/smartuc/generate_config', {
        method: 'POST',
        body: JSON.stringify({ ids, siem })
    });
}

/**
 * Fetch SmartUC config data for display in tables
 * @param {string} siem - The target SIEM platform
 * @param {Array<string>} ids - Array of entry IDs
 * @returns {Promise<Array>} - The config data array
 */
async function fetchSmartUCConfigData(siem, ids) {
    const response = await fetch(`/api/rule/configs?ids=${ids.join(',')}`);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }
    const result = await response.json();
    // Extract the data array from the response
    return result.data || [];
}

/**
 * Update a SmartUC config field
 * @param {string} entryId - The entry ID
 * @param {string} field - The field name to update
 * @param {string} value - The new value
 * @param {string} siem - The target SIEM platform (not used in current implementation)
 * @returns {Promise<void>}
 */
async function updateSmartUCConfigField(entryId, field, value, siem) {
    // Flask expects an array of [field, value] pairs
    const changes = [[field, value]];

    const response = await fetch(`/api/rule/${entryId}/config`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(changes)
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    } else {
        if (typeof smartucConfigPanel !== 'undefined' && smartucConfigPanel.syncPanel) {
            smartucConfigPanel.syncPanel();
        }
    }
}

/**
 * Deploy entries to Ansible
 * @param {Array<string>} ids - Array of entry IDs to deploy
 * @param {string} type - The deployment type (e.g., 'smartlp', 'smartuc')
 * @returns {Promise<Object>} - The deployment response
 */
async function deployToAnsible(ids, type) {
    return await apiRequest('/api/deploy', {
        method: 'POST',
        body: JSON.stringify({ ids, type })
    });
}

/**
 * Deploy entries to Ansible with UI feedback
 * @param {Array<string>} ids - Array of entry IDs to deploy
 * @param {string} type - The deployment type (e.g., 'smartlp', 'smartuc')
 * @param {Object} options - UI configuration options
 * @param {string} options.deployBtnSelector - CSS selector for deploy button
 * @param {string} options.feedbackDivId - ID of feedback container element
 * @param {string} options.messageDivId - ID of message element
 * @param {string} options.configModalId - ID of config modal to close on success
 * @param {Function} options.onSuccess - Optional callback on successful deployment
 * @param {Function} options.onError - Optional callback on deployment error
 * @returns {Promise<void>}
 */
async function deployWithFeedback(ids, type, options = {}) {
    const {
        deployBtnSelector = '#configModal button[onclick="deploy()"]',
        feedbackDivId = 'deploymentFeedback',
        messageDivId = 'deploymentMessage',
        configModalId = 'configModal',
        onSuccess = null,
        onError = null
    } = options;

    const deployBtn = document.querySelector(deployBtnSelector);
    const feedbackDiv = document.getElementById(feedbackDivId);
    const messageDiv = document.getElementById(messageDivId);

    if (!deployBtn || !feedbackDiv || !messageDiv) {
        console.error('Deploy UI elements not found');
        return;
    }

    // Check if there are entries to deploy
    if (!ids || ids.length === 0) {
        showDeploymentFeedback('No entries selected for deployment.', 'danger', feedbackDiv, messageDiv);
        return;
    }

    // Disable deploy button and show loading state
    const originalBtnContent = deployBtn.innerHTML;
    deployBtn.disabled = true;
    deployBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Deploying...';

    // Hide previous feedback
    feedbackDiv.style.display = 'none';

    try {
        // Use the shared deployment API function
        const result = await deployToAnsible(ids, type);

        // Success - show success message from backend
        showDeploymentFeedback(result.logger || 'Deployment successful!', 'success', feedbackDiv, messageDiv);

        // Call custom success callback if provided
        if (typeof onSuccess === 'function') {
            onSuccess(result);
        }

        // Default success behavior: close modal and refresh data
        setTimeout(() => {
            const modal = bootstrap.Modal.getInstance(document.getElementById(configModalId));
            if (modal) modal.hide();

            // Try to refresh data if searchData function exists
            if (typeof window.searchData === 'function') {
                window.searchData();
            }
        }, 2000);

    } catch (error) {
        console.error('Deploy error:', error);

        // Try to extract error message from API response
        let errorMessage = 'Deployment failed: Network error or server unavailable.';
        if (error.message && error.message.includes('HTTP')) {
            try {
                // Extract the JSON error message if available
                const jsonMatch = error.message.match(/\{.*\}/);
                if (jsonMatch) {
                    const errorData = JSON.parse(jsonMatch[0]);
                    errorMessage = errorData.logger || errorMessage;
                }
            } catch (parseError) {
                // Use default message if parsing fails
            }
        }

        showDeploymentFeedback(errorMessage, 'danger', feedbackDiv, messageDiv);

        // Call custom error callback if provided
        if (typeof onError === 'function') {
            onError(error, errorMessage);
        }

    } finally {
        // Re-enable deploy button
        deployBtn.disabled = false;
        deployBtn.innerHTML = originalBtnContent;
    }
}

/**
 * Helper function to show deployment feedback
 * @param {string} message - The message to display
 * @param {string} type - The alert type ('success', 'danger', etc.)
 * @param {HTMLElement} feedbackDiv - The feedback container element
 * @param {HTMLElement} messageDiv - The message element
 */
function showDeploymentFeedback(message, type, feedbackDiv, messageDiv) {
    if (!feedbackDiv || !messageDiv) return;

    // Set message and alert class
    messageDiv.textContent = message;
    messageDiv.className = `alert mb-0 alert-${type}`;

    // Show feedback
    feedbackDiv.style.display = 'block';

    // Auto-hide success messages after 3 seconds
    if (type === 'success') {
        setTimeout(() => {
            feedbackDiv.style.display = 'none';
        }, 3000);
    }
}

// ========================================
// Shared Modal Utility Functions
// ========================================

/**
 * Show configuration in a Bootstrap modal
 * @param {string} config - The configuration content to displayW
 * @param {string} modalId - The ID of the modal element (default: 'configModal')
 * @param {string} previewId - The ID of the preview element (default: 'configPreview')
 */
function showConfigModal(config, modalId = 'configModal', previewId = 'configPreview') {
    const configPreview = document.getElementById(previewId);
    if (configPreview) {
        configPreview.textContent = config || "[No config returned]";
    }

    const activeSiem = getActiveSiem();
    const hfButton = document.getElementById('hfBtn');
    if (hfButton) {
        hfButton.style.display = activeSiem === 'splunk' ? 'inline-block' : 'none';
    }

    const configModal = new bootstrap.Modal(document.getElementById(modalId));
    configModal.show();
}

/**
 * Generic error display function
 * @param {Array<string>} errors - Array of error messages
 * @param {string} loggerId - ID of the logger element (optional)
 */
function displayErrors(errors, loggerId = null) {
    if (errors.length === 0) return;

    // Format error messages for better readability
    const formattedErrors = errors.map(error => {
        // Improve formatting of validation error messages
        if (error.includes('missing')) {
            return error.replace(/Rule '([^']+)': missing (.+)/, '<strong>Rule "$1"</strong>: Missing required field "<em>$2</em>"');
        } else if (error.includes('empty')) {
            return error.replace(/Rule '([^']+)': (.+) is empty/, '<strong>Rule "$1"</strong>: Field "<em>$2</em>" cannot be empty');
        }
        return error;
    });

    const errorMessage = formattedErrors.join('<br>');

    // Display user-friendly error modal instead of console logging
    showErrorModal(`<div class="text-start">
        <h6 class="text-danger mb-2">Validation Errors</h6>
        <div class="small">${errorMessage}</div>
    </div>`);
}

/**
 * Generic success message display function
 * @param {string} message - Success message to display
 * @param {string} loggerId - ID of the logger element (optional)
 */
function displaySuccess(message, loggerId = null) {

    if (loggerId) {
        const logger = document.getElementById(loggerId);
        if (logger) {
            logger.textContent = message;
            logger.className = 'badge bg-info fs-6';
            setTimeout(() => {
                logger.textContent = '';
            }, 2000);
        }
    }
}

// ========================================
// Shared Config Generation Workflows
// ========================================

/**
 * Generic config validation workflow with status checking
 * @param {Array<string>} configIds - Array of entry IDs
 * @param {Object} options - Configuration options
 * @param {Function} options.validateFields - Function to validate required fields
 * @param {Function} options.generateConfig - Function to generate the config
 * @param {string} options.loggerId - ID of logger element for feedback
 * @returns {Promise<Object>} - Validation result
 */
async function validateConfigWorkflow(configIds, options = {}) {
    const { validateFields, generateConfig, loggerId } = options;

    if (configIds.length === 0) {
        const errors = ['No entries selected for configuration.'];
        displayErrors(errors, loggerId);
        return { valid: false, errors };
    }

    // Run field validation if provided
    if (validateFields) {
        try {
            const fieldValidation = await validateFields(configIds);
            if (!fieldValidation.valid) {
                displayErrors(fieldValidation.errors, loggerId);
                return fieldValidation;
            }
        } catch (error) {
            const errors = [`Field validation error: ${error.message}`];
            displayErrors(errors, loggerId);
            return { valid: false, errors };
        }
    }

    // Check deployable status for SmartLP entries
    if (options.checkDeployableStatus) {
        try {
            const statusData = await checkDeployableStatus(configIds);
            if (statusData.unmatched && statusData.unmatched.length > 0) {
                const errors = [];
                const statusGroups = {};

                statusData.unmatched.forEach(entry => {
                    const status = entry.status || "Unknown";
                    if (!statusGroups[status]) statusGroups[status] = [];
                    statusGroups[status].push(entry.id);
                });

                Object.keys(statusGroups).forEach(status => {
                    const statusLabel = status === "Unmatched" ? "Unmatched (needs parsing)" :
                        status === "Deployed" ? "Deployed (already deployed)" : `${status} status`;
                    errors.push(`${statusLabel}: ${statusGroups[status].join(", ")}`);
                });

                errors.push("Please ensure all entries have 'Matched' status before generating config.");
                displayErrors(errors, loggerId);
                return { valid: false, errors };
            }
        } catch (error) {
            const errors = [`Status check error: ${error.message}`];
            displayErrors(errors, loggerId);
            return { valid: false, errors };
        }
    }

    // Generate config if all validations pass
    if (generateConfig) {
        try {
            const configData = await generateConfig(configIds);
            showConfigModal(configData.config);
            displaySuccess('Configuration generated successfully!', loggerId);
            return { valid: true, errors: [] };
        } catch (error) {
            const errors = [`Config generation error: ${error.message}`];
            displayErrors(errors, loggerId);
            return { valid: false, errors };
        }
    }

    return { valid: true, errors: [] };
}

/**
 * SmartLP-specific config validation workflow
 * @param {Array<Object>} rows - Table rows for field validation
 * @param {Array<string>} configIds - Array of entry IDs
 * @param {string} loggerId - ID of logger element
 * @returns {Promise<Object>} - Validation result
 */
async function validateSmartLPConfig(rows, configIds, loggerId = null) {
    return await validateConfigWorkflow(configIds, {
        validateFields: async (ids) => {
            // Validate that all entries have both index and source_type filled
            const missingFields = [];
            let hasErrors = false;

            rows.forEach((row) => {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 4) {
                    const entryId = cells[0].textContent.trim();

                    // For index field (cell 2) - check if it contains an input element
                    const indexCell = cells[2];
                    const indexInput = indexCell.querySelector('input');
                    const indexValue = indexInput ? indexInput.value.trim() : indexCell.textContent.trim();

                    // For source_type field (cell 3) - check if it contains an input element
                    const sourceTypeCell = cells[3];
                    const sourceTypeInput = sourceTypeCell.querySelector('input');
                    const sourceTypeValue = sourceTypeInput ? sourceTypeInput.value.trim() : sourceTypeCell.textContent.trim();

                    if (!indexValue) {
                        missingFields.push(`Entry ${entryId}: missing index`);
                        hasErrors = true;
                    }
                    if (!sourceTypeValue) {
                        missingFields.push(`Entry ${entryId}: missing source_type`);
                        hasErrors = true;
                    }
                }
            });

            return hasErrors ? { valid: false, errors: missingFields } : { valid: true, errors: [] };
        },
        generateConfig: generateSmartLPConfig,
        checkDeployableStatus: true,
        loggerId
    });
}

/**
 * SmartUC-specific config validation workflow
 * @param {Array<Object>} rows - Table rows for field validation  
 * @param {Array<string>} configIds - Array of entry IDs
 * @param {string} siem - Target SIEM platform
 * @param {string} loggerId - ID of logger element
 * @returns {Promise<Object>} - Validation result
 */
async function validateSmartUCConfig(rows, configIds, siem, loggerId = null) {
    return await validateConfigWorkflow(configIds, {
        validateFields: async (ids) => {
            // Validate that all entries have required fields filled based on SIEM type
            const missingFields = [];
            let hasErrors = false;

            // Define required fields for each SIEM
            const requiredFields = {
                splunk: ['cron_schedule', 'dispatch_earliest_time', 'dispatch_latest_time'],
                elastic: ['interval', 'dispatch_earliest_time', 'dispatch_latest_time', 'risk_score']
            };

            const fieldsToCheck = requiredFields[siem] || requiredFields.splunk;

            rows.forEach((row) => {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 2) {
                    // Get rule title from first cell
                    const ruleTitle = cells[0].textContent.trim();

                    // Check each required field based on SIEM type
                    fieldsToCheck.forEach((fieldName, index) => {
                        // Field values are in cells starting from index 1 (after title)
                        const cellIndex = index + 1;
                        if (cellIndex < cells.length) {
                            const fieldValue = cells[cellIndex].textContent.trim();
                            if (!fieldValue) {
                                missingFields.push(`Rule "${ruleTitle}": missing ${fieldName}`);
                                hasErrors = true;
                            }
                        }
                    });
                }
            });

            return hasErrors ? { valid: false, errors: missingFields } : { valid: true, errors: [] };
        },
        generateConfig: (ids) => generateSmartUCConfig(ids, siem),
        checkDeployableStatus: false, // SmartUC doesn't use deployable status checks
        loggerId
    });
}

// ========================================
// Configuration Factory Functions
// ========================================

/**
 * Create SmartLP configuration panel with shared settings
 * @param {Object} selection - The selection module instance
 * @param {Object} customOptions - Optional custom configuration overrides
 * @returns {Object} - The configured config panel module
 */
function createSmartLPConfigPanel(selection, customOptions = {}) {
    const defaultConfig = {
        selection,
        configTableBodyId: 'configTableBody',
        popupBoxId: 'popupBox',
        selectionCountId: 'configSelectionCount',
        previewId: 'configPreview',
        openPanelBtnId: 'openConfigPanelBtn',
        validateAndConfigId: 'validateAndConfig',
        loggerId: 'smartlpConfigLogger',
        fetchConfigData: async (ids) => {
            // Use existing search API with comma-separated IDs in search_id parameter
            const searchIds = ids.join(',');
            const paramObj = {
                search_id: searchIds,
                per_page: ids.length + 10  // Ensure we get all results
            };
            const data = await fetchEntries(paramObj);
            let entries = data.results || [];

            // Filter to only include the exact IDs we requested (in case search returns partial matches)
            entries = entries.filter(entry => ids.includes(entry.id));

            // Sort entries to match the order of requested ids
            entries.sort((a, b) => ids.indexOf(a.id) - ids.indexOf(b.id));

            return entries;
        },
        validateConfig: async (rows) => {
            const configIds = Array.from(selection.ids);
            return await validateSmartLPConfig(rows, configIds, 'smartlpConfigLogger');
        },
        onPanelOpen: () => {
            // Update arrow direction when panel opens
            const arrowBtn = document.querySelector(".arrow-btn i");
            if (arrowBtn) {
                arrowBtn.classList.remove("fa-chevron-up");
                arrowBtn.classList.add("fa-chevron-down");
            }
        },
        onPanelClose: () => {
            // Update arrow direction when panel closes
            const arrowBtn = document.querySelector(".arrow-btn i");
            if (arrowBtn) {
                arrowBtn.classList.remove("fa-chevron-down");
                arrowBtn.classList.add("fa-chevron-up");
            }
        },
        customRenderConfigTable: function (configRows, configTableBody) {
            configTableBody.innerHTML = '';

            configRows.forEach(entry => {
                const row = configTableBody.insertRow();

                // ID column
                const idCell = row.insertCell();
                idCell.textContent = entry.id;
                idCell.classList.add('align-middle');

                // Timestamp column
                const timeCell = row.insertCell();
                const date = new Date(entry.timestamp);
                timeCell.textContent = date.toLocaleDateString();
                timeCell.classList.add('align-middle');

                // Index column (editable)
                const indexCell = row.insertCell();
                indexCell.classList.add('align-middle');
                const indexInput = document.createElement('input');
                indexInput.type = 'text';
                indexInput.className = 'form-control form-control-sm';
                indexInput.value = entry.index || '';
                indexInput.placeholder = 'Enter index...';

                // Auto-save on blur for index
                indexInput.addEventListener('blur', async () => {
                    const newValue = indexInput.value.trim();
                    if (newValue !== (entry.index || '')) {
                        try {
                            await updateEntry(entry.id, { index: newValue });
                            entry.index = newValue; // Update local data

                            // Refresh main table data to reflect changes
                            if (typeof window.searchData === 'function') {
                                window.searchData();
                            }

                            // Log success
                            const logger = document.getElementById('smartlpConfigLogger');
                            if (logger) {
                                logger.textContent = `Index updated for ${entry.id}`;
                                logger.className = 'badge bg-success fs-6';
                                setTimeout(() => {
                                    logger.textContent = '';
                                    logger.className = 'badge bg-info fs-6';
                                }, 2000);
                            }
                        } catch (error) {
                            console.error('Error updating index:', error);
                            indexInput.value = entry.index || ''; // Revert on error

                            // Log error
                            const logger = document.getElementById('smartlpConfigLogger');
                            if (logger) {
                                logger.textContent = `Error updating index`;
                                logger.className = 'badge bg-danger fs-6';
                                setTimeout(() => {
                                    logger.textContent = '';
                                    logger.className = 'badge bg-info fs-6';
                                }, 3000);
                            }
                        }
                    }
                });

                indexCell.appendChild(indexInput);

                // SourceType column (editable)
                const sourceTypeCell = row.insertCell();
                sourceTypeCell.classList.add('align-middle');
                const sourceTypeInput = document.createElement('input');
                sourceTypeInput.type = 'text';
                sourceTypeInput.className = 'form-control form-control-sm';
                sourceTypeInput.value = entry.source_type || '';
                sourceTypeInput.placeholder = 'Enter sourcetype...';

                // Auto-save on blur for sourcetype
                sourceTypeInput.addEventListener('blur', async () => {
                    const newValue = sourceTypeInput.value.trim();
                    if (newValue !== (entry.source_type || '')) {
                        try {
                            await updateEntry(entry.id, { source_type: newValue });
                            entry.source_type = newValue; // Update local data

                            // Refresh main table data to reflect changes
                            if (typeof window.searchData === 'function') {
                                window.searchData();
                            }

                            // Log success
                            const logger = document.getElementById('smartlpConfigLogger');
                            if (logger) {
                                logger.textContent = `SourceType updated for ${entry.id}`;
                                logger.className = 'badge bg-success fs-6';
                                setTimeout(() => {
                                    logger.textContent = '';
                                    logger.className = 'badge bg-info fs-6';
                                }, 2000);
                            }
                        } catch (error) {
                            console.error('Error updating source_type:', error);
                            sourceTypeInput.value = entry.source_type || ''; // Revert on error

                            // Log error
                            const logger = document.getElementById('smartlpConfigLogger');
                            if (logger) {
                                logger.textContent = `Error updating sourcetype`;
                                logger.className = 'badge bg-danger fs-6';
                                setTimeout(() => {
                                    logger.textContent = '';
                                    logger.className = 'badge bg-info fs-6';
                                }, 3000);
                            }
                        }
                    }
                });

                sourceTypeCell.appendChild(sourceTypeInput);

                // Log column
                const logCell = row.insertCell();
                let logContent = entry.log || '';
                if (logContent.length > 80) {
                    logContent = logContent.substring(0, 80) + '...';
                    logCell.title = entry.log; // Show full content on hover
                }
                logCell.textContent = logContent;
                logCell.classList.add('align-middle');

                // Action column (remove button)
                const actionCell = row.insertCell();
                actionCell.classList.add('text-center', 'align-middle');
                const removeBtn = document.createElement('button');
                removeBtn.className = 'btn btn-sm btn-outline-danger remove-config-btn';
                removeBtn.dataset.entryId = entry.id;
                removeBtn.innerHTML = '<i class="fa fa-times"></i>';
                removeBtn.title = 'Remove from configuration';
                panelContext = this;
                removeBtn.addEventListener('click', function () {
                    const entryId = this.dataset.entryId;
                    if (panelContext.removeFromConfig) {
                        panelContext.removeFromConfig(entryId);
                    } else {
                        selection.removeIds([entryId]);
                        if (panelContext.syncPanel) {
                            panelContext.syncPanel();
                        }
                    }
                });
                actionCell.appendChild(removeBtn);
            });
        }
    };

    return createConfigPanelModule({ ...defaultConfig, ...customOptions });
}

/**
 * Create SmartUC configuration panel with shared settings
 * @param {Object} selection - The selection module instance
 * @param {Object} customOptions - Optional custom configuration overrides
 * @returns {Object} - The configured config panel module
 */
function createSmartUCConfigPanel(selection, customOptions = {}) {
    const defaultConfig = {
        selection,
        configTableBodyId: 'configTableBody',
        popupBoxId: 'popupBox',
        selectionCountId: 'configSelectionCount',
        previewId: 'configPreview',
        openPanelBtnId: 'openConfigPanel',
        validateAndConfigId: 'createConfig',
        loggerId: 'smartucConfigLogger',
        fetchConfigData: async (ids) => {
            const activeSiem = getActiveSiem();
            const rows = await fetchSmartUCConfigData(activeSiem, ids);
            // Attach SIEM type for rendering
            rows.forEach(row => row._siem = activeSiem);
            return rows;
        }, validateConfig: async (rows) => {
            // For SmartUC, we call the API to generate config with field validation
            const activeSiem = getActiveSiem();
            const configIds = selection.ids;

            // Use shared validation workflow with table rows for field validation
            return await validateSmartUCConfig(rows, configIds, activeSiem, 'smartucConfigLogger');
        },
        onPanelOpen: () => {
            const arrowBtn = document.querySelector(".arrow-btn i");
            if (arrowBtn) {
                arrowBtn.classList.remove("fa-chevron-up");
                arrowBtn.classList.add("fa-chevron-down");
            }
        },
        onPanelClose: () => {
            const arrowBtn = document.querySelector(".arrow-btn i");
            if (arrowBtn) {
                arrowBtn.classList.remove("fa-chevron-down");
                arrowBtn.classList.add("fa-chevron-up");
            }
        },
        // Custom render for SmartUC config table with SIEM-specific fields
        customRenderConfigTable: function (configRows, configTableBody) {
            const activeSiem = getActiveSiem();
            configTableBody.innerHTML = '';
            // Render dynamic table header
            const thead = configTableBody.parentElement.querySelector('thead');
            if (thead) {
                if (activeSiem === 'splunk') {
                    thead.innerHTML = `<tr>
                        <th>Title</th>
                        <th>Cron Schedule</th>
                        <th>Earliest Time</th>
                        <th>Latest Time</th>
                        <th>Deployed</th>
                        <th>Remove</th>
                    </tr>`;
                } else {
                    thead.innerHTML = `<tr>
                        <th>Title</th>
                        <th>Interval</th>
                        <th>Earliest Time</th>
                        <th>Latest Time</th>
                        <th>Risk Score</th>
                        <th>Deployed</th>
                        <th>Remove</th>
                    </tr>`;
                }
            }

            if (configRows.length === 0) {
                configTableBody.innerHTML = `<tr><td colspan="${activeSiem === 'splunk' ? 5 : 6}" class="text-center text-muted">No entries selected</td></tr>`;
                return;
            }

            configRows.forEach(row => {
                const tr = document.createElement('tr');
                if (activeSiem === 'splunk') {
                    tr.innerHTML = `
                        <td>${row.title || ''}</td>
                        <td contenteditable="true" data-id="${row.id}" data-field="cron_schedule">${row.cron_schedule || ''}</td>
                        <td contenteditable="true" data-id="${row.id}" data-field="dispatch_earliest_time">${row.dispatch_earliest_time || ''}</td>
                        <td contenteditable="true" data-id="${row.id}" data-field="dispatch_latest_time">${row.dispatch_latest_time || ''}</td>
                        <td data-id="${row.id}" data-field="deployed">${row.deployed.toString() || 'false'}</td>
                        <td><button class="btn btn-sm btn-outline-danger remove-config-btn" data-entry-id="${row.id}" title="Remove from config"><i class="fa fa-times"></i></button></td>
                    `;
                } else {
                    tr.innerHTML = `
                        <td>${row.title || ''}</td>
                        <td contenteditable="true" data-id="${row.id}" data-field="interval">${row.interval || ''}</td>
                        <td contenteditable="true" data-id="${row.id}" data-field="dispatch_earliest_time">${row.dispatch_earliest_time || ''}</td>
                        <td contenteditable="true" data-id="${row.id}" data-field="dispatch_latest_time">${row.dispatch_latest_time || ''}</td>
                        <td contenteditable="true" data-id="${row.id}" data-field="risk_score">${row.risk_score || ''}</td>
                        <td data-id="${row.id}" data-field="deployed">${row.deployed.toString() || 'false'}</td>
                        <td><button class="btn btn-sm btn-outline-danger remove-config-btn" data-entry-id="${row.id}" title="Remove from config"><i class="fa fa-times"></i></button></td>
                    `;
                }
                configTableBody.appendChild(tr);
            });
            // Attach remove handlers
            const panelContext = this; // Store panel context reference
            configTableBody.querySelectorAll('.remove-config-btn').forEach(btn => {
                btn.addEventListener('click', function () {
                    const entryId = this.dataset.entryId;
                    if (panelContext.removeFromConfig) {
                        panelContext.removeFromConfig(entryId);
                    } else {
                        selection.removeIds([entryId]);
                        if (panelContext.syncPanel) {
                            panelContext.syncPanel();
                        }
                    }
                });
            });
            // Attach editable cell handlers
            configTableBody.querySelectorAll('[contenteditable]').forEach(cell => {
                cell.addEventListener('focus', function () {
                    this.dataset.originalValue = this.textContent.trim();
                });
                cell.addEventListener('blur', async function () {
                    const id = this.dataset.id;
                    const field = this.dataset.field;
                    const value = this.textContent.trim();

                    if (value !== this.dataset.originalValue) {
                        if (!id || !field) {
                            console.error('Missing id or field for SmartUC config update:', { id, field });
                            return;
                        }

                        try {
                            const activeSiem = getActiveSiem();
                            await updateSmartUCConfigField(id, field, value, activeSiem);
                        } catch (error) {
                            console.error('SmartUC field update failed:', error);
                        }
                    }
                });
            });
        }
    };

    return createConfigPanelModule({ ...defaultConfig, ...customOptions });
}

/**
 * Helper function to get active SIEM (used by SmartUC)
 * @returns {string} - The active SIEM platform
 */
function getActiveSiem() {
    return sessionStorage.getItem("activeSiem") || "splunk";
}

// ========================================
// Session Storage Debug Utilities
// ========================================

/**
 * Debug function to inspect session storage state across all modules
 * Call from browser console: debugSelectionState()
 */
function debugSelectionState() {
    console.log('=== Selection State Debug ===');

    // Get all selection-related keys from session storage (now using entryIds_ and ruleIds_)
    const selectionKeys = Object.keys(sessionStorage).filter(key =>
        key.startsWith('entryIds_') || key.startsWith('ruleIds_') || key.startsWith('selection_')
    );

    if (selectionKeys.length === 0) {
        console.log('No selection data found in session storage');
        return;
    }

    selectionKeys.forEach(key => {
        try {
            const data = JSON.parse(sessionStorage.getItem(key));
            let module = 'unknown';
            if (key.startsWith('entryIds_')) {
                module = 'SmartLP (' + key.replace('entryIds_', '') + ')';
            } else if (key.startsWith('ruleIds_')) {
                module = 'SmartUC (' + key.replace('ruleIds_', '') + ')';
            } else {
                module = key.replace('selection_', '');
            }
            console.log(`Module: ${module}`, {
                storageKey: key,
                selectedIds: data,
                count: data.length
            });
        } catch (error) {
            console.warn(`Error parsing ${key}:`, error);
        }
    });

    console.log('=== End Debug ===');
}

// Make it globally available for console debugging
window.debugSelectionState = debugSelectionState;
