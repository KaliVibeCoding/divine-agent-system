# syntax=docker/dockerfile:1.7
# =============================================================================
# Divine Agent System — Supreme Agentic Orchestrator (SAO)
# Multi-stage Docker build.  Targets:
#   base         — common Python 3.12 environment
#   dependencies — wheels + pip install
#   development  — adds dev tools + source code, default CMD = uvicorn dev server
#   production   — minimal runtime, gunicorn/uvicorn workers
#   testing      — runs pytest
#   quantum      — production + qiskit-aer (already in requirements, just env var)
#   final        — alias of production
#
# Build:
#   docker build --target production -t sao:2.0.0 .
#   docker build --target development -t sao:dev .
# =============================================================================

ARG PYTHON_VERSION=3.12

# ---------- base ------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ca-certificates \
        git \
        libpq-dev \
        libssl-dev \
        libffi-dev \
        pkg-config \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system divine && useradd --system --gid divine --create-home divine
WORKDIR /app

# ---------- dependencies ----------------------------------------------------
FROM base AS dependencies

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

# ---------- development -----------------------------------------------------
FROM dependencies AS development

# Dev tooling already lives in requirements.txt (ruff, black, mypy, pytest…)
COPY . .
RUN chown -R divine:divine /app

USER divine
EXPOSE 8000 8001 8080 9090

# Hot-reload dev server (FastAPI surface in orchestrator.main)
CMD ["uvicorn", "orchestrator.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------- production ------------------------------------------------------
FROM dependencies AS production

COPY agents/        ./agents/
COPY orchestrator/  ./orchestrator/
COPY config/        ./config/
COPY config.yaml setup.py README.md deploy.py docker-entrypoint.sh ./

RUN chmod +x docker-entrypoint.sh \
 && pip install -e . \
 && mkdir -p /app/logs /app/data /app/backups \
 && chown -R divine:divine /app

USER divine
EXPOSE 8000 8001 8080 9090

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "orchestrator.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ---------- testing ---------------------------------------------------------
FROM development AS testing

USER root
RUN pip install pytest pytest-asyncio pytest-cov
USER divine
CMD ["pytest", "-q", "test_system.py"]

# ---------- quantum (real qiskit-aer build) ---------------------------------
FROM production AS quantum

ENV DIVINE_AGENT_QUANTUM_ENABLED=true

# ---------- final default ---------------------------------------------------
FROM production AS final

LABEL org.opencontainers.image.title="Divine Agent System" \
      org.opencontainers.image.description="Supreme Agentic Orchestrator (SAO) — 2026 stack" \
      org.opencontainers.image.version="2.0.0" \
      org.opencontainers.image.created="2026-05-14" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/KaliVibeCoding/divine-agent-system"
