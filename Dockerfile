# syntax=docker/dockerfile:1

############################################################
# Builder stage: install Python dependencies
############################################################
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for building Python wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpcre2-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu


############################################################
# Runtime stage: minimal image with Python and MongoDB tools
############################################################
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SMARTLP_ARCHIVE=/smartlp.archive

WORKDIR /app

# Install tini, libpcre2, wget (for downloading tarball)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini wget libpcre2-8-0 libgssapi-krb5-2 \
    && rm -rf /var/lib/apt/lists/*

# Download MongoDB Database Tools tarball and install
ENV MONGO_TOOLS_VERSION=100.14.0
RUN wget -q https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian12-x86_64-${MONGO_TOOLS_VERSION}.tgz \
    && tar -xzf mongodb-database-tools-debian12-x86_64-${MONGO_TOOLS_VERSION}.tgz \
    && mv mongodb-database-tools-debian12-x86_64-${MONGO_TOOLS_VERSION}/bin/* /usr/local/bin/ \
    && rm -rf mongodb-database-tools-debian12-x86_64-${MONGO_TOOLS_VERSION}* 

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY . .

# Use tini for PID 1 signal handling
ENTRYPOINT ["tini", "--"]

# Default command to run your setup.py
CMD ["python", "setup.py"]
