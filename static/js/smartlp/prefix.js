/**
 * SmartLP Prefix Management JavaScript
 * Handles loading, adding, updating, and deleting prefix regex entries
 */

let prefixArray = [];
let currentPage = 1;
const entriesPerPage = 10;
const visiblePageCount = 5;

document.addEventListener("DOMContentLoaded", () => {
    // Only initialize if we're on the smartlp prefix page
    if (window.location.pathname === "/smartlp/prefix") {
        initializePrefixPage();
    }
});

/**
 * Initialize the prefix page
 */
function initializePrefixPage() {
    try {
        // Load prefixes from backend
        loadPrefixes();
        
        // Add event listeners
        const addButton = document.getElementById("addPrefixBtn");
        const inputField = document.getElementById("newPrefixInput");
        
        if (addButton) {
            addButton.addEventListener("click", addPrefix);
        }
        
        if (inputField) {
            inputField.addEventListener("keypress", (e) => {
                if (e.key === "Enter") {
                    addPrefix();
                }
            });
        }
        
        console.log("Prefix page initialized successfully");
    } catch (error) {
        console.error("Error initializing prefix page:", error);
        showPrefixError("Failed to initialize page");
    }
}

/**
 * Load prefixes from backend API
 */
async function loadPrefixes() {
    try {
        showLoading("Loading prefixes...");
        
        const response = await fetch('/api/prefix', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        prefixArray = data.prefix || [];
        
        console.log(`Loaded ${prefixArray.length} prefixes from backend`);
        
        hidePrefixError();
        enablePrefixInput();
        renderTable();
        hideLoading();
        
    } catch (error) {
        console.error("Error loading prefixes:", error);
        showPrefixError(`Could not load prefixes: ${error.message}`);
        disablePrefixInput();
        prefixArray = [];
        renderTable();
        hideLoading();
    }
}

/**
 * Add a new prefix entry
 */
async function addPrefix() {
    const input = document.getElementById("newPrefixInput");
    const addBtn = document.getElementById("addPrefixBtn");
    
    if (!input) return;
    
    const regexValue = input.value.trim();
    
    if (!regexValue) {
        showPrefixError("Please enter a regex pattern");
        return;
    }
    
    // Check for duplicates
    const isDuplicate = prefixArray.some(prefix => prefix.regex === regexValue);
    if (isDuplicate) {
        showPrefixError("This regex pattern already exists");
        return;
    }
    
    try {
        // Show loading state
        if (addBtn) {
            addBtn.disabled = true;
            addBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Adding...';
        }
        
        const response = await fetch('/api/prefix', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                regex: regexValue,
                description: `Prefix pattern: ${regexValue.substring(0, 50)}...`
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        console.log(`Added prefix with ID: ${result.id}`);
        
        // Clear input
        input.value = "";
        
        // Reload prefixes
        await loadPrefixes();
        
        // Go to last page to show new entry
        currentPage = getPageCount();
        renderTable();
        
        hidePrefixError();
        
    } catch (error) {
        console.error("Error adding prefix:", error);
        showPrefixError(`Failed to add prefix: ${error.message}`);
    } finally {
        // Restore button state
        if (addBtn) {
            addBtn.disabled = false;
            addBtn.innerHTML = '<i class="fa fa-plus" aria-hidden="true"></i>';
        }
    }
}

/**
 * Remove a prefix entry
 */
async function removePrefix(indexOnPage) {
    const globalIndex = (currentPage - 1) * entriesPerPage + indexOnPage;
    
    if (globalIndex < 0 || globalIndex >= prefixArray.length) {
        console.error("Invalid prefix index:", globalIndex);
        return;
    }
    
    const prefix = prefixArray[globalIndex];
    
    if (!confirm(`Are you sure you want to delete this prefix?\n\n${prefix.regex}`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/prefix/${prefix.id}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `HTTP ${response.status}`);
        }
        
        console.log(`Deleted prefix: ${prefix.id}`);
        
        // Reload prefixes
        await loadPrefixes();
        
        // Adjust current page if necessary
        const totalPages = getPageCount();
        if (currentPage > totalPages && totalPages > 0) {
            currentPage = totalPages;
        }
        
        renderTable();
        hidePrefixError();
        
    } catch (error) {
        console.error("Error removing prefix:", error);
        showPrefixError(`Failed to remove prefix: ${error.message}`);
    }
}

/**
 * Render the prefix table
 */
function renderTable() {
    const tbody = document.querySelector("#entryTable tbody");
    if (!tbody) return;
    
    tbody.innerHTML = "";
    
    const start = (currentPage - 1) * entriesPerPage;
    const end = Math.min(start + entriesPerPage, prefixArray.length);
    
    if (prefixArray.length === 0) {
        const row = tbody.insertRow();
        const cell = row.insertCell(0);
        cell.colSpan = 3;
        cell.className = "text-center text-muted py-4";
        cell.innerHTML = '<i class="fa fa-info-circle"></i> No prefix patterns available. Add one above to get started.';
    } else {
        for (let i = start; i < end; i++) {
            const prefix = prefixArray[i];
            const indexOnPage = i - start;
            
            const row = tbody.insertRow();
            
            // ID column
            const idCell = row.insertCell(0);
            idCell.textContent = i + 1;
            idCell.className = "text-center";
            
            // Regex column
            const regexCell = row.insertCell(1);
            regexCell.innerHTML = `
                <code class="bg-light p-1 rounded">${escapeHtml(prefix.regex || '')}</code>
                ${prefix.description ? `<br><small class="text-muted">${escapeHtml(prefix.description)}</small>` : ''}
            `;
            
            // Action column
            const actionCell = row.insertCell(2);
            actionCell.className = "text-center";
            actionCell.innerHTML = `
                <button class="btn btn-outline-danger btn-sm" 
                        onclick="removePrefix(${indexOnPage})"
                        title="Delete this prefix pattern">
                    <i class="fa fa-trash" aria-hidden="true"></i>
                </button>
            `;
        }
    }
    
    renderPagination();
    updatePageInfo();
}

/**
 * Update page information display
 */
function updatePageInfo() {
    const totalEntries = prefixArray.length;
    const start = totalEntries === 0 ? 0 : (currentPage - 1) * entriesPerPage + 1;
    const end = Math.min(currentPage * entriesPerPage, totalEntries);
    
    // Update header or add info if needed
    const header = document.querySelector("h2");
    if (header) {
        const existingInfo = header.querySelector(".entry-info");
        if (existingInfo) {
            existingInfo.remove();
        }
        
        if (totalEntries > 0) {
            const info = document.createElement("small");
            info.className = "entry-info text-muted ms-2";
            info.innerHTML = `<i class="fa fa-database"></i> ${totalEntries} total entries`;
            header.appendChild(info);
        }
    }
}

/**
 * Change to a specific page
 */
function changePage(newPage) {
    const totalPages = getPageCount();
    if (newPage < 1 || newPage > totalPages) return;
    
    currentPage = newPage;
    renderTable();
}

/**
 * Get total number of pages
 */
function getPageCount() {
    return Math.max(1, Math.ceil(prefixArray.length / entriesPerPage));
}

/**
 * Render pagination controls
 */
function renderPagination() {
    const totalPages = getPageCount();
    const pagination = document.getElementById("paginationControls");
    
    if (!pagination) return;
    
    pagination.innerHTML = "";
    
    if (totalPages <= 1) {
        pagination.style.display = "none";
        return;
    }
    
    pagination.style.display = "flex";
    
    // Previous button
    const prevBtn = document.createElement("button");
    prevBtn.className = `btn btn-outline-primary btn-sm ${currentPage === 1 ? 'disabled' : ''}`;
    prevBtn.innerHTML = '<i class="fa fa-chevron-left"></i> Prev';
    prevBtn.disabled = currentPage === 1;
    prevBtn.onclick = () => changePage(currentPage - 1);
    pagination.appendChild(prevBtn);
    
    // Page number buttons
    let startPage = Math.max(1, currentPage - Math.floor(visiblePageCount / 2));
    let endPage = startPage + visiblePageCount - 1;
    
    if (endPage > totalPages) {
        endPage = totalPages;
        startPage = Math.max(1, endPage - visiblePageCount + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement("button");
        pageBtn.textContent = i;
        pageBtn.className = `btn btn-sm ${i === currentPage ? 'btn-primary' : 'btn-outline-primary'}`;
        pageBtn.onclick = () => changePage(i);
        pagination.appendChild(pageBtn);
    }
    
    // Next button
    const nextBtn = document.createElement("button");
    nextBtn.className = `btn btn-outline-primary btn-sm ${currentPage === totalPages ? 'disabled' : ''}`;
    nextBtn.innerHTML = 'Next <i class="fa fa-chevron-right"></i>';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.onclick = () => changePage(currentPage + 1);
    pagination.appendChild(nextBtn);
}

/**
 * Show error message
 */
function showPrefixError(message) {
    const errorBox = document.getElementById("prefixErrorMsg");
    if (errorBox) {
        errorBox.textContent = message;
        errorBox.classList.remove("d-none");
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (errorBox.textContent === message) {
                hidePrefixError();
            }
        }, 5000);
    }
}

