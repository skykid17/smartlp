### templates/base.html
```bash
cat > "/opt/SmartSOC/web/templates/base.html" <<"ENDMSG"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page_title if page_title else "SmartSOC" }}</title>
    <link rel="icon" type="image/x-icon" href="/logos/logo.png">
    <link rel="stylesheet" type="text/css" href="/css/bootstrap.min.css">
    <link rel="stylesheet" href="/css/font-awesome.css">
    <!-- JavaScript -->
    <!-- Custom JavaScript for SmartLP -->
    <!-- <script src="/js/custom.js"></script> -->
    <script src="/js/jquery.min.js"></script>
    <script src="/js/popper.min.js"></script>
    <script src="/js/bootstrap.min.js"></script>
    <script src="/js/socket.io.min.js"></script>
    <script src="/js/settings.js"></script>
    <script src="/js/utils.js"></script>
    <script src="/js/html2pdf.bundle.min.js"></script>
    <script src="/js/chart.js"></script>
    <!-- Custom CSS for SmartLP -->
    <link rel="stylesheet" href="/css/custom.css">

</head>
<body class="d-flex flex-column min-vh-100">
    <!-- Navigation Bar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <!-- Left-aligned Brand/Title -->
            <span class="navbar-brand mb-0 h4 text-white">
                <a href="{{ url_for('dashboard') }}" class="text-white text-decoration-none d-flex align-items-center">
                    <img src="/logos/logo_white.png" class="me-2" height="20" alt="Logo">SmartSOC AI Cyber Engineer</a>
            </span>

            <!-- Toggler for mobile -->
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>

            <!-- Right-aligned Nav Links -->
            <div class="collapse navbar-collapse justify-content-end" id="navbarNav">
                <ul class="navbar-nav">
                    <!-- SmartLP Dropdown -->
                    <li class="nav-item dropdown">
                        <a class="nav-link text-white" href="{{ url_for('smartlp') }}">
                            SmartLP
                        </a>
                        <ul class="dropdown-menu dropdown-menu-dark">
                            <li><a class="dropdown-item" href="{{ url_for('smartlp') }}">Overview</a></li>
                            <li><a class="dropdown-item" href="{{ url_for('smartlp_parser') }}">Parser</a></li>
                            <li><a class="dropdown-item" href="{{ url_for('smartlp_prefix') }}">Prefix</a></li>
                        </ul>
                    </li>
            
                    <!-- SmartUC Dropdown -->
                    <li class="nav-item dropdown">
                        <a class="nav-link text-white" href="{{ url_for('smartuc') }}">
                            SmartUC
                        </a>
                        <ul class="dropdown-menu dropdown-menu-dark">
                            <li><a class="dropdown-item" href="{{ url_for('smartuc') }}">Overview</a></li>
                            <li><a class="dropdown-item" href="{{ url_for('smartuc_attack_navigator') }}">ATT&CK Navigator</a></li>
                        </ul>
                    </li>
            
                    <!-- SmartDB -->
                    <li class="nav-item">
                        <a class="nav-link text-white" href="{{ url_for('smartdb') }}">SmartDB</a>
                    </li>

                    <!-- SmartReport -->
                    <li class="nav-item dropdown">
                        <a class="nav-link text-white">
                            SmartReport
                        </a>
                        <ul class="dropdown-menu dropdown-menu-dark">
                            <li><a class="dropdown-item" href="{{ url_for('smartlp_report') }}">SmartLP</a></li>
                            <li><a class="dropdown-item">SmartUC</a></li>
                        </ul>
                    </li>

                    <!-- Report -->
                    <li class="nav-item">
                        <a class="nav-link text-white" href="{{ url_for('settings') }}">Settings</a>
                    </li>
                </ul>
            </div>            
        </div>
    </nav>
    <div class="position-fixed bottom-0 start-0 ms-2 mb-5 " style="z-index: 1060;">
        <button class="btn btn-dark" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasWithBothOptions" aria-controls="offcanvasWithBothOptions">
          <i class="fa fa-eye"></i>
        </button>
      </div>      
    <div class="offcanvas offcanvas-start logpanel" data-bs-scroll="true" tabindex="-1" id="offcanvasWithBothOptions" aria-labelledby="offcanvasWithBothOptionsLabel">
        <div class="offcanvas-header">
          <h5 class="offcanvas-title" id="offcanvasWithBothOptionsLabel"><i class="fa fa-eye"></i> Logger</h5>
          <button type="button" class="btn-close text-reset" data-bs-dismiss="offcanvas" aria-label="Close"></button>
        </div>
        <div class="offcanvas-body">
            <div id="logger"></div>
        </div>
    </div>
    <!-- Main Content -->
    <main class="container mt-4 flex-grow-1">
        <div class="toast-container position-fixed bottom-0 end-0 p-3">
            <div id="liveToast" class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="5000">
              <div class="toast-header">
                <strong class="me-auto">SmartLP</strong>
                <small class="toast-timestamp">Just now</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
              </div>
              <div class="toast-body">
                <div id="ingestNotification"></div>
              </div>
            </div>
          </div>
        {% block content %}{% endblock %}
        </main>
    <!-- Footer -->
    <footer class="bg-dark text-white text-center py-3 mt-4">
        <p class="mb-0">SmartSOC &copy; 2025. All Rights Reserved.</p>
    </footer>
</body>
</html>

ENDMSG
```
---
### templates/dashboard.html
```bash
cat > "/opt/SmartSOC/web/templates/dashboard.html" <<"ENDMSG"
{% extends "base.html" %}

{% block content %}
<div class="text-center mb-4">
    <img src="/logos/logo_name.png" height="150px" alt="Logo">
    <h1>AI Cyber Engineer</h1>
    <p class="text-muted">Manage your SmartSOC SmartUC, SmartLP, and SmartDB.</p>
</div>

<div class="row">
    <div class="col-md-4">
        <div class="card shadow-sm">
            <div class="card-body text-center">
                <h5 class="card-title">SmartLP</h5>
                <p class="card-text">Explore and Manage Log Parsers.</p>
                <a href="{{ url_for('smartlp') }}" class="btn btn-info">Go to SmartLP</a>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card shadow-sm">
            <div class="card-body text-center">
                <h5 class="card-title">SmartUC</h5>
                <p class="card-text">Explore and Manage Use Cases.</p>
                <a href="{{ url_for('smartuc') }}" class="btn btn-info">Go to SmartUC</a>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card shadow-sm">
            <div class="card-body text-center">
                <h5 class="card-title">SmartDB</h5>
                <p class="card-text">Explore and Manage Dashboards.</p>
                <a href="{{ url_for('smartdb') }}" class="btn btn-info">Go to SmartDB</a>
            </div>
        </div>
    </div>
</div>
{% endblock %}

ENDMSG
```
---
### templates/settings.html
```bash
cat > "/opt/SmartSOC/web/templates/settings.html" <<"ENDMSG"
{% extends "base.html" %}

{% block content %}
<body>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h2>Settings</h2>
    <p>Configure SmartSOC settings.</p>
    <div id="siemStatus" class="siem-status">
                  <!-- SIEM status indicators will be populated here -->
    </div>
  </div>
  <div class="row">
    <div class="col-2">
      <div class="nav flex-column nav-pills me-3" id="settings-tabs" role="tablist" aria-orientation="vertical">
        <button class="nav-link active" id="smartlp-tab" data-bs-toggle="pill" data-bs-target="#smartlp-settings" type="button" role="tab" aria-controls="smartlp-settings" aria-selected="true">SmartLP</button>
        <button class="nav-link" id="smartuc-tab" data-bs-toggle="pill" data-bs-target="#smartuc-settings" type="button" role="tab" aria-controls="smartuc-settings" aria-selected="false">SmartUC</button>
        <button class="nav-link" id="siem-tab" data-bs-toggle="pill" data-bs-target="#siem-settings" type="button" role="tab" aria-controls="siem-settings" aria-selected="false">SIEM</button>
        <button class="nav-link" id="llm-tab" data-bs-toggle="pill" data-bs-target="#llm-settings" type="button" role="tab" aria-controls="llm-settings" aria-selected="false">LLM</button>
      </div>
    </div>
    <div class="col-10">
      <div class="tab-content" id="settings-content">
        
        <!-- General Settings -->
        <div class="tab-pane fade show active" id="smartlp-settings" role="tabpanel" aria-labelledby="smartlp-tab">
          <h3>SmartLP Settings</h3>
          <div class="row">
            <div class="col">
              <div class="form-check form-switch mb-2">
                <label class="form-check-label" for="ingestOn" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Enable to ingest unparsed logs">Ingestion</label>
                <input class="form-check-input" type="checkbox" role="switch" id="ingestOn">
              </div>
              <div  id="ingestGroup">
                <div class="form-group mb-3">
                  <label for="ingestAlgoVersion" class="form-label">Parsing Algorithm Version</label>
                  <select id="ingestAlgoVersion" class="form-select">
                    <option value="v1">Version 1</option>
                    <option value="v2">Version 2</option>
                  </select>
                </div>
                <div class="form-group mb-3">
                  <label for="ingestFrequency" class="form-label" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="How often to ingest unparsed logs (in minutes).">Ingest Frequency (minutes):</label>
                  <input type="number" id="ingestFrequency" class="form-control" min="1" max="60">
                  <div id="ingestFrequencyError"></div>
                </div>
                <div class="form-group mb-2">
                  <div class="form-check form-switch">
                    <label class="form-check-label" for="similarityCheck" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Enable to skip logs similar to existing ones.">Similarity Check</label>
                    <input class="form-check-input" type="checkbox" role="switch" id="similarityCheck">
                  </div>
                </div>                  
                <div class="form-group mb-3" id="similarityThresholdGroup">
                  <label for="similarityThreshold" class="form-label" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Skip logs if similarity exceeds this value (0–1).">Similarity Threshold</label>
                  <input type="number" id="similarityThreshold" class="form-control" step="0.05" min="0" max="1">
                  <div id="similarityThresholdError"></div>
                </div>
              </div>
            </div>
            <div class="col" >
              <div class="form-group mb-3">
                <label for="activeSiem" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Current SIEM for ingestion">Active SIEM:</label>
                <select id="activeSiem" class="form-select">
                </select>
              </div>
              
            </div>
            <div class="col">
              <div class="form-group mb-3">
                <label for="activeLlmEndpoint" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Service running the model">Active LLM Endpoint:</label>
                <select id="activeLlmEndpoint" class="form-select">
                </select>
              </div>
              <div class="form-group mb-3">
                <label for="activeLlm" class="form-label" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Current running model for all queries">Active LLM Model:</label>
                <select id="activeLlm" class="form-select">
                </select>
              </div>
              <div class="form-group mb-3">
                <label for="fixCount" class="form-label" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Number of requeries to the LLM to fix the regex generated (0-100)">Regex Fix Count:</label>
                <input type="number" id="fixCount" class="form-control" min="0" max="100">
                <div id="fixCountError"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- SmartUC Settings-->
        <div class="tab-pane fade" id="smartuc-settings" role="tabpanel" aria-labelledby="smartuc-tab">
          <h3>SmartUC Settings</h3>
          <div class="row">
            <div class="col">
              <div class="form-group mb-3">
                <label for="smartucActiveLlmEndpoint" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Service running the model">Active LLM Endpoint:</label>
                <select id="smartucActiveLlmEndpoint" class="form-select">
                </select>
              </div>
              <div class="form-group mb-3">
                <label for="smartucActiveLlm" class="form-label" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Current running model for all queries">Active LLM Model:</label>
                <select id="smartucActiveLlm" class="form-select">
                </select>
              </div>
            </div>
          </div>
        </div>
        <!-- SIEM Settings -->
        <div class="tab-pane fade" id="siem-settings" role="tabpanel" aria-labelledby="siem-tab">
          <h3>SIEM Settings</h3>
          <div class="row">
            <div class="col-4">
              <div class="form-group mb-3">
                <label for="siem" class="form-label">SIEM:</label>
                <select id="siem" class="form-select">
                </select>
              </div>
              <div class="form-group mb-3" id="searchIndexGroup">
                <label for="searchIndex">Search Index:</label>
                <input type="text" id="searchIndex" class="form-control" placeholder="Search index name">
              </div>
              <div class="form-group mb-3" id="searchEntryGroup">
                <label for="searchEntryCount">Number of Entries:</label>
                <input type="text" id="searchEntryCount" class="form-control" placeholder="Search entry count">
              </div>
              <div class="form-group mb-3">
                <div id="searchQueryLogger"></div>
              </div>
            </div>
            <div class="col-8">
              <div class="form-group mb-3">
                <label for="searchQuery" class="form-label">Search Query:</label>
                <textarea type="text" id="searchQuery" class="form-control text-break" placeholder="Search string"></textarea>
              </div>
              <div class="form-group mb-3 d-flex">
                <button class="btn btn-secondary ms-auto" onclick="testQuery()">Test</button>
              </div>
            </div>
          </div>
        </div>

        <!-- LLM Settings -->
        <div class="tab-pane fade" id="llm-settings" role="tabpanel" aria-labelledby="llm-tab">
          <h3>LLM Settings</h3>
          <div class="row">
            <div class="col-8">
              <div class="form-group mb-3">
                <label for="llmEndpoint">LLM Endpoint:</label>
                <select id="llmEndpoint" class="form-select">
                </select>
              </div>
              <div class="form-group mb-3">
                <label for="llmUrl" class="form-label">LLM URL:</label>
                <textarea id="llmUrl" class="form-control" placeholder="API URL"></textarea>
              </div>
            </div>
            <div class="col-4">
              <div class="form-group mb-3">
                <div class="form-label">LLM Models:</div>
                <div class="input-group mb-3">
                  <input type="text" id="newModelInput" class="form-control" placeholder="Enter new model">
                  <button class="btn btn-outline-primary" type="button" onclick="addModel()">
                    <i class="fa fa-plus" aria-hidden="true"></i>
                  </button>
                </div>
                <div id="models" class="mb-3"></div>
                <div class="form-group mb-3">
                  <div id="testModelLogger"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Warning Modal for SIEM Change -->
  <div class="modal fade" id="siemChangeWarningModal" tabindex="-1" aria-labelledby="siemChangeWarningModalLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="siemChangeWarningModalLabel"><i class="fa fa-exclamation-triangle" style="color: orange;"></i> Warning: Changing Active SIEM</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          Any parsing/detection rule configurations left undone might return unintended results. Would you like to proceed?
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-danger" data-bs-dismiss="modal" id="cancelSiemChange">Cancel</button>
          <button type="button" class="btn btn-success" data-bs-dismiss="modal" id="confirmSiemChange">Proceed</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Alert Modal for Settings Change -->
  <div class="modal fade" id="settingChangeModal" tabindex="-1" aria-labelledby="siemChangeWarningModalLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="settingChangeModalLabel"></h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body"></div>
        <div class="modal-footer">
          <button type="button" class="btn" data-bs-dismiss="modal">OK</button>
        </div>
      </div>
    </div>
  </div>
  
  <div class="d-flex justify-content-between align-items-center my-4">
    <button id="saveSettingsButton" class="btn btn-primary" onclick="saveSettings()">Save</button>
    <div id="logger"></div>
  </div>
  
</body>
{% endblock %}ENDMSG
```
---
### templates/smartdb.html
```bash
cat > "/opt/SmartSOC/web/templates/smartdb.html" <<"ENDMSG"
{% extends "base.html" %}

{% block content %}
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h2>Smart Dashboard</h2>
    <div class="d-flex align-items-center gap-3">
      <div id="siemStatus" class="siem-status">
        <!-- SIEM status indicators will be populated here -->
      </div>
    </div>
  </div>
  <p>Explore and manage Dashboards.</p>


{% endblock %}

ENDMSG
```
---
### templates/smartlp.html
```bash
cat > "/opt/SmartSOC/web/templates/smartlp.html" <<"ENDMSG"
{% extends "base.html" %}

{% block content %}
<body>
    <!-- Header Section -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h2 class="mb-1">Smart Log Parser</h2>
            <small class="text-muted">Parse and manage log entries with intelligent pattern matching</small>
        </div>
        <div class="d-flex align-items-center gap-3">
            
            <div id="siemStatus" class="siem-status">
                <!-- SIEM status indicators will be populated here -->
            </div>
        </div>
    </div>

    <!-- Control Panel -->
    <div class="card shadow-sm mb-4">
        <div class="card-header bg-light">
            <h6 class="card-title mb-0">
                <i class="fa fa-search me-2"></i>Search & Filter
            </h6>
        </div>
        <div class="card-body">            
            
            <!-- Search Fields Row -->
            <div class="row g-3 mb-3">
                <div class="col-lg-4 col-md-6">
                    <label for="searchId" class="form-label">ID Search</label>
                    <div class="input-group">
                        <span class="input-group-text"><i class="fa fa-tag"></i></span>
                        <input type="text" id="searchId" class="form-control" placeholder="ID or comma-separated IDs..." oninput="searchData()" />
                    </div>
                </div>
                <div class="col-lg-3 col-md-6">
                    <label for="searchLog" class="form-label">Log Content</label>
                    <div class="input-group">
                        <span class="input-group-text"><i class="fa fa-file-text-o"></i></span>
                        <input type="text" id="searchLog" class="form-control" placeholder="Search in log content..." oninput="searchData()" />
                    </div>                    
                </div>
                <div class="col-lg-3 col-md-6">
                    <label for="searchRegex" class="form-label">Regex Pattern</label>
                    <div class="input-group">
                        <span class="input-group-text"><i class="fa fa-code"></i></span>
                        <input type="text" id="searchRegex" class="form-control" placeholder="Search regex patterns..." oninput="searchData()" />
                    </div>
                </div>
                <div class="col-lg-2 col-md-4">
                    <label for="filterStatusSelect" class="form-label">Status Filter</label>
                    <div class="input-group">
                        <span class="input-group-text"><i class="fa fa-filter"></i></span>
                        <select id="filterStatusSelect" class="form-select" onchange="searchData()">
                            <option value="">All Statuses</option>
                        {% for status in statuses %}
                            <option value="{{ status }}">{{ status }}</option>
                        {% endfor %}
                        </select>
                    </div>
                </div>
            </div>

            <!-- Filter and Actions Row -->
            <div class="row g-3 align-items-end">
                <div class="col-lg-2 col-md-6">
                    <button id="clearSearchButton" class="btn btn-secondary" onclick="clearSearch()" title="Clear all search fields">
                        <i class="fa fa-eraser"></i> Reset
                    </button>
                </div>
                
                <div class="col-lg-10 col-md-8">
                    <div class="d-flex flex-wrap gap-2 justify-content-end">
                        <button id="refreshButton" class="btn btn-outline-secondary" onclick="searchData()" title="Refresh data">
                            <i class="fa fa-refresh me-1"></i>Refresh
                        </button>
                        <button class="btn btn-outline-secondary selectEnable" id="clearSelectionButton" onclick="smartlpSelection.clearSelection()" disabled title="Clear selection">
                            <i class="fa fa-times me-1"></i>Clear Selection
                        </button>
                        <button class="btn btn-outline-secondary selectEnable" id="openParserButton" onclick="openParserWindow()" disabled title="Parse selected entries">
                            <i class="fa fa-edit me-1"></i>Parse
                        </button>                        
                        <button class="btn btn-outline-secondary selectEnable" id="openConfigPanel" onclick="handleCreateConfig()" title="Open configuration panel">
                            <i class="fa fa-cog me-1"></i>Open Config Panel
                        </button>
                        <button class="btn btn-outline-secondary selectEnable" id="deleteEntriesButton" onclick="deleteEntries()" disabled title="Delete selected entries">
                            <i class="fa fa-trash me-1"></i>Delete
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>    
    <!-- Pagination Section -->
    <div class="card shadow-sm mb-4">
        <div class="card-body py-3">
            <div class="d-flex flex-column flex-lg-row justify-content-between align-items-center gap-3">
                <!-- Pagination Navigation -->
                <nav aria-label="Page navigation" class="order-2 order-lg-1">
                    <ul class="pagination mb-0 pagination-sm">
                        <!-- Previous Button -->
                        <li id="prevPageItem" class="page-item">
                            <button id="prevPage" class="page-link" onclick="changePage('prev')" title="Previous page">
                                <i class="fa fa-chevron-left me-1"></i>Previous
                            </button>
                        </li>
                    
                        <!-- Page number buttons (dynamically populated) -->
                        <div id="pagination-buttons" class="d-flex align-items-center"></div>
                    
                        <!-- Next Button -->
                        <li id="nextPageItem" class="page-item">
                            <button id="nextPage" class="page-link" onclick="changePage('next')" title="Next page">
                                Next<i class="fa fa-chevron-right ms-1"></i>
                            </button>
                        </li>
                    </ul>
                </nav>                
                <!-- Page Info and Jump -->
                <div class="pagination-controls order-1 order-lg-2">
                    <small class="text-muted" id="pageInfo">
                        <!-- Page info will be populated by JavaScript -->
                    </small>
                    
                    <!-- Rows per page selector -->
                    <div class="rows-per-page-control">
                        <label for="rowsPerPage" class="form-label small mb-0 text-nowrap">Rows:</label>
                        <select id="rowsPerPage" class="form-select form-select-sm" onchange="changeRowsPerPage()" title="Rows per page">
                            <option value="10">10</option>
                            <option value="15" selected>15</option>
                            <option value="20">20</option>
                            <option value="50">50</option>
                            <option value="custom">Custom</option>
                        </select>
                        <input type="number" id="customRowsInput" class="form-control form-control-sm" style="display: none;" 
                               min="1" max="200" placeholder="Custom" title="Custom rows per page" onchange="applyCustomRows()" />
                    </div>
                    
                    <form class="d-flex align-items-center gap-2" id="goToPageForm" onsubmit="event.preventDefault(); changePage(parseInt(document.getElementById('pageInput').value))">
                        <label for="pageInput" class="form-label small mb-0 text-nowrap">Go to:</label>
                        <input type="number" id="pageInput" class="form-control form-control-sm" style="width: 80px;"
                                min="1" placeholder="Page" title="Enter page number" />
                        <button id="goToPage" class="btn btn-outline-primary btn-sm" type="submit" title="Go to page">
                            <i class="fa fa-arrow-right"></i>
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>    
    
    <!-- Entry Modal -->
    <div id="entryModal" class="modal fade" tabindex="-1" aria-labelledby="entryModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-dialog-scrollable">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 class="modal-title" id="entryModalLabel">Entry Details</h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <!-- ID Section -->
                    <div class="mb-3">
                        <label>ID</label>
                        <pre class="bg-light border rounded p-2 text-wrap position-relative">
                            <button class="copy-btn"><i class="fa fa-solid fa-copy"></i></button>
                            <code id="modalId"></code>
                        </pre>
                    </div>
                    <!-- Timestamp Section -->
                    <div class="mb-3">
                        <label data-bs-toggle="tooltip" data-bs-placement="right" data-bs-title="Entry creation timestamp">Timestamp</label>
                        <pre class="bg-light border rounded p-2 text-wrap position-relative">
                            <button class="copy-btn"><i class="fa fa-solid fa-copy"></i></button>
                            <code id="modalTimestamp"></code>
                        </pre>
                    </div>
                    <!-- Index Section -->
                    <div class="mb-3">
                        <label data-bs-toggle="tooltip" data-bs-placement="right" data-bs-title="New index to parse similar logs">Index</label>
                        <input type="text" class="form-control" id="modalIndex">
                    </div>
                    <!-- Source Type Section -->
                    <div class="mb-3">
                        <label data-bs-toggle="tooltip" data-bs-placement="right" data-bs-title="Custom tag for classifying logs">Source Type</label>
                        <input type="text" class="form-control" id="modalSourceType">
                    </div>
                    <!-- Log Type Section -->
                    <div class="mb-3">
                        <label data-bs-toggle="tooltip" data-bs-placement="right" data-bs-title="Logtype as determined by LLM">Suggested Log Type</label>
                        <pre class="bg-light border rounded p-2 text-wrap position-relative" style="min-height: 40px;">
                            <button class="copy-btn"><i class="fa fa-solid fa-copy"></i></button>
                            <code id="modalLogType"></code>
                        </pre>
                    </div>
                    <!-- RuleType Section -->
                    <div class="mb-3">
                        <label data-bs-toggle="tooltip" data-bs-placement="right" data-bs-title="Suggested Rule Types">Suggested Rule Type</label>
                        <pre class="bg-light border rounded p-2 text-wrap position-relative" style="min-height: 40px;">
                            <button class="copy-btn"><i class="fa fa-solid fa-copy"></i></button>
                            <code id="modalRuleTypes"></code>
                        </pre>
                    </div>
                    <!-- Log Section -->
                    <div class="mb-3">
                        <label data-bs-toggle="tooltip" data-bs-placement="right" data-bs-title="Log content">Log</label>
                        <pre class="bg-light border rounded p-2 text-wrap position-relative" style="min-height: 40px;">
                            <button class="copy-btn"><i class="fa fa-solid fa-copy"></i></button>
                            <code id="modalLog"></code>
                        </pre>
                    </div>
                    <!-- Regex Section -->
                    <div class="mb-3">
                        <label  data-bs-toggle="tooltip" data-bs-placement="right" data-bs-title="LLM-generated regex for the log">Regex</label>
                        <pre class="bg-light border rounded p-2 text-wrap position-relative" style="min-height: 40px;">
                            <button class="copy-btn"><i class="fa fa-solid fa-copy"></i></button>
                            <code id="modalRegex"></code>
                        </pre>
                    </div>
                    <!-- Status Section -->
                    <div class="mb-3">
                        <label data-bs-toggle="tooltip" data-bs-placement="right" data-bs-title="Log's parsing state">Status</label>
                        <pre class="bg-light border rounded p-2 text-wrap position-relative" style="min-height: 40px;">
                            <button class="copy-btn"><i class="fa fa-solid fa-copy"></i></button>
                            <code id="modalStatus"></code>
                        </pre>
                    </div>
                    <div class="mb-3">
                        <label data-bs-toggle="tooltip" data-bs-placement="right" data-bs-title="Retrieved from following SIEM">SIEM</label>
                        <pre class="bg-light border rounded p-2 text-wrap position-relative" style="min-height: 40px;">
                            <button class="copy-btn"><i class="fa fa-solid fa-copy"></i></button>
                            <code id="modalSiem"></code>
                        </pre>
                    </div>
                    <div class="mb-3">
                        <label data-bs-toggle="tooltip" data-bs-placement="right" data-bs-title="Retrieved using following search query">Query</label>
                        <pre class="bg-light border rounded p-2 text-wrap position-relative" style="min-height: 40px;">
                            <button class="copy-btn"><i class="fa fa-solid fa-copy"></i></button>
                            <code id="modalQuery"></code>
                        </pre>
                    </div>
                </div>
                <div id="modalButtons" class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button class="btn btn-outline-secondary modalButton" id="openParserButton" onclick="openParserWindow()">
                        <i class="fa fa-edit"></i> Parse
                    </button>
                    <button class="btn btn-outline-secondary modalButton" id="deleteEntriesButton" onclick="deleteEntries()">
                        <i class="fa fa-trash"></i> Delete
                    </button>
                    <button class="btn btn-outline-secondary" id="saveEntryChangesBtn">
                        <i class="fa fa-save"></i> Save Changes
                    </button>
                    <button class="btn btn-outline-secondary" id="openConfigPanelBtn" onclick="handleCreateConfig()">
                        <i class="fa fa-cog"></i> Open Config Panel
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Results Table -->
    <div class="card shadow-sm">
        <div class="card-header bg-light d-flex justify-content-between align-items-center">
            <h6 class="card-title mb-0">
                <i class="fa fa-table me-2"></i>Log Entries
            </h6>            <small class="text-muted" id="resultsCount">
                <!-- Results count will be populated by JavaScript -->
            </small>
            <div id="smartlpLogger" class="badge bg-info fs-6"></div>
        </div>
        <div class="card-body p-0">
            <div class="table-responsive">
                <table id="entryTable" class="table table-hover mb-0 entry-table">
                    <thead class="table-light sticky-top">
                        <tr>
                            <th id="entry_id" class="fw-semibold">
                                <i class="fa fa-tag me-1"></i>ID
                            </th>
                            <th id="entry_timestamp" class="fw-semibold" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Entry creation timestamp">
                                <i class="fa fa-clock-o me-1"></i>Timestamp
                            </th>
                            <th id="entry_log" class="fw-semibold">
                                <i class="fa fa-file-text-o me-1"></i>Log Content
                            </th>
                            <th id="entry_regex" class="fw-semibold" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="LLM-generated regex for the log">
                                <i class="fa fa-code me-1"></i>Regex Pattern
                            </th>
                            <th id="entry_status" class="fw-semibold" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Log's parsing state">
                                <i class="fa fa-info-circle me-1"></i>Status
                            </th>
                            <th id="entry_action" class="fw-semibold text-center" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Use checkboxes for bulk actions">
                                <i class="fa fa-check-square-o me-1"></i>Select
                            </th>
                        </tr>
                    </thead>
                    <tbody id="entryTableBody">
                        <!-- Results will be dynamically inserted here -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Configuration Panel -->
    <div id="popupBox" class="popup-box collapsed">
        <div class="popup-header" onclick="togglePopup()">
            <button class="arrow-btn"><i class="fa fa-chevron-up"></i></button>
            <span class="flex-grow-1 text-center">Configuration Panel</span>
        </div>        
        <div class="popup-content">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Smart Log Config</h5>
                <small class="text-muted" id="configSelectionCounter">
                    <i class="fa fa-list me-1"></i>
                    <span id="configSelectionCount">0</span> entries
                </small>
            </div>

            <div class="table-responsive">            
                <table id="configTable" class="table table-bordered table-hover table-striped entry-table">
                    <thead class="table-light">
                    <tr>
                        <th id="entry_id">ID</th>
                        <th id="entry_timestamp" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Entry creation timestamp">Time</th>
                        <th id="entry_index" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="New index to parse similar logs">Index</th>
                        <th id="entry_sourcetype"data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Custom tag for classifying logs">SourceType</th>
                        <th id="entry_log">Log</th>
                        <th id="entry_action" class="text-center" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Remove from configuration">Action</th>
                    </tr>
                    </thead>
                    <tbody id="configTableBody">
                        {% for entry in entries %}
                            <tr>
                                <td>{{ entry.id }}</td>
                                <td>{{ entry.timestamp }}</td>
                                <td>{{ entry.index }}</td>
                                <td>{{ entry.source_type }}</td>
                                <td>{{ entry.log }}</td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
                <div id="smartlpConfigLogger"></div>
                <button type="button" class="btn btn-primary btn-sm" id="validateAndConfig">
                    <i class="fa fa-upload"></i> Create Config
                </button>
            </div>
        </div>
    </div>

    <!-- Config Modal -->
    <div id="configModal" class="modal fade" tabindex="-1" aria-labelledby="configModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-dialog-scrollable">
            <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="configModalLabel">Generated Config</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <div class="codeblock-with-lines">
                    <pre class="bg-light border rounded mb-0 p-3" style="position:relative; overflow:auto;">
<code id="configPreview" class="config-preview" style="white-space:pre; display:block;">Placeholder config will appear here...</code>
                    </pre>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                <button class="btn btn-success" onclick="deploy()">Deploy</button>
                <button class="btn btn-success" id="hfBtn" onclick="deployHF()" style="display: none;">Deploy to HF</button>
                <!-- Add deployment feedback area -->
                <div id="deploymentFeedback" class="w-100 mt-2" style="display: none;">
                    <div class="alert mb-0" role="alert" id="deploymentMessage"></div>
                </div>
            </div>
            </div>
        </div>
    </div>

    <!-- Error Modal -->
    <div id="errorModal" class="modal fade" tabindex="-1" aria-labelledby="errorModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-scrollable">
            <div class="modal-content">
                <div class="modal-header">
                    <label class="modal-title" id="errorModalLabel"><i class="fa fa-exclamation-triangle" style="color: #ffa70f;"></i> Error</label>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p id="errorMessage"></p>
                </div>
            </div>
        </div>
    </div>
</body>
<script src="/js/smartlp/smartlp.js"></script>
{% endblock %}
ENDMSG
```
---
### templates/smartlp_parser.html
```bash
cat > "/opt/SmartSOC/web/templates/smartlp_parser.html" <<"ENDMSG"
{% extends "base.html" %}

{% block content %}
<body>
<div class="container">
    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="mb-0">Parser</h2>
        <div class="d-flex gap-2 align-items-center ">
            
            <button id="clearEntryButton" onclick="clearEntry()" class="btn btn-primary" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Clear all fields">
                Clear
            </button>
            <button id="pullEntryButton" onclick="pullEntry()" class="btn btn-primary" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Pull the latest Unmatched entry">
                Pull Unmatched
            </button>
        </div>
    </div>

    <!-- Main Content -->
    <div class="row">
        <!-- Left Column -->
        <div id="leftColumn" class="col-md-8">
            <!-- REGEX Section -->
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h5 class="mb-0">REGEX</h5>
                <div class="d-flex gap-2">
                    <button class="btn btn-secondary" onclick="reduceRegex()" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Returns the longest matching regex sequence.">
                        Reduce
                    </button>
                    <button id="generateButton"class="btn btn-secondary aiButton" onclick="queryLLM('generate')" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Use AI to generate a regex for the log..">
                        <img src="/smartlp_ai_icon/ai2.png" width="20" height="20"> Generate
                        <span id="generateSpinner" class="spinner-border spinner-border-sm ms-1 d-none" role="status" aria-hidden="true"></span>
                    </button>
                </div>
            </div>
            <textarea id="regexDisplay" class="form-control mb-3" placeholder="Generate/Add/Edit regex here" oninput="findMatch()"></textarea>

            <!-- LOG Section -->
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h5 class="mb-0">LOG</h5>
                <button id="fixButton" class="btn btn-secondary aiButton" onclick="queryLLM('fix')" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Use AI to improve or correct the current regex.">
                    <img src="/smartlp_ai_icon/ai2.png" width="20" height="20"> Fix
                    <span id="fixSpinner" class="spinner-border spinner-border-sm ms-1 d-none" role="status" aria-hidden="true"></span>
                </button>
            </div>
            <pre class="bg-light border rounded p-2 text-wrap position-relative mb-3">
                <button class="copy-btn"><i class="fa fa-solid fa-copy"></i></button>
                <code id="logDisplay"></code>
            </pre>
        </div>

        <!-- Right Column -->
        <div id="rightColumn" class="col-md-4">
            <div class="d-flex flex-row justify-content-between">
                <h5 class="mb-3">MATCHES</h5>
                <div id="matchLogger"></div>
            </div>
            <div id="matchDisplay" class="bg-light rounded p-2">Matches appear here</div>
        </div>
    </div>

    <!-- Footer -->
    <div class="d-flex justify-content-between align-items-center mt-4">
        <button id="backButton" class="btn btn-outline-secondary" onclick="window.location.href='/smartlp'">
            &lt; Back
        </button>
        <div id=logger></div>
        <button id="saveToDBButton" class="btn btn-primary" onclick="saveToDB()">
            <i class="fa fa-database"></i> Save to Database
            <span id="saveToDBSpinner" class="spinner-border spinner-border-sm ms-1 d-none" role="status" aria-hidden="true"></span>
        </button>
    </div>
</div>
</body>
<script src="/js/smartlp/parser.js"></script>
{% endblock %}
ENDMSG
```
---
### templates/smartlp_prefix.html
```bash
cat > "/opt/SmartSOC/web/templates/smartlp_prefix.html" <<"ENDMSG"
{% extends "base.html" %}

{% block content %}
<body>
  <div class="container">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2>Prefix</h2>
      <p>Add Prefix Regex to database.</p>
    </div>
    <h3>Prefix Regex</h3>
    <div class="row">
      <div class="col-7">
        <div class="form-group mb-3">
          <div class="form-label">Input Prefix Regex:</div>
          <div id="prefixErrorMsg" class="alert alert-danger d-none" role="alert">
            Could not connect to the backend database. Prefixes cannot be loaded or saved.
          </div>
          <div class="input-group mb-3">
            <textarea type="text" id="newPrefixInput" class="form-control" placeholder="Enter new prefix regex"></textarea>
            <button id="addPrefixBtn" class="btn btn-outline-primary" type="button" onclick="addPrefix()">
              <i class="fa fa-plus" aria-hidden="true"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div class="pagination d-flex justify-content-center align-items-center flex-wrap gap-2 my-3" id="paginationControls"></div>

    <!-- Results Table -->
    <div class="table-responsive ">
      <table id="entryTable" class="table table-striped table-bordered table-hover entry-table">
        <thead>
          <tr>
            <th id="entry_id" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Entry Index">ID</th>
            <th id="entry_regex" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="LLM-generated regex for the prefix header">Regex</th>
            <th id="entry_action" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Click the button to remove entry">Action</th>
          </tr>
        </thead>
        <tbody>                  
          <!-- Results will be dynamically inserted here -->
        </tbody>
      </table>
    </div>        
  </div>
</body>
<script src="/js/smartlp/prefix.js"></script>
{% endblock %}ENDMSG
```
---
### templates/smartlp_report.html
```bash
cat > "/opt/SmartSOC/web/templates/smartlp_report.html" <<"ENDMSG"
{% extends "base.html" %}

{% block content %}
<body>
<div class="container">
    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="mb-1">SmartLP Summary Report</h2>
        <div class="d-flex gap-2 align-items-center">
            <button id="refreshButton" class="btn btn-primary" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Refresh data">
                Refresh
            </button>
        </div>
    </div>

    <!-- Main Content -->
    <div class="row p-4">
        <!-- Report header -->
        <div class="pdf-only flex-column justify-content-between align-items-center" id="content1">
            <h1 class="data-bs-title mt-5">SMARTLP Report</h1>
            <img class="mt-5" src="/logos/logo.png" height="200"></image>
            <div class="mt-5">Generated at <time id="datetime"></time></div>
        </div>

        <!-- Logs Parsed Chart Section -->
        <div class="d-flex flex-column mb-4 align-items-center" id="content2">
            <h2 class="data-bs-title mt-5 mb-5">Percentage of Unparsed Logs</h4>
            <div>
                <div class="mb-5">
                    <canvas id="parsed-chart"></canvas>
                </div>
                <div class="table-responsive mb-2">
                    <table class="table" id="logParsedTable">
                        <thead class="table-light sticky-top">
                            <tr><th>Type of Log</th><th>LogType Count</th></tr>
                        </thead>
                        <tbody id="logParsedBody">
                            <!-- Results will be dynamically inserted here -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Top Logtype Chart Section -->
        <div class="d-flex flex-column mb-4 align-items-center" id="content3">
            <h2 class="data-bs-title mt-5 mb-5">Top 5 types of Unparsed Log</h4>
            <div class="table-responsive mb-2">
                <table class="table" id="logStatsTable">
                    <thead class="table-light sticky-top">
                        <tr><th>Log Type</th><th>Count</th></tr>
                    </thead>
                    <tbody id="logStatsBody">
                        <!-- Results will be dynamically inserted here -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <div class="d-flex justify-content-between align-items-center mt-2">
        <button id="backButton" class="btn btn-outline-secondary" onclick="window.location.href='/smartlp'">
            &lt; Back
        </button>
        <div id=logger></div>
        <button id="saveButton" class="btn btn-primary" data-bs-toggle="tooltip" data-bs-placement="top" data-bs-title="Save Report">
            <i class="fa fa-save"></i> Save Report
        </button>
    </div>
</div>
</body>
<script src="/js/smartlp/report.js"></script>
{% endblock %}
ENDMSG
```
---
### templates/smartuc_attacknavigator.html
```bash
cat > "/opt/SmartSOC/web/templates/smartuc_attacknavigator.html" <<"ENDMSG"
{% extends "base.html" %}

{% block content %}
<style>
    .mitre-matrix-container {
        display: flex;
        overflow-x: auto; /* Allow horizontal scrolling */
        padding-bottom: 15px; /* Space for scrollbar */
        border: 1px solid #ccc;
        background-color: #f8f9fa;
    }
    .tactic-column {
        min-width: 180px; /* Minimum width for each column */
        max-width: 220px; /* Maximum width */
        flex: 1 1 180px; /* Flex properties: grow, shrink, basis */
        border-left: 1px solid #ddd;
        padding: 0;
        display: flex;
        flex-direction: column; /* Stack header and techniques vertically */
    }
    .tactic-column:first-child {
        border-left: none;
    }
    .tactic-header {
        background-color: #e9ecef;
        padding: 8px 10px;
        font-weight: bold;
        text-align: center;
        border-bottom: 1px solid #ccc;
        position: sticky; /* Make header sticky */
        top: 0; /* Stick to the top */
        z-index: 10; /* Ensure it's above technique cells */
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .techniques-list {
        padding: 5px;
        flex-grow: 1; /* Allow list to take remaining space */
        overflow-y: auto; /* Allow vertical scroll within column if needed */
    }
    .technique-cell {
        background-color: #fff;
        border: 1px solid #eee;
        border-radius: 3px;
        padding: 4px 6px;
        margin-bottom: 4px;
        font-size: 0.85rem; /* Smaller font */
        line-height: 1.3;
        overflow: hidden; /* Prevent long names from breaking layout */
        white-space: normal; /* Allow wrapping */
        word-wrap: break-word;
    }
    .technique-cell a {
        color: #0056b3;
        text-decoration: none;
        display: block; /* Make the whole cell clickable */
    }
     .technique-cell a:hover {
        text-decoration: underline;
    }
    .subtechnique {
        margin-left: 10px; /* Indent sub-techniques */
        border-left: 3px solid #007bff; /* Add a visual indicator */
        padding-left: 8px; /* Adjust padding */
    }
</style>

<div class="container-fluid mt-3"> {# Use container-fluid for full width #}
    <h1>MITRE ATT&CK Matrix (Enterprise)</h1>
    <p>Techniques present in the local database.</p>
     <a href="{{ url_for('smartuc') }}" class="btn btn-secondary mb-3">Back to Sigma Rules</a>

    <div class="mitre-matrix-container">
        {% for tactic_phase in tactic_order %}
            <div class="tactic-column">
                <div class="tactic-header" title="{{ tactic_names.get(tactic_phase, tactic_phase) }}">
                    {{ tactic_names.get(tactic_phase, tactic_phase) }}
                </div>
                <div class="techniques-list">
                    {% set techniques = techniques_by_tactic.get(tactic_phase, []) %}
                    {% if techniques %}
                        {% for tech in techniques %}
                            <div class="technique-cell {% if tech.is_subtechnique %}subtechnique{% endif %}"
                            title="{{ tech.name }} ({{ tech.mitre_id }})&#10;{{ tech.description | default('', true) | truncate(150, true) }}"> {# Tooltip with description #}
                           {# --- Display text directly without the <a> tag --- #}
                           {{ tech.name }}
                           <small>({{ tech.mitre_id }})</small> {# Smaller ID #}
                       </div>
                        {% endfor %}
                    {% else %}
                        <div class="p-2 text-muted small">No techniques</div>
                    {% endif %}
                </div>
            </div>
        {% endfor %}
    </div>
</div>
{% endblock %}ENDMSG
```
---
### templates/smartuc.html
```bash
cat > "/opt/SmartSOC/web/templates/smartuc.html" <<"ENDMSG"
{% extends "base.html" %}

{% block content %}

<!-- Header Section -->
<div class="d-flex justify-content-between align-items-center mb-4">
    <div>
        <h2 class="mb-1">Smart Use Case</h2>
        <small class="text-muted">Browse and explore security detection rules with advanced filtering</small>
    </div>
    <div class="d-flex align-items-center gap-3">
        <div id="siemStatus" class="siem-status">
            <!-- SIEM status indicators will be populated here -->
        </div>
    </div>
</div>

<!-- Search and Filter Panel -->
<div class="card shadow-sm mb-4">
    <div class="card-header bg-light">
        <h6 class="card-title mb-0">
            <i class="fa fa-search me-2"></i>Search & Filter Rules
        </h6>
    </div>    
    <div class="card-body">
        <form method="GET" action="{{ url_for('smartuc') }}" class="smartuc-search-form row g-3 align-items-end">
            <!-- Hidden Page Reset -->
            <input type="hidden" name="page" value="1">

            <!-- Search Term -->
            <div class="col-lg-6 col-md-6">
                <label for="search" class="form-label">Search Term</label>
                <div class="input-group">
                    <span class="input-group-text"><i class="fa fa-search"></i></span>
                    <input type="text" class="form-control" id="search" name="search" 
                           value="{{ search_query or '' }}" placeholder="Search in titles and descriptions...">
                </div>
            </div>

            <!-- Main Type -->
            <div class="col-lg-3 col-md-6">
                <label for="main_type" class="form-label">Main Category</label>
                <div class="input-group">
                    <span class="input-group-text"><i class="fa fa-folder-o"></i></span>
                    <select class="form-select" id="main_type" name="main_type">
                        <option value="all" {% if selected_main_type == 'all' %}selected{% endif %}>All Categories</option>
                        {% for type in main_types %}
                            <option value="{{ type }}" {% if type == selected_main_type %}selected{% endif %}>{{ type }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>

            <!-- Sub Type -->
            <div class="col-lg-3 col-md-6">
                <label for="sub_type" class="form-label">Sub Category</label>
                <div class="input-group">
                    <span class="input-group-text"><i class="fa fa-tags"></i></span>
                    <select class="form-select" id="sub_type" name="sub_type">
                        <option value="all" {% if selected_sub_type == 'all' %}selected{% endif %}>All Sub Categories</option>
                        {% for type in sub_types %}
                            <option value="{{ type }}" {% if type == selected_sub_type %}selected{% endif %}>{{ type }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="mt-3 d-flex flex-wrap gap-2 justify-content-between">
                <div class="smartuc-action-buttons d-flex gap-2">
                    <button type="submit" class="btn btn-primary" title="Apply filters and search">
                        <i class="fa fa-filter me-1"></i>Apply Filters
                    </button>
                    <a href="{{ url_for('smartuc') }}" class="btn btn-secondary" title="Clear all filters">
                        <i class="fa fa-eraser me-1"></i>Reset
                    </a>
                </div>
                <div class="d-flex gap-2">
                    <button type="button" class="btn btn-outline-secondary selectEnable" id="clearSelection" title="Clear selected rules" onclick="smartucSelection.clearSelection()">
                        <i class="fa fa-times me-1"></i>Clear Selection
                    </button>
                    <button type="button" class="btn btn-outline-secondary selectEnable" id="openConfigPanel" title="Open Configuration Panel" onclick="handleCreateConfig()">
                        <i class="fa fa-cog me-1"></i>Open Config Panel
                    </button>
                </div>
            </div>
        </form>        
        
    </div>
</div>
<!-- Pagination Section -->
{% if total_pages > 1 %}
<div class="card shadow-sm mb-4">
    <div class="card-body py-3">
        <div class="d-flex flex-column flex-lg-row justify-content-between align-items-center gap-3">
            <!-- Pagination Navigation -->
            <nav aria-label="Page navigation" class="order-2 order-lg-1">
                <ul class="pagination mb-0 pagination-sm">
                    <!-- Previous Page -->
                    <li class="page-item {% if page <= 1 %}disabled{% endif %}">
                        <a class="page-link" href="{{ url_for('smartuc',
                                                              page=page-1,
                                                              per_page=per_page,
                                                              search=search_query if search_query else None,
                                                              main_type=selected_main_type,
                                                              sub_type=selected_sub_type) }}" title="Previous page">
                            <i class="fa fa-chevron-left me-1"></i>Previous
                        </a>
                    </li>

                    <!-- Page Numbers -->
                    {% for p in page_links %}
                        {% if p %}
                            <li class="page-item {% if p == page %}active{% endif %}">
                                <a class="page-link" href="{{ url_for('smartuc',
                                                                      page=p,
                                                                      per_page=per_page,
                                                                      search=search_query if search_query else None,
                                                                      main_type=selected_main_type,
                                                                      sub_type=selected_sub_type) }}">{{ p }}</a>
                            </li>
                        {% else %}
                            <li class="page-item disabled"><span class="page-link">...</span></li>
                        {% endif %}
                    {% endfor %}

                    <!-- Next Page -->
                    <li class="page-item {% if page >= total_pages %}disabled{% endif %}">
                        <a class="page-link" href="{{ url_for('smartuc',
                                                              page=page+1,
                                                              per_page=per_page,
                                                              search=search_query if search_query else None,
                                                              main_type=selected_main_type,
                                                              sub_type=selected_sub_type) }}" title="Next page">
                            Next<i class="fa fa-chevron-right ms-1"></i>
                        </a>
                    </li>
                </ul>
            </nav>            <!-- Page Info and Jump -->
            <div class="pagination-controls order-1 order-lg-2 pe-3">
                <small class="text-muted">
                    {% if rules %}
                        Page {{ page }} of {{ total_pages }} ({{ ((page-1) * per_page + 1) }}-{{ [page * per_page, rules|length + (page-1) * per_page]|min }} of {{ total_rules }} rules)
                    {% else %}
                        No rules found
                    {% endif %}
                </small>
                
                <!-- Rows per page selector -->
                <div class="rows-per-page-control">
                    <label for="rowsPerPage" class="form-label small mb-0 text-nowrap">Rows:</label>
                    <select id="rowsPerPage" class="form-select form-select-sm" onchange="changeRowsPerPage()" title="Rows per page">
                        <option value="10" {% if per_page == 10 %}selected{% endif %}>10</option>
                        <option value="15" {% if per_page == 15 %}selected{% endif %}>15</option>
                        <option value="20" {% if per_page == 20 %}selected{% endif %}>20</option>
                        <option value="50" {% if per_page == 50 %}selected{% endif %}>50</option>
                        <option value="custom" {% if per_page not in [10, 15, 20, 50] %}selected{% endif %}>Custom</option>
                    </select>
                    <input type="number" id="customRowsInput" class="form-control form-control-sm"
                           {% if per_page in [10, 15, 20, 50] %}style="display: none;"{% endif %}
                           min="1" max="200" placeholder="Custom" title="Custom rows per page" 
                           value="{% if per_page not in [10, 15, 20, 50] %}{{ per_page }}{% endif %}" 
                           onchange="applyCustomRows()" />
                </div>
                
                <form id="goToPageForm"
                      class="d-flex align-items-center gap-2"
                      data-total-pages="{{ total_pages }}"
                      data-base-url="{{ url_for('smartuc') }}"
                      data-per-page="{{ per_page }}"
                      data-search="{{ search_query if search_query else '' }}"
                      data-main-type="{{ selected_main_type }}"
                      data-sub-type="{{ selected_sub_type }}">
                    <label for="goToPageInput" class="form-label small mb-0 text-nowrap">Go to:</label>
                    <input type="number"
                           id="goToPageInput"
                           class="form-control form-control-sm"
                           style="width: 80px;"
                           placeholder="Page"
                           min="1"
                           max="{{ total_pages }}"
                           title="Enter page number">                    
                    <button class="btn btn-primary-outline btn-sm" type="submit" title="Go to page">
                        <i class="fa fa-arrow-right"></i>
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endif %}
<!-- Results Table -->
<div class="card shadow-sm">
    <div class="card-header bg-light d-flex justify-content-between align-items-center">
        <h6 class="card-title mb-0">
            <i class="fa fa-list me-2"></i>Detection Rules
            {% if rules %}
                <span class="badge bg-primary ms-2">{{ rules|length }} rules</span>
            {% endif %}
        </h6>
        {% if rules %}
            <small class="text-muted">
                Showing {{ ((page-1) * per_page + 1) }}-{{ [page * per_page, rules|length + (page-1) * per_page]|min }} of {{ total_rules }}
            </small>
        {% endif %}        <div>
            <div id="smartucLogger" class="badge bg-info fs-6"></div>
        </div>
    </div>
    <div class="card-body p-0">
        {% if rules %}
            <div class="table-responsive">                
                <table class="table table-hover mb-0 rules-table">
                    <thead class="table-light">
                        <tr>
                            <th style="width: 25%;">
                                <i class="fa fa-file-text-o me-1"></i>Title
                            </th>
                            <th style="width: 30%;">
                                <i class="fa fa-info-circle me-1"></i>Description
                            </th>
                            <th style="width: 15%;">
                                <i class="fa fa-tag me-1"></i>Type
                            </th>
                            <th style="width: 10%;">
                                <i class="fa fa-exclamation-triangle me-1"></i>Level
                            </th>
                            <th style="width: 10%;" class="text-center">
                                <i class="fa fa-eye me-1"></i>Actions
                            </th>                        
                            <th style="width: 10%;" class="text-center">
                                <i class="fa fa-check-square-o me-1"></i>Select
                            </th>
                        </tr>
                    </thead>
                    <tbody id="entryTableBody">
                        {% for rule in rules %}                        
                        <tr class="rule-row" data-rule-id="{{ rule.id }}">
                            <td class="title-cell fw-semibold">
                                {{ rule.title }}
                            </td>
                            <td class="description-cell text-muted">
                                {{ rule.description }}
                            </td>
                            <td>
                                <span class="badge bg-secondary">{{ rule.get('rule_type', 'N/A') }}</span>
                            </td>
                            <td>
                                {% set level_class = 'warning' if rule.level == 'medium' else 'danger' if rule.level == 'high' else 'info' if rule.level == 'low' else 'secondary' %}
                                <span class="badge bg-{{ level_class }}">{{ rule.level|title }}</span>
                            </td>                            
                            <td>
                                <div class="d-flex flex-column gap-1">
                                    <button type="button" 
                                        class="btn btn-outline-primary btn-sm"
                                        data-bs-toggle="modal"
                                        data-bs-target="#yamlModal"
                                        data-rule-id="{{ rule.id }}"
                                        title="View YAML Rule">
                                        <i class="fa fa-code me-1"></i>YAML
                                    </button>
                                    <button type="button" 
                                            class="btn btn-outline-secondary btn-sm"
                                            data-bs-toggle="modal"
                                            data-bs-target="#siemRuleModal"
                                            data-rule-id="{{ rule.id }}"
                                            title="View {{ activeSiem|title }} Rule">
                                        <i class="fa fa-shield me-1"></i>{{ activeSiem|title }}
                                    </button>
                                </div>
                                    
                            </td>
                            <td class="text-center">
                                <input type="checkbox" class="form-check-input" id="ruleSelect{{ rule.id }}" name="ruleSelect" value="{{ rule.id }}">
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        {% else %}
            <div class="text-center py-5">
                <div class="mb-3">
                    <i class="fa fa-search text-muted" style="font-size: 3rem;"></i>
                </div>
                <h5 class="text-muted">No Rules Found</h5>
                <p class="text-muted mb-4">No detection rules match your current search criteria.</p>                <a href="{{ url_for('smartuc') }}" class="btn btn-secondary">
                    <i class="fa fa-refresh me-1"></i>Reset Filters
                </a>
            </div>
        {% endif %}
    </div>
</div>

<!-- Config Panel Popup (SmartUC) -->
<div id="popupBox" class="popup-box collapsed">
    <div class="popup-header" onclick="smartucConfigPanel.togglePanel()">
        <button class="arrow-btn"><i class="fa fa-chevron-up"></i></button>
        <span class="flex-grow-1 text-center">Configuration Panel</span>
    </div>
    <div class="popup-content">
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="mb-0">SmartUC Config</h5>
            <small class="text-muted" id="configSelectionCounter">
                <i class="fa fa-list me-1"></i>
                <span id="configSelectionCount">0</span> rules
            </small>
        </div>        
        <div class="table-responsive mb-3">
            <table class="table table-bordered table-sm mb-0">
                <thead class="table-light">
                    <!-- Dynamic headers will be rendered by JavaScript -->
                </thead>
                <tbody id="configTableBody">
                    <tr><td colspan="6" class="text-center text-muted">No entries selected</td></tr>
                </tbody>
            </table>
        </div>        
        <div id="smartucConfigLogger"></div>
        <div class="d-flex justify-content-end gap-2">
            <button class="btn btn-secondary" onclick="smartucConfigPanel.togglePanel()">
                <i class="fa fa-times me-1"></i>Close
            </button>
            <button class="btn btn-success" id="createConfig">
                <i class="fa fa-upload me-1"></i>Create Config
            </button>        
        </div>
        
    </div>
</div>

<!-- YAML Rule Modal -->
<div class="modal fade" id="yamlModal" tabindex="-1" aria-labelledby="yamlModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="yamlModalLabel">
                    <i class="fa fa-code me-2"></i>YAML Rule Details
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body p-0">                
                <div class="position-relative">
                    <pre class="bg-light border-0 rounded-0 p-4 m-0 text-wrap position-relative" style="max-height: 70vh; overflow-y: auto; font-size: 0.875rem; line-height: 1.4; width: 97%;">
                        <code id="yamlContent" class="text-dark">Loading rule details...</code>
                    </pre>
                    <button class="copy-btn btn btn-secondary btn-sm position-absolute" 
                            style="top: 0.5rem; right: 0.1rem; z-index: 10;" 
                            title="Copy to clipboard">
                        <i class="fa fa-copy me-1"></i>
                    </button>
                </div>
            </div>
            <div class="modal-footer">
                <div class="d-flex justify-content-between w-100 align-items-center">
                    <small class="text-muted">
                        <i class="fa fa-info-circle me-1"></i>YAML format detection rule
                    </small>
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        <i class="fa fa-times me-1"></i>Close
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- SIEM Rule Modal -->
<div class="modal fade" id="siemRuleModal" tabindex="-1" aria-labelledby="siemRuleModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="siemRuleModalLabel">
                    <i class="fa fa-shield me-2"></i>{{ activeSiem|title }} Rule
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body p-0">                
                <div class="position-relative">
                    <pre class="bg-light border-0 rounded-0 p-4 m-0 text-wrap position-relative" style="max-height: 70vh; overflow-y: auto; font-size: 0.875rem; line-height: 1.4; width: 97%;">
                        <code id="siemRuleContent" class="text-dark">Loading {{ activeSiem }} rule...</code>
                    </pre>
                    <button class="copy-btn btn btn-secondary btn-sm position-absolute" 
                                style="top: 0.5rem; right: 0.1rem; z-index: 10;" 
                                title="Copy to clipboard">
                        <i class="fa fa-copy me-1"></i>
                    </button>
                </div>
            </div>            <div class="modal-footer">
                <div class="d-flex justify-content-between w-100 align-items-center">
                    <small class="text-muted">
                        <i class="fa fa-shield me-1"></i>{{ activeSiem|title }} format detection rule
                    </small>
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        <i class="fa fa-times me-1"></i>Close
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Config Modal -->
<div id="configModal" class="modal fade" tabindex="-1" aria-labelledby="configModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
        <div class="modal-header">
            <h5 class="modal-title" id="configModalLabel">Generated Config</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
            <div class="codeblock-with-lines">
                <pre class="bg-light border rounded mb-0 p-3" style="position:relative; overflow:auto;">
<code contenteditable="true" spellcheck="false" id="configPreview" class="config-preview" style="white-space:pre; display:block;">Placeholder config will appear here...</code>
                </pre>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            <button class="btn btn-success" onclick="deploy()">Deploy</button>
            <button class="btn btn-success"  id="hfBtn" onclick="deployHF()" style="display: none;">Deploy to HF</button>
            <!-- Add deployment feedback area -->
            <div id="deploymentFeedback" class="w-100 mt-2" style="display: none;">
                <div class="alert mb-0" role="alert" id="deploymentMessage"></div>
            </div>
        </div>
        </div>    </div>
</div>

<!-- Error Modal -->
<div id="errorModal" class="modal fade" tabindex="-1" aria-labelledby="errorModalLabel" aria-hidden="true" data-bs-backdrop="true" data-bs-keyboard="true">
    <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
            <div class="modal-header">
                <label class="modal-title" id="errorModalLabel"><i class="fa fa-exclamation-triangle" style="color: #ffa70f;"></i> Error</label>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <p id="errorMessage"></p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            </div>
        </div>
    </div>
</div>

{# --- JavaScript for Modal and Page Jump --- #}
<script src="/js/smartuc/smartuc.js"></script>
{% endblock %}ENDMSG
```
---
### templates/smartuc_rule_detail.html
```bash
cat > "/opt/SmartSOC/web/templates/smartuc_rule_detail.html" <<"ENDMSG"
{% extends "base.html" %}

{% block content %}
<div class="container mt-4">
<h2>Settings</h2>
<p>Configure SmartSOC settings.</p>

<div class="container">
  <h1>Sigma Rule Details</h1>
  <a href="{{ url_for('smartuc') }}" class="btn btn-primary mb-3">Back to List</a>
   <pre>{{ rule }}</pre>
</div>
</div>
{% endblock %}

ENDMSG
```
---
