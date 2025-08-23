# Project Directory Tree (3 Levels)

.
├── AGENTS.md
├── alembic.ini
├── app
│   ├── __init__.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── logging.py
│   ├── line
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── service.py
│   ├── main.py
│   ├── user
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── service.py
│   └── weather
│       ├── __init__.py
│       ├── models.py
│       └── service.py
├── blogs
│   └── README.md
├── CHANGELOG.md
├── CLAUDE.md
├── coverage.xml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── docker-compose.yml
├── Dockerfile
├── docs
│   ├── Architecture.md
│   ├── changelog
│   │   ├── AI-Agent-Guide.md
│   │   ├── ask-page-repo-CHANGELOG.md
│   │   ├── Implementation-Report.md
│   │   ├── MEMORY-HOOK.md
│   │   └── README.md
│   ├── Example.md
│   ├── rich_menu
│   │   ├── implementation-plan.md
│   │   ├── preview.html
│   │   ├── README.md
│   │   ├── rich_menu_config.json
│   │   ├── rich_menu_template-min.png
│   │   ├── rich_menu_template.png
│   │   └── rich_menu_template.svg
│   ├── seed
│   │   ├── DONE-LIFF-Location-Settings-Complete.md
│   │   └── Security-Assessment-and-Checklist.md
│   ├── Todo.md
│   └── Tree.md
├── GEMINI.md
├── LICENSE
├── logs
│   └── app.log
├── Makefile
├── migrations
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions
│       ├── 526d69e2321e_restrict_wea_bot_weather_permissions.py
│       ├── 67c6acf6e8df_setup_database_permissions.py
│       ├── 69db147baaec_grant_location_insert_update_.py
│       ├── 7f11c9b6d545_feature_liff_location_settings_20250816_.py
│       ├── 8fda37b4a59c_optimize_weather_table_indexes.py
│       ├── b05ddf47e04e_create_user_table.py
│       └── f557a1959851_create_location_weather_tables.py
├── prd
│   └── weamind-prd-v1.md
├── pyproject.toml
├── README.md
├── scripts
│   ├── changelog.sh
│   ├── clean_docs.sh
│   ├── cleanup_local_branches_preview.sh
│   ├── cleanup_local_branches.sh
│   ├── export_branch_docs.sh
│   ├── gen_tree.sh
│   ├── rich_menu_manager.py
│   ├── sync_instructions.sh
│   ├── update_liff_version.sh
│   ├── worktree_add.sh
│   ├── worktree_clean.sh
│   ├── worktree_list.sh
│   └── worktree_remove.sh
├── static
│   ├── data
│   │   └── tw_admin_divisions.json
│   └── liff
│       └── location
├── tests
│   ├── conftest.py
│   ├── core
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_config.py
│   │   └── test_logging.py
│   ├── line
│   │   ├── conftest.py
│   │   └── test_line.py
│   ├── user
│   │   ├── conftest.py
│   │   └── test_user.py
│   └── weather
│       ├── conftest.py
│       └── test_location_service.py
└── uv.lock

25 directories, 89 files
