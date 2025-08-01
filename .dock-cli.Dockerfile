#####################
# -- builder stage --
#####################
FROM python:3.12-bookworm AS builder

RUN apt-get update && apt-get install -y \
    python3-tk \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Create virtual environment and install dependencies only (not the workspace package)
RUN uv venv /app/.venv
RUN uv sync --frozen --no-dev --no-install-workspace
# Copy source code and install the package
COPY . .
RUN uv pip install --no-deps .
######################
# -- runtime stage --
######################

FROM python:3.12-slim AS runtime
LABEL org.opencontainers.image.title="neptoon-cli"

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" 

# Copy the virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy the application code
COPY --from=builder /app /app

WORKDIR /workingdir

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 8501

ENTRYPOINT ["neptoon", "-p", "/workingdir/processconfig.yaml", "-s", "/workingdir/sensorconfig.yaml"]