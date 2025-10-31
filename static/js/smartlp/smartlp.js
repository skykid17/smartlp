// SmartLP page specific variables
let currentPage = 1;
let entriesPerPage = 15; // Make it mutable
let selectEnableButtons;
let smartlpLogger; // Local logger variable for SmartLP

// Import selection module from utils.js (assume loaded in HTML before this script)
// Initialize selection for SmartLP
const smartlpSelection = createSelectionModule({
    tableBodyId: 'entryTableBody',
    selectEnableSelector: '.selectEnable',
    loggerId: 'smartlpLogger',
    configPanelSync: () => smartlpConfigPanel.syncPanel(),
    storagePrefix: 'entryIds', // Use entryIds for SmartLP
    idLabel: 'entries', // Display "entries" in logger messages
    checkboxSelector: 'input[type="checkbox"].entry-checkbox' // Use SmartLP-specific checkbox selector
});

// --- Config Panel Module Initialization ---
const smartlpConfigPanel = createSmartLPConfigPanel(smartlpSelection);

// Note: API utility functions are now in utils.js as shared functions:
// - apiRequest, fetchEntries, updateEntry, deleteEntry
// - checkDeployableStatus, generateSmartLPConfig
// - showConfigModal, displayErrors, displaySuccess

document.addEventListener("DOMContentLoaded", () => {
    if (window.location.pathname === "/smartlp") {
        // Initialize local logger for SmartLP
        smartlpLogger = document.getElementById("smartlpLogger");

        // Initialize ingestion status monitoring
        initializeIngestionStatus();

        selectEnableButtons = document.querySelectorAll(".selectEnable");

        if (entryModal) {
            entryModal.addEventListener("hidden.bs.modal", closeModal);
        }

        addEventIfExists(filterStatusSelect, "change", () => {
            currentPage = 1;
        });        // Clear config table and collapse popup on initial load
        const configTableBody = document.getElementById("configTableBody");
        const popup = document.getElementById("popupBox");
        if (configTableBody) configTableBody.innerHTML = "";
        if (popup) popup.classList.add("collapsed");

        document.getElementById("validateAndConfig").addEventListener("click", () => {
            smartlpConfigPanel.validateAndConfig();
        });

        // Setup shared click-to-select functionality
        setupClickToSelect(smartlpSelection, {
            tableBodyId: 'entryTableBody',
            rowSelector: '.table-row',
            checkboxSelector: 'input[type="checkbox"].entry-checkbox'
        });        // Run initial search and initialize ingestion status
        searchData();
        initializeIngestionStatus();

        // Initialize rows per page dropdown
        initializeRowsPerPage();
    }
    const saveBtn = document.getElementById("saveEntryChangesBtn");
    if (saveBtn) {
        saveBtn.addEventListener("click", async () => {
            const entryId = getSessionItem("id");
            const indexValue = document.getElementById("modalIndex").value.trim();
            const sourceTypeValue = document.getElementById("modalSourceType").value.trim();

            try {
                await updateEntry(entryId, {
                    index: indexValue,
                    source_type: sourceTypeValue
                });

                // Refresh main table data to reflect changes
                searchData();

                // If config panel is open, refresh it too
                const popup = document.getElementById("popupBox");
                if (popup && !popup.classList.contains("collapsed")) {
                    smartlpConfigPanel.syncPanel();
                }

                closeModal();

                // Show success message
                smartlpLogger.textContent = `Entry ${entryId} updated successfully`;
                smartlpLogger.className = 'badge bg-success fs-6';
                setTimeout(() => {
                    smartlpLogger.textContent = '';
                }, 3000);
            } catch (error) {
                console.error("Error saving changes:", error);
                alert("Error saving changes: " + error.message);
            }
        });
    }
});

