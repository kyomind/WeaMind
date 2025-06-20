# AGENTS.md

## What is WeaMind?

WeaMind is a system that delivers intelligent weather-related services by integrating weather data and AI-powered interactions.

This repository only contains the line-bot (FastAPI) module, which serves as the user-facing entry point and collaborates with other microservices.

## Test Commands

- Run tests: `uv run pytest`
- Lint check: `uv run ruff check .`
- Format code: `uv run ruff format .`

## Coding Guidelines

1. Use type hints to ensure type safety for FastAPI routes and models.
2. Add comments to special or important parts of the code to help readers understand the design intent. (very important)
3. Every function must include a docstring; follow the `.github/prompts/docstring.prompt.md` standard.

## Naming Conventions

- pytest fixtures:
  - return a helper function: start with verb, like a normal function, e.g., `create_user`
  - return a object or value: use noun, like a variable, e.g., `user`
- FastAPI router functions:
  - the parameter name represents the HTTP request body: use `payload` in any case

## Commit Message Guidelines

Write a concise and natural commit message summarizing the following code diff in English. Avoid listing specific method or variable names unless essential. Focus on the overall intent of the change. Keep the message short and readable, ideally under 10 words. Do not invent motivations unless explicitly obvious in the code.

## WeaMind High-Level Architecture

- Three-component separation: line-bot (FastAPI app, this project), wea-data (periodically updates weather data), wea-ai (provides AI-related features)
- wea-ai: deployed independently, only provides intent/schema, does not access data directly
- wea-data: deployed independently, responsible for ETL, updates the latest weather data from external sources

## Project Scope

- This repo only contains the **line-bot** module code
- wea-data and wea-ai are independent components (microservices) and are not included in this repo

## Key References

- Todo list: `docs/Todo.md`
- Project architecture & technical decisions: `docs/Architecture.md`
- Project directory structure: `docs/Tree.md`
