# WeaMind System Documentation

> The architecture is inspired by Domain-Driven Design (DDD) principles.

## High-Level Architecture Overview

- Three-component separation: line-bot (FastAPI app, this project), wea-data (periodically updates weather data), wea-ai (provides AI-related features)
- wea-ai: Deployed independently, only outputs intent/schema, does not access data directly
- wea-data: Deployed independently, operates separately from the other two. Responsible only for ETL, updating the latest weather data from external sources

## Project Scope

- This repo only contains the **line-bot** module code
- wea-data and wea-ai are independent components (microservices) and are not included in this repo

## Component Interaction Flow

- line-bot handles all external requests; only interacts with wea-ai via HTTP API when intent analysis or AI features are needed
- line-bot processes LINE webhook events, and may forward to wea-ai depending on the request type
- wea-data only performs scheduled ETL, writing weather data into the database, and does not provide any API
- All data queries and access are performed directly by line-bot via the database
- wea-ai provides intent detection and dialogue schema, but does not access data directly

## Main Module Responsibilities

- app/core: Global configuration, database connection
- app/user: User data models, CRUD API, validation
- app/weather: For weather data access and logic (not yet implemented)
- app/main.py: FastAPI app entry point, router registration

## Data Flow and Persistence

- wea-data periodically ETLs external weather data into PostgreSQL
- line-bot directly queries/writes PostgreSQL, including user state and weather data
- Alembic manages database schema migrations
- SQLAlchemy manages all tables

## API Design Principles

- RESTful style, JSON as the main payload format
- All POST/PUT request body parameters are uniformly named payload
- Must verify the signature of incoming LINE webhook requests

## Tech Stack

- FastAPI: High performance, type safety, easy to test
- Pydantic: Data validation and serialization
- SQLAlchemy 2.0: ORM, convenient for database management
- Alembic: Database migration
- pytest: Testing

## Typical Request Flow (LINE webhook example)

1. LINE platform pushes a webhook to /line/webhook
2. line-bot verifies the signature and parses the event
3. Depending on the event, queries user state or calls wea-ai to determine intent
4. If weather data is needed:
   - Fixed-format query: line-bot queries the database directly
   - Natural language query: line-bot interacts with wea-ai to obtain intent, then queries the database, repeating until a clear result is obtained
5. Composes the response message and returns it to the LINE platform
