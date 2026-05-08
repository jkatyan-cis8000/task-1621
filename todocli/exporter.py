"""
CSV export functionality for the Todo CLI.

Provides functions to export todos to CSV format with various filtering options.
"""

import csv
from pathlib import Path
from typing import List, Optional

from todocli.models import Todo


# Column order for CSV output
CSV_COLUMNS = [
    "id",
    "title",
    "description",
    "priority",
    "category",
    "completed",
    "created_at",
    "updated_at",
]


def export_to_csv(todos: List[Todo], filepath: str) -> None:
    """
    Export a list of todos to a CSV file.
    
    All todo fields are included in the output with the following columns:
    id, title, description, priority, category, completed, created_at, updated_at
    
    Args:
        todos: List of Todo instances to export
        filepath: Path where the CSV file will be written
        
    Raises:
        IOError: If the file cannot be written
        ValueError: If filepath is invalid or empty
        
    Example:
        >>> from todocli.database import Database
        >>> from todocli.exporter import export_to_csv
        >>> db = Database("todos.db")
        >>> todos = db.get_todos()
        >>> export_to_csv(todos, "todos_backup.csv")
    """
    if not filepath:
        raise ValueError("Filepath cannot be empty")
    
    filepath = Path(filepath)
    
    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            
            for todo in todos:
                todo_dict = todo.to_dict()
                # Convert completed boolean to string representation
                todo_dict["completed"] = "Yes" if todo_dict["completed"] else "No"
                writer.writerow(todo_dict)
    except IOError as e:
        raise IOError(f"Failed to write CSV file to {filepath}: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error during CSV export: {e}")


def export_by_category(
    todos: List[Todo], category: str, filepath: str
) -> None:
    """
    Export todos of a specific category to a CSV file.
    
    Filters the todos list to only include items matching the specified category,
    then exports them using export_to_csv().
    
    Args:
        todos: List of Todo instances to filter and export
        category: Category to filter by (exact match, case-sensitive)
        filepath: Path where the CSV file will be written
        
    Raises:
        IOError: If the file cannot be written
        ValueError: If filepath or category is invalid/empty
        
    Example:
        >>> from todocli.database import Database
        >>> from todocli.exporter import export_by_category
        >>> db = Database("todos.db")
        >>> todos = db.get_todos()
        >>> export_by_category(todos, "work", "work_todos.csv")
    """
    if not category:
        raise ValueError("Category cannot be empty")
    
    if not filepath:
        raise ValueError("Filepath cannot be empty")
    
    # Filter todos by category
    filtered_todos = [todo for todo in todos if todo.category == category]
    
    # Export the filtered list
    export_to_csv(filtered_todos, filepath)


def export_by_priority(
    todos: List[Todo], priority: str, filepath: str
) -> None:
    """
    Export todos of a specific priority to a CSV file.
    
    Filters the todos list to only include items matching the specified priority,
    then exports them using export_to_csv().
    
    Args:
        todos: List of Todo instances to filter and export
        priority: Priority level to filter by (high, medium, low)
        filepath: Path where the CSV file will be written
        
    Raises:
        IOError: If the file cannot be written
        ValueError: If filepath or priority is invalid/empty
        
    Example:
        >>> from todocli.database import Database
        >>> from todocli.exporter import export_by_priority
        >>> db = Database("todos.db")
        >>> todos = db.get_todos()
        >>> export_by_priority(todos, "high", "high_priority_todos.csv")
    """
    valid_priorities = {"high", "medium", "low"}
    
    if priority not in valid_priorities:
        raise ValueError(
            f"Invalid priority: {priority}. Must be one of {valid_priorities}"
        )
    
    if not filepath:
        raise ValueError("Filepath cannot be empty")
    
    # Filter todos by priority
    filtered_todos = [todo for todo in todos if todo.priority == priority]
    
    # Export the filtered list
    export_to_csv(filtered_todos, filepath)


def export_completed(todos: List[Todo], filepath: str, completed: bool = True) -> None:
    """
    Export completed or incomplete todos to a CSV file.
    
    Filters the todos list based on completion status and exports them.
    
    Args:
        todos: List of Todo instances to filter and export
        filepath: Path where the CSV file will be written
        completed: If True, export completed todos; if False, export incomplete todos.
                  Defaults to True (completed).
        
    Raises:
        IOError: If the file cannot be written
        ValueError: If filepath is invalid/empty
        
    Example:
        >>> from todocli.database import Database
        >>> from todocli.exporter import export_completed
        >>> db = Database("todos.db")
        >>> todos = db.get_todos()
        >>> # Export all completed todos
        >>> export_completed(todos, "completed_todos.csv", completed=True)
        >>> # Export all incomplete todos
        >>> export_completed(todos, "incomplete_todos.csv", completed=False)
    """
    if not filepath:
        raise ValueError("Filepath cannot be empty")
    
    # Filter todos by completion status
    filtered_todos = [todo for todo in todos if todo.completed == completed]
    
    # Export the filtered list
    export_to_csv(filtered_todos, filepath)


def export_by_text_search(
    todos: List[Todo], search_text: str, filepath: str, search_fields: Optional[List[str]] = None
) -> None:
    """
    Export todos matching search text in specified fields to a CSV file.
    
    Searches in title and description by default (case-insensitive).
    
    Args:
        todos: List of Todo instances to search and export
        search_text: Text to search for (case-insensitive)
        filepath: Path where the CSV file will be written
        search_fields: List of fields to search in. Defaults to ["title", "description"].
                      Other valid fields: "category"
        
    Raises:
        IOError: If the file cannot be written
        ValueError: If filepath or search_text is invalid/empty
        
    Example:
        >>> from todocli.database import Database
        >>> from todocli.exporter import export_by_text_search
        >>> db = Database("todos.db")
        >>> todos = db.get_todos()
        >>> export_by_text_search(todos, "grocery", "grocery_todos.csv")
    """
    if not filepath:
        raise ValueError("Filepath cannot be empty")
    
    if not search_text:
        raise ValueError("Search text cannot be empty")
    
    if search_fields is None:
        search_fields = ["title", "description"]
    
    search_text_lower = search_text.lower()
    filtered_todos = []
    
    for todo in todos:
        for field in search_fields:
            if field == "title":
                if search_text_lower in todo.title.lower():
                    filtered_todos.append(todo)
                    break
            elif field == "description":
                if search_text_lower in todo.description.lower():
                    filtered_todos.append(todo)
                    break
            elif field == "category":
                if search_text_lower in todo.category.lower():
                    filtered_todos.append(todo)
                    break
    
    # Export the filtered list
    export_to_csv(filtered_todos, filepath)
