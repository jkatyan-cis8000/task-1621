"""
SQLite database operations and management for the Todo CLI.

Handles database initialization, schema creation, and all CRUD operations for todos.
"""

import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from todocli.models import Todo


class Database:
    """
    Manages SQLite database operations for todos.
    
    Handles database initialization, connection management, and CRUD operations.
    """
    
    SCHEMA = """
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
    """
    
    def __init__(self, db_path: str = "todos.db"):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file. Defaults to "todos.db"
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.
        
        Yields a connection with row factory set for easy dict access.
        Handles automatic commit on success and rollback on error.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def init_db(self) -> None:
        """
        Initialize the database schema.
        
        Creates the todos table if it doesn't exist.
        Safe to call multiple times.
        """
        with self._get_connection() as conn:
            conn.execute(self.SCHEMA)
    
    def add_todo(self, todo: Todo) -> int:
        """
        Add a new todo to the database.
        
        Args:
            todo: Todo instance to add (id should be None)
            
        Returns:
            The database-assigned ID of the new todo
            
        Raises:
            ValueError: If todo.id is not None (should only insert new todos)
            sqlite3.Error: If database operation fails
        """
        if todo.id is not None:
            raise ValueError("Cannot insert a todo that already has an id")
        
        todo_dict = todo.to_dict()
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO todos 
                (title, description, priority, category, completed, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    todo_dict["title"],
                    todo_dict["description"],
                    todo_dict["priority"],
                    todo_dict["category"],
                    1 if todo_dict["completed"] else 0,
                    todo_dict["created_at"],
                    todo_dict["updated_at"],
                ),
            )
            return cursor.lastrowid
    
    def get_todos(self, filters: Optional[Dict[str, Any]] = None) -> List[Todo]:
        """
        Retrieve todos from the database with optional filtering.
        
        Args:
            filters: Optional dictionary of filters:
                - "category": str - filter by category (exact match)
                - "priority": str - filter by priority (exact match)
                - "completed": bool - filter by completion status
                Can combine multiple filters (AND logic)
                
        Returns:
            List of Todo instances matching the filters
            
        Raises:
            ValueError: If filter values are invalid
            sqlite3.Error: If database operation fails
        """
        if filters is None:
            filters = {}
        
        # Validate filter values
        valid_priorities = {"high", "medium", "low"}
        
        if "priority" in filters and filters["priority"] not in valid_priorities:
            raise ValueError(
                f"Invalid priority filter: {filters['priority']}. "
                f"Must be one of {valid_priorities}"
            )
        
        if "completed" in filters and not isinstance(filters["completed"], bool):
            raise ValueError("Completed filter must be a boolean")
        
        # Build query dynamically
        query = "SELECT * FROM todos WHERE 1=1"
        params = []
        
        if "category" in filters:
            query += " AND category = ?"
            params.append(filters["category"])
        
        if "priority" in filters:
            query += " AND priority = ?"
            params.append(filters["priority"])
        
        if "completed" in filters:
            query += " AND completed = ?"
            params.append(1 if filters["completed"] else 0)
        
        query += " ORDER BY created_at DESC"
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        todos = []
        for row in rows:
            todo_dict = {
                "id": row["id"],
                "title": row["title"],
                "description": row["description"],
                "priority": row["priority"],
                "category": row["category"],
                "completed": bool(row["completed"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            todos.append(Todo.from_dict(todo_dict))
        
        return todos
    
    def update_todo(self, id: int, fields: Dict[str, Any]) -> bool:
        """
        Update specific fields of a todo.
        
        Args:
            id: ID of the todo to update
            fields: Dictionary of fields to update
                Allowed fields: title, description, priority, category, completed
                
        Returns:
            True if a todo was updated, False if no todo with that id exists
            
        Raises:
            ValueError: If id is invalid or fields contain invalid values
            sqlite3.Error: If database operation fails
        """
        if not isinstance(id, int) or id < 1:
            raise ValueError("ID must be a positive integer")
        
        allowed_fields = {"title", "description", "priority", "category", "completed"}
        invalid_fields = set(fields.keys()) - allowed_fields
        
        if invalid_fields:
            raise ValueError(f"Cannot update fields: {invalid_fields}")
        
        if not fields:
            return False  # Nothing to update
        
        # Build update query
        update_parts = []
        params = []
        
        for field, value in fields.items():
            if field == "completed":
                update_parts.append("completed = ?")
                params.append(1 if value else 0)
            else:
                update_parts.append(f"{field} = ?")
                params.append(value)
        
        # Always update the timestamp
        update_parts.append("updated_at = datetime('now')")
        
        params.append(id)
        
        query = f"UPDATE todos SET {', '.join(update_parts)} WHERE id = ?"
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount > 0
    
    def delete_todo(self, id: int) -> bool:
        """
        Delete a todo from the database.
        
        Args:
            id: ID of the todo to delete
            
        Returns:
            True if a todo was deleted, False if no todo with that id exists
            
        Raises:
            ValueError: If id is invalid
            sqlite3.Error: If database operation fails
        """
        if not isinstance(id, int) or id < 1:
            raise ValueError("ID must be a positive integer")
        
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM todos WHERE id = ?", (id,))
            return cursor.rowcount > 0
    
    def mark_complete(self, id: int) -> bool:
        """
        Mark a todo as completed.
        
        Args:
            id: ID of the todo to mark complete
            
        Returns:
            True if a todo was updated, False if no todo with that id exists
            
        Raises:
            ValueError: If id is invalid
            sqlite3.Error: If database operation fails
        """
        return self.update_todo(id, {"completed": True})
    
    def get_todo_by_id(self, id: int) -> Optional[Todo]:
        """
        Retrieve a single todo by ID.
        
        Args:
            id: ID of the todo to retrieve
            
        Returns:
            Todo instance if found, None otherwise
            
        Raises:
            ValueError: If id is invalid
            sqlite3.Error: If database operation fails
        """
        if not isinstance(id, int) or id < 1:
            raise ValueError("ID must be a positive integer")
        
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM todos WHERE id = ?", (id,))
            row = cursor.fetchone()
        
        if row is None:
            return None
        
        todo_dict = {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "priority": row["priority"],
            "category": row["category"],
            "completed": bool(row["completed"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        return Todo.from_dict(todo_dict)
    
    def get_all_todos(self) -> List[Todo]:
        """
        Retrieve all todos from the database.
        
        Returns:
            List of all Todo instances, ordered by creation date (newest first)
            
        Raises:
            sqlite3.Error: If database operation fails
        """
        return self.get_todos()
    
    def get_categories(self) -> List[str]:
        """
        Get all unique categories currently in use.
        
        Returns:
            List of unique category strings (empty strings are included)
            
        Raises:
            sqlite3.Error: If database operation fails
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT category FROM todos WHERE category != '' ORDER BY category"
            )
            rows = cursor.fetchall()
        
        return [row[0] for row in rows]
    
    def count_todos(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count todos matching optional filters.
        
        Args:
            filters: Optional filters (same as get_todos)
            
        Returns:
            Number of todos matching the filters
            
        Raises:
            sqlite3.Error: If database operation fails
        """
        if filters is None:
            filters = {}
        
        # Validate filter values
        valid_priorities = {"high", "medium", "low"}
        
        if "priority" in filters and filters["priority"] not in valid_priorities:
            raise ValueError(
                f"Invalid priority filter: {filters['priority']}. "
                f"Must be one of {valid_priorities}"
            )
        
        if "completed" in filters and not isinstance(filters["completed"], bool):
            raise ValueError("Completed filter must be a boolean")
        
        # Build query
        query = "SELECT COUNT(*) FROM todos WHERE 1=1"
        params = []
        
        if "category" in filters:
            query += " AND category = ?"
            params.append(filters["category"])
        
        if "priority" in filters:
            query += " AND priority = ?"
            params.append(filters["priority"])
        
        if "completed" in filters:
            query += " AND completed = ?"
            params.append(1 if filters["completed"] else 0)
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()[0]
    
    def clear_all(self) -> None:
        """
        Delete all todos from the database.
        
        WARNING: This is destructive and cannot be undone.
        Primarily useful for testing.
        
        Raises:
            sqlite3.Error: If database operation fails
        """
        with self._get_connection() as conn:
            conn.execute("DELETE FROM todos")
