# syntax=docker/dockerfile:1

############################################################
# Builder stage: install Python dependencies
############################################################
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for building Python wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libpcre2-dev \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


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
    tini \
    wget \
    libpcre2-8-0 \
    libgssapi-krb5-2 \
    && rm -rf /var/lib/apt/lists/*

# Download MongoDB Database Tools tarball and install
ENV MONGO_TOOLS_VERSION=100.14.0
RUN wget -q https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian12-x86_64-${MONGO_TOOLS_VERSION}.tgz \
    && tar -xzf mongodb-database-tools-debian12-x86_64-${MONGO_TOOLS_VERSION}.tgz \
    && mv mongodb-database-tools-debian12-x86_64-${MONGO_TOOLS_VERSION}/bin/* /usr/local/bin/ \
    && rm -rf mongodb-database-tools-debian12-x86_64-${MONGO_TOOLS_VERSION}* 

# Copy Python packages from builder
COPY --from=builder /install/lib /usr/local/lib
COPY --from=builder /install/bin /usr/local/bin
COPY --from=builder /install/include /usr/local/include


# Copy application code
COPY . .

# Use tini for PID 1 signal handling
ENTRYPOINT ["tini", "--"]

# Default command to run your setup.py
CMD ["python", "setup.py"]
