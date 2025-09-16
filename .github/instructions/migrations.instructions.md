---
applyTo: '**/models.py'
---

# Migrations Instructions

## Overview
When working with Python files in the `/migrations` directory, you must first read and understand the project's Makefile content.

## Required Reading
- **File**: `Makefile`
- **Purpose**: Understand database migration-related commands and workflows

## Key Commands from Makefile
When processing migrations, pay special attention to the following commands in the Makefile:
- `migrate`: Execute database migrations
- `revision`: Create new migration files
- `rollback`: Rollback migrations

## Critical Requirements

### When Generating Database Migration Files
1. **ALWAYS use the `revision` command**: For any action that generates a new database migration file (e.g., creating, modifying, or deleting SQLAlchemy models/tables), use the `revision` command from the Makefile to generate migration files.
2. **Rename migration files for readability**: After using the `revision` command, rename the generated migration file to a descriptive and readable name to improve maintainability.

## Best Practices
1. Before modifying or creating migration files, understand the existing migration workflow
2. Use standardized commands defined in the Makefile for migration operations
3. Ensure migration files comply with the project's naming conventions and structural requirements