//Clear all search fields
function clearSearch() {
    const searchId = document.getElementById('searchId');
    const searchLog = document.getElementById('searchLog');
    const searchRegex = document.getElementById('searchRegex');
    const filterStatusSelect = document.getElementById('filterStatusSelect');

    if (searchId) searchId.value = '';
    if (searchLog) searchLog.value = '';
    if (searchRegex) searchRegex.value = '';
    if (filterStatusSelect) filterStatusSelect.value = '';

    // Reset to first page
    currentPage = 1;

    // Provide visual feedback
    smartlpLogger.textContent = 'Search cleared';
    smartlpLogger.className = 'badge bg-success fs-6';

    // Clear the message after a short delay
    setTimeout(() => {
        if (smartlpLogger.textContent === 'Search cleared') {
            smartlpLogger.textContent = '';
        }
    }, 2000);

    searchData(true); // Refresh data, with flag to keep previous message.

    setTimeout(() => {
        if (smartlpLogger.textContent === 'Search cleared') {
            smartlpLogger.textContent = '';
            smartlpLogger.className = 'badge bg-info fs-6';
            sessionStorage.removeItem('isSearchCleared');
        }
    }, 2000);
}

// Populate modal with item data
function populateModal(item) {
    const fields = ['Id', 'Timestamp', 'Index', 'Source_Type', 'Log_Type', 'Rule_Types', 'Log', 'Regex', 'Status', 'Siem', 'Query'];
    fields.forEach(field => {
        const el = document.getElementById(`modal${field.split("_").join("")}`);
        if (el) {
            // For input fields, set value; for display elements, set text
            if (el.tagName.toLowerCase() === 'input') {
                el.value = item[field.toLowerCase()] || '';
            } else {
                el.innerText = item[field.toLowerCase()] || '';
            }
        }
    });
    ['log', 'regex', 'id'].forEach(key => setSessionItem(key, item[key]));
}

// Close the entry modal
function closeModal() {
    const modal = bootstrap.Modal.getInstance(entryModal);
    if (modal) modal.hide();
    smartlpSelection.removeIds([getSessionItem("id")]);
}

// Handle row selection and modal display
function handleRowSelection(row, item, event = {}) {
    const isRowSelected = row.classList.contains('selected');
    const isMultiSelect = event.ctrlKey || event.metaKey;
    if (isMultiSelect) {
        smartlpSelection.toggleRowSelection(row, item.id);
    } else {
        if (isRowSelected) {
            smartlpSelection.toggleRowSelection(row, item.id);
        } else {
            populateModal(item);
            const modalInstance = new bootstrap.Modal(entryModal);
            modalInstance.show();
            // append selected entry to ids
            smartlpSelection.ids.push(item.id);
            smartlpSelection.updateMainTableSelection();
        }
    }
}

// Update pagination UI with the appropriate page links
function updatePagination(totalEntries) {
    const totalPages = Math.ceil(totalEntries / entriesPerPage);
    const paginationButtons = document.getElementById("pagination-buttons");
    const prevButton = document.getElementById("prevPage");
    const nextButton = document.getElementById("nextPage");
    const pageInput = document.getElementById("pageInput");
    const pageInfo = document.getElementById("pageInfo");
    const resultsCount = document.getElementById("resultsCount");

    paginationButtons.innerHTML = "";

    // Update page information
    const startEntry = totalEntries > 0 ? (currentPage - 1) * entriesPerPage + 1 : 0;
    const endEntry = Math.min(currentPage * entriesPerPage, totalEntries);

    if (pageInfo) {
        pageInfo.textContent = totalEntries > 0
            ? `Page ${currentPage} of ${totalPages} (${startEntry}-${endEntry} of ${totalEntries})`
            : 'No entries found';
    }
    if (resultsCount) {
        resultsCount.textContent = totalEntries > 0
            ? `${totalEntries} entries found (${entriesPerPage} per page)`
            : 'No entries';
    }

    const pageLinks = generatePageLinks(currentPage, totalPages, 5); // Generate page links dynamically
    pageLinks.forEach(link => {
        const button = document.createElement("button");
        button.className = "page-link";
        button.innerText = link || "...";
        if (link === currentPage) button.classList.add("active");
        if (link) button.onclick = () => changePage(link);
        else button.className = "page-link disabled"; // Disable ellipsis buttons
        paginationButtons.appendChild(button);
    });

    if (currentPage === 1) prevButton.classList.add("disabled");
    else prevButton.classList.remove("disabled");
    if (currentPage === totalPages || totalPages === 0) nextButton.classList.add("disabled");
    else nextButton.classList.remove("disabled");
    if (pageInput) pageInput.max = totalPages;
}

