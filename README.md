# SmartLP Platform
- [Introduction](#introduction)

Smart Log Parer (SmartLP) is a modular platform that automates log parsing, regex generation, and use-case deployment across multiple SIEM platforms. The project now follows a services-first architecture with a unified Flask/Socket.IO backend, a MongoDB data layer, and a Retrieval-Augmented Generation (RAG) pipeline for SIEM field intelligence.

## Table of Contents
- [Overview](#overview)
- [Solution Architecture](#solution-architecture)
- [Directory Map](#directory-map)
- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Environment Variables](#environment-variables)
    - [Install Dependencies](#install-dependencies)
    - [Run The Application](#run-the-application)
- [Core Services](#core-services)
    - [SmartLP Service](#smartlp-service)
    - [Settings Service](#settings-service)
    - [SIEM Service Factory](#siem-service-factory)
    - [LLM Service](#llm-service)
    - [Deployment Service](#deployment-service)
- [Frontend Experience](#frontend-experience)
- [RAG Pipeline](#rag-pipeline)
- [REST API Cheatsheet](#rest-api-cheatsheet)
- [MongoDB Collections](#mongodb-collections)
- [Automation Scripts](#automation-scripts)
- [Troubleshooting](#troubleshooting)
- [Maintenance Tips](#maintenance-tips)

## Overview

SmartSOC focuses on two flagship capabilities:

- **SmartLP (Log Parser)** – Automates regex creation, log similarity detection, and SIEM-ready configuration exports. SmartLP uses LLM assistance, background ingestion jobs, and a prefix library to accelerate analyst workflows.
- **SmartReport** – Delivers real-time visibility and operational controls. Socket.IO streams keep the UI, notification toasts, and log panels synchronized with backend events.

Key highlights of the current codebase:
- Flask 3 + Flask-SocketIO entry point (`app.py` via `ApplicationFactory`)
- MongoDB-backed service layer (`src/services/…`) with reusable CRUD helpers
- Background ingestion thread managed inside the SmartLP service
- RAG-ready embeddings (ChromaDB) populated through `setup_rag.py`
- Ansible-driven deployment workflows wired into REST endpoints

## Solution Architecture

- **Backend**: Flask application factory (`src/core/app_factory.py`) configures routes, Socket.IO, and background workers. Request handlers live under `src/api/`.
- **Services**: Business logic is encapsulated in service classes (SmartLP, Settings, SIEM, LLM, Deployment). Each service extends a shared `BaseService` for logging, database access, and error handling.
- **Database**: MongoDB hosts parser entries, prefixes, settings, SIEM/LLM metadata, Sigma rules, and MITRE ATT&CK content. Connection helpers live in `src/database/`.
- **Realtime**: `socketio_manager` provides push notifications for logs, ingestion status, and UI toasts.
- **Frontend**: Bootstrap-based templates under `templates/` with Socket.IO aware JS modules in `static/js/`.
- **RAG**: `rag/` holds scripts, cached CSVs, and Chroma repositories required to build vector stores for Splunk and Elastic metadata.
- **Automation**: Ansible playbooks (`ansible/`) deploy generated configurations to downstream platforms.

## Directory Map

```
smartlp/
├── app.py                 # Application entry point
├── src/
│   ├── api/               # Flask blueprints (dashboard, smartlp, settings, deployment)
│   ├── config/            # Environment + application configuration loading
│   ├── core/              # App factory and Socket.IO manager
│   ├── database/          # MongoDB connection helpers
│   ├── models/            # Dataclasses and enums used across services
│   ├── services/          # SmartLP, Settings, SIEM, LLM, Deployment services
│   └── utils/             # Logging, formatters, pagination helpers
├── templates/             # Jinja templates (dashboard, SmartLP pages, settings)
├── static/                # CSS, JS, fonts, logos
├── rag/                   # RAG helpers, cached field lists, repo sync utilities
├── ansible/               # Inventories, playbooks, roles used for deployment
├── certs/                 # TLS materials (Elastic CA chain, etc.)
├── mongo/                 # Seed JSON configuration for MongoDB
├── requirements.txt       # Python dependency lock
├── setup_rag.py           # Build embeddings / populate ChromaDB
├── deploy_playbook.py     # Thin wrapper around ansible-playbook
└── README.md              # This document
```

## Getting Started

### Prerequisites
- Python 3.12+
- MongoDB 8+
- Access to at least one SIEM source (Splunk Enterprise 9.x or Elastic 8.x)
- Optional: ChromaDB (installed automatically via requirements) for RAG, Ansible 11+ for remote deployments

### Environment Variables
Create an `.env` file at the project root. The sample below lists the required keys without exposing credentials.

```
# Elastic
ELASTIC_HOST=https://elastic.example.com:9200
ELASTIC_USER=elastic
ELASTIC_PASSWORD=<password>
ELASTIC_CERT_PATH=./certs/elastic_chain_cert.cer

# Splunk
SPLUNK_HOST=splunk.example.com
SPLUNK_PORT=8089
SPLUNK_USER=spladmin
SPLUNK_PASSWORD=<password>

# MongoDB
MONGO_URL=mongodb://localhost:27017/
MONGO_DB_PARSER=parser_db
MONGO_DB_SETTINGS=settings
MONGO_DB_MITRE=mitre_db
MONGO_DB_MITRE_TECH=mitre_techniques
MONGO_COLLECTION_ENTRIES=parser_entries
MONGO_COLLECTION_GLOBAL_SETTINGS=global_settings
MONGO_COLLECTION_LLMS_SETTINGS=llms_settings
MONGO_COLLECTION_SIEMS_SETTINGS=siems_settings
MONGO_COLLECTION_SIGMA_RULES=sigma_rules
MONGO_COLLECTION_SPLUNK_RULES=splunk_rules
MONGO_COLLECTION_ELASTIC_RULES=elastic_rules
MONGO_COLLECTION_SECOPS_RULES=secops_rules
MONGO_COLLECTION_MITRE_TECHNIQUES=techniques

# Ansible (optional for deployments)
ANSIBLE_USER=admin
ANSIBLE_SSH_PASSWORD=<password>
ANSIBLE_BECOME_PASSWORD=<password>

# App
APP_HOST=0.0.0.0
APP_PORT=8800
APP_DEBUG=True
SECRET_KEY=<random-string>
```

### Install Dependencies

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

> If you run on Linux, activate the venv with `source .venv/bin/activate`.

### Run The Application

```bash
python app.py
```

The server starts with Socket.IO enabled. By default the UI is served at `http://<host>:8800`.

For production, pair the app with Gunicorn or systemd using the templates under `install.sh` and `update.sh`.

## Core Services

### SmartLP Service
Source: `src/services/smartlp.py`

- Background ingestion thread pulls fresh logs according to `ingestFrequency`, `activeSiem`, and similarity thresholds stored in MongoDB.
- Manual endpoints cover CRUD, regex testing, SmartReport statistics, prefix management, and config exports (Splunk props/transforms or Elastic pipelines).
- Regex generation combines LLM prompts with iterative refinement (see `smartlp_algorithm.md`).
- Deployments are validated before Ansible hand-off (`/api/smartlp/generate_config`).

### Settings Service
Source: `src/services/settings.py`

- Normalizes MongoDB field names (snake_case) into camelCase for the UI.
- Tracks change history and produces human-friendly audit messages returned to the client.
- Controls the active SIEM, ingestion flags, similarity thresholds, and LLM endpoints.

### SIEM Service Factory
Source: `src/services/siem.py`

- Provides a single entry point to Splunk and Elasticsearch connectors.
- Handles certificate fallbacks (Elastic) and job polling (Splunk) transparently.
- Powers query tests, ingestion, and search utilities.

### LLM Service
Source: `src/services/llm.py`

- Wraps requests to OpenAI-compatible endpoints (local or cloud). Prompts cover generation, regex fixing, typing, and suggestion tasks.
- Cleans response payloads and enforces PCRE2-compatible endings.
- Exposes `/api/query_llm` and integrations inside SmartLP workflows.

### Deployment Service
Source: `src/services/deployment.py`

- Bridges REST requests with Ansible playbooks located in `ansible/`.
- Injects inventory, authentication, and `entries_id_list` variables before running `ansible-playbook`.
- Uses `.env` credentials and configurable collection paths.

## Frontend Experience

- **Dashboard (`/`)** – Landing page (placeholder for summary widgets).
- **SmartLP (`/smartlp`)** – Data table, filtering, status badges, and action menus for regex deployments.
- **SmartLP Parser (`/smartlp/parser`)** – Manual ingestion and LLM-driven regex generation.
- **SmartLP Prefix (`/smartlp/prefix`)** – Library of reusable header/prefix expressions.
- **SmartReport (`/smartlp/report`)** – Charts showing parsed vs unmatched counts (Chart.js with `/api/report/smartlp`).
- **Settings (`/settings`)** – Configure SIEMs, LLM endpoints, ingestion cadence, similarity checks, and run connectivity tests.

Every page inherits `templates/base.html`, which wires Toast notifications, the Socket.IO log panel, and shared navigation.

## RAG Pipeline

Located under `rag/` with orchestration in `setup_rag.py`:
- Downloads Splunk CIM field definitions, Elastic ECS metadata, and vendor packages.
- Builds ChromaDB collections (`splunk_fields`, `elastic_fields`, `splunk_addons`, `elastic_packages`, etc.) using sentence-transformer embeddings.
- Supports incremental refresh via CLI flags: `--siem`, `--skip-repos`, `--skip-fields`, `--skip-embeddings`.
- Splunk add-ons must be downloaded manually and extracted into `rag/repos/splunk_repo/` due to licensing.

Example commands:

```bash
python setup_rag.py                      # Full refresh
python setup_rag.py --siem elastic       # Only Elastic artifacts
python setup_rag.py --siem splunk --skip-fields  # Re-embed Splunk add-ons after manual updates
```

## REST API Cheatsheet

### SmartLP

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET    | `/api/entries` | Paginated search with filters (`search_id`, `search_log`, `search_regex`, `filter_status`, `page`, `per_page`). |
| POST   | `/api/entries` | Create a manual entry (log + regex). Auto-populates status based on regex match. |
| PUT    | `/api/entries/<id>` | Update an entry. Status recalculated when log/regex change. |
| DELETE | `/api/entries/<id>` | Remove an entry by ID. |
| GET    | `/api/entries/oldest` | Retrieve the oldest unmatched entry with metadata. |
| GET    | `/api/entries/stats` | Aggregate counts by status. |
| POST   | `/api/smartlp/ingestion/start` | Manually start background ingestion. |
| POST   | `/api/smartlp/ingestion/stop` | Stop ingestion thread. |
| GET    | `/api/smartlp/ingestion/status` | Inspect ingestion + unmatched summary. |
| POST   | `/api/smartlp/generate_config` | Build SIEM deployment config for a list of IDs. |
| GET/POST/PUT/DELETE | `/api/prefix` | CRUD operations for prefix library. |
| GET    | `/api/report/smartlp` | Data for SmartReport visualizations. |

### Settings & Connectivity

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET    | `/api/settings` | Fetch global, SIEM, and LLM settings in camelCase. |
| PUT    | `/api/settings` | Persist changes. Returns a list of human-readable change descriptions. |
| POST   | `/api/query_llm` | Test LLM connectivity with `task`, `model`, `url`, `llmEndpoint`. |
| POST   | `/api/test_connection` | Validate SIEM connectivity (`siem`: `elastic`, `splunk`, or `all`). |
| POST   | `/api/test_query` | Execute a dry-run SIEM query (`siem`, `searchQuery`, `searchIndex`, `entriesCount`). |

### Deployment

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST   | `/api/deploy` | Run Ansible deployment for the active SIEM. Payload requires `ids` (list) and deployment `type` (e.g., `smartlp`). |

## MongoDB Collections

Key collections and indicative schemas:

- `parser_entries`
    ```json
    {
        "id": "uuid",
        "log": "<raw log>",
        "regex": "<pcre2>",
        "status": "Matched|Unmatched|Pending",
        "log_type": "string",
        "source_type": "string",
        "timestamp": "ISO8601",
        "ingestion_method": "automatic|manual"
    }
    ```
- `prefix_entries`
    ```json
    {
        "id": "uuid",
        "regex": "^<prefix>",
        "description": "optional",
        "created_at": "ISO8601"
    }
    ```
- `global_settings`
    ```json
    {
        "id": "global",
        "active_siem": "elastic",
        "active_llm_endpoint": "local_llm",
        "active_llm": "gpt-4o-mini",
        "ingest_on": true,
        "ingest_frequency": 30,
        "similarity_check": false,
        "similarity_threshold": 0.8,
        "fix_count": 3,
        "ingest_algo_version": "v2",
        "updated_at": "ISO8601"
    }
    ```
- `siems_settings` – search indexes, default queries, entry counts per SIEM connector.
- `llms_settings` – endpoint URL, friendly name, allowed models, timestamps.
- `sigma_rules`, `splunk_rules`, `elastic_rules`, `secops_rules`, `mitre_techniques` – content supporting SmartUC and report capabilities.

## Automation Scripts

- `install.sh` – Reference install script for RHEL-based servers. Creates the `smartsoc` user, installs MongoDB/Python, deploys Gunicorn, and wires systemd.
- `update.sh` – Idempotent updater for production rollouts.
- `deploy_playbook.py` – Programmatic wrapper around `ansible-playbook`. Reads credentials from `.env` and injects `entries_id_list` to the selected playbook.
- `update_repository.py` and friends in `rag/` – Sync Splunk/Elastic content prior to embedding.

> The scripts assume a Linux target under `/opt/SmartSOC`. Adjust paths as needed for local development.

## Troubleshooting

- **MongoDB connection failures**: Verify the service is running and reachable via `mongosh`. Ensure `.env` hosts/ports match reality.
- **Elastic SSL issues**: If self-signed certificates fail, the connector automatically retries without verification. Confirm `ELASTIC_CERT_PATH` if verification is desired.
- **Splunk API errors**: Validate credentials and check that the role can run REST searches. The app uses blocking job polling, so slow searches delay responses.
- **LLM timeouts**: `/api/query_llm` will surface network timeouts. Check endpoint reachability and certificate requirements. Responses are stripped of code fences automatically.
- **Background ingestion not running**: Toggle `ingestOn` in settings and review `/api/smartlp/ingestion/status`. The background thread starts after the first HTTP request to the app.
- **Ansible prompts for passwords**: Populate `ANSIBLE_SSH_PASSWORD` and `ANSIBLE_BECOME_PASSWORD` in `.env`. Otherwise, the deployment service will append `--ask-pass` flags which are not supported in headless mode.

## Maintenance Tips

- **Backups**: Use `mongodump` on the parser and settings databases. Store exports with timestamps (`mongodump --out ./backups/$(date +%F)`).
- **Log review**: Socket.IO streams application logs to the UI. For backend-only review, enable file handlers or pipe stdout to systemd journald.
- **Dependency refresh**: `pip install -r requirements.txt --upgrade` keeps the RAG and LLM stacks current. Re-run `setup_rag.py` after bumping `sentence-transformers`.
- **Regex algorithm tuning**: Update `smartlp_algorithm.md` and adjust prompts in `src/services/llm.py` when experimenting with new parsing logic.
- **Scaling**: For production, front the app with Gunicorn (eventlet workers) and a reverse proxy. Configure MongoDB indexes on frequently filtered fields (`status`, `timestamp`, `log_type`).

---

SmartSOC continues to evolve around the SmartLP pipeline, LLM-assisted workflows, and tightly integrated SIEM connectors. Contributions should follow the service-oriented layout under `src/services/` and expose new features through dedicated API routes and UI pages.
