// Element references used across functions — declare in module scope so
// all functions can access them (avoids ReferenceError when functions
// run outside the DOMContentLoaded callback).
let logDisplay, regexDisplay, matchDisplay, captureGroupDisplay, matchLogger;
let fixButton, generateButton, saveToDBButton;
let fixSpinner, generateSpinner, saveToDBSpinner;

document.addEventListener("DOMContentLoaded", () => {
    // Initialize if parser section exists (unified interface)
    const parserSection = document.getElementById("parser-section");
    if (parserSection) {
        // Assign elements to the module-scope variables
        logDisplay = document.getElementById("logDisplay");
        regexDisplay = document.getElementById("regexDisplay");
        matchDisplay = document.getElementById("matchDisplay");
        captureGroupDisplay = document.getElementById("captureGroupDisplay");
        matchLogger = document.getElementById("matchLogger");
        // Primary logger element used across this module. If an element with id
        // `logger` is not present in the DOM, fall back to the match logger so
        // existing UI still receives status messages.
        logger = document.getElementById("logger") || matchLogger;
        fixButton = document.getElementById("fixButton");
        generateButton = document.getElementById("generateButton");
        saveToDBButton = document.getElementById("saveToDBButton");
        fixSpinner = document.getElementById('fixSpinner');
        generateSpinner = document.getElementById('generateSpinner');
        saveToDBSpinner = document.getElementById('saveToDBSpinner');

        // Add event listeners
        addEventIfExists(regexDisplay, "input", findMatch);

        // Initialize with data from session storage
        logger.innerText = `Entry: ${getSessionItem("id", "New Entry")}`;
        logDisplay.innerText = getSessionItem("log");
        regexDisplay.value = getSessionItem("regex");
        findMatch();

        // Load entry statistics
        loadEntryStatistics();
    }
});

// Pull oldest unmatched entry from the database
async function pullEntry() {
    const pullButton = document.getElementById("pullEntryButton");

    try {
        // Disable button and show loading state
        if (pullButton) {
            pullButton.disabled = true;
            pullButton.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Pulling...';
        }

        logger.innerText = "Searching for oldest unmatched entry...";

        const response = await fetch("/api/entries/oldest", {
            method: "GET",
            headers: { "Content-Type": "application/json" }
        });

        if (!response.ok) {
            if (response.status === 404) {
                logger.innerText = "No unmatched entries found in database";
                return;
            }
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Validate response data
        if (!data.id || !data.log) {
            throw new Error("Invalid entry data received from server");
        }

        // Update UI with entry data
        logDisplay.innerText = data.log || '';
        regexDisplay.value = data.regex || '';
        logger.innerText = `Entry ${data.id} pulled successfully (${new Date(data.timestamp).toLocaleString()})`;

        // Store in session for persistence
        setSessionItem("id", data.id);
        setSessionItem("log", data.log);
        setSessionItem("regex", data.regex || '');

        // Trigger match finding if regex exists
        if (data.regex) {
            findMatch();
        }

        // Refresh statistics after pulling entry
        setTimeout(() => loadEntryStatistics(), 500);

    } catch (error) {
        console.error("Error pulling entry:", error);
        logger.innerText = `Error pulling entry: ${error.message}`;
    } finally {
        // Re-enable button and restore original text
        if (pullButton) {
            pullButton.disabled = false;
            pullButton.innerHTML = '<i class="fa fa-download"></i> Pull Latest Unmatched Entry';
        }
    }
}

// Query the LLM for regex generation or fixing
async function queryLLM(task) {
    const taskMessages = {
        generate: "AI is generating regex...",
        fix: "AI is fixing regex..."
    };

    const log = logDisplay.innerText;
    if (!log) {
        logger.innerText = "No log to analyze";
        return;
    }

    const regex = regexDisplay?.value;
    if (!regex && task === "fix") {
        logger.innerText = "No regex to fix";
        return;
    }

    // Show spinner for fix operation
    if (task === 'fix') {
        if (fixSpinner) fixSpinner.classList.remove('d-none');
        if (fixButton) fixButton.disabled = true;
    }

    if (task === "generate") {
        if (generateSpinner) generateSpinner.classList.remove('d-none');
        if (generateButton) generateButton.disabled = true;
    }

    logger.innerText = taskMessages[task];

    try {
        const response = await fetch("/api/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ task, regex, log: getSessionItem("log") })
        });

        if (!response.ok) throw new Error(`Server returned ${response.status}`);

        const data = await response.json();
        regexDisplay.value = data.regex;

        if (task === 'fix') {
            // Show success alert
            showAlert('Success! Regex has been improved.', 'success');
        }
        if (task === 'generate') {
            // Show success alert
            showAlert('Success! Regex has been generated.', 'success');
        }

        logger.innerText = data.logger;
        findMatch();
    } catch (error) {
        console.error(`Error during ${task} task:`, error);
        logger.innerText = `Error: ${error.message}`;
    } finally {
        // Hide spinner and re-enable button when done (whether success or error)
        if (task === 'fix') {
            if (fixSpinner) fixSpinner.classList.add('d-none');
            if (fixButton) fixButton.disabled = false;
        }
        if (task === 'generate') {
            if (generateSpinner) generateSpinner.classList.add('d-none');
            if (generateButton) generateButton.disabled = false;
        }
    }
}