// Generate page link numbers to display in pagination
function generatePageLinks(currentPage, totalPages, maxPagesToShow) {
    const halfRange = Math.floor(maxPagesToShow / 2);
    let startPage = Math.max(2, currentPage - halfRange); // Start from 2 to leave space for the first page
    let endPage = Math.min(totalPages - 1, currentPage + halfRange); // End at totalPages - 1 to leave space for the last page

    // Adjust range if near the beginning or end
    if (currentPage <= halfRange) {
        endPage = Math.min(totalPages - 1, maxPagesToShow);
    } else if (currentPage + halfRange > totalPages) {
        startPage = Math.max(2, totalPages - maxPagesToShow + 1);
    }

    const pages = [1]; // Always include the first page

    if (startPage > 2) {
        pages.push(null); // Add ellipsis after the first page
    }

    for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
    }

    if (endPage < totalPages - 1) {
        pages.push(null); // Add ellipsis before the last page
    }

    if (totalPages > 1) {
        pages.push(totalPages); // Always include the last page
    }

    return pages;
}

// Change to a different page
function changePage(action) {
    if (!action) {
        smartlpLogger.innerText = "Invalid page number";
        return; // Invalid page number
    } else if (typeof action === "string") {
        currentPage += action === "prev" ? -1 : 1;
    } else {
        currentPage = action;
    }
    smartlpLogger.innerText = "";
    searchData(); // Refresh data for the new page
}

// Search for data with filters
async function searchData(hasPreviousMessage = false) {
    const searchId = document.getElementById('searchId');
    const searchLog = document.getElementById('searchLog');
    const searchRegex = document.getElementById('searchRegex');
    const filterStatusSelect = document.getElementById('filterStatusSelect');
    const entryTable = document.getElementById('entryTable');

    if (!searchId || !searchLog || !searchRegex || !filterStatusSelect) {
        return;
    }

    const currentSelections = [...smartlpSelection.ids]; // List of current selections

    // Add loading state
    if (entryTable) entryTable.classList.add('loading');

    try {
        const paramObj = {
            "search_id": searchId.value.trim(),
            "search_log": searchLog.value.trim(),
            "search_regex": searchRegex.value.trim(),
            "filter_status": filterStatusSelect.value,
            "page": currentPage,
            "per_page": entriesPerPage
        };

        const data = await fetchEntries(paramObj);
        smartlpSelection.updateTableData(data.results, {
            emptyStateColSpan: 6,
            rowRenderer: populateRow,
            afterUpdate: () => {
                updatePagination(data.total_entries);
                if (!hasPreviousMessage) {
                    smartlpLogger.textContent = '';
                    smartlpLogger.className = 'badge bg-info fs-6';
                }
            }
        }); // Update table with new data

        smartlpSelection.updateSelectionUI();
    } catch (error) {
        console.error('Search error:', error);
        smartlpLogger.textContent = 'Error in search. Please try again.';
        smartlpLogger.className = 'badge bg-danger fs-6';

        // Clear table on error
        smartlpSelection.updateTableData([]);
        updatePagination(0);
    } finally {
        // Remove loading state
        if (entryTable) entryTable.classList.remove('loading');
    }
}

