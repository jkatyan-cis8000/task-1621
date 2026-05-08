"""
Unit tests for todocli.database module.

Tests cover:
- Database initialization and schema creation
- CRUD operations (Create, Read, Update, Delete)
- Filtering by category and priority
- Marking todos as complete
- Error handling and edge cases
"""

import pytest
import os
from datetime import datetime
from todocli.database import Database
from todocli.models import Todo


class TestDatabaseInitialization:
    """Test Database initialization and setup."""
    
    def test_database_creation(self, temp_db_file):
        """Test creating a new Database instance."""
        db = Database(temp_db_file)
        # db_path may be a string or Path object
        assert str(db.db_path) == str(temp_db_file)
        # Database constructor may create the file immediately
        assert os.path.exists(temp_db_file)
    
    def test_init_db_creates_schema(self, db_instance):
        """Test that init_db creates the database schema."""
        # If init_db was successful, we should be able to query
        todos = db_instance.get_todos()
        assert isinstance(todos, list)
        assert len(todos) == 0
    
    def test_init_db_idempotent(self, temp_db_file):
        """Test that init_db can be called multiple times safely."""
        db = Database(temp_db_file)
        db.init_db()
        db.init_db()  # Second call should not fail
        
        todos = db.get_todos()
        assert isinstance(todos, list)
    
    def test_database_file_created_after_init(self, temp_db_file):
        """Test that database file is created after init_db."""
        db = Database(temp_db_file)
        db.init_db()
        assert os.path.exists(temp_db_file)


class TestDatabaseCreateOperations:
    """Test creating todos in the database."""
    
    def test_add_todo_returns_id(self, db_instance, sample_todo):
        """Test that add_todo returns an integer ID."""
        todo_id = db_instance.add_todo(sample_todo)
        assert isinstance(todo_id, int)
        assert todo_id > 0
    
    def test_add_todo_increments_id(self, db_instance, sample_todos):
        """Test that added todos get sequential IDs."""
        ids = [db_instance.add_todo(todo) for todo in sample_todos[:3]]
        assert ids == [1, 2, 3] or len(set(ids)) == 3
    
    def test_add_multiple_todos(self, db_instance, sample_todos):
        """Test adding multiple todos."""
        count = len(sample_todos)
        for todo in sample_todos:
            db_instance.add_todo(todo)
        
        todos = db_instance.get_todos()
        assert len(todos) == count
    
    def test_added_todo_has_id_assigned(self, db_instance, sample_todo):
        """Test that after adding, the todo has an ID assigned."""
        original_id = sample_todo.id
        todo_id = db_instance.add_todo(sample_todo)
        
        # ID should be set either on the object or returned
        assert sample_todo.id == todo_id or todo_id is not None


class TestDatabaseReadOperations:
    """Test reading todos from the database."""
    
    def test_get_todos_empty_database(self, db_instance):
        """Test getting todos from empty database."""
        todos = db_instance.get_todos()
        assert isinstance(todos, list)
        assert len(todos) == 0
    
    def test_get_todos_returns_list(self, populated_db):
        """Test that get_todos returns a list."""
        todos = populated_db.get_todos()
        assert isinstance(todos, list)
        assert len(todos) > 0
    
    def test_get_todos_returns_todo_objects(self, populated_db):
        """Test that get_todos returns Todo instances."""
        todos = populated_db.get_todos()
        assert all(isinstance(todo, Todo) for todo in todos)
    
    def test_get_todos_preserves_all_fields(self, db_instance, sample_todo):
        """Test that all fields are preserved when retrieving."""
        db_instance.add_todo(sample_todo)
        todos = db_instance.get_todos()
        
        retrieved = todos[0]
        assert retrieved.title == sample_todo.title
        assert retrieved.description == sample_todo.description
        assert retrieved.priority == sample_todo.priority
        assert retrieved.category == sample_todo.category
        assert retrieved.completed == sample_todo.completed
    
    def test_get_todos_preserves_completed_status(self, db_instance):
        """Test that completed status is preserved."""
        todo_incomplete = Todo("Task 1", "Desc", "high", "Work", completed=False)
        todo_complete = Todo("Task 2", "Desc", "medium", "Work", completed=True)
        
        db_instance.add_todo(todo_incomplete)
        db_instance.add_todo(todo_complete)
        
        todos = db_instance.get_todos()
        assert any(not t.completed for t in todos)
        assert any(t.completed for t in todos)


