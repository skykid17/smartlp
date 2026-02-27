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
- `tools/` – maintenance and migration scripts
  - `tools/rebuild_knowledge_base.py` – rebuild the knowledge base collection from source files
  - `tools/migrate_kb_ids.py` – migrate knowledge base document IDs
  - `tools/download_embedding.py` – download the embedding model
- `templates/` – main UI template (`smartlp.html`) and sections
- `static/` – CSS/JS assets used by the UI
- `demo/` – demo JSON and utility scripts
- `knowledge_base/` – source data for RAG knowledge base
- `models/` – local embedding model (`all-MiniLM-L6-v2`)
- `ansible/` – Ansible playbooks for Splunk deployment

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
docker compose up -d
```

4) Monitor Initialization The first setup involves seeding the database (approx. 10-15 minutes). You can track progress via real-time logs in a separate terminal:

```
docker logs -f smartlp
```

5) Start the application at http://localhost:8800/

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
  - `POST /api/smartlp/generate_config` – generate Splunk/Elastic configuration
  - `POST /api/check_deployable` – verify entries are ready for deployment
  - `POST /api/smartlp/deploy_config` – deploy configurations via Ansible (Splunk) or direct API (Elastic)
  - `POST /api/smartlp/deploy_rule` – deploy single rule to SIEM

- **LLM / RAG**
  - `POST /api/query` – task router (`generate`, `fix`, or default RAG query)

## Deployment architecture

### Splunk Configuration Deployment

SmartLP uses **Ansible playbooks** to deploy Splunk log parsing configurations, replacing the previous REST API `.refresh()` approach. This provides:

- **File-based configuration management** in a single app location: `/etc/apps/smartlp/local/`
- **Idempotent deployments** that can be run multiple times safely
- **Automatic backups** before configuration changes
- **Configuration merging** to prevent duplicates
- **CLI-based reload** instead of REST API calls

#### Deployment Flow

1. User triggers deployment via UI or API (`/api/smartlp/deploy_config`)
2. Python service (`src/services/siem.py`) invokes Ansible playbook
3. Ansible queries MongoDB for entry data by IDs
4. Configurations are generated and written to `props.conf` and `transforms.conf`
5. Splunk configuration is reloaded via CLI
6. MongoDB entry status is updated to "Deployed"

#### Configuration Location

All SmartLP configurations are stored in:
```
/opt/splunk/etc/apps/smartlp/local/
├── props.conf       # Sourcetype configurations
└── transforms.conf  # Regex transformations
```

For detailed Ansible deployment documentation, see [`ansible/README.md`](ansible/README.md).

### Elasticsearch Configuration Deployment

Elasticsearch deployments use direct API calls to update Logstash pipeline configurations.

## Background ingestion behavior

The ingestion loop runs in a daemon thread started on the first HTTP request after initialization. It reads `global_settings` each cycle, and only ingests when `ingest_on` is enabled. You can also start/stop ingestion manually via the ingestion endpoints.

## Knowledge base

The `smartlp.knowledge_base` MongoDB collection stores embedded documents used for RAG retrieval. Documents use MongoDB auto-generated `ObjectId` for `_id` and a SHA1 `hash` field for content deduplication.

### Document schema

Every document contains the following fields:

| Field                | Type       | Description                                      |
|----------------------|------------|--------------------------------------------------|
| `_id`                | ObjectId   | Auto-generated MongoDB identifier                |
| `content`            | string     | The text content used for retrieval              |
| `metadata`           | object     | Contains `category`, `source`, `file_type`, etc. |
| `embedding`          | float[384] | Vector embedding (all-MiniLM-L6-v2)             |
| `embedding_provider` | string     | Embedding model identifier                       |
| `hash`               | string     | SHA1 content hash for deduplication              |
| `created_at`         | datetime   | UTC timestamp of insertion                       |

Detection rule documents additionally include:

| Field           | Type   | Description                                         |
|-----------------|--------|-----------------------------------------------------|
| `sigma_id`      | string | Sigma rule UUID                                     |
| `splunk_rule`   | object | Nested Splunk translation (`rule`, `deployed`, etc.)|
| `elastic_rule`  | object | Nested Elastic translation (`rule`, `deployed`, etc.)|

### Categories

| Category           | Source                          | Description                                   |
|--------------------|---------------------------------|-----------------------------------------------|
| `detection_rules`  | `sigma_rules.json`, `splunk_rules.json`, `elastic_rules.json` | Unified detection rules (1:1 with sigma rules) |
| `splunk_fields`    | `splunk_fields.csv`             | Splunk CIM field definitions                  |
| `elastic_fields`   | `elastic_fields.csv`            | Elastic ECS field definitions                 |
| `splunk_packages`  | `splunk_packages/`              | Splunk Technology Add-on configuration files  |
| `elastic_packages` | `elastic_packages/`             | Elastic integration package files             |

### Indexes

- `vector_index` – MongoDB Atlas vector search index on the `embedding` field with `metadata.category` as a filter
- `text_index` – MongoDB Atlas full-text search index on the `content` field
- Unique index on `hash` for deduplication

### Knowledge base management

Rebuild the entire collection or specific categories:

```bash
# Full rebuild (drops and recreates the collection)
python tools/rebuild_knowledge_base.py

