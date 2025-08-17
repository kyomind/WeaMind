# WeaMind System Documentation

## High-Level Architecture Overview

- Two-component separation: line-bot (FastAPI app, this project), wea-data (periodically updates weather data)
- wea-data: Deployed independently, operates separately from line-bot. Responsible only for ETL, updating the latest weather data from external sources

## Project Scope

- This repo only contains the **line-bot** module code
- wea-data is an independent component (microservice) and is not included in this repo

## Component Interaction Flow

- line-bot handles all external requests and processes text input using implemented location parsing logic
- line-bot processes LINE webhook events with location query parsing and user interaction management
- wea-data only performs scheduled ETL, writing weather data into the database, and does not provide any API
- All data queries and access are performed directly by line-bot via the database

## Main Module Responsibilities

> Project architecture is inspired by Domain-Driven Design (DDD) principles.

- app/core: Global configuration, database connection
- app/line: Handles LINE webhook requests, processes events, location parsing
- app/user: User data models, CRUD API, validation
- app/weather: Weather data models and location query logic
- app/main.py: FastAPI app entry point, router registration

## Data Flow and Persistence

- wea-data periodically ETLs external weather data into PostgreSQL
- line-bot directly queries/writes PostgreSQL, including user state and weather data
- Alembic manages database schema migrations
- SQLAlchemy manages all tables

## Tech Stack

- FastAPI: LINE bot framework, provides async support
- Pydantic: Data validation and serialization
- SQLAlchemy 2.0: ORM, convenient for database management
- Alembic: Database migration
- pytest: Testing

## Typical Request Flow (LINE webhook example)

1. LINE platform pushes a webhook to /line/webhook
2. line-bot verifies the signature and parses the event
3. Depending on the event type, queries user state or processes location queries
4. If weather data is needed, line-bot queries the database directly using appropriate parsing logic
5. Composes the response message and returns it to the LINE platform