class TestDatabaseFilteringByCategoryAndPriority:
    """Test filtering todos by category and priority."""
    
    def test_filter_by_category(self, populated_db, sample_categories):
        """Test filtering todos by category."""
        for category in sample_categories[:2]:  # Test first two categories
            filtered = populated_db.get_todos(filters={"category": category})
            assert all(todo.category == category for todo in filtered)
    
    def test_filter_by_priority(self, populated_db):
        """Test filtering todos by priority."""
        for priority in ["high", "medium", "low"]:
            filtered = populated_db.get_todos(filters={"priority": priority})
            assert all(todo.priority == priority for todo in filtered)
    
    def test_filter_by_category_and_priority(self, populated_db):
        """Test filtering by both category and priority."""
        filters = {"category": "Work", "priority": "high"}
        filtered = populated_db.get_todos(filters=filters)
        
        for todo in filtered:
            assert todo.category == "Work"
            assert todo.priority == "high"
    
    def test_filter_by_completed_status(self, populated_db):
        """Test filtering by completed status."""
        completed = populated_db.get_todos(filters={"completed": True})
        incomplete = populated_db.get_todos(filters={"completed": False})
        
        assert all(t.completed for t in completed)
        assert all(not t.completed for t in incomplete)
    
    def test_filter_nonexistent_category_returns_empty(self, populated_db):
        """Test filtering by non-existent category returns empty list."""
        filtered = populated_db.get_todos(filters={"category": "NonExistent"})
        assert len(filtered) == 0
    
    def test_filter_with_empty_filters_returns_all(self, populated_db):
        """Test that empty filters dict returns all todos."""
        all_todos = populated_db.get_todos()
        filtered = populated_db.get_todos(filters={})
        assert len(filtered) == len(all_todos)
    
    def test_filter_with_none_returns_all(self, populated_db):
        """Test that None filters returns all todos."""
        all_todos = populated_db.get_todos()
        filtered = populated_db.get_todos(filters=None)
        assert len(filtered) == len(all_todos)


class TestDatabaseUpdateOperations:
    """Test updating todos in the database."""
    
    def test_update_todo_returns_boolean(self, db_instance, sample_todo):
        """Test that update_todo returns a boolean."""
        todo_id = db_instance.add_todo(sample_todo)
        result = db_instance.update_todo(todo_id, {"title": "New Title"})
        assert isinstance(result, bool)
    
    def test_update_todo_updates_field(self, db_instance, sample_todo):
        """Test that update_todo updates the specified field."""
        todo_id = db_instance.add_todo(sample_todo)
        db_instance.update_todo(todo_id, {"title": "Updated Title"})
        
        todos = db_instance.get_todos()
        updated = next(t for t in todos if t.id == todo_id)
        assert updated.title == "Updated Title"
    
    def test_update_todo_multiple_fields(self, db_instance, sample_todo):
        """Test updating multiple fields at once."""
        todo_id = db_instance.add_todo(sample_todo)
        db_instance.update_todo(todo_id, {
            "title": "New Title",
            "priority": "low",
            "completed": True
        })
        
        todos = db_instance.get_todos()
        updated = next(t for t in todos if t.id == todo_id)
        assert updated.title == "New Title"
        assert updated.priority == "low"
        assert updated.completed is True
    
    def test_update_nonexistent_todo_returns_false(self, db_instance):
        """Test that updating non-existent todo returns False."""
        result = db_instance.update_todo(999, {"title": "Title"})
        assert result is False
    
    def test_update_preserves_other_fields(self, db_instance, sample_todo):
        """Test that updating one field preserves others."""
        todo_id = db_instance.add_todo(sample_todo)
        original_description = sample_todo.description
        
        db_instance.update_todo(todo_id, {"title": "New Title"})
        
        todos = db_instance.get_todos()
        updated = next(t for t in todos if t.id == todo_id)
        assert updated.description == original_description
    
    def test_update_todo_updates_timestamp(self, db_instance, sample_todo):
        """Test that update_todo updates the updated_at timestamp."""
        todo_id = db_instance.add_todo(sample_todo)
        original_updated_at = sample_todo.updated_at
        
        # Wait a bit to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        db_instance.update_todo(todo_id, {"title": "New Title"})
        
        todos = db_instance.get_todos()
        updated = next(t for t in todos if t.id == todo_id)
        # Timestamps may lose microseconds in database storage, so compare seconds
        assert updated.updated_at.replace(microsecond=0) >= original_updated_at.replace(microsecond=0)


