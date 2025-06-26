# WeaMind

[![WeaMind CI](https://github.com/kyomind/WeaMind/actions/workflows/ci.yml/badge.svg)](https://github.com/kyomind/WeaMind/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/kyomind/WeaMind/branch/main/graph/badge.svg)](https://codecov.io/gh/kyomind/WeaMind)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)

This project uses Docker for local development. Copy `.env.example` to `.env` and start the containers:

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`.

## LINE Webhook Setup

Set `LINE_CHANNEL_SECRET` in `.env` for signature verification. You can test the
webhook locally with:

```bash
curl -X POST \
  -H "X-Line-Signature: <signature>" \
  -H "Content-Type: application/json" \
  -d '{}' http://localhost:8000/line/webhook
```
