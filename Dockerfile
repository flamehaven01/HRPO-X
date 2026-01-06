# HRPO-X Dockerfile
# Multi-stage build for production deployment

# ============================================================================
# Stage 1: Builder - Install dependencies and prepare environment
# ============================================================================
FROM python:3.10-slim AS builder

LABEL maintainer="hrpo-x@flamehaven.io"
LABEL version="1.0.0"
LABEL description="HRPO-X - Hybrid Reasoning with Policy Optimization"

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Install package
RUN pip install --no-cache-dir -e .

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM python:3.10-slim AS runtime

LABEL maintainer="hrpo-x@flamehaven.io"
LABEL version="1.0.0"

# Create non-root user for security
RUN useradd -m -u 1000 hrpox && \
    mkdir -p /app /data /models && \
    chown -R hrpox:hrpox /app /data /models

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=hrpox:hrpox . .

# Switch to non-root user
USER hrpox

# Expose ports
EXPOSE 8000 8001 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HRPO_HOME=/app \
    HRPO_DATA_DIR=/data \
    HRPO_MODEL_DIR=/models

# Default command
CMD ["python", "hrpo_core_v2_2.py"]

# ============================================================================
# Stage 3: Development - Include dev tools
# ============================================================================
FROM runtime AS development

USER root

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install dev Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir pytest pytest-cov black isort flake8 mypy

USER hrpox

# Override command for development
CMD ["bash"]

# ============================================================================
# Stage 4: Training - GPU support with PyTorch
# ============================================================================
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04 AS training

LABEL maintainer="hrpo-x@flamehaven.io"
LABEL version="1.0.0"

# Install Python 3.10
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 hrpox && \
    mkdir -p /app /data /models /checkpoints && \
    chown -R hrpox:hrpox /app /data /models /checkpoints

WORKDIR /app

# Install PyTorch with CUDA support
RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Copy and install requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=hrpox:hrpox . .
RUN pip3 install --no-cache-dir -e .

USER hrpox

# Expose TensorBoard port
EXPOSE 6006

ENV PYTHONUNBUFFERED=1 \
    CUDA_VISIBLE_DEVICES=0 \
    HRPO_HOME=/app \
    HRPO_DATA_DIR=/data \
    HRPO_MODEL_DIR=/models \
    HRPO_CHECKPOINT_DIR=/checkpoints

CMD ["python3", "-m", "training.trainer", "--config", "config/base_config.yaml"]
