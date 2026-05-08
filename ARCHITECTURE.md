# Todo CLI Manager - Architecture

## Overview
A modular Python CLI todo manager with SQLite persistence, CSV export, and comprehensive testing.

## Module Structure

### 1. `todocli/models.py`
**Responsibility**: Define data models for todos
- `Todo` class with fields: id, title, description, priority, category, completed, created_at, updated_at
- Data validation and serialization
- Interfaces:
  - `Todo.__init__(title, description, priority, category)`
  - `Todo.to_dict()` → dict
  - `Todo.from_dict(data)` → Todo instance

### 2. `todocli/database.py`
**Responsibility**: SQLite database operations and migrations
- Database initialization and connection management
- CRUD operations for todos
- Schema management
- Interfaces:
  - `Database.__init__(db_path)`
  - `Database.init_db()` → None
  - `Database.add_todo(todo)` → int (id)
  - `Database.get_todos(filters=None)` → List[Todo]
  - `Database.update_todo(id, fields)` → bool
  - `Database.delete_todo(id)` → bool
  - `Database.mark_complete(id)` → bool

### 3. `todocli/exporter.py`
**Responsibility**: Export todos to CSV format
- CSV file generation
- Include all todo fields
- Interfaces:
  - `export_to_csv(todos, filepath)` → None
  - `export_by_category(todos, category, filepath)` → None

### 4. `todocli/cli.py`
**Responsibility**: Command-line interface using argparse
- Command definitions: add, list, complete, delete, export
- Filtering by category and priority
- Display formatting
- Interfaces:
  - `main(args)` → None
  - `execute_command(command, args)` → None

### 5. `todocli/__main__.py`
**Responsibility**: Entry point for the package
- Delegates to CLI

### 6. `tests/`
**Responsibility**: Unit and integration tests
- `test_models.py` - Model validation and serialization
- `test_database.py` - Database CRUD operations
- `test_exporter.py` - CSV export functionality
- `test_cli.py` - CLI commands and integration
- `conftest.py` - Pytest fixtures

## Priority Levels
- high
- medium
- low

## Valid Categories
User-defined, stored as free-form strings

## File Structure
```
todo-cli/
├── todocli/
│   ├── __init__.py
│   ├── __main__.py
│   ├── models.py
│   ├── database.py
│   ├── exporter.py
│   └── cli.py
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_database.py
│   ├── test_exporter.py
│   └── test_cli.py
├── setup.py
├── requirements.txt
└── README.md
```

## Dependencies
- argparse (stdlib)
- sqlite3 (stdlib)
- csv (stdlib)
- pytest (dev)
- pytest-cov (dev)

## Task Dependencies
1. Define models → Database implementation → CLI
2. Database implementation → Tests
3. CLI implementation → Tests
4. Exporter implementation → Tests
5. All tests must pass before final integration

