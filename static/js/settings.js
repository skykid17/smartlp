// === Settings related variables ===
let siemsData = {};
let llmEndpointsData = {};
let modelArray = [];
let previousActiveSiem = null; // Track previous SIEM selection
let originalSettings = {}; // Track original settings for change detection
let originalModels = []; // Track original models for change detection
let hasUnsavedChanges = false; // Track if there are unsaved changes

// Human-friendly field names mapping
const fieldDisplayNames = {
    'activeSiem': 'Active SIEM',
    'activeLlmEndpoint': 'Active LLM Endpoint',
    'activeLlm': 'Active LLM Model',
    'ingestFrequency': 'Ingestion Frequency',
    'similarityThreshold': 'Similarity Threshold',
    'similarityCheck': 'Similarity Check',
    'ingestOn': 'Log Ingestion',
    'ingestAlgoVersion': 'Parsing Algorithm Version',
    'fixCount': 'Regex Fix Count',
    'searchIndex': 'Search Index',
    'searchEntryCount': 'Search Entry Count',
    'searchQuery': 'Search Query',
    'models': 'LLM Models'
};

const elements = [
    "activeSiem", "searchIndex", "searchEntryCount", "searchQuery", "ingestFrequency", "similarityThreshold", "siem",
    "activeLlmEndpoint", "llmUrl", "activeLlm", "fixCount", "models", "similarityCheck", "ingestOn", "similarityThresholdGroup",
    "ingestGroup", "ingestAlgoVersion",
];

// Utility function to safely add event listeners
function addEventIfExists(element, event, handler) {
    if (element && typeof element.addEventListener === 'function') {
        element.addEventListener(event, handler);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // Cache DOM elements globally
    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            window[id] = element;
        } else {
            console.warn(`Element with ID '${id}' not found`);
        }
    });

    // Also cache siem element for SIEM functionality
    const siemElement = document.getElementById('siem');
    if (siemElement) {
        window.siem = siemElement;
    }

    // Initialize settings
    getSettings();

    // Event listeners
    addEventIfExists(window.siem, "change", toggleSIEMFields);
    addEventIfExists(window.activeLlmEndpoint, "change", toggleActiveLlmField);
    addEventIfExists(window.similarityCheck, "change", () => toggleIngestFields(window.similarityCheck, window.similarityThresholdGroup));
    addEventIfExists(window.ingestOn, "change", () => toggleIngestFields(window.ingestOn, window.ingestGroup));

    // Add warning modal event listener for activeSiem
    addEventIfExists(window.activeSiem, "change", handleActiveSiemChange);

    // Add change detection listeners to all form elements
    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            if (element.type === 'checkbox') {
                element.addEventListener('change', trackChanges);
            } else {
                element.addEventListener('input', trackChanges);
                element.addEventListener('change', trackChanges);
            }
        }
    });

    // Add navigation warning
    window.addEventListener('beforeunload', handleBeforeUnload);

    // Override navigation links to check for unsaved changes
    document.addEventListener('click', handleLinkClick);

    // Modal button event listeners
    const confirmSiemChange = document.getElementById("confirmSiemChange");
    const cancelSiemChange = document.getElementById("cancelSiemChange");

    if (confirmSiemChange) {
        confirmSiemChange.addEventListener("click", () => {
            if (window.activeSiem) {
                previousActiveSiem = window.activeSiem.value;
            }
        });
    }

    if (cancelSiemChange) {
        cancelSiemChange.addEventListener("click", () => {
            if (window.activeSiem && previousActiveSiem !== null) {
                window.activeSiem.value = previousActiveSiem;
            }
        });
    }

    validateInputs(["similarityThreshold", "fixCount", "ingestFrequency"]);
    validateElasticQuery();
});

// SIEM status indicators removed - using new ingestion status in SmartLP