// Show an alert message that fades away
function showAlert(message, type = 'success') {
    // Create alert element
    const alertEl = document.createElement('div');
    alertEl.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertEl.style.top = '20px';
    alertEl.style.right = '20px';
    alertEl.style.zIndex = '9999';

    // Add content
    alertEl.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Add to document
    document.body.appendChild(alertEl);

    // Initialize Bootstrap alert
    const bsAlert = new bootstrap.Alert(alertEl);

    // Auto-dismiss after 3 seconds
    setTimeout(() => {
        if (alertEl) {
            bsAlert.close();
            // Remove from DOM after animation completes
            alertEl.addEventListener('closed.bs.alert', () => {
                alertEl.remove();
            });
        }
    }, 3000);
}

// Save entry to database
async function saveToDB() {
    logger.innerText = "Sending to database...";
    if (saveToDBSpinner) saveToDBSpinner.classList.remove('d-none');
    if (saveToDBButton) saveToDBButton.disabled = true;
    await fetchAndHandle(`/api/entries/${getSessionItem("id")}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            log: getSessionItem("log"),
            regex: regexDisplay?.value,
        })
    }, (data) => {
        logger.innerText = data.message;
        showAlert(`Entry ${getSessionItem("id")} saved successfully`, 'success');
    }, "Error sending to database:");
    if (saveToDBButton) saveToDBButton.disabled = false;
    if (saveToDBSpinner) saveToDBSpinner.classList.add('d-none');
}

async function findMatch() {
    const log = getSessionItem("log") || logDisplay.innerText;
    const regex = regexDisplay?.value || getSessionItem("regex") || "";

    if (!regex.trim()) {
        matchDisplay.innerText = '';
        captureGroupDisplay.innerText = '';
        matchLogger.innerText = "No Regex";
        logDisplay.innerText = log;
        return;
    }

    try {
        const response = await fetch('/api/find_match', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ log, regex })
        });
        const data = await response.json();

        // --- Status UI ---
        matchLogger.innerText = data.status;
        matchLogger.className =
            data.status.includes("Unmatched") ? "text-danger" :
                data.status.includes("Partially") ? "text-warning" :
                    data.status === "Matched" ? "text-success" : "";

        // --- Normalise matches ---
        let matches = [];
        if (data.full) {
            matches.push(["matched1", data.full]);
            if (Array.isArray(data.groups)) {
                data.groups.forEach((g, i) => matches.push([g.name, g]));
            }
        }

        const fullMatchObj = matches.find(([k]) => k === "matched1")?.[1] || null;
        const groupMatches = matches.filter(([k]) => k !== "matched1");

        // --- Update displays ---
        matchDisplay.innerText = fullMatchObj ? fullMatchObj.value : '';
        captureGroupDisplay.innerText = groupMatches
            .map(([k, v]) => `${k}: ${v?.value ?? ''}`)
            .join('\n');

        // --- Highlight log ---
        highlightLog(log, fullMatchObj, groupMatches);

    } catch (err) {
        console.error("findMatch() error:", err);
        matchLogger.innerText = "Request Error";
    }
}
function highlightLog(logText, fullMatch, groups) {
    if (!logDisplay) return;

    const escapeHtml = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // Collect all highlights: full match first (lower priority), capture groups higher priority
    const highlights = [];

    if (fullMatch && typeof fullMatch.start === 'number') {
        highlights.push({ start: fullMatch.start, end: fullMatch.end, color: 'rgba(255,255,0,0.3)' });
    }

    groups.forEach(([_, g]) => {
        if (!g || typeof g.start !== 'number' || typeof g.end !== 'number') return;
        highlights.push({ start: g.start, end: g.end, color: 'rgba(0,0,255,0.2)' });
    });

    // Sort by start
    highlights.sort((a, b) => a.start - b.start || a.end - b.end);

    // Merge highlights into segments
    const segments = [];
    let pointer = 0;
    while (pointer < logText.length) {
        let overlapping = highlights.filter(h => h.start <= pointer && h.end > pointer);
        let nextBoundary = logText.length;
        if (overlapping.length) {
            nextBoundary = Math.min(...overlapping.map(h => h.end));
        } else {
            const future = highlights.find(h => h.start > pointer);
            if (future) nextBoundary = future.start;
        }

        const segmentText = logText.slice(pointer, nextBoundary);
        segments.push({ text: segmentText, highlights: overlapping.slice() });
        pointer = nextBoundary;
    }

    // Build final HTML
    const finalHtml = segments.map(seg => {
        let text = escapeHtml(seg.text);
        seg.highlights.forEach(h => {
            text = `<mark style="background:${h.color}">${text}</mark>`;
        });
        return text;
    }).join('');

    logDisplay.innerHTML = finalHtml;
}

async function reduceRegex() {
    if (!regexDisplay.value) return logger.innerText = "No regex to reduce";

    const response = await fetch('/api/reduce_regex', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ log: logDisplay.innerText, regex: regexDisplay.value })
    });

    const data = await response.json();
    regexDisplay.value = data.regex;
    findMatch();
    logger.innerText = "Regex reduced successfully";
}

// Update match display with data
function updateMatchDisplay(matches) {
    matchDisplay.innerText = '';
    Object.entries(matches).forEach(([key, value]) => {
        matchDisplay.innerText += `${key}: ${value['value']}\n`;
    });
}

// Clear all entry fields
function clearEntry() {
    logDisplay.innerText = "";
    regexDisplay.value = "";
    logger.innerText = "Entry cleared";
    sessionStorage.clear();
}

// Load and display entry statistics
async function loadEntryStatistics() {
    const statsElement = document.getElementById("entryStats");

    try {
        const response = await fetch("/api/entries/stats", {
            method: "GET",
            headers: { "Content-Type": "application/json" }
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch statistics: ${response.status}`);
        }

        const stats = await response.json();

        // Update statistics display
        const totalEntries = stats.total_entries || 0;
        const unmatchedCount = stats.unmatched_count || 0;
        const matchedCount = stats.status_counts?.Matched || 0;
        const matchRate = totalEntries > 0 ? Math.round((matchedCount / totalEntries) * 100) : 0;

        statsElement.innerHTML = `
            <i class="fa fa-database"></i> ${totalEntries} total entries | 
            <i class="fa fa-exclamation-triangle text-warning"></i> ${unmatchedCount} unmatched | 
            <i class="fa fa-check-circle text-success"></i> ${matchedCount} matched (${matchRate}%)
        `;

        // Update pull button tooltip
        const pullButton = document.getElementById("pullEntryButton");
        if (pullButton && unmatchedCount > 0) {
            pullButton.setAttribute("data-bs-title", `Pull oldest unmatched entry (${unmatchedCount} available)`);
        } else if (pullButton) {
            pullButton.setAttribute("data-bs-title", "No unmatched entries available");
            pullButton.disabled = unmatchedCount === 0;
        }

    } catch (error) {
        console.error("Error loading statistics:", error);
        statsElement.innerHTML = '<i class="fa fa-exclamation-circle text-danger"></i> Unable to load statistics';
    }
}
