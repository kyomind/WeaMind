# AGENTS.md

## Test Commands

- Run tests: `uv run pytest`
- Lint check: `uv run ruff check .`
- Format code: `uv run ruff format .`

## Coding Guidelines

1. Use type hints to ensure type safety for FastAPI routes and models.
2. Every function must include a docstring; complex ones should follow the `.github/prompts/docstring.prompt.md` standard.
3. Add comments to special or important parts of the code to help readers understand the design intent. (very important)
4. When writing a Python docstring with only a summary, place the opening triple quotes, the summary, and the closing triple quotes each on a separate line.
5. For Router (API) functions, only a summary docstring is required.

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
  - Todo example: `docs/Example.md`
- Project architecture & technical decisions: `docs/Architecture.md`
- Project directory structure: `docs/Tree.md`
