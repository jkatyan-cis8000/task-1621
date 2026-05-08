# Todo Data Models Design

## Overview
The `todocli/models.py` module defines the core data structure for the application: the `Todo` class. This class encapsulates all todo item properties, validation logic, and serialization/deserialization operations.

## Todo Class Design

### Fields
The Todo class maintains the following fields:

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `id` | int \| None | No | None | Database-assigned unique identifier |
| `title` | str | Yes | — | Non-empty, required field |
| `description` | str | No | "" | Can be empty string |
| `priority` | str | No | "medium" | Must be one of: high, medium, low |
| `category` | str | No | "" | Free-form user-defined string |
| `completed` | bool | No | False | Completion status |
| `created_at` | datetime | No | now() | Auto-set to current time |
| `updated_at` | datetime | No | now() | Auto-updated on modifications |

### Valid Priority Levels
```python
VALID_PRIORITIES = {"high", "medium", "low"}
```

## Key Design Decisions

### 1. Constructor Validation
The `__init__` method validates all inputs before assignment:
- **Title**: Must be a non-empty string (after stripping whitespace)
- **Description**: Must be a string (empty allowed)
- **Priority**: Must be in VALID_PRIORITIES set
- **Category**: Must be a string (empty allowed)
- **Completed**: Must be boolean
- **ID**: Must be int or None
- All string fields are stripped of leading/trailing whitespace

**Rationale**: Prevents invalid state from the start, making the class reliable throughout the application.

### 2. Automatic Timestamp Handling
- `created_at` and `updated_at` are automatically set to current time if not provided
- This simplifies creation of new todos (no need to manually set timestamps)
- `updated_at` is automatically updated by the `update()` method and completion methods

**Rationale**: Ensures all todos have consistent timestamp tracking without requiring caller intervention.

### 3. Serialization with `to_dict()`
Converts the Todo instance to a dictionary with:
- All fields included
- Datetime objects converted to ISO format strings
- Ready for JSON serialization or database storage

```python
{
    "id": 1,
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "priority": "high",
    "category": "shopping",
    "completed": False,
    "created_at": "2026-05-08T06:46:00.123456",
    "updated_at": "2026-05-08T06:46:00.123456",
}
```

**Rationale**: Provides a clean dictionary representation for various use cases (JSON serialization, database insertion, export).

### 4. Deserialization with `from_dict()`
Reconstructs a Todo instance from a dictionary:
- Validates all required fields are present
- Handles both string and datetime formats for timestamps
- Auto-parses ISO format datetime strings
- Can reconstruct from `to_dict()` output or database rows

**Rationale**: Enables round-trip serialization and reconstruction from various data sources.

### 5. Immutable ID, Mutable Others
- `id` is set once at creation and not changeable (database responsibility)
- Other fields can be modified via the `update()` method
- `completed` state can be toggled via `mark_complete()` / `mark_incomplete()`

**Rationale**: ID represents identity in the database; allowing mutation would break data integrity. Other fields are user-modifiable.

### 6. Update Method with Validation
The `update(**kwargs)` method:
- Only allows updating specific fields: title, description, priority, category
- Validates each field according to the same rules as `__init__`
- Automatically updates `updated_at` timestamp
- Prevents invalid state after creation

```python
todo.update(priority="high", description="Updated description")
# updated_at is automatically set to current time
```

**Rationale**: Provides a controlled way to modify todos while maintaining invariants.

### 7. Equality Comparison
The `__eq__` method compares todos by their data content (not timestamps):
- Useful for testing and validation
- Ignores `created_at` and `updated_at` (which may vary)
- Two todos with same properties are equal regardless of timestamps

**Rationale**: Timestamps naturally vary; content is what matters for equality.

## Special Methods

### `mark_complete()` and `mark_incomplete()`
Convenience methods to toggle completion status and update `updated_at`:

```python
todo.mark_complete()  # Sets completed=True, updates timestamp
todo.mark_incomplete()  # Sets completed=False, updates timestamp
```

**Rationale**: Clearer intent than generic `update()`, ensures timestamp is maintained.

### `__repr__()`
Provides a readable string representation for debugging:
```
Todo(id=1, title="Buy groceries", priority=high, completed=False)
```

## Type Hints and Validation

All methods use type hints for clarity:
```python
def __init__(
    self,
    title: str,
    description: str = "",
    priority: str = "medium",
    category: str = "",
    completed: bool = False,
    id: Optional[int] = None,
    created_at: Optional[datetime] = None,
    updated_at: Optional[datetime] = None,
) -> None:
```

Validation is strict:
- Invalid types raise `TypeError`
- Invalid values raise `ValueError`
- Missing required fields raise `ValueError`

## Integration Points

### With Database (todocli/database.py)
- Database will call `to_dict()` to extract fields for storage
- Database will call `from_dict()` to reconstruct todos from rows
- Database manages persistence; models manage structure

### With CLI (todocli/cli.py)
- CLI accepts user input and creates Todo instances
- CLI calls `to_dict()` and other methods to format output
- CLI uses validation errors to report user mistakes

### With Exporter (todocli/exporter.py)
- Exporter calls `to_dict()` to extract all fields for CSV
- Exporter iterates over Todo instances

## Testing Strategy

The models module should be tested for:
1. **Valid construction**: Creating todos with all valid combinations
2. **Invalid construction**: Raising errors for invalid inputs
3. **Serialization**: `to_dict()` produces correct output
4. **Deserialization**: `from_dict()` reconstructs correctly, including round-trip
5. **State transitions**: `update()`, `mark_complete()`, `mark_incomplete()` work correctly
6. **Timestamp handling**: Timestamps are set appropriately
7. **Equality**: `__eq__` works as expected
8. **Edge cases**: Empty strings, whitespace handling, None values

## Future Considerations

1. **Validation hooks**: Could add custom validators for specific domains
2. **Change tracking**: Could track which fields were modified
3. **Immutability**: Could make Todo immutable and use factory methods
4. **Tags**: Could extend category to support multiple tags (currently single string)
5. **Recurrence**: Could add support for recurring todos
