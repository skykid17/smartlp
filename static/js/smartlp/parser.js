document.addEventListener("DOMContentLoaded", () => {
    // Only initialize if we're on the parser page
    if (window.location.pathname === "/smartlp/parser") {
        // Initialize elements
        let logDisplay = document.getElementById("logDisplay");
        let regexDisplay = document.getElementById("regexDisplay");
        let matchDisplay = document.getElementById("matchDisplay");
        let matchLogger = document.getElementById("matchLogger");
        let fixButton = document.getElementById("fixButton");
        let generateButton = document.getElementById("generateButton");
        let saveToDBButton = document.getElementById("saveToDBButton");
        let fixSpinner = document.getElementById('fixSpinner');
        let generateSpinner = document.getElementById('generateSpinner');
        let saveToDBSpinner = document.getElementById('saveToDBSpinner');

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
        const response = await fetch("/api/query_llm", {
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

// Find matches using regex
async function findMatch() {
    const log = getSessionItem("log") || logDisplay.innerText;
    const regex = regexDisplay?.value || getSessionItem("regex") || "";

    if (!regex.trim()) {
        matchDisplay.innerText = '';
        matchLogger.innerText = "No Regex";
        return;
    }

    try {
        const response = await fetch('/api/find_match', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ log, regex })
        });

        const data = await response.json();
        matchLogger.innerText = data.logger; // Use .innerText and set class manually.
        if (data.logger.includes("Error")) matchLogger.className = "text-danger";
        else if (data.logger.includes("Partial")) matchLogger.className = "text-warning";
        else if (data.logger == "Fully Matched") matchLogger.className = "text-success";
        matchDisplay.innerText = '';

        if (data.matches && Object.keys(data.matches).length > 0) {
            // Skip if key starts with 'matched
            const output = data.matches
                .filter(([key]) => !key.startsWith('matched'))
                .map(([key, val]) => `${key}: ${val.value}`)
                .join('\n');
            matchDisplay.innerText = output;

            // Highlight matched substrings in the logDisplay
            highlightMatches(log, data.matches);
        } else {
            // If no matches, display the original log without highlights
            logDisplay.innerText = log;
        }
    } catch (error) {
        console.error("Error in findMatch:", error);
        matchLogger.innerText = "Request Error";
    }
}

function highlightMatches(logText, matches) {
    const matchArray = matches.filter(([key]) => key == 'matched1'); // Only get first regex match. Rest is ignored 
    if (matchArray.length === 0) {
        logDisplay.innerText = logText;
        return;
    }
    const matchGroups = matches.filter(([key]) => !key.startsWith('matched'));
    console.log(matchGroups);

    const matchValue = matchArray[0][1].value;
    const matchStartIndex = matchArray[0][1].start;
    const matchEndIndex = matchArray[0][1].end;
    logDisplay.innerText = '';

    // Add text before match
    logDisplay.appendChild(
        document.createTextNode(logText.substring(0, matchStartIndex))
    );

    // Add highlighted match
    const highlightElement = document.createElement('mark');
    highlightElement.setAttribute('class', 'highlight-base');
    // Create nested highlights for each capture group
    if (matchGroups.length > 0) {
        var processedGroups = [];

        matchGroups.forEach(([groupName, groupData], index) => {
            // Skip if outside main match
            if (groupData.start < matchStartIndex || groupData.end > matchEndIndex) {
                return;
            }

            // Determine info about the groups
            const relativeStart = groupData.start - matchStartIndex;
            const relativeEnd = groupData.end - matchStartIndex;
            const groupContent = matchValue.substring(relativeStart, relativeEnd);
            const groupHighlight = document.createElement('mark');
            groupHighlight.setAttribute('class', index % 2 === 0 ? 'highlight1' : 'highlight2');
            groupHighlight.setAttribute('title', groupName);
            groupHighlight.textContent = groupContent;

            // Store information about this group for processing
            processedGroups.push({
                start: relativeStart,
                end: relativeEnd,
                element: groupHighlight,
                name: groupName
            });
        });
        // Sort groups by start position (to handle nesting correctly)
        processedGroups.sort((a, b) => a.start - b.start);

        // Add the groups
        var lastPosition = 0;
        for (const group of processedGroups) {
            if (group.start > lastPosition) {
                highlightElement.appendChild(
                    document.createTextNode(matchValue.substring(lastPosition, group.start))
                );
            }
            highlightElement.appendChild(group.element);
            lastPosition = group.end;
        }

        // Add any remaining text
        if (lastPosition < matchValue.length) {
            highlightElement.appendChild(
                document.createTextNode(matchValue.substring(lastPosition))
            );
        }
    }
    logDisplay.appendChild(highlightElement);

    logDisplay.appendChild(
        document.createTextNode(logText.substring(matchEndIndex))
    );

}

async function reduceRegex() {
    if (regexDisplay.value === "") {
        logger.innerText = "No regex to reduce";
        return;
    }
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
