# WeaMind

## Development Setup

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Start PostgreSQL using Docker Compose:

   ```bash
   docker compose up -d db
   ```

   The `db_data` volume will persist your database data across container restarts.