// Populate a table row with data and selection behavior
function populateRow(row, item) {
    // Create cells for each field
    ['id', 'timestamp', 'log', 'regex'].forEach((field, index) => {
        const cell = row.insertCell(index);
        let content = item[field] || '';

        // Truncate long content for better display
        if (field === 'log' && content.length > 80) {
            content = content.substring(0, 80) + '...';
            cell.title = item[field]; // Show full content on hover
        } else if (field === 'regex' && content.length > 50) {
            content = content.substring(0, 50) + '...';
            cell.title = item[field]; // Show full content on hover
        } else if (field === 'timestamp') {
            // Format timestamp nicely
            const date = new Date(content);
            content = date.toLocaleString();
        }

        cell.textContent = content;
        cell.classList.add('align-middle');
    });

    // Status cell with badge
    const statusCell = row.insertCell(4);
    statusCell.classList.add('align-middle');
    const status = item.status || 'Unknown';
    const statusBadge = document.createElement('span');
    statusBadge.className = `status-badge ${status.toLowerCase()}`;
    statusBadge.textContent = status;
    statusCell.appendChild(statusBadge);

    // Selection checkbox
    const selectCell = row.insertCell(5);
    selectCell.classList.add('text-center', 'align-middle');

    selectCell.addEventListener('click', event => {
        event.stopPropagation(); // This stops the modal from opening
    });
    const label = document.createElement('label');
    label.classList.add('form-check', 'd-flex', 'justify-content-center'); const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = item.id;  // Set the value to the entry ID for identification
    checkbox.id = `checkbox-${item.id}`;
    checkbox.classList.add('form-check-input', 'entry-checkbox');

    // Note: Click handling is now managed by shared setupClickToSelect function
    label.appendChild(checkbox);
    selectCell.appendChild(label);

    // Row click event
    row.addEventListener('click', event => {
        handleRowSelection(row, item, event);
        checkbox.checked = row.classList.contains('selected');
    });

    row.classList.add('table-row', 'cursor-pointer');
}

// Deploy selected entries to SIEM
async function showDeployModal() {
    if (smartlpSelection.ids.length === 0) {
        alert('Error: No entries selected for pushing to SIEM.');
        return;
    }
    var activeSiem = sessionStorage.getItem("activeSiem") || "siem"; try {
        const data = await checkDeployableStatus(smartlpSelection.ids);

        // : show deploy modal
        document.getElementById('logIndex').value = '';
        document.getElementById('logSourcetype').value = '';
        document.getElementById('deployError').style.display = 'none';
        const deployModal = new bootstrap.Modal(document.getElementById('deployModal'));
        deployModal.show();

    } catch (error) {
        // Check if error has response data for detailed error messages
        let html = "An error occurred while checking entries for deployment.";
        if (error.message && error.message.includes('HTTP error')) {
            try {
                // Try to parse error response if available
                html = `The following entries are not yet matched or have deployment issues. Please check the entry status.`;
            } catch (parseError) {
                // Use default message if parsing fails
            }
        }
        showErrorModal(html);
    }
}

async function deploy() {
    // Use the shared deployment function from utils.js
    await deployWithFeedback(smartlpSelection.ids, 'smartlp', {
        deployBtnSelector: '#configModal button[onclick="deploy()"]',
        feedbackDivId: 'deploymentFeedback',
        messageDivId: 'deploymentMessage',
        configModalId: 'configModal',
        onSuccess: (result) => {
            // SmartLP-specific success handling if needed
            console.log('SmartLP deployment successful:', result);
        },
        onError: (error, errorMessage) => {
            // SmartLP-specific error handling if needed
            console.error('SmartLP deployment failed:', error);
        }
    });
}

async function deployHF() {
    // Use the shared deployment function from utils.js
    await deployWithFeedback(smartlpSelection.ids, 'smartlpHF', {
        deployBtnSelector: '#configModal button[onclick="deployHF()"]',
        feedbackDivId: 'deploymentFeedback',
        messageDivId: 'deploymentMessage',
        configModalId: 'configModal',
        onSuccess: (result) => {
            // SmartLP-specific success handling if needed
            console.log('SmartLP to HF deployment successful:', result);
        },
        onError: (error, errorMessage) => {
            // SmartLP-specific error handling if needed
            console.error('SmartLP to HF deployment failed:', error);
        }
    });
}

// Delete selected entries
async function deleteEntries() {
    if (smartlpSelection.ids.length === 0) return alert('Error: No entries selected for deletion.');

    try {
        // Delete all selected entries
        await Promise.all(smartlpSelection.ids.map(id => deleteEntry(id)));

        // Refresh the data
        smartlpSelection.clearSelection();
        await searchData();
        closeModal();
    } catch (error) {
        console.error("Error deleting entries:", error);
    }
}

