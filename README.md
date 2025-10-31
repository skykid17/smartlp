# SmartSOC Documentation

## Table of Contents
- [Introduction](#introduction)
- [System Architecture](#system-architecture)
- [Installation](#installation)
 - [Prerequisites](#prerequisites)
 - [Step-by-Step Installation](#step-by-step-installation)
 - [Create Systemd for SmartSOC](#create-systemd-for-smartsoc)
- [Configuration](#configuration)
 - [SIEM Integration](#siem-integration)
   - [Splunk Integration](#splunk-integration)
   - [Elasticsearch Integration](#elasticsearch-integration)
- [Core Module](#core-module)
 - [SmartLP (Log Parser)](#smartlp-log-parser)
   - [Key Features](#key-features)
   - [Using SmartLP](#using-smartlp)
   - [Key Functions](#key-functions)
- [API Reference](#api-reference)
 - [SmartLP API Endpoints](#smartlp-api-endpoints)
 - [Settings API Endpoints](#settings-api-endpoints)
- [Database Layout](#database-layout)
 - [MongoDB Collections](#mongodb-collections)
   - [Parser Collections](#parser-collections)
   - [Settings Collections](#settings-collections)
- [Frontend Components](#frontend-components)
 - [Main Pages](#main-pages)
 - [JavaScript Libraries](#javascript-libraries)
- [Integration Points](#integration-points)
 - [LLM Integration](#llm-integration)
   - [Example: Sending a Request to LLM](#example-sending-a-request-to-llm)
 - [SIEM Integration](#siem-integration)
   - [Splunk Integration](#splunk-integration)
   - [Elasticsearch Integration](#elasticsearch-integration)
- [Troubleshooting](#troubleshooting)
 - [Common Issues and Solutions](#common-issues-and-solutions)
   - [Connection to MongoDB Failed](#connection-to-mongodb-failed)
   - [SIEM Integration Issues](#siem-integration-issues)
   - [LLM Service Issues](#llm-service-issues)
   - [Performance Issues](#performance-issues)
- [Advanced Configuration](#advanced-configuration)
 - [Fine-tuning LLM Prompts](#fine-tuning-llm-prompts)
 - [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Appendix A: Detailed Installation Guide](#appendix-a-detailed-installation-guide)
 - [Prerequisites](#prerequisites)
 - [Install Development Tools and Dependencies](#install-development-tools-and-dependencies)
 - [Create SmartSOC User and Directory Structure](#create-smartsoc-user-and-directory-structure)
 - [Install MongoDB](#install-mongodb)
   - [Additional MongoDB Operations](#additional-mongodb-operations)
 - [Configure MongoDB](#configure-mongodb)
 - [Apply SELinux Security Context](#apply-selinux-security-context)
 - [Install Python 3.13.2](#install-python-3132)
 - [Setup Web Application](#setup-web-application)
 - [Install Required Python Packages](#install-required-python-packages)
 - [Download Static Assets](#download-static-assets)
 - [Configure Gunicorn](#configure-gunicorn)
 - [Create SmartSOC Daemon Script](#create-smartsoc-daemon-script)
 - [Create Systemd Service](#create-systemd-service)

## Introduction

SmartSOC is a Security Operations Center (SOC) platform focused on automated log parsing. It provides integration with popular SIEM platforms (Splunk, Elasticsearch) and leverages Large Language Models (LLMs) for automated log parsing and regex generation.

**Key Features:**
- Automated log parsing with regex generation (SmartLP)
- RAG (Retrieval-Augmented Generation) system for enhanced SIEM field and package queries
- Real-time monitoring and alerts
- Integration with Splunk and Elasticsearch
- LLM-powered analysis and insights

## System Architecture

SmartSOC is built on a modern web stack:

- **Backend**: Python/Flask with Socket.IO for real-time communication
- **Database**: MongoDB for document storage
- **RAG System**: ChromaDB for vector embeddings and semantic search
- **Frontend**: HTML/CSS/JavaScript with Bootstrap for UI components
- **External Integrations**: 
  - Splunk and Elasticsearch for SIEM data
  - External LLM services for natural language processing

The application consists of one main module:
1. **SmartLP**: Log Parser for automated regex generation

**RAG System Components:**
- **Vector Database**: ChromaDB for storing embeddings
- **Collections**: Separate collections for Splunk/Elastic fields, packages, and log types
- **Embedding Model**: HuggingFace sentence-transformers for semantic similarity
- **Checkpointing**: Resumable processing for large datasets

## Installation

### Prerequisites

- RHEL 9.6
- Python 3.12.11
- MongoDB 8.0.13
- Network access to SIEM platforms (Splunk/Elasticsearch)

### Step-by-Step Installation

Currently, installation can be done using the `install.sh` script, which now includes automated RAG (Retrieval-Augmented Generation) setup. For future updates of code, a sample of the code can be found in `update.sh`. If you prefer to install the different portions of the code separately, you can have a look at the bottom and [Appendix A](#appendix-a-detailed-installation-guide).

1. **Create User and Directory Structure**:
```bash
useradd -M smartsoc
usermod -s /sbin/nologin smartsoc
usermod -d /opt/SmartSOC smartsoc

mkdir -p /opt/SmartSOC/{bin,conf,tmp,pid,web}
mkdir -p /opt/SmartSOC/var/{log,run}
mkdir -p /opt/SmartSOC/var/lib/db
```

2. **Install MongoDB**:
```bash
curl -O https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-rhel93-8.0.13.tgz
tar -xzf mongodb-linux-x86_64-rhel93-8.0.13.tgz -C /opt/SmartSOC/
mv /opt/SmartSOC/mongodb-linux-x86_64-rhel93-8.0.13/bin/* /opt/SmartSOC/bin/.
rm -rf /opt/SmartSOC/mongodb-linux-x86_64-rhel93-8.0.13
```

3. **Configure MongoDB**:
```bash
cat > /opt/SmartSOC/conf/mongod.conf << "endmsg"
systemLog:
  destination: file
  logAppend: true
  path: /opt/SmartSOC/var/log/mongodb.log

storage:
  dbPath: /opt/SmartSOC/var/lib/db

processManagement:
  pidFilePath: /opt/SmartSOC/pid/mongod.pid

net:
  port: 27017
  bindIp: 0.0.0.0
  unixDomainSocket:
    pathPrefix: /opt/SmartSOC/tmp
endmsg
```

4. **Install Python**:
```bash
dnf -y groupinstall "Development Tools"
dnf -y install libffi-devel

# Define installation directory
PREFIX=/opt/SmartSOC/
VERSION=3.12.11

# Download & extract Python source
curl -O https://www.python.org/ftp/python/${VERSION}/Python-${VERSION}.tgz
tar xvf Python-${VERSION}.tgz
cd Python-${VERSION}

# Build and install Python
make distclean
CPPFLAGS="-I/usr/include" LDFLAGS="-L/usr/lib64" \
./configure --prefix=/opt/SmartSOC --enable-shared --with-ensurepip=install --with-build-python=$(which /opt/SmartSOC/bin/python3)
make -j$(nproc)
make install

# Configure library paths
echo "/opt/SmartSOC/lib" | tee /etc/ld.so.conf.d/smartsoc.conf
ldconfig
```

5. **Setup Initial SmartSOC**:
```bash
cd /opt/SmartSOC/web
git init
cat > /opt/SmartSOC/web/.git/config <<"endmsg"
[core]
        repositoryformatversion = 0
        filemode = true
        bare = false
        logallrefupdates = true
[remote "origin"]
        url = https://[YOUR_GITHUB_TOKEN]@github.com/[YOUR_ORG]/smartsoc.git
        fetch = +refs/heads/*:refs/remotes/origin/*
[pull]
        rebase = true
[branch "main"]
        remote = origin
        merge = refs/heads/main
endmsg

chown -R smartsoc. /opt/SmartSOC/
su -s /bin/bash -c 'git pull origin main'
su -s /bin/bash -c '/opt/SmartSOC/bin/python3 -m pip install -r /opt/SmartSOC/web/requirements.txt' smartsoc
```

6. **Set Up Systemd Service**:

### Configure Gunicorn
```bash
cat > /opt/SmartSOC/conf/gunicorn.conf.py << "endmsg"
import multiprocessing
bind = "0.0.0.0:8080"
#workers = multiprocessing.cpu_count() * 2 + 1
workers = 2
chdir = "/opt/SmartSOC/web"
pidfile = "/opt/SmartSOC/var/run/gunicorn.pid"
accesslog = "/opt/SmartSOC/var/log/gunicorn.access.log"
errorlog = "/opt/SmartSOC/var/log/gunicorn.error.log"
loglevel = "info"
endmsg
```

### Create SmartSOC Daemon Script
```bash
cat > /opt/SmartSOC/bin/smartsocd << "endmsg"
#!/bin/bash

SMARTSOC_HOME="/opt/SmartSOC"
MONGO_CONF="$SMARTSOC_HOME/conf/mongod.conf"
GUNICORN_CONF="$SMARTSOC_HOME/conf/gunicorn.conf.py"

start() {
    echo "Starting SmartSOC services..."

    # Start MongoDB (No sudo needed)
    echo "Starting MongoDB..."
    $SMARTSOC_HOME/bin/mongod --config $MONGO_CONF --fork
    if [[ $? -ne 0 ]]; then
        echo "Failed to start MongoDB." >&2
        exit 1
    fi

    # Start Gunicorn (No sudo needed)
    echo "Starting Gunicorn..."
    $SMARTSOC_HOME/bin/gunicorn -c $GUNICORN_CONF app:app
    if [[ $? -ne 0 ]]; then
        echo "Failed to start Gunicorn." >&2
        exit 1
    fi

    echo "SmartSOC started successfully."
}

stop() {
    echo "Stopping SmartSOC services..."
    pkill -f gunicorn
    sleep 2
    pkill -f mongod
    sleep 2
    echo "SmartSOC stopped."
}

restart() {
    stop
    sleep 2
    start
}

status() {
    echo "Checking service status..."
    pgrep -f gunicorn >/dev/null && echo "Gunicorn is running" || echo "Gunicorn is not running"
    pgrep -f mongod >/dev/null && echo "MongoDB is running" || echo "MongoDB is not running"
}

case "$1" in
    start) start ;;
    stop) stop ;;
    restart) restart ;;
    status) status ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
endmsg

chown -R smartsoc. /opt/SmartSOC
chmod +x /opt/SmartSOC/bin/smartsocd
```

### Create Systemd for SmartSOC

```bash
cat > /etc/systemd/system/SmartSOC.service << "endmsg"
[Unit]
Description=SmartSOC Service
After=network.target

[Service]
User=smartsoc
Group=smartsoc
ExecStart=/opt/SmartSOC/bin/smartsocd start
ExecStop=/opt/SmartSOC/bin/smartsocd stop
Restart=always
Type=simple

[Install]
WantedBy=multi-user.target
endmsg

systemctl daemon-reload
systemctl enable SmartSOC
systemctl start SmartSOC
```

*** TILL HERE TESTED



### Post-Installation RAG Setup

The installation script automatically sets up the RAG system for Elasticsearch. However, **Splunk Add-ons require manual download** due to licensing restrictions:

1. Download Splunk Add-ons from [Splunkbase](https://splunkbase.splunk.com/apps?page=1&keyword=add-on&filters=built_by%3Asplunk%2Fproduct%3Asplunk) (login required)
2. Place them in `/opt/SmartSOC/web/rag/repos/splunk_repo/`
3. Run the RAG setup for Splunk:
   ```bash
   cd /opt/SmartSOC/web
   sudo -u smartsoc /opt/SmartSOC/bin/python3 rag/setup_rag.py --siem splunk --skip-fields
   ```

## Configuration

### ENV file setup
We would need an env file with the configuration to log into the SIEMs and the local database. A sample of the env file can be found below:
```
# Elastic Configuration
ELASTIC_HOST = 'https://192.168.31.62:9200'
ELASTIC_USER='elastic'
ELASTIC_PASSWORD='P@55w0rd12345'
ELASTIC_API_TOKEN = "dnBVVzU1WUI2MFhUUENVblpCSzA6OVdHN2JGamVUSC1SWHEtd0hpQmhhUQ=="
ELASTIC_CERT_PATH = "./certs/elastic_chain_cert.cer"
ELASTIC_PIPELINE_ID = "unparsed_test_1"

# Splunk Configuration
SPLUNK_USER = 'spladmin'
SPLUNK_PASSWORD = 'P@ssw0rd12345'
SPLUNK_HOST = '192.168.30.52'
SPLUNK_PORT = 8089

# Ansible Configuration
ANSIBLE_USER = 'admin'
ANSIBLE_SSH_PASSWORD = 'STEcyberlab12#'
ANSIBLE_BECOME_PASSWORD = 'STEcyberlab12#'

# MongoDB Configuration
MONGO_URL = 'mongodb://192.168.30.91:27017/'

# Database Names
MONGO_DB_PARSER=parser_db
MONGO_DB_SETTINGS=settings
MONGO_DB_MITRE=mitre_db
MONGO_DB_MITRE_TECH=mitre_techniques

# Parser Collections
MONGO_COLLECTION_ENTRIES=entries

# Settings Collections
MONGO_COLLECTION_GLOBAL_SETTINGS=global
MONGO_COLLECTION_LLMS_SETTINGS=llms
MONGO_COLLECTION_SIEMS_SETTINGS=siems

# MITRE Collections
MONGO_COLLECTION_SIGMA_RULES=sigma_rules
MONGO_COLLECTION_SPLUNK_RULES=splunk_rules
MONGO_COLLECTION_ELASTIC_RULES=elastic_rules
MONGO_COLLECTION_SECOPS_RULES=secops_rules

# MITRE Techniques Collection
MONGO_COLLECTION_MITRE_TECHNIQUES=techniques
```

### SIEM Integration

To integrate with SIEMs, configure the connection details in Settings page or directly in the MongoDB collections:

#### Splunk Integration
- Host: The Splunk server address
- Port: Typically 8089 for API access
- Username & Password: Splunk credentials with sufficient permissions
- Search Query: Default query for log ingestion

#### Elasticsearch Integration
- Host URL: Full URL with protocol and port
- Authentication: Username and password
- Certificate: Path to CA certificate file
- Index: Default index for log ingestion
- Query: Default query for log ingestion

### RAG System

**RAG (Retrieval-Augmented Generation) is automatically set up during installation.**

The `install.sh` script now includes automated RAG setup that:
- Installs all required dependencies
- Downloads Elastic integration packages
- Extracts field definitions and log types
- Creates vector embeddings for all collections

#### Post-Installation RAG Setup

If you need to reconfigure RAG or encounter issues during installation, you can run the setup script manually:

#### Quick Setup (Recommended)

```bash
python rag/setup_rag.py
```

#### Advanced Setup Options

```bash
# Setup only for Splunk
python rag/setup_rag.py --siem splunk

# Setup only for Elasticsearch  
python rag/setup_rag.py --siem elastic

# Skip repository download (if already done)
python rag/setup_rag.py --skip-repos

# Skip field extraction (if already done)
python rag/setup_rag.py --skip-fields

# Skip embedding creation (if already done)
python rag/setup_rag.py --skip-embeddings

# Get help and see all options
python rag/setup_rag.py --help
```

#### Manual Steps Required

**Splunk Add-ons**: Must be downloaded manually from Splunkbase (login required) and placed in `./rag/repos/splunk_repo/`

After downloading Splunk Add-ons, re-run the RAG setup:
```bash
python rag/setup_rag.py --siem splunk --skip-fields
```

#### Reference Documentation

Splunk Fields can be found on their CIM field reference documentation site:
https://docs.splunk.com/Documentation/CIM/6.1.0/User/Overview

Elastic Fields can be found on their ECS field reference documentation site:
https://www.elastic.co/docs/reference/ecs/ecs-field-reference

Elastic Logtypes & Packages can be found on their github integrations repository:
https://github.com/elastic/integrations/tree/main/packages

Splunk Add-ons must be downloaded manually from Splunkbase (login required):
https://splunkbase.splunk.com/apps?page=1&keyword=add-on&filters=built_by%3Asplunk%2Fproduct%3Asplunk

## Core Modules

### SmartLP (Log Parser)

SmartLP is the log parsing engine that uses LLM technology to automatically generate regex patterns for log entries.

#### Key Features
- Automatic log ingestion from configured SIEMs
- LLM-powered regex generation
- Log similarity detection to avoid duplicates
- Manual and automatic regex refinement
- Advanced pattern matching with named capture groups

#### Using SmartLP

1. **Automatic Log Ingestion**:
   - Enable ingestion in settings
   - Configure frequency and similarity threshold
   - Set SIEM source (Splunk or Elasticsearch)

2. **Manual Log Parsing**:
   - Navigate to `/smartlp/parser`
   - Input a log entry
   - Click "Generate Regex" to create a pattern
   - Save the entry to the database

3. **Managing Parsed Logs**:
   - Navigate to `/smartlp`
   - Search, filter, and manage existing entries
   - Deploy matched patterns to SIEMs

#### Key Functions

```python
# Generate regex pattern for a log entry
def generate_full_regex_v2(log: str, fix_count) -> str:
    """
    Generates a complete regex pattern for the given log using an iterative approach.
    
    Args:
        log: The log entry to parse
        fix_count: Maximum number of iterations for refinement
        
    Returns:
        A PCRE2 regex pattern with named capture groups
    """
    # Implementation details...
```

```python
# Check if a new log is similar to existing logs
def check_similarity(log):
    """
    Checks if a new log entry is similar to existing entries based on configured threshold.
    
    Args:
        log: The log entry to check
        
    Returns:
        Boolean indicating if similar log was found
    """
    # Implementation details...
```

### SmartUC (Use Case Generator)

SmartUC manages security use cases with MITRE ATT&CK framework integration.

#### Key Features
- Browse and search Sigma rules
- Filter by rule types and subtypes
- View SIEM-specific implementations (Splunk, Elasticsearch)
- MITRE ATT&CK Navigator integration

## API Reference

### SmartLP API Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/entries/oldest` | GET | Retrieves the oldest unmatched log entry | None |
| `/api/entries` | GET | Gets a list of entries with pagination | `page`, `per_page`, `<field>` `<value>` (key value pairs in body) |
| `/api/entries` | POST | Creates an entry | `log`, `regex` |
| `/api/entries/<id>` | DELETE | Deletes an entry of given id | `id` (path) |
| `/api/entries/<id>` | PUT | Updates an entry of given id | `id` (path), `<field>` `<value>` (key value pairs in body) |
| `/api/entries` | PATCH | Update various entries | `ids`, `<field>` `<value>` (key value pairs in body) |
| `/api/query_llm` | POST | Sends queries to LLM for regex generation | `task`, `log`, `regex` (optional) |
| `/api/reduce_regex` | POST | Reduces a regex to its longest matching form | `log`, `regex` |
| `/api/find_match` | POST | Tests a regex against a log | `log`, `regex` |
| `/api/check_deployable` | POST | Checks if entries can be deployed | `ids` |
| `/api/prefix` | GET | Retrives a collection of log header prefixes available | None |
| `/api/prefix` | PUT | Saves the collection of log header prefixes available | `prefix` |
| `/api/smartlp/generate_config` | POST | Given a list of log entry IDs, generates a config file | `ids` |

### Settings API Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/api/settings` | GET | Gets all application settings | None |
| `/api/settings` | PUT | Saves application settings | Multiple settings parameters |
| `/api/test_query` | POST | Tests a SIEM query | `siem`, `searchQuery`, `searchIndex` |

## Database Layout

### MongoDB Collections

#### Parser Collections
- **entries**: Stores parsed log entries and regex patterns
  ```json
  {
    "id": "nanoid",
    "timestamp": "ISODate",
    "index": "string",
    "source_type": "string",
    "log": "string",
    "regex": "string",
    "status": "string (Matched, Unmatched, Pending)",
    "siem": "string",
    "query": "string",
    "log_type": "string",
    "rule_types": ["string"],
  }
  ```

#### Settings Collections
- **global_settings**: Global application settings
  ```json
  {
    "id": "global",
    "active_llm": "string",
    "fix_count": "number",
    "ingest_frequency": "number",
    "similarity_threshold": "number",
    "active_siem": "string",
    "active_llm_endpoint": "string",
    "similarityCheck": "boolean",
    "ingest_on": "boolean",
    "ingest_algo_version": "string",
    "prefixes": ["string"]
  }
  ```
- **llm_settings**: LLM endpoint configurations
  ```json
  {
    "id": "string",
    "url": "string",
    "models": ["string"]
  }
  ```
- **siem_settings**: SIEM configurations
  ```json
  {
    "id": "string",
    "search_index": "string",
    "search_query": "string"
  }
  ```

## Frontend Components

### Main Pages

1. **Dashboard** (`/`): Main overview and statistics
2. **SmartLP** (`/smartlp`): Log entry management interface
3. **SmartLP Parser** (`/smartlp/parser`): Log parsing interface
4. **Settings** (`/settings`): Application configuration interface

### JavaScript Libraries

- **utils.js**: Common utility functions
- **settings.js**: Settings management
- **smartlp/parser.js**: Log parsing logic
- **smartlp/smartlp.js**: Log entry management

## Integration Points

### LLM Integration

SmartSOC integrates with LLM services for generating regex patterns and analyzing log entries.

#### Example: Sending a Request to LLM

```python
# Send a request to the LLM service
def send_llm_request(task, log, regex=None, data=None):
    """
    Sends a request to the LLM service for processing.
    
    Args:
        task: Type of request (generate, fix, query, test)
        log: Log entry text
        regex: Optional existing regex pattern
        data: Optional override configuration
        
    Returns:
        Tuple of (response_text, status_code)
    """
    payload = build_llm_payload(task, log, regex, data)
    
    # Determine endpoint URL from settings or override
    endpoint_id = data.get("llmEndpoint") if data else get_settings().get("activeLlmEndpoint")
    url = data["url"] if task == "test" else mongo_settings_llms.find_one({"id": endpoint_id}).get("url")
    
    # Make the request and process response
    try:
        response = requests.post(url, json=payload, verify=False)
        response.raise_for_status()
        response_json = response.json()
        
        # Extract and clean the response
        reply = (
            (response_json.get("choices", [{}])[0].get("message", {}).get("content")) or
            response_json.get("message", {}).get("content") or
            "No response from LLM"
        ).strip()
        
        # Clean up the output
        reply = reply.replace("```", "").replace("\n", "")
        if reply.startswith("regex"):
            reply = reply[len("regex"):]
            
        return reply.strip(), response.status_code
    except Exception as e:
        return f"Error: {str(e)}", 500
```

### RAG - ChromaDB
#### Collections
Splunk Sourcetypes: splunk_sourcetypes
Elastic Logtypes: elastic_logtypes
Splunk Fields: splunk_fields
Elastic Fields: elastic_fields
Splunk Packages: splunk_addons
Elastic Packages: elastic_packages


### SIEM Integration

SmartSOC integrates with popular SIEM platforms for log ingestion and rule deployment.

#### Splunk Integration

```python
# Ingest logs from Splunk
def ingest_from_splunk(search_query):
    """
    Fetches log entries from Splunk based on a search query.
    
    Args:
        search_query: The Splunk search query
        
    Returns:
        Tuple of (log_text, error_message)
    """
    try:
        xml_response = service_splunk.jobs.oneshot('search ' + search_query)
        if not xml_response:
            return None, "No response from Splunk"
        
        response_bytes = xml_response.read()
        xml_string = response_bytes.decode('utf-8')
        root = ET.fromstring(xml_string)

        # Find all results and check for the _raw field
        for result in root.findall(".//result"):
            raw_field = result.find(".//field[@k='_raw']/v")
            if raw_field is not None:
                # Use itertext() to get the full raw log, including nested tags
                full_log = ''.join(raw_field.itertext()).strip()
                return full_log, None

        return None, "No '_raw' field found in any Splunk result"
    except Exception as e:
        return None, f"Error ingesting from Splunk: {e}"
```

#### Elasticsearch Integration

```python
# Ingest logs from Elasticsearch
def ingest_from_elastic(search_query, search_index):
    """
    Fetches log entries from Elasticsearch based on a query and index.
    
    Args:
        search_query: The Elasticsearch query
        search_index: The index to search
        
    Returns:
        Tuple of (log_text, error_message)
    """
    try:
        response = service_elastic.search(index=search_index, body=search_query)
        hits = response.get("hits", {}).get("hits", [])
        
        if not hits:
            return None, "No hits found in Elastic"
        
        source = hits[0].get("_source", {})
        log_data = source.get("event.original") or source.get("message")
        if log_data:
            return log_data.strip(), None
        else:
            return None, "No raw log found in Elastic"
    except Exception as e:
        return None, f"Error ingesting from Elastic: {e}"
```

## Troubleshooting

### Common Issues and Solutions

#### Connection to MongoDB Failed

**Symptoms**: Application fails to start or database operations fail
**Possible Causes**:
- MongoDB service not running
- Incorrect connection string in .env
- Firewall blocking port 27017

**Solutions**:
1. Verify MongoDB service status: `systemctl status mongod`
2. Check MongoDB logs: `tail -f /opt/SmartSOC/var/log/mongodb.log`
3. Validate connection string in .env file
4. Check firewall settings: `firewall-cmd --list-all`

#### SIEM Integration Issues

**Symptoms**: Unable to ingest logs or test queries fail
**Possible Causes**:
- Incorrect credentials
- Network connectivity issues
- Invalid search query syntax

**Solutions**:
1. Verify SIEM credentials in .env
2. Check network connectivity to SIEM
3. Validate query syntax in settings
4. Check SIEM server logs for errors

#### LLM Service Issues

**Symptoms**: Regex generation fails or returns errors
**Possible Causes**:
- LLM service unavailable
- Incorrect endpoint URL
- Authentication issues

**Solutions**:
1. Verify LLM service is running
2. Check endpoint URL in LLM settings
3. Review logs for error messages
4. Test connection with the Test button in settings

#### Performance Issues

**Symptoms**: Slow response times or high CPU/memory usage
**Possible Causes**:
- Insufficient hardware resources
- Large number of database entries
- Inefficient queries

**Solutions**:
1. Increase server resources (CPU/memory)
2. Create indexes on frequently queried fields
3. Implement pagination for large result sets
4. Optimize LLM prompts for faster processing

---

## Advanced Configuration

### Fine-tuning LLM Prompts

The system uses two main prompts for LLM interaction:

1. **Generate Prompt**: For initial regex generation
   ```python
   GENERATE_PROMPT = '''You are an expert in log parsing and regular expressions. Given a part of a raw log entry, generate a precise `pcre2` regex pattern with named capture groups.  
   - Ensure each capture group captures everything until the next field name or end of the log, including spaces and special characters. 
   - If consecutive fields follow the pattern `label=value value ... label=value`, use a pattern like `label=(?<label>.*)\s+nextLabel=` to accurately capture multi-word values.
   - Do not use the anchor ^ in regex patterns.
   - GMT is part of the date and should be included in the regex.
   Return only the regex pattern.
   '''
   ```

2. **Fix Prompt**: For refining existing regex patterns
   ```python
   FIX_PROMPT = '''Given a raw log entry and a partially matched regex, refine the pcre2 regex by generating 
   only the missing portion that was not captured. Ensure the new segment seamlessly integrates with 
   the existing regex without modifying it. Maintain named capture groups and use non-greedy quantifiers 
   in capture groups. Escape all literal special characters. Return only the full regex.'''
   ```

These prompts can be customized to improve regex generation based on specific log formats and requirements.

### Monitoring and Maintenance

Regular maintenance tasks:

1. **Database Backup**: 
   ```bash
   /opt/SmartSOC/bin/mongodump --uri mongodb://localhost:27017/ --out /opt/SmartSOC/backups/$(date +%Y-%m-%d)
   ```

2. **Log Rotation**:
   ```bash
   logrotate /opt/SmartSOC/conf/logrotate.conf
   ```

3. **Performance Monitoring**:
   ```bash
   # Check MongoDB performance
   /opt/SmartSOC/bin/mongosh --eval "db.serverStatus()"
   
   # Check application logs
   tail -f /opt/SmartSOC/var/log/gunicorn.error.log
   ```

## Appendix A: Detailed Installation Guide

The following detailed installation guide is reproduced from the README.md file for easy reference:

### Prerequisites

Ensure that you have the RHEL installation ISO available and mounted.

```bash
mkdir /mnt/rhel-iso
mount /dev/sr0 /mnt/rhel-iso
```

### Install Development Tools and Dependencies

```bash
dnf groupinstall -y "Development Tools"
dnf install -y wget gcc gcc-c++ make zlib-devel bzip2 bzip2-devel readline-devel \
               sqlite sqlite-devel xz xz-devel libffi-devel tk-devel \
               ncurses-devel openssl-devel
```

### Install Nvidia CUDA toolkit and drivers

Enable EPEL and CRB repositories

```bash
subscription-manager repos --enable=rhel-9-for-$arch-appstream-rpms
subscription-manager repos --enable=rhel-9-for-$arch-baseos-rpms
subscription-manager repos --enable=codeready-builder-for-rhel-9-$arch-rpms
```

Install CUDA 12.8

```bash
dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo
dnf clean all
dnf -y install cuda-toolkit-12-8
dnf module enable nvidia-driver:open-dkms
dnf install nvidia-open
reboot
export PATH=${PATH}:/usr/local/cuda-12.8/bin
```

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install vLLM

```bash
uv venv --python 3.12 --seed
source .venv/bin/activate
pip install vllm --extra-index-url https://download.pytorch.org/whl/cu128
```

### Download LLM model

```bash
dnf install git-lfs
git clone https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-AWQ
```

### Create SmartSOC User and Directory Structure
```bash
useradd -M smartsoc
usermod -s /sbin/nologin smartsoc
usermod -d /opt/SmartSOC smartsoc

mkdir -p /opt/SmartSOC/{bin,conf,tmp,pid,web}
mkdir -p /opt/SmartSOC/var/{log,run}
mkdir -p /opt/SmartSOC/var/lib/db
```

### Install MongoDB
```bash
curl -O https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-rhel93-8.0.6.tgz
tar -xzf mongodb-linux-x86_64-rhel93-8.0.6.tgz -C /opt/SmartSOC/
mv /opt/SmartSOC/mongodb-linux-x86_64-rhel93-8.0.6/bin/* /opt/SmartSOC/bin/.
rm -rf /opt/SmartSOC/mongodb-linux-x86_64-rhel93-8.0.6

wget -O /opt/SmartSOC/tmp/mongo_db_tools.tgz https://fastdl.mongodb.org/tools/db/mongodb-database-tools-rhel93-x86_64-100.11.0.tgz
tar -zxf /opt/SmartSOC/tmp/mongo_db_tools.tgz --strip-components=2 -C /opt/SmartSOC/bin mongodb-database-tools-rhel93-x86_64-100.11.0/bin/*
```

#### Additional MongoDB Operations

**Create backup dump**
```bash
/opt/SmartSOC/bin/mongodump --uri mongodb://192.168.50.191:27017/
```

**Restore dump**
```bash
/opt/SmartSOC/bin/mongorestore --uri mongodb://192.168.50.191:27017/ /root/dump/
```

**Connect to MongoDB using mongosh**
```bash
wget -O /opt/SmartSOC/tmp/mongodb-mongosh.rpm https://downloads.mongodb.com/compass/mongodb-mongosh-2.4.2.x86_64.rpm
rpm -ivh /opt/SmartSOC/tmp/mongodb-mongosh.rpm
mv /usr/bin/mongosh /opt/SmartSOC/bin/.
chown -R smartsoc. /opt/SmartSOC
/opt/SmartSOC/bin/mongosh --host 192.168.50.191 --port 27017
```

### Configure MongoDB

**Create MongoDB configuration file**
```bash
cat > /opt/SmartSOC/conf/mongod.conf << "endmsg"
systemLog:
  destination: file
  logAppend: true
  path: /opt/SmartSOC/var/log/mongodb.log

storage:
  dbPath: /opt/SmartSOC/var/lib/db

processManagement:
  pidFilePath: /opt/SmartSOC/pid/mongod.pid

net:
  port: 27017
  bindIp: 0.0.0.0
  unixDomainSocket:
    pathPrefix: /opt/SmartSOC/tmp
endmsg
```

### Apply SELinux Security Context
```bash
semanage fcontext -a -t mongod_log_t /opt/SmartSOC/var/log/
semanage fcontext -a -t mongod_var_lib_t /opt/SmartSOC/var/lib/db/
chcon -Rv -u system_u -t mongod_log_t /opt/SmartSOC/var/log/
chcon -Rv -u system_u -t mongod_var_lib_t /opt/SmartSOC/var/lib/db/
```














### Install Python 3.13.2
```bash
# Define installation directory
PREFIX=/opt/SmartSOC/
VERSION=3.13.2

# Download & extract Python source
wget https://www.python.org/ftp/python/${VERSION}/Python-${VERSION}.tgz
tar xvf Python-${VERSION}.tgz
cd Python-${VERSION}

# Build and install Python
make clean
./configure --prefix=$PREFIX --enable-shared --with-ensurepip=install
make -j$(nproc)
make install

# Configure library paths
echo "/opt/SmartSOC/lib" | sudo tee /etc/ld.so.conf.d/smartsoc.conf
ldconfig
```

### Setup Web Application

**Create necessary directories**
```bash
mkdir -p /opt/SmartSOC/web/{templates,static}
```

### Install Required Python Packages
```bash
cat > /opt/SmartSOC/web/requirements.txt << "endmsg"
pymongo
python-dotenv
bottle
gunicorn
dotenv
elasticsearch
flask
openpyxl
pycryptodome
requests
flask-cors
splunk-sdk
nanoid
endmsg

chown -R smartsoc. /opt/SmartSOC/
sudo -u smartsoc /opt/SmartSOC/bin/python3 -m pip install -r /opt/SmartSOC/web/requirements.txt
```

### Download Static Assets
```bash
mkdir -p /opt/SmartSOC/web/static/{css,js}

wget -O /opt/SmartSOC/web/static/css/bootstrap.min.css \
    https://cdn.jsdelivr.net/npm/bootstrap@5.3.5/dist/css/bootstrap.min.css

wget -O /opt/SmartSOC/web/static/js/bootstrap.min.js \
    https://cdn.jsdelivr.net/npm/bootstrap@5.3.5/dist/js/bootstrap.bundle.min.js

wget -O /opt/SmartSOC/web/static/js/jquery.min.js \
    https://code.jquery.com/jquery-3.5.1.min.js

wget -O /opt/SmartSOC/web/static/js/popper.min.js \
    https://cdnjs.cloudflare.com/ajax/libs/popper.js/2.11.8/umd/popper.min.js
```

### Configure Gunicorn
```bash
cat > /opt/SmartSOC/conf/gunicorn.conf.py << "endmsg"
import multiprocessing
bind = "0.0.0.0:8080"
#workers = multiprocessing.cpu_count() * 2 + 1
workers = 2
chdir = "/opt/SmartSOC/web"
pidfile = "/opt/SmartSOC/var/run/gunicorn.pid"
accesslog = "/opt/SmartSOC/var/log/gunicorn.access.log"
errorlog = "/opt/SmartSOC/var/log/gunicorn.error.log"
loglevel = "info"
endmsg
```

### Create SmartSOC Daemon Script
```bash
cat > /opt/SmartSOC/bin/smartsocd << "endmsg"
#!/bin/bash

SMARTSOC_HOME="/opt/SmartSOC"
MONGO_CONF="$SMARTSOC_HOME/conf/mongod.conf"
GUNICORN_CONF="$SMARTSOC_HOME/conf/gunicorn.conf.py"

start() {
    echo "Starting SmartSOC services..."

    # Start MongoDB (No sudo needed)
    echo "Starting MongoDB..."
    $SMARTSOC_HOME/bin/mongod --config $MONGO_CONF --fork
    if [[ $? -ne 0 ]]; then
        echo "Failed to start MongoDB." >&2
        exit 1
    fi

    # Start Gunicorn (No sudo needed)
    echo "Starting Gunicorn..."
    $SMARTSOC_HOME/bin/gunicorn -c $GUNICORN_CONF app:app
    if [[ $? -ne 0 ]]; then
        echo "Failed to start Gunicorn." >&2
        exit 1
    fi

    echo "SmartSOC started successfully."
}

stop() {
    echo "Stopping SmartSOC services..."
    pkill -f gunicorn
    sleep 2
    pkill -f mongod
    sleep 2
    echo "SmartSOC stopped."
}

restart() {
    stop
    sleep 2
    start
}

status() {
    echo "Checking service status..."
    pgrep -f gunicorn >/dev/null && echo "Gunicorn is running" || echo "Gunicorn is not running"
    pgrep -f mongod >/dev/null && echo "MongoDB is running" || echo "MongoDB is not running"
}

case "$1" in
    start) start ;;
    stop) stop ;;
    restart) restart ;;
    status) status ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
endmsg

chown -R smartsoc. /opt/SmartSOC
chmod +x /opt/SmartSOC/bin/smartsocd
```

### Create Systemd Service
```bash
cat > /etc/systemd/system/SmartSOC.service << "endmsg"
[Unit]
Description=SmartSOC Service
After=network.target

[Service]
User=smartsoc
Group=smartsoc
ExecStart=/opt/SmartSOC/bin/smartsocd start
ExecStop=/opt/SmartSOC/bin/smartsocd stop
Restart=always
Type=simple

[Install]
WantedBy=multi-user.target
endmsg
```

### Serve model on vLLM

```bash
vllm serve ./Qwen2.5-Coder-32B-Instruct-AWQ --host 0.0.0.0 --port 8000 --served-model-name qwen25-coder-32b-awq
```

### Run vLLM Docker

docker run --runtime nvidia --gpus all `
    -v local/model/directory:/root/.cache/models `
    -p 8000:8000 `
    --ipc=host `
    vllm/vllm-openai:latest `
    --model /root/.cache/models/Qwen2.5-Coder-32B-Instruct-AWQ
