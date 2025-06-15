# WeaMind

FastAPI-based backend for a weather LINE Bot.

## Setup

1. Install Python 3.12.
2. Install dependencies:
   ```bash
   pip install -e .
   ```
3. Copy `.env.example` to `.env` and adjust values.
4. Start PostgreSQL with Docker Compose:
   ```bash
   docker-compose up -d
   ```
5. Run the API server:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`.
