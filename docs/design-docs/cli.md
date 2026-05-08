# CLI Interface Design

## Overview
The `todocli/cli.py` module provides a command-line interface for managing todos. It uses Python's `argparse` library for robust argument parsing and implements commands for adding, listing, completing, deleting, and exporting todos.

## Entry Points

### `todocli/__main__.py`
Enables running the package as a module:
```bash
python -m todocli add "My task"
```

```python
from todocli.cli import main

if __name__ == "__main__":
    main()
```

### Console Script (via setup.py)
After installation, users can run:
```bash
todocli add "My task"
```

This is configured in setup.py with the entry point:
```python
entry_points={
    "console_scripts": [
        "todocli=todocli.cli:main",
    ],
}
```

## TodoCLI Class

The `TodoCLI` class encapsulates all CLI operations with a database connection.

### Initialization

```python
cli = TodoCLI(db_path="todos.db")
```

- Initializes a Database connection
- Automatically calls `init_db()` to create tables if needed
- Default database path: "todos.db"

### Methods

#### `add(title, description="", priority="medium", category="")`
Adds a new todo.

**Example**:
```bash
todocli add "Buy groceries" -d "Milk, eggs, bread" -p high -c shopping
```

**Output**:
```
✓ Todo added with ID: 1
  Title: Buy groceries
  Category: shopping
  Priority: high
```

**Error Handling**:
- Validates input using Todo class
- Prints error message and exits with code 1 on failure

#### `list(category=None, priority=None, completed=None, format="table")`
Lists todos with optional filtering and formatting.

**Examples**:
```bash
# List all todos in table format
todocli list

# List high-priority items
todocli list -p high

# List todos in 'work' category
todocli list -c work

# List only completed todos
todocli list --completed

# List in simple format
todocli list -f simple
```

**Table Format Output**:
```
ID   Status   Priority Priority Title                         Category       
---- -------- -------- -------- ------------------------------ ---------------
1    ✓        high     high     Buy groceries                  shopping       
2             medium   medium   Write report                   work           
```

**Simple Format Output**:
```
✓ 1: Buy groceries (high) [shopping]
○ 2: Write report (medium) [work]
```

**Filtering**:
- `--category/-c`: Exact match on category
- `--priority/-p`: Filter by priority (high, medium, low)
- `--completed`: Show only completed todos
- `--incomplete`: Show only incomplete todos

#### `complete(todo_id)`
Marks a todo as completed.

**Example**:
```bash
todocli complete 1
```

**Output**:
```
✓ Todo 1 marked as complete
```

#### `delete(todo_id)`
Deletes a todo.

**Example**:
```bash
todocli delete 1
```

**Output**:
```
✓ Todo 1 deleted
```

#### `export(filepath, category=None)`
Exports todos to a CSV file.

**Examples**:
```bash
# Export all todos
todocli export todos.csv

# Export only shopping category
todocli export shopping.csv -c shopping
```

**Output**:
```
✓ Exported 5 todos to todos.csv
```

## Main Function

The `main(args=None)` function is the primary entry point that:
1. Sets up argument parser with subcommands
2. Parses command-line arguments
3. Creates a TodoCLI instance
4. Executes the appropriate command

### Global Options

```
--db PATH    Path to SQLite database (default: todos.db)
```

### Subcommands

#### `add`
```
todocli add TITLE [OPTIONS]

Options:
  -d, --description TEXT    Detailed description (optional)
  -p, --priority LEVEL      Priority level: high, medium, low (default: medium)
  -c, --category TEXT       Category/tag (optional)
```

#### `list`
```
todocli list [OPTIONS]

Options:
  -c, --category TEXT       Filter by category
  -p, --priority LEVEL      Filter by priority (high, medium, low)
  --completed               Show only completed todos
  --incomplete              Show only incomplete todos
  -f, --format FORMAT       Output format: table, simple (default: table)
```

#### `complete`
```
todocli complete ID
```

#### `delete`
```
todocli delete ID
```

#### `export`
```
todocli export FILEPATH [OPTIONS]

Options:
  -c, --category TEXT       Export only this category
```

## Design Decisions

### 1. Subcommand Architecture
Uses argparse subcommands instead of flags for different operations:

```python
subparsers = parser.add_subparsers(dest="command", help="Command to execute")
add_parser = subparsers.add_parser("add", help="Add a new todo")
```

**Rationale**:
- Clear, intuitive command structure
- Separate argument handling per command
- Easy to add new commands
- Standard CLI pattern (git, docker, etc.)