/**
 * Hide error message
 */
function hidePrefixError() {
    const errorBox = document.getElementById("prefixErrorMsg");
    if (errorBox) {
        errorBox.classList.add("d-none");
    }
}

/**
 * Show loading message
 */
function showLoading(message) {
    const tbody = document.querySelector("#entryTable tbody");
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" class="text-center py-4">
                    <i class="fa fa-spinner fa-spin"></i> ${message}
                </td>
            </tr>
        `;
    }
}

/**
 * Hide loading message
 */
function hideLoading() {
    // Loading is hidden when renderTable() is called
}

/**
 * Disable prefix input controls
 */
function disablePrefixInput() {
    const input = document.getElementById("newPrefixInput");
    const addBtn = document.getElementById("addPrefixBtn");
    
    if (input) {
        input.disabled = true;
        input.placeholder = "Backend connection required";
    }
    if (addBtn) {
        addBtn.disabled = true;
    }
}

/**
 * Enable prefix input controls
 */
function enablePrefixInput() {
    const input = document.getElementById("newPrefixInput");
    const addBtn = document.getElementById("addPrefixBtn");
    
    if (input) {
        input.disabled = false;
        input.placeholder = "Enter new prefix regex";
    }
    if (addBtn) {
        addBtn.disabled = false;
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}