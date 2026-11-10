---
description: "依既有 Makefile 與 Alembic 流程建立、檢查及執行資料庫遷移"
---

# Migrate the Database

## Goal

Create or apply the requested database migration using the existing Alembic and Makefile workflow. Separate generating a revision from applying it to a database.

## Workflow

1. Read `Makefile`, the relevant SQLAlchemy models, recent revisions in `migrations/versions/`, and the Alembic configuration. Confirm whether the task is to generate, apply, or roll back a migration.
2. For new model or schema changes, use `make revision` to generate the revision. Rename the generated file descriptively if needed, preserving its revision ID and `down_revision` chain.
3. Review generated `upgrade()` and `downgrade()` operations. Check for accidental drops, destructive type changes, nullability issues, and existing-data requirements; autogeneration is not proof of a safe migration. Do not rewrite already-applied shared revisions to change their behavior.
4. Inspect the Makefile's actual database target before applying anything. Use `make migrate` for upgrades and `make rollback` for the supported rollback operation only after confirming the environment and requested revision. Do not assume rollback is nondestructive.
5. Validate against a disposable or explicitly approved database when available. Before production or destructive operations, obtain explicit approval and confirm the backup/recovery plan. If no safe test database is available, review the revision statically and report the untested execution path; do not test on production by default.

## Output

Report the revision ID, changed files, intended schema/data effects, commands run, target environment, validation results, and recovery limitations. Do not report a migration as applied based only on generating its file.
