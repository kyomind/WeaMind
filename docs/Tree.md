# Project Directory Tree (3 Levels)

.
├── AGENTS.md
├── alembic.ini
├── app
│   ├── __init__.py
│   ├── core
│   │   ├── config.py
│   │   └── database.py
│   ├── line
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   └── utils.py
│   ├── main.py
│   └── user
│       ├── constants.py
│       ├── models.py
│       ├── router.py
│       ├── schemas.py
│       ├── service.py
│       └── utils.py
├── blogs
│   └── README.md
├── conftest.py
├── coverage.xml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── docker-compose.yml
├── Dockerfile
├── docs
│   ├── Architecture.md
│   ├── Discuss.md
│   ├── Example.md
│   ├── Todo.md
│   └── Tree.md
├── LICENSE
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
│   ├── test_line.py
│   └── test_user.py
└── uv.lock

11 directories, 44 files
