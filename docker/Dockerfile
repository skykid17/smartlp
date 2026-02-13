# syntax=docker/dockerfile:1

############################################################
# Builder stage
############################################################
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpcre2-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /app/wheels \
    -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu


############################################################
# Runtime stage
############################################################
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SMARTLP_ARCHIVE=/smartlp.archive

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini wget libpcre2-8-0 libgssapi-krb5-2 \
    && rm -rf /var/lib/apt/lists/*

ENV MONGO_TOOLS_VERSION=100.14.0
RUN wget -q https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian12-x86_64-${MONGO_TOOLS_VERSION}.tgz \
    && tar -xzf mongodb-database-tools-debian12-x86_64-${MONGO_TOOLS_VERSION}.tgz \
    && mv mongodb-database-tools-debian12-x86_64-${MONGO_TOOLS_VERSION}/bin/* /usr/local/bin/ \
    && rm -rf mongodb-database-tools-debian12-x86_64-${MONGO_TOOLS_VERSION}*

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Preload embedding model
RUN python - <<EOF
from pathlib import Path
from huggingface_hub import snapshot_download
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
TARGET_DIR = Path("./models/all-MiniLM-L6-v2")

snapshot_download(
    repo_id=MODEL_ID,
    local_dir=str(TARGET_DIR)
)

print("Embedding model downloaded to", TARGET_DIR)
EOF

# Runtime artefacts (explicit, single-copy)
COPY build-assets/smartlp.archive /smartlp.archive

# Application code 
COPY *.py .
COPY src/ ./src/
COPY certs/ ./certs/
COPY ansible/ ./ansible/
COPY static/ ./static/
COPY templates/ ./templates/
COPY tailwind.config.js .

ENTRYPOINT ["tini", "--"]
CMD ["python", "setup.py"]