// Open parser window for editing entries
async function openParserWindow() {
    if (smartlpSelection.ids.length === 0) {
        smartlpLogger.innerText = "No entry selected";
        return;
    }
    else if (smartlpSelection.ids.length > 1) {
        showErrorModal('Multiple rows cannot be edited at once. Please select only one row for editing.');
        smartlpSelection.clearSelection();
        return;
    }

    // Put the index, log & prefix to Session Storage
    selected = document.getElementsByClassName('table-row selected')[0];
    setSessionItem("key", selected.childNodes[0].textContent)
    setSessionItem("log", selected.childNodes[2].title)
    setSessionItem("regex", selected.childNodes[3].title)

    window.location.href = "/smartlp/parser";
}

// Helper function to update main table selection display
function updateMainTableSelection() {
    smartlpSelection.updateMainTableSelection();
}

async function handleCreateConfig() {
    try {
        // Close any open modals without affecting selection
        const modal = bootstrap.Modal.getInstance(entryModal);
        const deployModal = bootstrap.Modal.getInstance(document.getElementById('deployModal'));
        if (deployModal) deployModal.hide();
        if (modal) {
            setSessionItem("id", 0);
            modal.hide();

        }

        // Unhide popup first
        const popup = document.getElementById("popupBox");
        popup.classList.remove("collapsed");

        // Update arrow direction
        const arrowBtn = document.querySelector(".arrow-btn i");
        if (arrowBtn) {
            arrowBtn.classList.remove("fa-chevron-up");
            arrowBtn.classList.add("fa-chevron-down");
        }
        // Now then we update selection and sync config panel
        smartlpSelection.updateMainTableSelection();
        smartlpConfigPanel.syncPanel();

    } catch (error) {
        console.error("Error in handleCreateConfig:", error);
        alert(`Failed to open config panel: ${error.message}`);
    }
}

function togglePopup() {
    const popup = document.getElementById("popupBox");
    const arrowBtn = document.querySelector(".arrow-btn i");
    popup.classList.toggle("collapsed");

    // If panel is being opened, sync with current selection
    if (!popup.classList.contains("collapsed")) {
        arrowBtn.classList.remove("fa-chevron-up");
        arrowBtn.classList.add("fa-chevron-down");
        smartlpConfigPanel.syncPanel();
    } else {
        arrowBtn.classList.remove("fa-chevron-down");
        arrowBtn.classList.add("fa-chevron-up");
    }
}

// --- Rows Per Page Functionality ---
async function changeRowsPerPage() {
    const rowsSelect = document.getElementById('rowsPerPage');
    const customInput = document.getElementById('customRowsInput');

    if (rowsSelect.value === 'custom') {
        customInput.style.display = 'block';
        customInput.focus();
        return;
    } else {
        customInput.style.display = 'none';
        entriesPerPage = parseInt(rowsSelect.value);
    }

    // Update logger with feedback
    smartlpLogger.textContent = `Showing ${entriesPerPage} entries per page`;
    smartlpLogger.className = 'badge bg-info fs-6';

    // Reset to first page and refresh data
    currentPage = 1;
    await searchData(true);

    // Reset logger
    setTimeout(() => {
        smartlpLogger.textContent = '';
    }, 2000);
}

async function applyCustomRows() {
    const customInput = document.getElementById('customRowsInput');
    const rowsSelect = document.getElementById('rowsPerPage');

    const customValue = parseInt(customInput.value);
    if (customValue && customValue > 0 && customValue <= 200) {
        entriesPerPage = customValue;

        // Reset to first page and refresh data
        currentPage = 1;
        await searchData(true);

        // Update logger with feedback
        smartlpLogger.textContent = `Showing ${entriesPerPage} entries per page`;
        smartlpLogger.className = 'badge bg-info fs-6';

        // Clear feedback
        setTimeout(() => {
            smartlpLogger.textContent = '';
        }, 2000);
    } else {
        // Invalid input, revert to default
        customInput.value = '';
        entriesPerPage = 15;
        rowsSelect.value = '15';
        customInput.style.display = 'none';

        // Reset to first page and refresh data
        currentPage = 1;
        await searchData(true);

        // Update logger with feedback
        smartlpLogger.textContent = 'Invalid custom value. Using default (15)';
        smartlpLogger.className = 'badge bg-warning fs-6';

        // Clear feedback
        setTimeout(() => {
            smartlpLogger.textContent = '';
        }, 2000);
    }
}

