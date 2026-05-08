# Project Structure Design

## Overview
This document describes the initial project structure setup for the Todo CLI Manager application. The structure follows Python packaging best practices and is designed to be installable as a package.

## Directory Layout
```
todo-cli/
├── todocli/                  # Main package directory
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # CLI entry point (to be created)
│   ├── models.py            # Data models (to be created)
│   ├── database.py          # Database operations (to be created)
│   ├── exporter.py          # CSV export functionality (to be created)
│   └── cli.py               # CLI interface (to be created)
├── tests/                    # Test suite directory
│   ├── __init__.py          # Test package initialization
│   ├── conftest.py          # Pytest fixtures (to be created)
│   ├── test_models.py       # Model tests (to be created)
│   ├── test_database.py     # Database tests (to be created)
│   ├── test_exporter.py     # Export tests (to be created)
│   └── test_cli.py          # CLI tests (to be created)
├── setup.py                  # Package setup and installation
├── requirements.txt          # Development dependencies
├── ARCHITECTURE.md           # Detailed architecture specification
└── README.md                 # Project documentation
```

## Key Design Decisions

### 1. Python Packaging Structure
- Used setuptools with `setup.py` for proper package installation
- Package named `todocli` follows Python naming conventions (lowercase)
- Includes console entry point via `todocli=todocli.cli:main`
- This allows installation via `pip install -e .` for development

### 2. Package Initialization
- `todocli/__init__.py` contains version and author metadata
- Enables imports like `from todocli import models` once implemented
- Follows standard Python package initialization patterns

### 3. Test Organization
- Tests are in a separate `tests/` directory (not inside package)
- Pytest fixtures will be centralized in `conftest.py`
- Allows tests to be excluded from package distribution

### 4. Dependencies
- **Runtime**: Only standard library modules (argparse, sqlite3, csv)
- **Development**: pytest>=7.0.0, pytest-cov>=4.0.0
- No external runtime dependencies keeps the package lightweight

### 5. Entry Point
The `setup.py` configures a console script entry point:
```python
entry_points={
    "console_scripts": [
        "todocli=todocli.cli:main",
    ],
}
```
This allows users to run `todocli` directly from the command line after installation.

## Installability
The package is installable in two modes:

1. **Development mode**: `pip install -e .`
   - Installs with symlinks to source
   - Changes to source code are immediately available
   - Ideal for development

2. **Production mode**: `pip install .`
   - Creates a full installation
   - Ready for distribution

## Dependencies Between Modules
According to ARCHITECTURE.md, the implementation follows this dependency chain:
1. Models (models.py) - no dependencies
2. Database (database.py) - depends on models
3. Exporter (exporter.py) - depends on database
4. CLI (cli.py) - depends on database
5. Tests - depend on all implemented modules

## Notes for Implementation Teams
- The structure is now ready for parallel development
- Database and Exporter/CLI teams can work independently on their implementations
- All module files are placeholders to be filled in subsequent tasks
- The package will be installable once the CLI entry point (todocli.cli.main) is implemented
