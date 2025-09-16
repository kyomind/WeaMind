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

### When Creating New Tables (SQLAlchemy Models)
1. **ALWAYS use the `revision` command**: When creating new SQLAlchemy base models (i.e., adding new tables), you MUST use the `revision` command from the Makefile. Never manually create database migration files.
2. **Rename migration files for readability**: After using the `revision` command, you MUST rename the generated migration file to make it more readable and descriptive. The default filename is often generic and should be improved for better maintainability.

## Best Practices
1. Before modifying or creating migration files, understand the existing migration workflow
2. Use standardized commands defined in the Makefile for migration operations
3. Ensure migration files comply with the project's naming conventions and structural requirements