// === Fetch settings from backend ===
async function getSettings() {
    try {
        const response = await fetch('/api/settings');
        const data = await response.json();
        siemsData = Object.fromEntries(data.siems.map(s => [s.id, s]));
        llmEndpointsData = Object.fromEntries(data.llmEndpoints.map(l => [l.id, l]));
        sessionStorage.setItem('activeSiem', data.settings.activeSiem);
        sessionStorage.setItem('activeLlmEndpoint', data.settings.activeLlmEndpoint);
        sessionStorage.setItem('activeLlm', data.settings.activeLlm);
        if (window.location.pathname === "/settings") {
            setDropdown(siemsData, siem);
            setDropdown(siemsData, activeSiem);
            setDropdown(llmEndpointsData, activeLlmEndpoint);
            setDropdown(llmEndpointsData, activeLlm);

            // Create LLM endpoint tabs
            createLlmEndpointTabs();

            // Set values for SmartLP settings
            Object.entries(data.settings).forEach(([key, value]) => {
                const el = document.getElementById(key);
                if (el) {
                    if (el.type === "checkbox") {
                        // Handle checkbox specially
                        el.checked = value === true || value === "true";
                    } else {
                        el.value = value;
                    }
                }
            });

            // Select the active endpoint from settings and load its models
            const activeEndpointId = data.settings.activeLlmEndpoint;
            if (activeEndpointId && llmEndpointsData[activeEndpointId]) {
                selectLlmEndpoint(activeEndpointId);
            }
            toggleActiveLlmField();
            toggleSIEMFields();
            toggleIngestFields(ingestOn, ingestGroup);
            toggleIngestFields(similarityCheck, similarityThresholdGroup);

            // Store original settings after loading for change detection
            storeOriginalSettings();
        }
    } catch (error) {
        console.error("Error fetching settings:", error);
    }
}

function toggleIngestFields(toggleSwitch, targetGroup) {
    if (toggleSwitch) {
        // Only toggle visibility based on checkbox state
        targetGroup.style.display = toggleSwitch.checked ? "block" : "none";
    }
}

// === toggle SIEM-related fields ===
function toggleSIEMFields() {
    const siemElement = window.siem;
    if (!siemElement) return;

    const selectedSiemData = siemsData[siemElement.value];
    const searchIndexGroup = document.getElementById("searchIndexGroup");
    const searchEntryGroup = document.getElementById("searchEntryGroup");

    if (!selectedSiemData) return;

    if (window.searchIndex) window.searchIndex.value = selectedSiemData.searchIndex || '';
    if (window.searchQuery) window.searchQuery.value = selectedSiemData.searchQuery || '';
    if (window.searchEntryCount) window.searchEntryCount.value = selectedSiemData.searchEntryCount || '';

    if (siemElement.value === "splunk") {
        if (searchIndexGroup) searchIndexGroup.style.display = "none";
        if (searchEntryGroup) searchEntryGroup.style.display = "none";
    } else {
        if (searchIndexGroup) searchIndexGroup.style.display = "block";
        if (searchEntryGroup) searchEntryGroup.style.display = "block";
    }
}

// === LLM Endpoint Tab Management ===
let currentLlmEndpoint = null;

function createLlmEndpointTabs() {
    const tabContainer = document.getElementById('llmEndpointTabs');
    if (!tabContainer) return;

    tabContainer.innerHTML = '';

    // Create tabs for existing endpoints
    Object.values(llmEndpointsData).forEach(endpoint => {
        const tab = document.createElement('button');
        tab.className = 'btn btn-outline-primary btn-sm';
        tab.textContent = endpoint.name || endpoint.id;
        tab.onclick = () => selectLlmEndpoint(endpoint.id);
        tab.dataset.endpointId = endpoint.id;
        tabContainer.appendChild(tab);
    });

    // Create "+" tab for adding new endpoint
    const addTab = document.createElement('button');
    addTab.className = 'btn btn-outline-success btn-sm';
    addTab.innerHTML = '<i class="fa fa-plus"></i>';
    addTab.onclick = showAddEndpointModal;
    addTab.title = 'Add New LLM Endpoint';
    tabContainer.appendChild(addTab);

    // Select first endpoint by default
    if (Object.keys(llmEndpointsData).length > 0) {
        const firstEndpoint = Object.keys(llmEndpointsData)[0];
        selectLlmEndpoint(firstEndpoint);
    }
}