// Initialize rows per page dropdown
function initializeRowsPerPage() {
    const rowsSelect = document.getElementById('rowsPerPage');
    const customInput = document.getElementById('customRowsInput');

    if (!rowsSelect) return;

    // Set the current entriesPerPage in the dropdown
    const currentValue = entriesPerPage.toString();
    if (['10', '15', '20', '50'].includes(currentValue)) {
        rowsSelect.value = currentValue;
        customInput.style.display = 'none';
    } else {
        rowsSelect.value = 'custom';
        customInput.value = entriesPerPage;
        customInput.style.display = 'block';
    }
}

// Ingestion Status Functions
function initializeIngestionStatus() {
    updateIngestionStatus();
    // Update status every 30 seconds
    setInterval(updateIngestionStatus, 30000);
}

function updateIngestionStatus() {
    fetch('/api/smartlp/ingestion/status')
        .then(response => response.json())
        .then(data => {
            displayIngestionStatus(data);
        })
        .catch(error => {
            console.error('Error fetching ingestion status:', error);
            displayIngestionStatus({
                ingestion_running: false,
                ingestion_enabled: false,
                active_siem: 'unknown',
                error: 'Status unavailable'
            });
        });
}

function displayIngestionStatus(status) {
    const siemStatus = document.getElementById('siemStatus');
    if (!siemStatus) return;

    let statusHtml = '';

    if (status.error) {
        statusHtml = `
            <div class="d-flex align-items-center gap-2">
                <span class="badge bg-secondary">
                    <i class="fa fa-exclamation-triangle me-1"></i>Status: Unavailable
                </span>
            </div>
        `;
    } else {
        const runningClass = status.ingestion_running ? 'bg-success' : 'bg-secondary';
        const runningIcon = status.ingestion_running ? 'fa-play' : 'fa-pause';
        const runningText = status.ingestion_running ? 'Running' : 'Stopped';

        const enabledClass = status.ingestion_enabled ? 'bg-primary' : 'bg-warning';
        const enabledText = status.ingestion_enabled ? 'Enabled' : 'Disabled';

        statusHtml = `
            <div class="d-flex align-items-center gap-2 flex-wrap">
                <span class="badge ${runningClass}" title="Ingestion Process Status">
                    <i class="fa ${runningIcon} me-1"></i>Ingestion: ${runningText}
                </span>
                <span class="badge bg-info" title="Active SIEM">
                    <i class="fa fa-database me-1"></i>SIEM: ${status.active_siem.toUpperCase()}
                </span>
                ${status.unmatched_entries !== undefined ? `
                    <span class="badge bg-warning text-dark" title="Unmatched Entries">
                        <i class="fa fa-exclamation me-1"></i>Unmatched: ${status.unmatched_entries}
                    </span>
                ` : ''}
                <div class="dropdown">
                    <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">
                        <i class="fa fa-cog"></i>
                    </button>
                    <ul class="dropdown-menu">
                        <li><a class="dropdown-item" href="#" onclick="startIngestion()">
                            <i class="fa fa-play me-2"></i>Start Ingestion
                        </a></li>
                        <li><a class="dropdown-item" href="#" onclick="stopIngestion()">
                            <i class="fa fa-stop me-2"></i>Stop Ingestion
                        </a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item" href="/settings">
                            <i class="fa fa-cog me-2"></i>Configure Settings
                        </a></li>
                    </ul>
                </div>
            </div>
        `;
    }

    siemStatus.innerHTML = statusHtml;
}

function startIngestion() {
    fetch('/api/smartlp/ingestion/start', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateIngestionStatus(); // Refresh status
            } else {
                console.error('Failed to start ingestion:', data.error);
            }
        })
        .catch(error => {
            console.error('Error starting ingestion:', error);
        });
}

function stopIngestion() {
    fetch('/api/smartlp/ingestion/stop', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateIngestionStatus(); // Refresh status
            } else {
                console.error('Failed to stop ingestion:', data.error);
            }
        })
        .catch(error => {
            console.error('Error stopping ingestion:', error);
        });
}

// --- End Rows Per Page Functionality ---