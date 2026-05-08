# CSV Exporter Module Design

## Overview
The `todocli/exporter.py` module provides functionality to export todos to CSV format with various filtering options. It enables users to backup their todos, analyze them in spreadsheet applications, or integrate with other tools.

## Core Functions

### `export_to_csv(todos: List[Todo], filepath: str) -> None`
The primary export function that writes todos to a CSV file.

**Parameters**:
- `todos`: List of Todo instances to export
- `filepath`: Path where the CSV file will be written (creates parent directories as needed)

**Behavior**:
- Creates parent directories if they don't exist
- Writes UTF-8 encoded CSV with headers
- Converts `completed` boolean to human-readable "Yes"/"No"
- All 8 fields included in output

**CSV Columns** (in order):
```
id, title, description, priority, category, completed, created_at, updated_at
```

**Example Output**:
```csv
id,title,description,priority,category,completed,created_at,updated_at
1,Buy groceries,Milk eggs bread,high,shopping,No,2026-05-08T10:30:45.123456,2026-05-08T10:30:45.123456
2,Write report,Project summary,medium,work,Yes,2026-05-08T09:15:20.654321,2026-05-08T11:00:00.000000
```

**Error Handling**:
- `ValueError`: If filepath is empty
- `IOError`: If file cannot be written (permission denied, disk full, etc.)

**Raises**:
```python
if not filepath:
    raise ValueError("Filepath cannot be empty")
```

### `export_by_category(todos: List[Todo], category: str, filepath: str) -> None`
Exports todos filtered by a specific category.

**Parameters**:
- `todos`: List of all Todo instances
- `category`: Category to filter by (exact match, case-sensitive)
- `filepath`: Output file path

**Behavior**:
- Filters todos where `todo.category == category`
- Calls `export_to_csv()` with the filtered list
- Empty list results in a CSV with only headers

**Example**:
```python
db = Database("todos.db")
all_todos = db.get_todos()
export_by_category(all_todos, "work", "work_todos.csv")
```

**Error Handling**:
- `ValueError`: If category or filepath is empty
- `IOError`: From underlying export_to_csv call

## Additional Export Functions

### `export_by_priority(todos: List[Todo], priority: str, filepath: str) -> None`
Exports todos filtered by priority level.

**Parameters**:
- `todos`: List of all Todo instances
- `priority`: One of "high", "medium", "low"
- `filepath`: Output file path

**Behavior**:
- Filters todos where `todo.priority == priority`
- Validates priority value
- Calls `export_to_csv()` with filtered list

**Example**:
```python
db = Database("todos.db")
all_todos = db.get_todos()
export_by_priority(all_todos, "high", "high_priority.csv")
```

### `export_completed(todos: List[Todo], filepath: str, completed: bool = True) -> None`
Exports todos filtered by completion status.

**Parameters**:
- `todos`: List of all Todo instances
- `filepath`: Output file path
- `completed`: If True, export completed todos; if False, export incomplete todos

**Behavior**:
- Filters todos where `todo.completed == completed`
- Defaults to exporting completed todos

**Examples**:
```python
# Export only completed todos
export_completed(todos, "done.csv", completed=True)

# Export only incomplete todos
export_completed(todos, "pending.csv", completed=False)
```

### `export_by_text_search(todos: List[Todo], search_text: str, filepath: str, search_fields: Optional[List[str]] = None) -> None`
Exports todos matching search text in specified fields.

**Parameters**:
- `todos`: List of all Todo instances
- `search_text`: Text to search for (case-insensitive)
- `filepath`: Output file path
- `search_fields`: Fields to search in (default: ["title", "description"])
  - Valid fields: "title", "description", "category"

**Behavior**:
- Searches case-insensitively in specified fields
- A todo matches if search_text appears in any of the specified fields
- Returns empty CSV if no matches

**Examples**:
```python
# Search in title and description (default)
export_by_text_search(todos, "grocery", "grocery_items.csv")

# Search only in category
export_by_text_search(todos, "work", "work_category.csv", search_fields=["category"])

# Search in all fields
export_by_text_search(
    todos,
    "urgent",
    "urgent_items.csv",
    search_fields=["title", "description", "category"]
)
```

## Design Decisions

### 1. Filtering at Application Level
Export functions filter in Python rather than at the database level:

**Rationale**:
- Simplifies API (filter already-retrieved todos)
- Reduces database queries
- Works with any data source (not just database)
- Flexibility for complex filtering logic

**Trade-off**:
- For very large datasets (thousands of todos), database-level filtering would be faster
- But database already provides filtering via `get_todos(filters=...)`
- Export module provides convenience functions for application layer