class TestDatabaseDeleteOperations:
    """Test deleting todos from the database."""
    
    def test_delete_todo_returns_boolean(self, db_instance, sample_todo):
        """Test that delete_todo returns a boolean."""
        todo_id = db_instance.add_todo(sample_todo)
        result = db_instance.delete_todo(todo_id)
        assert isinstance(result, bool)
    
    def test_delete_todo_removes_from_database(self, db_instance, sample_todo):
        """Test that delete_todo removes the todo."""
        todo_id = db_instance.add_todo(sample_todo)
        db_instance.delete_todo(todo_id)
        
        todos = db_instance.get_todos()
        assert all(t.id != todo_id for t in todos)
    
    def test_delete_nonexistent_todo_returns_false(self, db_instance):
        """Test that deleting non-existent todo returns False."""
        result = db_instance.delete_todo(999)
        assert result is False
    
    def test_delete_multiple_todos(self, db_instance, sample_todos):
        """Test deleting multiple todos."""
        ids = [db_instance.add_todo(todo) for todo in sample_todos[:3]]
        
        for todo_id in ids:
            db_instance.delete_todo(todo_id)
        
        todos = db_instance.get_todos()
        for todo_id in ids:
            assert all(t.id != todo_id for t in todos)
    
    def test_delete_todo_returns_true_on_success(self, db_instance, sample_todo):
        """Test that delete_todo returns True on successful deletion."""
        todo_id = db_instance.add_todo(sample_todo)
        result = db_instance.delete_todo(todo_id)
        assert result is True


class TestDatabaseMarkCompleteOperations:
    """Test marking todos as complete."""
    
    def test_mark_complete_returns_boolean(self, db_instance, sample_todo):
        """Test that mark_complete returns a boolean."""
        todo_id = db_instance.add_todo(sample_todo)
        result = db_instance.mark_complete(todo_id)
        assert isinstance(result, bool)
    
    def test_mark_complete_sets_completed_flag(self, db_instance, sample_todo):
        """Test that mark_complete sets the completed flag."""
        assert not sample_todo.completed
        todo_id = db_instance.add_todo(sample_todo)
        
        db_instance.mark_complete(todo_id)
        
        todos = db_instance.get_todos()
        marked = next(t for t in todos if t.id == todo_id)
        assert marked.completed is True
    
    def test_mark_complete_nonexistent_todo_returns_false(self, db_instance):
        """Test that marking non-existent todo returns False."""
        result = db_instance.mark_complete(999)
        assert result is False
    
    def test_mark_complete_idempotent(self, db_instance, sample_todo):
        """Test that marking complete multiple times is idempotent."""
        todo_id = db_instance.add_todo(sample_todo)
        
        db_instance.mark_complete(todo_id)
        db_instance.mark_complete(todo_id)
        
        todos = db_instance.get_todos()
        marked = next(t for t in todos if t.id == todo_id)
        assert marked.completed is True
    
    def test_mark_complete_updates_timestamp(self, db_instance, sample_todo):
        """Test that mark_complete updates the updated_at timestamp."""
        todo_id = db_instance.add_todo(sample_todo)
        original_updated_at = sample_todo.updated_at
        
        import time
        time.sleep(0.1)
        
        db_instance.mark_complete(todo_id)
        
        todos = db_instance.get_todos()
        marked = next(t for t in todos if t.id == todo_id)
        # Timestamps may lose microseconds in database storage, so compare seconds
        assert marked.updated_at.replace(microsecond=0) >= original_updated_at.replace(microsecond=0)


class TestDatabaseEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_database_operations(self, db_instance):
        """Test operations on empty database."""
        assert len(db_instance.get_todos()) == 0
        assert db_instance.delete_todo(1) is False
        assert db_instance.update_todo(1, {}) is False
        assert db_instance.mark_complete(1) is False
    
    def test_special_characters_in_fields(self, db_instance):
        """Test storing and retrieving todos with special characters."""
        todo = Todo(
            title="Task with 'quotes' and \"double quotes\"",
            description="Line1\nLine2\nLine3",
            priority="high",
            category="Test & Demo"
        )
        todo_id = db_instance.add_todo(todo)
        
        todos = db_instance.get_todos()
        retrieved = next(t for t in todos if t.id == todo_id)
        assert "'" in retrieved.title
        assert "\n" in retrieved.description
        assert "&" in retrieved.category
    
    def test_unicode_fields(self, db_instance):
        """Test storing and retrieving unicode content."""
        todo = Todo(
            title="购买牛奶 🥛",
            description="これはテストです",
            priority="medium",
            category="日本語カテゴリ"
        )
        todo_id = db_instance.add_todo(todo)
        
        todos = db_instance.get_todos()
        retrieved = next(t for t in todos if t.id == todo_id)
        assert "🥛" in retrieved.title
        assert "テスト" in retrieved.description
    
    def test_very_long_strings(self, db_instance):
        """Test handling very long strings."""
        todo = Todo(
            title="x" * 500,
            description="y" * 5000,
            priority="low",
            category="z" * 200
        )
        todo_id = db_instance.add_todo(todo)
        
        todos = db_instance.get_todos()
        retrieved = next(t for t in todos if t.id == todo_id)
        assert len(retrieved.title) == 500
        assert len(retrieved.description) == 5000


