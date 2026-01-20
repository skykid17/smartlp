# SmartLP

SmartLP (Smart Log Parser) is a Flask-based web application for ingesting security logs from SIEM platforms (Splunk or Elasticsearch), generating and validating parsing regex, and managing a workflow for improving parse coverage. It ships with a single-page Tailwind UI, REST APIs, and optional LLM/RAG capabilities.

## Highlights

- **SIEM ingestion** with a background worker driven by runtime settings in MongoDB
- **Regex workflow** with PCRE2 validation, match inspection, and reduction utilities
- **Reporting & analytics** for status coverage, volume, and log-type trends
- **Config generation & deployment** for SIEM-ready rules and pipelines
- **LLM/RAG integration** for regex generation, fixes, and general assistance

## Architecture overview

- **Entry point:** `app.py` creates and runs the Flask app via `ApplicationFactory`.
- **Application factory:** initializes Socket.IO logging, sets up the first-run guard, registers routes, and starts ingestion on the first request.
- **Service layer:** `src/services/` encapsulates SmartLP logic, SIEM connectors, settings, LLM, RAG, and regex processing.
- **Data access:** `src/database/connection.py` manages MongoDB connection lifecycle and CRUD helpers.
- **UI:** server-rendered templates in `templates/` with Tailwind assets in `static/`.

## Project layout

- `app.py` – application entrypoint
- `src/` – backend source code
  - `src/core/` – application factory, Socket.IO manager
  - `src/api/` – Flask routes (init, settings, SmartLP, main)
  - `src/services/` – SmartLP, SIEM, settings, LLM, RAG, regex engine
  - `src/database/` – MongoDB connection wrapper
  - `src/utils/` – logging, formatting, pagination helpers
- `templates/` – main UI template (`smartlp.html`) and sections
- `static/` – CSS/JS assets used by the UI
- `demo/` – demo JSON and utility scripts

## Requirements

- Python 3.10+
- MongoDB (local or remote)
- Access to Splunk or Elasticsearch (only required for ingestion)
- Docker
- Optional: OpenAI-compatible LLM endpoint (Ollama, vLLM, LM Studio, OpenAI API)

## Quick start (Docker)

1) Download the application file
```bash
git pull https://github.com/skykid17/smartlp.git
```

2) Create the Docker network (first time only)

```bash
docker network create search-community
```

3) Build and start the stack

```bash
docker compose up --build
```

Open http://localhost:8800/.

## First-run initialization

SmartLP gates access until initial configuration is complete. Visit /init to run the setup wizard or call the init APIs directly:

- `POST /api/init/siem/test` – test SIEM connection details
- `POST /api/init/siem/save` – persist SIEM settings
- `POST /api/init/llm/test` – test LLM endpoint/model
- `POST /api/init/llm/save` – persist LLM endpoint/model
- `POST /api/init/finish` – mark initialization complete

Once initialized, SmartLP routes are registered and ingestion can run.

## Configuration model (MongoDB)

The application stores runtime configuration in the `smartlp.settings` collection. Documents are grouped by `category`:

- **`global_settings`** (id: `global`)
  - `active_siem`, `ingest_on`, `ingest_frequency`, `similarity_check`, `similarity_threshold`, `fix_count`
  - `active_llm_model_id`, `ingest_algo_version`, `initialized`
- **`siem_settings`** (id: `elastic` or `splunk`)
  - Splunk: `host`, `port`, `user`, `password`, `search_index`, `search_query`, `search_entry_count`
  - Elasticsearch: `host`, `kibana_url`, `api_key`, `user`, `password`, `search_index`, `search_query`, `cert_path`
- **`llm_endpoint`** – endpoint URL, API key, display name
- **`llm_model`** – model name, provider, `endpoint_id`
- **`prompts`** – LLM system prompts used by the regex/assistant flows

Notes:

- The backend stores keys in snake_case; the UI works in camelCase and is normalized in the settings service.
- SmartLP defaults to a safe `global_settings` document on first access if one does not exist.

## API overview

Common endpoints used by the UI (non-exhaustive):

- **Entries**
  - `GET /api/smartlp/entries` – list entries with pagination and filters
  - `PUT|PATCH /api/smartlp/entries/<entry_id>` – update a log entry
  - `POST /api/smartlp/entries/delete` – bulk delete entries
  - `GET /api/entries/oldest` – fetch the oldest unmatched entry

- **Regex utilities**
  - `POST /api/find_match` – run regex match and return groups/status
  - `POST /api/reduce_regex` – reduce regex to the longest valid match

- **Ingestion**
  - `GET /api/smartlp/ingestion/status`
  - `POST /api/smartlp/ingestion/start`
  - `POST /api/smartlp/ingestion/stop`

- **Reporting**
  - `GET /api/entries/stats`
  - `GET /api/report/smartlp`

- **Settings**
  - `GET /api/settings` – full settings payload for the UI
  - `GET /api/settings/global` – global settings document
  - `PUT /api/settings` – save settings changes
  - `POST /api/settings/siem/test` – test a candidate SIEM config
  - `POST /api/settings/siem` – add a SIEM configuration
  - `POST /api/test_siem_connection` – test saved SIEM config(s)
  - `POST /api/test_llm_connection` – test saved LLM endpoint/model
  - `POST /api/test_query` – run a SIEM query test

- **Config generation & deployment**
  - `POST /api/smartlp/generate_config`
  - `POST /api/check_deployable`
  - `POST /api/smartlp/deploy_config`
  - `POST /api/smartlp/deploy_rule`

- **LLM / RAG**
  - `POST /api/query` – task router (`generate`, `fix`, or default RAG query)

## Background ingestion behavior

The ingestion loop runs in a daemon thread started on the first HTTP request after initialization. It reads `global_settings` each cycle, and only ingests when `ingest_on` is enabled. You can also start/stop ingestion manually via the ingestion endpoints.

## RAG and LLM notes

- RAG uses MongoDB vector search with a fallback local retriever. Index names are `vector_index` and `text_index`.
- LLM integration uses LangChain’s `ChatOpenAI` client with OpenAI-compatible endpoints.

## Development notes

- Static assets are served from `static/` and templates from `templates/`.
- Socket.IO forwards log events to the UI via a structured `log` event payload.
- Tailwind assets are prebuilt in `static/css/`.