function selectLlmEndpoint(endpointId) {
    currentLlmEndpoint = endpointId;

    // Update active tab appearance
    const tabContainer = document.getElementById('llmEndpointTabs');
    if (tabContainer) {
        tabContainer.querySelectorAll('button').forEach(btn => {
            if (btn.dataset.endpointId === endpointId) {
                btn.classList.remove('btn-outline-primary');
                btn.classList.add('btn-primary');
            } else if (btn.dataset.endpointId) {
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-outline-primary');
            }
        });
    }

    // Load endpoint data
    const selectedLlm = llmEndpointsData[endpointId];
    if (!selectedLlm) return;

    // Update URL field
    if (window.llmUrl) {
        window.llmUrl.value = selectedLlm.url || '';
    }

    // Update modelArray with current endpoint's models
    modelArray = Array.isArray(selectedLlm.models) ? [...selectedLlm.models] : [];
    console.log(`Loaded models for ${endpointId}:`, modelArray);
    setModelList();
}

function showAddEndpointModal() {
    const modalHtml = `
        <div class="modal fade" id="addEndpointModal" tabindex="-1" aria-labelledby="addEndpointModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="addEndpointModalLabel">
                            <i class="fa fa-plus me-2"></i>Add New LLM Endpoint
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group mb-3">
                            <label for="newEndpointId" class="form-label">Endpoint ID:</label>
                            <input type="text" id="newEndpointId" class="form-control" placeholder="e.g., openai, anthropic">
                            <div class="form-text">Unique identifier for this endpoint</div>
                        </div>
                        <div class="form-group mb-3">
                            <label for="newEndpointName" class="form-label">Endpoint Name:</label>
                            <input type="text" id="newEndpointName" class="form-control" placeholder="e.g., OpenAI GPT">
                            <div class="form-text">Display name for the endpoint</div>
                        </div>
                        <div class="form-group mb-3">
                            <label for="newEndpointUrl" class="form-label">API URL:</label>
                            <textarea id="newEndpointUrl" class="form-control" placeholder="https://api.example.com/v1/chat/completions"></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="addNewEndpoint()">Add Endpoint</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if present
    const existingModal = document.getElementById('addEndpointModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const addEndpointModal = new bootstrap.Modal(document.getElementById('addEndpointModal'));
    addEndpointModal.show();
}

function addNewEndpoint() {
    const idInput = document.getElementById('newEndpointId');
    const nameInput = document.getElementById('newEndpointName');
    const urlInput = document.getElementById('newEndpointUrl');

    if (!idInput || !nameInput || !urlInput) return;

    const id = idInput.value.trim();
    const name = nameInput.value.trim();
    const url = urlInput.value.trim();

    if (!id || !name || !url) {
        alert('Please fill in all fields');
        return;
    }

    if (llmEndpointsData[id]) {
        alert('An endpoint with this ID already exists');
        return;
    }

    // Add new endpoint to local data
    llmEndpointsData[id] = {
        id: id,
        name: name,
        url: url,
        models: []
    };

    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('addEndpointModal'));
    if (modal) modal.hide();

    // Refresh tabs and select new endpoint
    createLlmEndpointTabs();
    selectLlmEndpoint(id);

    // Mark as changed
    trackChanges();
}

// === toggle activeLlm dropdown from activeLlmEndpoint ===
function toggleActiveLlmField() {
    const activeLlmEndpointElement = window.activeLlmEndpoint;
    const activeLlmElement = window.activeLlm;

    if (!activeLlmEndpointElement || !activeLlmElement) return;

    // Handle primary LLM dropdown
    setDropdown(llmEndpointsData, activeLlmElement);
    if (activeLlmEndpointElement.value === sessionStorage.getItem("activeLlmEndpoint")) {
        activeLlmElement.value = sessionStorage.getItem("activeLlm");
    }
}


// === set model list + dropdown ===
function setModelList() {
    const container = document.getElementById("models");
    if (!container) return;

    container.innerHTML = "";

    modelArray.forEach((model, index) => {
        const modelDiv = document.createElement("div");
        modelDiv.className = "input-group mb-2";
        modelDiv.innerHTML = `
            <input type="text" name="model${index}" class="form-control" value="${model}" disabled>
            <button class="btn btn-outline-secondary" type="button" onclick="testModel('${model}')">
                Test
            </button>
            <button class="btn btn-outline-danger" type="button" onclick="removeModel(${index})">
                <i class="fa fa-minus"></i>
            </button>
        `;
        container.appendChild(modelDiv);
    });
}

// === Add and remove model logic ===
function addModel() {
    const input = document.getElementById("newModelInput");
    const value = input.value.trim();
    if (value && !modelArray.includes(value)) {
        modelArray.push(value);
        input.value = "";
        console.log(`Added model: ${value}. Current models:`, modelArray);
        setModelList();
        trackChanges(); // Trigger change detection
    }
}

function removeModel(index) {
    const removedModel = modelArray[index];
    modelArray.splice(index, 1);
    console.log(`Removed model: ${removedModel}. Current models:`, modelArray);
    setModelList();
    trackChanges(); // Trigger change detection
}

// === Save settings to backend ===
async function saveSettings() {
    try {
        const settingChangeModal = new bootstrap.Modal(document.getElementById('settingChangeModal'));
        const settings = {};

        // Collect settings from form elements
        elements.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                if (el.type === "checkbox") {
                    settings[id] = el.checked;
                } else {
                    settings[id] = el.value;
                }
            }
        });

        // Add models array and LLM endpoint data if we have a current endpoint selected
        if (currentLlmEndpoint) {
            settings["llmEndpoint"] = currentLlmEndpoint;
            settings["models"] = modelArray;

            // Include any new endpoints that were created
            settings["llmEndpoints"] = llmEndpointsData;
        }

        console.log("Sending settings data:", settings);

        // Show loading state
        const saveButton = document.getElementById("saveSettingsButton");
        if (saveButton) {
            const originalText = saveButton.textContent;
            saveButton.textContent = "Saving...";
            saveButton.disabled = true;
        }

        const response = await fetch('/api/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });

        const data = await response.json();

        // Update session storage
        if (settings.activeSiem) sessionStorage.setItem("activeSiem", settings.activeSiem);
        if (settings.activeLlmEndpoint) sessionStorage.setItem("activeLlmEndpoint", settings.activeLlmEndpoint);
        if (settings.activeLlm) sessionStorage.setItem("activeLlm", settings.activeLlm);

        // Show results in modal
        const modalTitle = document.querySelector("#settingChangeModal .modal-title");
        const modalBody = document.querySelector("#settingChangeModal .modal-body");
        const modalButton = document.querySelector("#settingChangeModal .modal-footer .btn");

        if (modalTitle && modalBody && modalButton) {
            // Get actual changes made
            const actualChanges = detectChanges();

            if (actualChanges.length > 0) {
                const formattedChanges = actualChanges.map(change => {
                    const fieldName = change.displayName || fieldDisplayNames[change.field] || change.field;
                    if (change.field === 'ingestOn' || change.field === 'similarityCheck') {
                        return `${fieldName}: ${change.newValue ? 'Enabled' : 'Disabled'}`;
                    } else {
                        return `${fieldName}: ${change.newValue}`;
                    }
                }).join('\n');

                modalTitle.innerText = "Settings Updated Successfully!";
                modalBody.innerHTML = `<div class="alert alert-success"><strong>Changes Applied:</strong><br>${formattedChanges.replace(/\n/g, '<br>')}</div>`;
                modalButton.classList.remove("btn-danger");
                modalButton.classList.add("btn-success");

                // Reset change tracking after successful save
                updateOriginalSettings();
                hasUnsavedChanges = false;
                updateSaveButtonState();
            } else {
                modalTitle.innerText = "No Changes Made";
                modalBody.innerHTML = `<div class="alert alert-info">No settings were modified.</div>`;
                modalButton.classList.remove("btn-success");
                modalButton.classList.add("btn-info");
            }
            settingChangeModal.show();
        }

        // SIEM status removed

        // Reset save button
        if (saveButton) {
            saveButton.textContent = "Save";
            saveButton.disabled = false;
        }

    } catch (error) {
        console.error("Error saving settings:", error);

        // Reset save button on error
        const saveButton = document.getElementById("saveSettingsButton");
        if (saveButton) {
            saveButton.textContent = "Save";
            saveButton.disabled = false;
        }

        // Show error modal
        const modalTitle = document.querySelector("#settingChangeModal .modal-title");
        const modalBody = document.querySelector("#settingChangeModal .modal-body");
        if (modalTitle && modalBody) {
            modalTitle.innerText = "Error Saving Settings";
            modalBody.innerText = `Failed to save settings: ${error.message}`;
            const settingChangeModal = new bootstrap.Modal(document.getElementById('settingChangeModal'));
            settingChangeModal.show();
        }
    }
}

// === Change Detection Functions ===
function storeOriginalSettings() {
    // Store the original settings values for change detection
    originalSettings = {};
    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            if (element.type === 'checkbox') {
                originalSettings[id] = element.checked;
            } else {
                originalSettings[id] = element.value;
            }
        }
    });

    // Store original models array
    originalModels = [...modelArray];

    hasUnsavedChanges = false;
    updateSaveButtonState();
}

function updateOriginalSettings() {
    // Update original settings after successful save
    storeOriginalSettings();
}

function trackChanges() {
    // Track changes to form elements
    hasUnsavedChanges = false;

    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element && originalSettings.hasOwnProperty(id)) {
            let currentValue = element.type === 'checkbox' ? element.checked : element.value;
            if (currentValue !== originalSettings[id]) {
                hasUnsavedChanges = true;
            }
        }
    });

    // Check for model changes
    if (hasModelChanges()) {
        hasUnsavedChanges = true;
    }

    updateSaveButtonState();
}

function detectChanges() {
    // Detect actual changes made to settings
    const changes = [];

    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element && originalSettings.hasOwnProperty(id)) {
            let currentValue = element.type === 'checkbox' ? element.checked : element.value;
            if (currentValue !== originalSettings[id]) {
                changes.push({
                    field: id,
                    oldValue: originalSettings[id],
                    newValue: currentValue
                });
            }
        }
    });

    // Check for model changes
    if (hasModelChanges()) {
        const endpointName = currentLlmEndpoint ? (llmEndpointsData[currentLlmEndpoint]?.name || currentLlmEndpoint) : 'Unknown Endpoint';
        changes.push({
            field: 'models',
            oldValue: originalModels.join(', ') || 'None',
            newValue: modelArray.join(', ') || 'None',
            displayName: `LLM Models (${endpointName})`
        });
    }

    return changes;
}

function hasModelChanges() {
    // Check if models have changed from original
    if (originalModels.length !== modelArray.length) {
        return true;
    }

    // Check if all models are the same and in the same order
    for (let i = 0; i < originalModels.length; i++) {
        if (originalModels[i] !== modelArray[i]) {
            return true;
        }
    }

    return false;
}

function updateSaveButtonState() {
    // Update save button appearance and enabled state based on unsaved changes
    const saveButton = document.getElementById('saveSettingsButton');
    if (saveButton) {
        if (hasUnsavedChanges) {
            saveButton.disabled = false;
        } else {
            saveButton.disabled = true;
        }
    }
}

function handleBeforeUnload(event) {
    // Handle navigation away from page with unsaved changes
    if (hasUnsavedChanges) {
        event.preventDefault();
        event.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return 'You have unsaved changes. Are you sure you want to leave?';
    }
}

function handleLinkClick(event) {
    // Handle clicks on navigation links
    const target = event.target.closest('a');
    if (!target || !hasUnsavedChanges) return;

    // Check if it's a navigation link (not settings modal links or external links)
    const href = target.getAttribute('href');
    if (href && href.startsWith('/') && !href.includes('#') && href !== '/settings') {
        event.preventDefault();
        window.pendingNavigation = href;
        showUnsavedChangesModal();
    }
}

function showUnsavedChangesModal() {
    // Show modal warning about unsaved changes
    const changes = detectChanges();
    if (changes.length === 0) return;

    const formattedChanges = changes.map(change => {
        const fieldName = change.displayName || fieldDisplayNames[change.field] || change.field;
        if (change.field === 'ingestOn' || change.field === 'similarityCheck') {
            return `• ${fieldName}: ${change.newValue ? 'Enabled' : 'Disabled'}`;
        } else {
            return `• ${fieldName}: ${change.newValue}`;
        }
    }).join('\n');

    const modalHtml = `
        <div class="modal fade" id="unsavedChangesModal" tabindex="-1" aria-labelledby="unsavedChangesModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-warning">
                        <h5 class="modal-title" id="unsavedChangesModalLabel">
                            <i class="fa fa-exclamation-triangle me-2"></i>Unsaved Changes
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-warning">
                            <strong>You have unsaved changes that will be lost if you leave this page:</strong>
                        </div>
                        <div class="mb-3">
                            <pre class="bg-light p-2 rounded">${formattedChanges}</pre>
                        </div>
                        <p>What would you like to do?</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" onclick="saveAndContinue()">
                            <i class="fa fa-save me-2"></i>Save & Continue
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="discardAndContinue()">
                            <i class="fa fa-trash me-2"></i>Discard Changes
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if present
    const existingModal = document.getElementById('unsavedChangesModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const unsavedChangesModal = new bootstrap.Modal(document.getElementById('unsavedChangesModal'));
    unsavedChangesModal.show();
}

async function saveAndContinue() {
    // Save changes and continue navigation
    await saveSettings();
    const modal = bootstrap.Modal.getInstance(document.getElementById('unsavedChangesModal'));
    if (modal) modal.hide();

    // Navigate to pending URL if there is one
    if (window.pendingNavigation) {
        window.location.href = window.pendingNavigation;
        window.pendingNavigation = null;
    }
}

function discardAndContinue() {
    // Discard changes and continue navigation
    hasUnsavedChanges = false;
    const modal = bootstrap.Modal.getInstance(document.getElementById('unsavedChangesModal'));
    if (modal) modal.hide();

    // Reset form to original values
    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element && originalSettings.hasOwnProperty(id)) {
            if (element.type === 'checkbox') {
                element.checked = originalSettings[id];
            } else {
                element.value = originalSettings[id];
            }
        }
    });

    updateSaveButtonState();

    // Navigate to pending URL if there is one
    if (window.pendingNavigation) {
        window.location.href = window.pendingNavigation;
        window.pendingNavigation = null;
    }
}

