# Project Directory Tree (3 Levels)

.
├── AGENTS.md
├── alembic.ini
├── app
│   ├── __init__.py
│   ├── core
│   │   ├── __init__.py
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
├── CLAUDE.md
├── coverage.xml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── docker-compose.yml
├── Dockerfile
├── docs
│   ├── Architecture.md
│   ├── Example.md
│   ├── Location-Input-Parsing-Implementation.md
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
│       ├── 8fda37b4a59c_optimize_weather_table_indexes.py
│       ├── b05ddf47e04e_create_user_table.py
│       └── f557a1959851_create_location_weather_tables.py
├── prd
│   └── weamind-prd-v1.md
├── pyproject.toml
├── README.md
├── scripts
│   ├── clean_docs.sh
│   ├── cleanup_local_branches_preview.sh
│   ├── cleanup_local_branches.sh
│   ├── export_branch_docs.sh
│   ├── gen_tree.sh
│   └── sync_instructions.sh
├── tests
│   ├── conftest.py
│   ├── core
│   │   ├── conftest.py
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

18 directories, 64 files