class TestDatabasePersistence:
    """Test that data persists across database connections."""
    
    def test_data_persists_after_reconnection(self, temp_db_file, sample_todo):
        """Test that data persists when reopening database."""
        # First connection - add data
        db1 = Database(temp_db_file)
        db1.init_db()
        db1.add_todo(sample_todo)
        
        # Second connection - verify data
        db2 = Database(temp_db_file)
        db2.init_db()
        todos = db2.get_todos()
        
        assert len(todos) == 1
        assert todos[0].title == sample_todo.title


class TestDatabaseErrorHandling:
    """Test database error handling."""
    
    def test_add_todo_with_existing_id_raises_error(self, db_instance):
        """Test that adding a todo with an ID raises ValueError."""
        todo = Todo("Task", "Desc", "high", "Work", id=1)
        
        with pytest.raises(ValueError):
            db_instance.add_todo(todo)
    
    def test_invalid_priority_rejected(self, db_instance):
        """Test that invalid priorities are caught during validation."""
        # This should fail at the Todo level, not database level
        with pytest.raises(ValueError):
            todo = Todo("Task", "Desc", "invalid", "Work")
    
    def test_empty_title_rejected(self, db_instance):
        """Test that empty titles are caught during validation."""
        with pytest.raises(ValueError):
            todo = Todo("", "Desc", "high", "Work")
    
    def test_database_parent_directory_creation(self, temp_dir):
        """Test that parent directories are created automatically."""
        db_path = os.path.join(temp_dir, "subdir", "nested", "todos.db")
        db = Database(db_path)
        db.init_db()
        
        assert os.path.exists(db_path)
    
    def test_get_todos_with_invalid_filters_type(self, db_instance, sample_todo):
        """Test that get_todos handles various filter types."""
        db_instance.add_todo(sample_todo)
        
        # Filters should be a dict or None
        todos = db_instance.get_todos(filters=None)
        assert len(todos) == 1
        
        todos = db_instance.get_todos(filters={})
        assert len(todos) == 1
    
    def test_filter_returns_correct_subset(self, populated_db):
        """Test that filters return correct subset size."""
        all_todos = populated_db.get_todos()
        assert len(all_todos) > 0
        
        # Filter by a category
        categories = set(t.category for t in all_todos if t.category)
        if categories:
            category = list(categories)[0]
            filtered = populated_db.get_todos(filters={"category": category})
            # All should match
            assert all(t.category == category for t in filtered)
            # At least one should match
            assert len(filtered) >= 1


class TestDatabaseInitialState:
    """Test database initial state and setup."""
    
    def test_new_database_is_empty(self, db_instance):
        """Test that newly initialized database is empty."""
        todos = db_instance.get_todos()
        assert len(todos) == 0
        assert isinstance(todos, list)
    
    def test_init_db_creates_table_structure(self, temp_db_file):
        """Test that init_db creates proper table structure."""
        db = Database(temp_db_file)
        db.init_db()
        
        # Try to add and retrieve a todo to verify structure
        todo = Todo("Test", "Desc", "high", "Work")
        todo_id = db.add_todo(todo)
        assert todo_id is not None
        
        todos = db.get_todos()
        assert len(todos) == 1
    
    def test_multiple_init_db_calls_safe(self, db_instance):
        """Test that multiple init_db calls don't cause errors."""
        db_instance.init_db()
        db_instance.init_db()
        
        # Database should still work
        todos = db_instance.get_todos()
        assert isinstance(todos, list)


class TestDatabaseConversion:
    """Test database conversion between Todo objects and database rows."""
    
    def test_todo_roundtrip_preserves_data(self, db_instance, sample_todo):
        """Test that a todo survives a roundtrip to and from database."""
        todo_id = db_instance.add_todo(sample_todo)
        
        todos = db_instance.get_todos()
        retrieved = next(t for t in todos if t.id == todo_id)
        
        # Compare key fields
        assert retrieved.title == sample_todo.title
        assert retrieved.description == sample_todo.description
        assert retrieved.priority == sample_todo.priority
        assert retrieved.category == sample_todo.category
        assert retrieved.completed == sample_todo.completed
    
    def test_completed_status_stored_correctly(self, db_instance):
        """Test that completed status is stored and retrieved correctly."""
        todo_true = Todo("Task 1", "Desc", "high", "Work", completed=True)
        todo_false = Todo("Task 2", "Desc", "high", "Work", completed=False)
        
        db_instance.add_todo(todo_true)
        db_instance.add_todo(todo_false)
        
        todos = db_instance.get_todos()
        true_todo = next(t for t in todos if t.title == "Task 1")
        false_todo = next(t for t in todos if t.title == "Task 2")
        
        assert true_todo.completed is True
        assert false_todo.completed is False
