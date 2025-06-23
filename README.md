# WeaMind

[![codecov](https://codecov.io/gh/kyomind/WeaMind/branch/main/graph/badge.svg)](https://codecov.io/gh/kyomind/WeaMind)

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
