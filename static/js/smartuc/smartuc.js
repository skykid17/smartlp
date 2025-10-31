// --- Modern Modal Logic (Using Fetch API) ---
document.addEventListener('DOMContentLoaded', function () {
    // --- YAML Modal Logic ---
    const yamlModal = document.getElementById('yamlModal');
    if (yamlModal) {
        yamlModal.addEventListener('show.bs.modal', async function (event) {
            const button = event.relatedTarget;
            const ruleId = button.getAttribute('data-rule-id');
            const modal = this;
            const modalTitle = modal.querySelector('.modal-title');
            const yamlContent = modal.querySelector('#yamlContent');

            modalTitle.textContent = 'Loading Rule...';
            yamlContent.textContent = 'Loading...';

            try {
                const response = await fetch(`/api/rule/${encodeURIComponent(ruleId)}/content`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                modalTitle.textContent = data.title || 'Rule siemRule';

                // Create pre/code element for better formatting
                const preElement = document.createElement('pre');
                const codeElement = document.createElement('code');
                codeElement.textContent = data.content || '# Content not found';
                preElement.appendChild(codeElement);
                yamlContent.innerHTML = '';
                yamlContent.appendChild(preElement);

            } catch (error) {
                console.error("Error fetching rule content:", error);
                modalTitle.textContent = 'Error';
                yamlContent.textContent = 'Failed to load rule content.';
            }
        });
    }
    // --- End YAML Modal Logic ---

    // --- SIEM Rule Modal Logic ---
    const siemRuleModal = document.getElementById('siemRuleModal');
    if (siemRuleModal) {
        siemRuleModal.addEventListener('show.bs.modal', async function (event) {
            const button = event.relatedTarget;
            const ruleId = button.getAttribute('data-rule-id');
            const modal = this;
            const modalTitle = modal.querySelector('.modal-title');
            const siemRuleContent = modal.querySelector('#siemRuleContent');
            const activeSiem = sessionStorage.getItem("activeSiem") || "SIEM";

            modalTitle.textContent = `${activeSiem.charAt(0).toUpperCase() + activeSiem.slice(1)} Rule`;
            siemRuleContent.textContent = 'Loading...';

            try {
                const response = await fetch(`/api/rule/${encodeURIComponent(ruleId)}/${encodeURIComponent(activeSiem)}`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();

                // Create pre/code element for better formatting
                const preElement = document.createElement('pre');
                const codeElement = document.createElement('code');
                codeElement.textContent = data;
                preElement.appendChild(codeElement);
                siemRuleContent.innerHTML = '';
                siemRuleContent.appendChild(preElement);

            } catch (error) {
                console.error("Error fetching SIEM rule:", error);
                siemRuleContent.textContent = `Failed to load ${activeSiem} rule.`;
            }
        });
    }
    // --- End SIEM Rule Modal Logic ---

    // --- Go To Page Logic ---    // --- Go To Page Logic (Keep existing) ---
    const goToPageForm = document.getElementById('goToPageForm');
    const goToPageInput = document.getElementById('goToPageInput');

    if (goToPageForm && goToPageInput) {
        goToPageForm.addEventListener('submit', function (event) {
            event.preventDefault(); // Prevent default form submission

            // --- Get data from form attributes ---
            const totalPages = parseInt(goToPageForm.dataset.totalPages, 10);
            const baseUrl = goToPageForm.dataset.baseUrl; // e.g., "/smartuc"
            const perPage = goToPageForm.dataset.perPage;
            const search = goToPageForm.dataset.search;
            const mainType = goToPageForm.dataset.mainType;
            const subType = goToPageForm.dataset.subType;

            // --- Get and validate the input value ---
            const pageValue = parseInt(goToPageInput.value, 10);

            if (isNaN(pageValue) || pageValue < 1 || pageValue > totalPages) {
                alert(`Please enter a valid page number between 1 and ${totalPages}.`);
                goToPageInput.focus(); // Focus back on the input
                goToPageInput.select(); // Select the invalid text
                return; // Stop processing
            }

            // --- Construct the new URL with all parameters ---
            const params = new URLSearchParams();
            params.append('page', pageValue); // The target page
            params.append('per_page', perPage); // Preserve per_page

            // Add other parameters only if they have meaningful values
            if (search) {
                params.append('search', search);
            }
            if (mainType && mainType !== 'all') {
                params.append('main_type', mainType);
            }
            if (subType && subType !== 'all') {
                params.append('sub_type', subType);
            }

            // --- Navigate to the new URL ---
            window.location.href = `${baseUrl}?${params.toString()}`;
        });
    }
    // --- End Go To Page Logic ---

    // --- Initialize Visible IDs and Filters ---
    populateVisibleIds();

    // Make sure visibleIds is tracked after filters/search
    const filterSelects = document.querySelectorAll('#mainTypeFilter, #subTypeFilter');
    filterSelects.forEach(select => {
        select.addEventListener('change', function () {
            setTimeout(populateVisibleIds, 100);
        })
    });

    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function () {
            setTimeout(populateVisibleIds, 100);
        });
    }

    // --- Initialize Selection and Config Panel ---
    // Setup shared click-to-select functionality
    setupClickToSelect(smartucSelection, {
        tableBodyId: 'entryTableBody',
        rowSelector: '.rule-row',
        checkboxSelector: 'input[name="ruleSelect"]'
    });

    // Initialize rows per page dropdown
    initializeRowsPerPage();

}); // --- End DOMContentLoaded ---
// --- Selection Feature Integration ---
const smartucSelection = createSelectionModule({
    tableBodyId: 'entryTableBody',
    selectEnableSelector: '.selectEnable',
    loggerId: 'smartucLogger',
    storagePrefix: 'ruleIds', // Use ruleIds for SmartUC
    idLabel: 'rules', // Display "rules" in logger messages
    checkboxSelector: 'input[name="ruleSelect"]' // Use SmartUC-specific checkbox selector
});