function cancelNavigation() {
    // Cancel pending navigation
    window.pendingNavigation = null;
}

// === Input validation ===
function validateInputs(ids) {
    ids.forEach(id => {
        const field = document.getElementById(id);
        const errorDiv = document.getElementById(`${id}Error`);
        if (!field || !errorDiv) return;

        field.addEventListener("input", () => {
            const min = parseFloat(field.min);
            const max = parseFloat(field.max);
            const value = parseFloat(field.value);

            if (isNaN(value) || value < min || value > max) {
                field.value = Math.min(Math.max(value, min), max);
                errorDiv.innerHTML = `<div class="alert alert-danger alert-sm">${field.previousElementSibling.textContent} must be between ${min} and ${max}</div>`;
            } else {
                errorDiv.innerHTML = "";
            }
        });
    });
}

// === JSON validation for Elastic ===
function validateElasticQuery() {
    searchQuery?.addEventListener("input", () => {
        const errorDiv = document.getElementById("searchQueryLogger");
        if (siem?.value === "elastic") {
            try {
                JSON.parse(searchQuery.value);
                errorDiv.innerHTML = "";
            } catch (e) {
                errorDiv.innerHTML = `<div class="alert alert-danger alert-sm">Invalid JSON in Search Query: ${e.message}</div>`;
            }
        } else {
            errorDiv.innerHTML = "";
        }
    });
}