### 2. Short Flags for Common Options
Supports both short and long flags:

```bash
todocli list -c work          # Short flag
todocli list --category work  # Long flag
```

**Rationale**:
- Short flags for power users
- Long flags for clarity
- Standard argparse behavior

### 3. Validation at Model Layer
Input validation happens in the Todo class, not in CLI:

```python
try:
    todo = Todo(title=title, priority=priority, ...)
except ValueError as e:
    print(f"✗ Error: {e}", file=sys.stderr)
    sys.exit(1)
```

**Rationale**:
- Single source of truth for validation
- Consistent error messages
- Validation reusable in tests and other interfaces

### 4. Separate Display Methods
Table and simple format rendering are in separate methods:

```python
if format == "table":
    self._print_table(todos)
else:
    self._print_simple(todos)
```

**Rationale**:
- Easy to add new formats (JSON, markdown, etc.)
- Methods focus on their responsibility
- Testable in isolation

### 5. Exit Codes
- Exit code 0: Success
- Exit code 1: Error (validation, not found, etc.)

**Rationale**:
- Standard Unix convention
- Scripts can detect failures
- Follows argparse defaults

### 6. Status Symbols
Different symbols for different contexts:

- Table format: `✓` for completed, space for incomplete
- Simple format: `✓` for completed, `○` for incomplete

**Rationale**:
- Visual distinction at a glance
- Unicode symbols are readable in modern terminals
- Clear intent of status

### 7. Text Truncation in Table
Long titles and categories are truncated with ellipsis:

```python
title = todo.title[:30] if len(todo.title) <= 30 else todo.title[:27] + "..."
```

**Rationale**:
- Table format needs fixed width columns
- Ellipsis indicates truncation
- Users can still see the full content with details command (future)

## Usage Examples

### Basic Workflow

```bash
# Initialize database and add a todo
todocli add "Buy groceries" -c shopping -p high

# List all todos
todocli list

# List only high priority items
todocli list -p high

# Mark a todo as complete
todocli complete 1

# Export to backup
todocli export backup.csv

# List only incomplete todos
todocli list --incomplete
```

### Using Different Database

```bash
# Use a specific database file
todocli --db /path/to/custom.db add "Task"
todocli --db /path/to/custom.db list

# Useful for multiple projects
todocli --db work.db list
todocli --db personal.db list
```

### Piping and Scripting

The simple format is designed for easier script parsing:

```bash
# List and count todos
todocli list -f simple | wc -l

# List and filter with grep
todocli list -f simple | grep "\[shopping\]"
```

## Error Handling Strategy

### Validation Errors
Caught from Todo class validation:
```
✗ Error: Title must be a non-empty string
```

### Not Found Errors
When deleting/completing non-existent todo:
```
✗ Todo 999 not found
```

### Database Errors
Any SQLite errors:
```
✗ Error: database disk image is malformed
```

### File Errors
CSV export failures:
```
✗ Error: Failed to write CSV file to todos.csv: Permission denied
```

All errors:
1. Print to stderr with ✗ prefix
2. Exit with code 1
3. Are user-friendly (not stack traces)

## Integration with Other Modules

### With Database
```python
from todocli.database import Database

self.db = Database(db_path)
self.db.init_db()
todos = self.db.get_todos(filters)
```

### With Models
```python
from todocli.models import Todo

todo = Todo(title=title, priority=priority, ...)
```

### With Exporter
```python
from todocli.exporter import export_to_csv, export_by_category

export_to_csv(todos, filepath)
```

## Testing Considerations

The CLI can be tested by:

1. **Unit tests** for each method:
```python
cli = TodoCLI(":memory:")  # Use in-memory database
cli.add("Test", priority="high")
```

2. **Integration tests** with main():
```python
from todocli.cli import main

# Simulate: todocli add "Test"
main(["add", "Test"])
```

3. **End-to-end tests** with actual files

## Future Enhancements

1. **Show command**: Display full details of a specific todo
2. **Edit command**: Modify existing todos
3. **Search command**: Full-text search
4. **Stats command**: Summary statistics (total, completed, by category)
5. **Config file**: Support configuration in ~/.todocli.conf
6. **Shell completion**: bash/zsh completion scripts
7. **Color output**: Colored text based on priority/status
8. **Interactive mode**: Menu-driven interface
9. **Bulk operations**: Delete multiple todos, bulk category assignment
10. **Undo/history**: Track and undo changes
