FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Compile bytecode and avoid symlinks
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# When DEV=true also install dev dependencies
ARG DEV=false

# ---------- layer 1: heavy dependencies ----------
# Cache only invalidates when these two files change
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$DEV" = "true" ]; then \
    uv sync --locked; \
    else \
    uv sync --locked --no-dev; \
    fi

# ---------- layer 2: application code ----------
COPY . /app

# Put the venv at the beginning of PATH
ENV PATH="/app/.venv/bin:$PATH"

# Do not use uv as the entrypoint
ENTRYPOINT []