function setDropdown(data, dropdownElement) {
    if (!dropdownElement) return;

    dropdownElement.innerHTML = ""; // Clear existing options

    // Handle model dropdowns specially
    if (dropdownElement === window.activeLlm) {
        const endpointElement = window.activeLlmEndpoint;
        if (endpointElement) {
            const endpointValue = endpointElement.value;
            if (data[endpointValue] && Array.isArray(data[endpointValue].models)) {
                const models = data[endpointValue].models || [];
                models.forEach(model => {
                    const option = document.createElement("option");
                    option.value = model;
                    option.textContent = model;
                    dropdownElement.appendChild(option);
                });
            }
        }
        return;
    }

    // Handle regular dropdowns
    Object.values(data).forEach(item => {
        const option = document.createElement("option");
        option.value = item.id; // Assuming `id` is a unique identifier
        option.textContent = item.name; // Assuming `name` is a human-readable name
        dropdownElement.appendChild(option);
    });
}

async function testModel(model) {
    const testModelLogger = document.getElementById("testModelLogger");
    if (!testModelLogger) return;

    try {
        testModelLogger.innerHTML = `<div class="alert alert-primary" role="alert">Testing ${model}...</div>`;

        const llmUrlElement = window.llmUrl;

        if (!llmUrlElement) {
            testModelLogger.innerHTML = `<div class="alert alert-danger" role="alert">Missing LLM URL element</div>`;
            return;
        }

        if (!currentLlmEndpoint) {
            testModelLogger.innerHTML = `<div class="alert alert-danger" role="alert">No LLM endpoint selected. Please select an endpoint first.</div>`;
            return;
        }

        if (!llmUrlElement.value.trim()) {
            testModelLogger.innerHTML = `<div class="alert alert-danger" role="alert">LLM URL is empty. Please enter a valid API URL.</div>`;
            return;
        }

        const response = await fetch("/api/query_llm", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                task: "test",
                model: model,
                url: llmUrlElement.value,
                llmEndpoint: currentLlmEndpoint
            })
        });

        const data = await response.json();

        if (data.status_code === 200) {
            testModelLogger.innerHTML = `<div class="alert alert-success" role="alert">Success for ${model}</div>`;
        } else {
            const errorMsg = data.error?.error || "Unknown error";
            testModelLogger.innerHTML = `<div class="alert alert-danger" role="alert">Error for ${model}: ${errorMsg}</div>`;
        }
    } catch (error) {
        testModelLogger.innerHTML = `<div class="alert alert-danger" role="alert">Network error testing ${model}: ${error.message}</div>`;
    }
}

