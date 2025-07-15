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
│   └── user
│       ├── __init__.py
│       ├── constants.py
│       ├── models.py
│       ├── router.py
│       ├── schemas.py
│       ├── service.py
│       └── utils.py
├── blogs
│   └── README.md
├── coverage.xml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── docker-compose.yml
├── Dockerfile
├── docs
│   ├── Architecture.md
│   ├── Config-Refactor-Simple.md
│   ├── Discuss.md
│   ├── Example.md
│   ├── Todo.md
│   └── Tree.md
├── LICENSE
├── logs
│   └── app.log
├── Makefile
├── migrations
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions
│       └── b05ddf47e04e_create_user_table.py
├── pyproject.toml
├── pyrightconfig.json
├── README.md
├── scripts
│   ├── cleanup_local_branches_preview.sh
│   ├── cleanup_local_branches.sh
│   └── gen_tree.sh
├── tests
│   ├── conftest.py
│   ├── core
│   │   ├── conftest.py
│   │   ├── test_config.py
│   │   └── test_logging.py
│   ├── line
│   │   ├── conftest.py
│   │   └── test_line.py
│   └── user
│       ├── conftest.py
│       └── test_user.py
└── uv.lock

15 directories, 52 files
