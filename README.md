# SmartLP

SmartLP (Smart Log Parser) is a Flask-based web application for ingesting security logs from SIEM platforms (Splunk / Elasticsearch), generating and validating parsing regex, and managing a workflow for improving parse coverage. It includes a modern single-page UI (Tailwind) plus REST APIs for ingestion, parsing, reporting, and configuration deployment.

## Key capabilities

- **Log ingestion** from Splunk or Elasticsearch based on runtime settings stored in MongoDB
- **Regex workflow**: generate, reduce/optimize, validate matching (PCRE2 engine), and save rules/log entries
- **Analytics/reporting**: basic statistics and a report endpoint consumed by the UI
- **Config generation & deployment**: generate SIEM-specific config for selected entries and deploy to the active SIEM
- **LLM/RAG integration** (optional): uses a configurable LLM endpoint for tasks like regex generation and log-type inference

## Tech stack

- **Backend:** Python, Flask, Flask-SocketIO
- **Database:** MongoDB (pymongo)
- **Regex engine:** PCRE2 (`pcre2` Python package)
- **Frontend:** Server-rendered template + Tailwind-based UI with ES module scripts in `static/js/`

## Project layout

- `app.py` – application entrypoint
- `src/` – backend source code
  - `src/core/` – app factory, Socket.IO manager
  - `src/api/` – Flask routes
  - `src/services/` – SmartLP, SIEM, settings, LLM, RAG services
  - `src/database/` – MongoDB connection wrapper
- `templates/` – main UI template (`smartlp.html`) and sections
- `static/` – CSS/JS assets used by the UI
- `mongo/` – example MongoDB documents and datasets used by the application
- `rag/` – scripts/data used to build/update RAG resources

## Requirements

- Python 3.10+ recommended
- MongoDB (local or remote)
- Access to at least one SIEM endpoint (Splunk or Elasticsearch) if you want ingestion
- Optional: an OpenAI-compatible LLM endpoint (Ollama/vLLM/LM Studio/OpenAI-style API)

## Quick start

1) Create and activate a virtual environment

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
```

2) Install dependencies

```bash
pip install -r requirements.txt
```

3) Configure environment variables

Create a `.env` file in the project root:

```env
# Required
MONGO_URL=mongodb://localhost:27017

# Optional application settings
APP_HOST=0.0.0.0
APP_PORT=8800
APP_DEBUG=True
SECRET_KEY=change-me

# Optional (used for deployment workflows)
ANSIBLE_USER=
ANSIBLE_SSH_PASSWORD=
ANSIBLE_BECOME_PASSWORD=
ANSIBLE_COLLECTIONS_PATH=
```

4) Ensure MongoDB has the required collections/documents

SmartLP expects MongoDB database **`soc_rag_db`** (hard-coded in the configuration) and uses these collections:

- `logs` – ingested and curated log entries
- `knowledge_base` – RAG knowledge store
- `settings` – runtime configuration (global settings, SIEM configs, LLM endpoints, prompts)

The repo contains example JSON documents in `mongo/` (e.g., `mongo/settings.global.json`, `mongo/settings.siems.json`, `mongo/settings.llms.json`). When seeding your database, ensure the documents in the `settings` collection include the `category` fields expected by the backend:

- `category: global_settings` (global config)
- `category: siem_settings` (Splunk/Elastic configs)
- `category: llm_settings` (LLM endpoint configs)

5) Run the app

```bash
python app.py
```

Open:

- http://localhost:8800/

Note: the ingestion thread is started on the first request (after the UI is loaded), and only runs if `ingest_on` is enabled in global settings.

## Configuration model (MongoDB)

SmartLP reads most runtime configuration from MongoDB `soc_rag_db.settings`:

- **Global settings** (ingestion, active SIEM, LLM selection)
  - `active_siem`, `ingest_on`, `ingest_frequency`, `similarity_check`, `similarity_threshold`, `fix_count`, `active_llm_endpoint`, `active_llm`
- **SIEM settings**
  - Splunk: `host`, `port`, `user`, `password`, `search_index`, `search_query`, `search_entry_count`
  - Elasticsearch: `host`, `user`, `password`, `cert_path`, `search_index`, `search_query`, `search_entry_count`
- **LLM endpoint settings**
  - `id`, `name`, `url`, `models`, optional `api_key`, optional `temperature`

## API overview

The UI calls these endpoints (non-exhaustive):

- **Entries**
  - `GET /api/smartlp/entries` – list entries with pagination and filters
  - `PUT|PATCH /api/smartlp/entries/<entry_id>` – update a log entry
  - `POST /api/smartlp/entries/delete` – bulk delete entries
  - `GET /api/entries/oldest` – fetch oldest unmatched entry

- **Regex utilities**
  - `POST /api/find_match` – run regex match and return groups/status
  - `POST /api/reduce_regex` – attempt regex reduction/optimization

- **Ingestion**
  - `GET /api/smartlp/ingestion/status`
  - `POST /api/smartlp/ingestion/start`
  - `POST /api/smartlp/ingestion/stop`

- **Reporting**
  - `GET /api/entries/stats`
  - `GET /api/report/smartlp`

- **Settings**
  - `GET /api/settings`
  - `PUT /api/settings`
  - `POST /api/test_siem_connection`
  - `POST /api/test_llm_connection`
  - `POST /api/test_query`

- **Config generation & deployment**
  - `POST /api/smartlp/generate_config`
  - `POST /api/check_deployable`
  - `POST /api/smartlp/deploy_config`

- **LLM / RAG**
  - `POST /api/query` – task router used by the UI (generate/fix/default)

## Notes for development

- Static assets are served from `static/` and templates from `templates/`.
- Socket.IO is initialized via Flask-SocketIO; logs/events are managed through the app’s logging utilities.
- The application is currently configured to use Tailwind assets already present in `static/css/`.