async function testConnection() {
    const connectionTestLogger = document.getElementById("connectionTestLogger");
    const siemElement = window.siem;

    if (!connectionTestLogger) {
        console.error('Connection test logger element not found');
        return;
    }

    // Test all SIEMs by default, or specific one if selected
    const selectedSiem = siemElement && siemElement.value ? siemElement.value : 'all';

    // Show loading state
    connectionTestLogger.innerHTML = '<div class="alert alert-info"><i class="fa fa-spinner fa-spin me-2"></i>Testing SIEM connections...</div>';

    try {
        const response = await fetch('/api/test_connection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                siem: selectedSiem
            })
        });

        const result = await response.json();

        // Handle single SIEM response
        if (result.status) {
            if (result.status === 'connected') {
                let detailsHtml = '';
                if (result.details && Object.keys(result.details).length > 0) {
                    detailsHtml = '<br><small class="text-muted">';
                    Object.entries(result.details).forEach(([key, value]) => {
                        if (key !== 'info_error' && key !== 'error') {
                            detailsHtml += `<strong>${key}:</strong> ${value} `;
                        }
                    });
                    detailsHtml += '</small>';
                }
                connectionTestLogger.innerHTML = `<div class="alert alert-success"><i class="fa fa-check me-2"></i>${result.message}${detailsHtml}</div>`;
            } else {
                connectionTestLogger.innerHTML = `<div class="alert alert-danger"><i class="fa fa-times me-2"></i>${result.message}</div>`;
            }
        }
        // Handle multiple SIEM responses
        else {
            let resultHtml = '<div class="mb-3"><h6>SIEM Connection Test Results:</h6>';

            // Check if we have results for multiple SIEMs
            const siems = ['elastic', 'splunk'];
            let hasResults = false;

            siems.forEach(siem => {
                if (result[siem]) {
                    hasResults = true;
                    const siemResult = result[siem];
                    let alertClass = 'alert-secondary';
                    let icon = 'fa-question';

                    if (siemResult.status === 'connected') {
                        alertClass = 'alert-success';
                        icon = 'fa-check';
                    } else if (siemResult.status === 'failed') {
                        alertClass = 'alert-warning';
                        icon = 'fa-exclamation-triangle';
                    } else if (siemResult.status === 'error') {
                        alertClass = 'alert-danger';
                        icon = 'fa-times';
                    }

                    let detailsHtml = '';
                    if (siemResult.details && Object.keys(siemResult.details).length > 0) {
                        detailsHtml = '<br><small class="text-muted">';
                        Object.entries(siemResult.details).forEach(([key, value]) => {
                            if (key !== 'info_error' && key !== 'error') {
                                // Special formatting for SSL-related fields
                                if (key === 'ssl_verified') {
                                    const sslStatus = value ? 'Enabled' : 'Disabled';
                                    const sslIcon = value ? '🔒' : '🔓';
                                    detailsHtml += `<strong>SSL Verification:</strong> ${sslIcon} ${sslStatus} `;
                                } else if (key === 'cert_path' && value !== 'Unknown') {
                                    detailsHtml += `<strong>Certificate:</strong> ${value} `;
                                } else if (key !== 'cert_path' || value !== 'Unknown') {
                                    detailsHtml += `<strong>${key}:</strong> ${value} `;
                                }
                            }
                        });
                        detailsHtml += '</small>';
                    }

                    resultHtml += `
                        <div class="alert ${alertClass} mb-2">
                            <i class="fa ${icon} me-2"></i>
                            <strong>${siem.toUpperCase()}:</strong> ${siemResult.message}
                            ${detailsHtml}
                        </div>
                    `;
                }
            });

            if (!hasResults) {
                resultHtml += '<div class="alert alert-warning"><i class="fa fa-exclamation-triangle me-2"></i>No SIEM results received</div>';
            }

            resultHtml += '</div>';
            connectionTestLogger.innerHTML = resultHtml;
        }

    } catch (error) {
        console.error('Connection test error:', error);
        connectionTestLogger.innerHTML = `<div class="alert alert-danger"><i class="fa fa-times me-2"></i>Connection test failed: ${error.message}</div>`;
    }
}

