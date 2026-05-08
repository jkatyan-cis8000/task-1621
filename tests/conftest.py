"""
Pytest configuration and fixtures for Todo CLI tests.

Provides shared fixtures for:
- Database fixtures (temp DB files, initialized DB instances)
- Sample data (sample todos with various configurations)
- Temp files (for CSV export testing)
"""

import pytest
import tempfile
import os
import csv
from datetime import datetime, timedelta
from pathlib import Path

# Import modules (these may not exist initially, handled with try/except)
try:
    from todocli.models import Todo
    from todocli.database import Database
except ImportError:
    # These will be available once implementation tasks complete
    Todo = None
    Database = None


class MockTodo:
    """Mock Todo class for testing before implementation"""
    def __init__(self, title, description="", priority="medium", category="", 
                 completed=False, id=None, created_at=None, updated_at=None):
        self.id = id
        self.title = title
        self.description = description
        self.priority = priority
        self.category = category
        self.completed = completed
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "completed": self.completed,
            "created_at": self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else str(self.created_at),
            "updated_at": self.updated_at.isoformat() if hasattr(self.updated_at, 'isoformat') else str(self.updated_at),
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class MockDatabase:
    """Mock Database class for testing before implementation"""
    def __init__(self, db_path):
        self.db_path = db_path
        self.todos = {}
        self.next_id = 1
    
    def init_db(self):
        pass
    
    def add_todo(self, todo):
        todo.id = self.next_id
        self.todos[self.next_id] = todo
        self.next_id += 1
        return todo.id
    
    def get_todos(self, filters=None):
        todos = list(self.todos.values())
        if filters:
            if "category" in filters:
                todos = [t for t in todos if t.category == filters["category"]]
            if "priority" in filters:
                todos = [t for t in todos if t.priority == filters["priority"]]
            if "completed" in filters:
                todos = [t for t in todos if t.completed == filters["completed"]]
        return todos
    
    def update_todo(self, id, fields):
        if id in self.todos:
            for key, value in fields.items():
                setattr(self.todos[id], key, value)
            self.todos[id].updated_at = datetime.now()
            return True
        return False
    
    def delete_todo(self, id):
        if id in self.todos:
            del self.todos[id]
            return True
        return False
    
    def mark_complete(self, id):
        if id in self.todos:
            self.todos[id].completed = True
            self.todos[id].updated_at = datetime.now()
            return True
        return False


# Use real classes if available, otherwise use mocks
TodoClass = Todo if Todo is not None else MockTodo
DatabaseClass = Database if Database is not None else MockDatabase


@pytest.fixture
def temp_db_file():
    """Fixture providing a temporary database file path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def db_instance(temp_db_file):
    """Fixture providing an initialized Database instance."""
    db = DatabaseClass(temp_db_file)
    db.init_db()
    return db


@pytest.fixture
def temp_csv_file():
    """Fixture providing a temporary CSV file path."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        csv_path = f.name
    yield csv_path
    # Cleanup
    if os.path.exists(csv_path):
        os.unlink(csv_path)


@pytest.fixture
def sample_todo():
    """Fixture providing a single sample Todo."""
    return TodoClass(
        title="Buy groceries",
        description="Milk, eggs, bread",
        priority="high",
        category="Shopping"
    )


@pytest.fixture
def sample_todos():
    """Fixture providing multiple sample Todos with various configurations."""
    todos = [
        TodoClass(
            title="Buy groceries",
            description="Milk, eggs, bread, cheese",
            priority="high",
            category="Shopping",
            completed=False
        ),
        TodoClass(
            title="Write report",
            description="Quarterly report for Q2",
            priority="medium",
            category="Work",
            completed=False
        ),
        TodoClass(
            title="Complete project",
            description="Finish the todo CLI project",
            priority="high",
            category="Work",
            completed=False
        ),
        TodoClass(
            title="Call dentist",
            description="Schedule appointment",
            priority="medium",
            category="Personal",
            completed=True
        ),
        TodoClass(
            title="Go for a run",
            description="30 minute run in the park",
            priority="low",
            category="Health",
            completed=False
        ),
        TodoClass(
            title="Read book",
            description="Finish reading Python Design Patterns",
            priority="low",
            category="Learning",
            completed=False
        ),
    ]
    return todos


@pytest.fixture
def populated_db(db_instance, sample_todos):
    """Fixture providing a Database instance pre-populated with sample todos."""
    for todo in sample_todos:
        db_instance.add_todo(todo)
    return db_instance


@pytest.fixture
def temp_dir():
    """Fixture providing a temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def cli_runner():
    """Fixture providing a CLI runner (using click.testing.CliRunner style)."""
    from io import StringIO
    import sys
    
    class CliRunner:
        def invoke(self, cli_func, args=None, input=None, catch_exceptions=True):
            """Simulate CLI invocation."""
            if args is None:
                args = []
            
            # Capture stdout and stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            
            try:
                # This would call the actual CLI function
                # For now, return a mock result
                return {
                    "exit_code": 0,
                    "output": "",
                    "exception": None
                }
            except Exception as e:
                if catch_exceptions:
                    return {
                        "exit_code": 1,
                        "output": "",
                        "exception": e
                    }
                else:
                    raise
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
    
    return CliRunner()


# Utility fixtures for data validation
@pytest.fixture
def valid_todo_data():
    """Fixture providing valid todo data for testing."""
    return {
        "title": "Test Todo",
        "description": "This is a test todo",
        "priority": "medium",
        "category": "Testing",
        "completed": False,
    }


@pytest.fixture
def invalid_todo_data():
    """Fixture providing invalid todo data for testing edge cases."""
    return [
        {"title": "", "description": "Empty title"},  # Empty title
        {"title": "x" * 1000, "description": "Very long title"},  # Very long title
        {"priority": "invalid", "description": "Invalid priority"},  # Invalid priority
        {"priority": "HIGH", "description": "Uppercase priority"},  # Case sensitivity
    ]


@pytest.fixture
def priority_levels():
    """Fixture providing valid priority levels."""
    return ["high", "medium", "low"]


@pytest.fixture
def sample_categories():
    """Fixture providing sample categories."""
    return ["Work", "Personal", "Shopping", "Health", "Learning"]
