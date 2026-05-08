# Database Module Design

## Overview
The `todocli/database.py` module manages all SQLite database operations for the Todo CLI application. It provides a clean abstraction over SQLite with methods for CRUD operations, filtering, and data persistence.

## Database Schema

### Todos Table
```sql
CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    priority TEXT NOT NULL DEFAULT 'medium',
    category TEXT NOT NULL DEFAULT '',
    completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### Column Details

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique identifier, auto-assigned |
| `title` | TEXT | NOT NULL | Required field, indexed for queries |
| `description` | TEXT | NOT NULL, DEFAULT '' | Optional, empty string default |
| `priority` | TEXT | NOT NULL, DEFAULT 'medium' | Values: high, medium, low |
| `category` | TEXT | NOT NULL, DEFAULT '' | Optional free-form string |
| `completed` | INTEGER | NOT NULL, DEFAULT 0 | Boolean as integer (0 or 1) |
| `created_at` | TEXT | NOT NULL | ISO format datetime string |
| `updated_at` | TEXT | NOT NULL | ISO format datetime string |

**Note**: SQLite doesn't have a native BOOLEAN or DATETIME type. We use:
- INTEGER (0/1) for boolean `completed` status
- TEXT for ISO format timestamps for consistency with Python's datetime.isoformat()

## Database Class API

### Connection Management

#### `__init__(db_path: str = "todos.db")`
Initializes the Database instance with a path to the SQLite file.
- Creates parent directories if they don't exist
- Does NOT automatically initialize the schema

#### `init_db() -> None`
Creates the todos table if it doesn't exist.
- Idempotent - safe to call multiple times
- Should be called once when application starts

#### `_get_connection()` (context manager)
Internal helper for managing database connections.
- Automatically sets row factory for dict-like access
- Handles commit on success, rollback on error
- Ensures connections are properly closed

### CRUD Operations

#### `add_todo(todo: Todo) -> int`
Inserts a new todo into the database.

**Behavior**:
- Extracts fields from Todo using `to_dict()`
- Converts `completed` boolean to integer (0 or 1)
- Returns the database-assigned ID
- Raises `ValueError` if todo already has an id

**Example**:
```python
db = Database("todos.db")
db.init_db()
todo = Todo("Buy groceries")
new_id = db.add_todo(todo)
print(new_id)  # e.g., 1
```

#### `get_todos(filters: Optional[Dict[str, Any]] = None) -> List[Todo]`
Retrieves todos with optional filtering.

**Filters**:
- `category`: str - exact match on category
- `priority`: str - exact match on priority (validated against valid values)
- `completed`: bool - filter by completion status

**Behavior**:
- All filters use AND logic (e.g., category='work' AND priority='high')
- Results ordered by created_at DESC (newest first)
- Returns empty list if no matches
- Validates filter values

**Example**:
```python
# All high priority items
high_priority = db.get_todos(filters={"priority": "high"})

# All completed items in 'work' category
completed_work = db.get_todos(filters={"category": "work", "completed": True})

# All todos (no filters)
all_todos = db.get_todos()
```

#### `get_todo_by_id(id: int) -> Optional[Todo]`
Retrieves a single todo by its ID.

**Returns**:
- Todo instance if found
- None if no todo with that id exists

**Raises**:
- ValueError if id is not a positive integer

#### `update_todo(id: int, fields: Dict[str, Any]) -> bool`
Updates specific fields of an existing todo.

**Allowed fields**:
- title, description, priority, category, completed

**Behavior**:
- `updated_at` is automatically set to current time
- Returns True if todo was updated, False if id doesn't exist
- Only updates specified fields (partial updates)
- Validates field values

**Example**:
```python
# Mark as complete and change priority
updated = db.update_todo(1, {"completed": True, "priority": "high"})
```

#### `delete_todo(id: int) -> bool`
Deletes a todo from the database.

**Returns**:
- True if todo was deleted
- False if no todo with that id exists

**Raises**:
- ValueError if id is invalid

#### `mark_complete(id: int) -> bool`
Convenience method to mark a todo as completed.

**Returns**:
- True if todo was updated
- False if no todo with that id exists

**Behavior**:
- Sets `completed = True`
- Automatically updates `updated_at`

## Additional Methods

#### `get_all_todos() -> List[Todo]`
Convenience method equivalent to `get_todos()` with no filters.

#### `get_categories() -> List[str]`
Gets all unique non-empty categories currently in use, sorted alphabetically.

**Returns**:
- List of category strings (empty strings excluded)

**Use case**: Building UI dropdowns of available categories

#### `count_todos(filters: Optional[Dict[str, Any]] = None) -> int`
Counts todos matching optional filters (same filters as `get_todos()`).

**Returns**:
- Integer count of matching todos

**Use case**: "You have 5 high priority items"

#### `clear_all() -> None`
Deletes all todos from the database.

**WARNING**: This is destructive and irreversible. Primarily for testing.

## Design Decisions

### 1. Connection Management with Context Manager
Using `_get_connection()` as a context manager ensures:
- Connections are always properly closed
- Transactions are automatically committed on success
- Automatic rollback on errors
- Clean, readable code

```python
with self._get_connection() as conn:
    cursor = conn.execute(query, params)
    result = cursor.fetchone()