### 2. Boolean Conversion to "Yes"/"No"
The `completed` field is stored as boolean in the model but exported as "Yes"/"No":

```python
todo_dict["completed"] = "Yes" if todo_dict["completed"] else "No"
```

**Rationale**:
- More readable in spreadsheet applications
- Common convention for CSV exports
- Users don't see technical "True"/"False" values

### 3. Case-Insensitive Text Search
The `export_by_text_search()` function uses case-insensitive matching:

```python
search_text_lower = search_text.lower()
if search_text_lower in todo.title.lower():
```

**Rationale**:
- More user-friendly (users don't need to match case)
- Matches user expectations from web search
- Consistent with database filtering behavior

### 4. Flexible Field Selection in Text Search
Allows customizing which fields to search:

```python
export_by_text_search(todos, "urgent", "file.csv", search_fields=["title"])
```

**Rationale**:
- Advanced users can optimize searches
- Different use cases need different fields
- Default behavior suits most cases

### 5. Directory Creation
Export functions automatically create parent directories:

```python
filepath.parent.mkdir(parents=True, exist_ok=True)
```

**Rationale**:
- Convenience - users don't need to pre-create directories
- Fails gracefully if directory creation not allowed
- More user-friendly error messages

### 6. UTF-8 Encoding
Always uses UTF-8 for CSV files:

```python
with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
```

**Rationale**:
- Unicode support for international characters
- Standard modern encoding
- Consistent across platforms
- Excel handles UTF-8 well in modern versions

### 7. CSV Module Usage
Uses Python's built-in `csv` module rather than manual string concatenation:

**Rationale**:
- Proper CSV formatting (handles commas, quotes, newlines)
- Handles edge cases automatically
- Standards-compliant output
- More maintainable code

## Integration Points

### With Database (todocli/database.py)
```python
db = Database("todos.db")
todos = db.get_todos(filters={"priority": "high"})
export_to_csv(todos, "high_priority.csv")
```

The exporter works with any List[Todo], including results from database queries.

### With CLI (todocli/cli.py)
The CLI can call export functions with user-specified options:
```python
# User runs: todocli export --category work --output work.csv
export_by_category(all_todos, "work", "work.csv")
```

### With Models (todocli/models.py)
Export functions call `Todo.to_dict()` to extract all fields:
```python
todo_dict = todo.to_dict()
```

## CSV Format Specification

### Headers
```
id,title,description,priority,category,completed,created_at,updated_at
```

### Data Rows
- **id**: Integer (database-assigned)
- **title**: String (quoted if contains comma/newline/quote)
- **description**: String (can be empty, quoted if needed)
- **priority**: One of "high", "medium", "low"
- **category**: String (can be empty)
- **completed**: "Yes" or "No"
- **created_at**: ISO format datetime string
- **updated_at**: ISO format datetime string

### Field Handling
- All string fields quoted by default (RFC 4180 compliant)
- Commas within fields properly escaped
- Newlines preserved in multiline description fields
- Unicode characters supported (UTF-8)

## Error Handling Strategy

### ValueError
Raised for:
- Empty filepath
- Empty search text or category
- Invalid priority values
- These are caller errors, not runtime failures

### IOError
Raised for:
- File cannot be written
- Permission denied
- Disk full
- These are environment/system errors

### General Exception Wrapper
Catches unexpected errors with clear messaging:
```python
except Exception as e:
    raise Exception(f"Unexpected error during CSV export: {e}")
```

## Testing Considerations

Tests should cover:
1. **Basic export**: export_to_csv with valid todos
2. **Empty export**: export with empty todo list (headers only)
3. **File creation**: Parent directories created
4. **Formatting**: Proper CSV format with quotes/escaping
5. **Filter functions**: Each filter type produces correct results
6. **Edge cases**:
   - Todos with special characters (commas, quotes, newlines)
   - Missing optional fields (empty description, empty category)
   - Very long descriptions
   - Non-ASCII characters
7. **Error handling**: Invalid inputs raise appropriate errors
8. **File overwrites**: Export can overwrite existing files

## Performance Notes

- Reading all todos into memory: O(n) where n = number of todos
- Filtering: O(n) per filter operation
- CSV writing: O(n)
- For typical datasets (hundreds of todos): negligible
- For very large datasets (millions of todos): could benefit from streaming writes

## Future Enhancements

1. **JSON export**: Export to JSON format for programmatic use
2. **Excel export**: Native .xlsx format with formatting
3. **Streaming export**: For very large datasets
4. **Filtering combinations**: Support AND/OR logic
5. **Template exports**: User-defined column selections
6. **Date range filtering**: Export todos within date range
7. **Recursive export**: Export nested/related todos
8. **Compression**: Support gzip-compressed CSV output
