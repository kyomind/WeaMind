# 第一階段：建構並安裝 uv 與專案相依
FROM python:3.12-slim AS builder

# 安裝系統工具
RUN apt update && apt install -y curl && rm -rf /var/lib/apt/lists/*

# 安裝 astral-sh/uv，並把 uv 放到 PATH
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# 複製鎖定檔
COPY pyproject.toml uv.lock ./

# 直接在 system Python 安裝 main dependencies
RUN export UV_PROJECT_ENVIRONMENT=/usr/local
RUN uv sync --locked --no-dev

# 第二階段：乾淨映像只帶執行環境
FROM python:3.12-slim

WORKDIR /app

# 把 builder 階段安裝好的 site-packages 複製過來
COPY --from=builder /usr/local/lib/python3.12/site-packages \
    /usr/local/lib/python3.12/site-packages

# 確保 PATH 包含全域二進位
ENV PATH="/usr/local/bin:$PATH"

# 複製專案程式碼
COPY . .

EXPOSE 8000

# 最終執行指令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--workers", "4"]
