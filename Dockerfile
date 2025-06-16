# 第一階段：建構環境與全域安裝 uv 及相依套件
FROM python:3.12-slim-bookworm AS builder

# 安裝系統相依套件（僅 curl，build-essential 非必要可省略）
RUN apt update && apt install -y curl && rm -rf /var/lib/apt/lists/*

# 全域安裝 uv 並設定 PATH
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked

# 第二階段：建立乾淨的 image
FROM python:3.12-slim-bookworm

WORKDIR /app
# 設定 PATH 讓 uv 可用
ENV PATH="/root/.local/bin:$PATH"
# 從 builder 階段複製已安裝的 site-packages 及 uv 執行檔
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /root/.local/bin/uv /root/.local/bin/uv
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--workers", "4"]
