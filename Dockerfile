FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# 編譯 bytecode、避免軟連結
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# DEV=true 時會連同 dev-deps 一起安裝
ARG DEV=false

# ---------- layer 1：重依賴 ----------
# 只有這兩檔案改變才會失效
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$DEV" = "true" ]; then \
    uv sync --locked; \
    else \
    uv sync --locked --no-dev; \
    fi

# ---------- layer 2：專案程式碼 ----------
COPY . /app

# 把 venv 放到 PATH 最前
ENV PATH="/app/.venv/bin:$PATH"

# 不用 uv 當 entrypoint
ENTRYPOINT []