```

### 2. Boolean and DateTime Handling
- **completed**: Stored as INTEGER (0/1) since SQLite has no native boolean
  - Conversion happens in add_todo() and get_todos()
  - update_todo() handles the conversion
- **Timestamps**: Stored as TEXT in ISO format
  - Matches Python's `datetime.isoformat()` output
  - Easy to parse back with `datetime.fromisoformat()`
  - Human-readable and database-agnostic

### 3. Flexible Filtering
The `get_todos()` method supports multiple filters with AND logic:
- Invalid filter values raise ValueError (fail-fast)
- Unspecified filters are ignored (no filter)
- Easy to extend with new filters in future

```python
# Filter construction is dynamic - easy to add new filters
if "category" in filters:
    query += " AND category = ?"
    params.append(filters["category"])
```

### 4. ID Validation
All methods that take an ID validate:
- Must be an integer
- Must be positive (> 0)
- Prevents database errors and unexpected behavior

### 5. Partial Updates with update_todo()
The `update_todo()` method only updates specified fields:
- Allows fine-grained control
- Prevents accidental overwrites
- Uses empty dict for no-op updates

### 6. Return Values for Mutation Operations
Methods that modify data return boolean:
- `add_todo()`: returns the new id (special case - not boolean)
- `update_todo()`: returns True/False indicating if anything changed
- `delete_todo()`: returns True/False indicating if anything was deleted
- `mark_complete()`: returns True/False indicating if anything changed

This allows callers to detect "not found" errors without exceptions.

## Integration Points

### With Models (todocli/models.py)
- Uses `Todo.to_dict()` to convert models to database format
- Uses `Todo.from_dict()` to reconstruct models from database rows
- Models handle validation; database assumes valid data

### With CLI (todocli/cli.py)
- CLI calls database methods to persist/retrieve todos
- CLI handles user input validation
- Database returns structured data (List[Todo])

### With Exporter (todocli/exporter.py)
- Exporter calls `get_todos()` or `get_all_todos()`
- Exporter calls `to_dict()` on returned Todo instances

## Error Handling Strategy

### ValueError
Raised for:
- Invalid id (not positive int)
- Invalid filter values
- Inserting a todo that already has an id

### sqlite3.Error
Raised for:
- Database connection failures
- SQL errors
- Schema issues

Both exception types propagate to the caller (no silent failures).

## Testing Considerations

Tests should cover:
1. **Schema creation**: init_db() idempotency
2. **CRUD operations**: add, retrieve, update, delete
3. **Filtering**: category, priority, completed filters
4. **Edge cases**: 
   - Empty database operations
   - Non-existent IDs
   - Invalid filter values
5. **Timestamps**: created_at and updated_at handling
6. **Boolean conversion**: completed field handling
7. **Transaction safety**: Error handling and rollback

## Performance Notes

- Single todos table keeps queries simple
- No indexes created by default (reasonable for small datasets)
- Could add indexes on (category, priority, completed) for large datasets
- Pagination could be added if datasets grow large
- Query ordering by created_at DESC provides reverse-chronological display

## Future Enhancements

1. **Pagination**: Add LIMIT/OFFSET to get_todos()
2. **Sorting**: Allow specifying sort order in get_todos()
3. **Search**: Add full-text search on title/description
4. **Indexes**: Create indexes for frequently filtered columns
5. **Backup**: Add backup/restore functionality
6. **Migration system**: Version the schema for future changes
7. **Relationships**: Support parent/subtask relationships
