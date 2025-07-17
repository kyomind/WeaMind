FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Use 'code' to avoid confusion with the 'app' directory
WORKDIR /code

# Compile bytecode and avoid symlinks
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# ---------- layer 1: heavy dependencies ----------
# Cache only invalidates when these two files change
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# ---------- layer 2: application code ----------
COPY . /code

# Put the venv at the beginning of PATH
ENV PATH="/code/.venv/bin:$PATH"

# Do not use uv as the entrypoint
ENTRYPOINT []