// --- Config Panel Module Initialization (SmartUC) ---
const smartucConfigPanel = createSmartUCConfigPanel(smartucSelection);

// --- Config Panel Open Handler (always open and sync, never toggle/close) ---
function handleCreateConfig() {
    const popup = document.getElementById("popupBox");
    if (popup) popup.classList.remove("collapsed");
    // Update arrow direction
    const arrowBtn = document.querySelector(".arrow-btn i");
    if (arrowBtn) {
        arrowBtn.classList.remove("fa-chevron-up");
        arrowBtn.classList.add("fa-chevron-down");
    }
    smartucSelection.updateMainTableSelection();
    smartucConfigPanel.syncPanel();
}

// --- Selection and Config Panel Initialization (moved to main DOMContentLoaded) ---

// --- Function to populate visible IDs from server-rendered rules ---
function populateVisibleIds() {
    smartucSelection.visibleIds.clear();

    // Get all rule IDs from the current page
    document.querySelectorAll('input[type="checkbox"][name="ruleSelect"]').forEach(cb => {
        smartucSelection.visibleIds.add(cb.value);
    });

    // Check for hidden selections
    const ids = smartucSelection.ids;
    const hiddenCount = ids.length - ids.filter(id => smartucSelection.visibleIds.has(id)).length;
    const logger = document.getElementById('smartucLogger');
    if (hiddenCount > 0) {
        logger.textContent = `Selected ${ids.length} rules (${hiddenCount} filtered out)`;
    }

    // Update the selection UI to reflect current state
    smartucSelection.updateSelectionUI();
}

// --- Rows Per Page Functionality ---
function changeRowsPerPage() {
    const rowsSelect = document.getElementById('rowsPerPage');
    const customInput = document.getElementById('customRowsInput');

    if (rowsSelect.value === 'custom') {
        customInput.style.display = 'block';
        customInput.focus();
        return;
    } else {
        customInput.style.display = 'none';
        navigateWithRowsPerPage(parseInt(rowsSelect.value));
    }
}

function applyCustomRows() {
    const customInput = document.getElementById('customRowsInput');
    const rowsSelect = document.getElementById('rowsPerPage');

    const customValue = parseInt(customInput.value);
    if (customValue && customValue > 0 && customValue <= 200) {
        navigateWithRowsPerPage(customValue);
    } else {
        // Invalid input, revert to current per_page
        const goToPageForm = document.getElementById('goToPageForm');
        const currentPerPage = parseInt(goToPageForm.dataset.perPage) || 10;

        rowsSelect.value = [10, 15, 20, 50].includes(currentPerPage) ? currentPerPage.toString() : 'custom';
        if ([10, 15, 20, 50].includes(currentPerPage)) {
            customInput.value = '';
            customInput.style.display = 'none';
        } else {
            customInput.value = currentPerPage;
            customInput.blur();
        }
        alert('Invalid custom value. Please enter a number between 1 and 200.');
    }
}

function navigateWithRowsPerPage(perPage) {
    const goToPageForm = document.getElementById('goToPageForm');
    const baseUrl = goToPageForm.dataset.baseUrl;
    const search = goToPageForm.dataset.search;
    const mainType = goToPageForm.dataset.mainType;
    const subType = goToPageForm.dataset.subType;

    // Construct the new URL with all parameters, starting from page 1
    const params = new URLSearchParams();
    params.append('page', 1);
    params.append('per_page', perPage);

    // Add other parameters only if they have meaningful values
    if (search) {
        params.append('search', search);
    }
    if (mainType && mainType !== 'all') {
        params.append('main_type', mainType);
    }
    if (subType && subType !== 'all') {
        params.append('sub_type', subType);
    }

    smartucSelection.updateSelectionUI();
    window.location.href = `${baseUrl}?${params.toString()}`;
}

// --- Initialize Rows Per Page Dropdown ---
function initializeRowsPerPage() {
    const rowsSelect = document.getElementById('rowsPerPage');
    const customInput = document.getElementById('customRowsInput');

    if (!rowsSelect) return;

    // Get current per_page from the form data
    const goToPageForm = document.getElementById('goToPageForm');
    const currentPerPage = parseInt(goToPageForm?.dataset.perPage) || 10;

    // Set the dropdown to the current value
    if (['10', '15', '20', '50'].includes(currentPerPage.toString())) {
        rowsSelect.value = currentPerPage.toString();
        if (customInput) customInput.style.display = 'none';
    } else {
        rowsSelect.value = 'custom';
        if (customInput) {
            customInput.value = currentPerPage;
            customInput.style.display = 'block';
        }
    }
}
// --- End Rows Per Page Functionality ---

// --- Deploy Function for SmartUC ---
async function deploy() {
    // Use the shared deployment function from utils.js
    await deployWithFeedback(smartucSelection.ids, 'smartuc', {
        deployBtnSelector: '#configModal button[onclick="deploy()"]',
        feedbackDivId: 'deploymentFeedback',
        messageDivId: 'deploymentMessage',
        configModalId: 'configModal',
        onSuccess: (result) => {
            smartucSelection.togglePanel() // Close panel
            console.log('SmartUC deployment successful:', result);
        },
        onError: (error, errorMessage) => {
            // SmartUC-specific error handling if needed
            console.error('SmartUC deployment failed:', error);
        }
    });
}
// --- End Deploy Function for SmartUC ---