# Rebuild only detection rules (deletes and re-inserts that category)
python tools/rebuild_knowledge_base.py --categories detection_rules

# Preview without writing to MongoDB
python tools/rebuild_knowledge_base.py --dry-run

# Rebuild without recreating indexes
python tools/rebuild_knowledge_base.py --skip-drop --skip-indexes
```

Migrate existing documents (e.g. after schema changes):

```bash
python tools/migrate_kb_ids.py
python tools/migrate_kb_ids.py --dry-run
python tools/migrate_kb_ids.py --keep-backup
```

## RAG and LLM

- RAG uses MongoDB Atlas hybrid search (RankFusion combining vector search and text search) with a fallback local retriever. Index names are `vector_index` and `text_index`.
- Embeddings are generated locally using `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, cosine similarity).
- LLM integration uses LangChain's `ChatOpenAI` client with OpenAI-compatible endpoints.
- `POST /api/query` serves as the task router (`generate`, `fix`, or default RAG query).

## Regex Generation Algorithms

SmartLP implements multiple regex generation strategies for parsing log entries:

### Algorithm v1: Single-Pass Generation

```
1. Initialize:
   - Request regex from LLM for the entire log entry
   - Normalize and clean the response

2. Validation:
   - Compile regex using PCRE2
   - Test against input log
   - Return regex with end-of-line anchor ($)

3. Return:
   - Success/failure status
   - Generated regex pattern
   - Latency metrics
```

### Algorithm v2: Iterative Progressive Generation

```
1. Initialize:
   - remaining_log ← log
   - final_regex ← ""
   - failure_count ← 0
   - total_latency ← 0

2. Loop for fix_count iterations:
   a. If remaining_log is empty:
      - Break loop

   b. Request regex from LLM for remaining_log
      - Accumulate latency
      - If request fails, return error

   c. Normalize and clean LLM response
      - Add end-anchor ($) if missing

   d. Reduce regex to longest matching pattern:
      - Try progressively shorter regex substrings
      - Find candidate that yields longest partial match
      - Keep best matching substring

   e. Match reduced regex against remaining_log:
      - Extract matched substring and end position

   f. Handle match failure:
      - If unmatched or no progress:
        * Increment failure_count
        * If failure_count >= 3:
          · Append wildcard pattern (\\s?.*)
          · Break loop
        * Continue to next iteration without advancing

   g. On successful match:
      - Reset failure_count to 0
      - Append reduced regex to final_regex with optional whitespace (\\s?)
      - Advance remaining_log past matched portion

3. Post-processing:
   - Resolve duplicate named capture groups
   - Add incremental suffixes (_1, _2, etc.) to duplicates

4. Return:
   - Success status
   - Final assembled regex
   - Total latency
```

## Development notes

- Static assets are served from `static/` and templates from `templates/`.
- Socket.IO forwards log events to the UI via a structured `log` event payload.
- Tailwind assets are prebuilt in `static/css/`.