async function testQuery() {
    const searchQueryLogger = document.getElementById("searchQueryLogger");
    if (!searchQueryLogger) return;

    try {
        searchQueryLogger.innerHTML = `<div class="alert alert-primary" role="alert">Testing query...</div>`;

        const searchQueryElement = window.searchQuery;
        const siemElement = window.siem;
        const searchIndexElement = window.searchIndex;
        const searchEntryCountElement = window.searchEntryCount;

        if (!searchQueryElement || !siemElement) {
            searchQueryLogger.innerHTML = `<div class="alert alert-danger" role="alert">Missing required query parameters</div>`;
            return;
        }

        const response = await fetch("/api/test_query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                searchQuery: searchQueryElement.value,
                siem: siemElement.value,
                searchIndex: searchIndexElement?.value || "",
                entriesCount: searchEntryCountElement?.value || "10"
            })
        });

        const data = await response.json();

        if (data.status_code === 200) {
            searchQueryLogger.innerHTML = `<div class="alert alert-success" role="alert">Query test successful</div>`;
        } else {
            const errorMsg = data.error || "Unknown error";
            searchQueryLogger.innerHTML = `<div class="alert alert-danger" role="alert">Query test failed: ${errorMsg}</div>`;
        }
    } catch (error) {
        searchQueryLogger.innerHTML = `<div class="alert alert-danger" role="alert">Network error testing query: ${error.message}</div>`;
    }
}

// === Handle activeSiem change with warning ===
function handleActiveSiemChange() {
    const modalElement = document.getElementById('siemChangeWarningModal');
    if (modalElement) {
        const siemChangeWarningModal = new bootstrap.Modal(modalElement);
        siemChangeWarningModal.show();
    }
}