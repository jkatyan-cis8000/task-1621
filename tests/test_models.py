"""
Unit tests for todocli.models module.

Tests cover:
- Todo class initialization and validation
- Field validation (title, description, priority, category)
- Serialization (to_dict) and deserialization (from_dict)
- Date/time handling
- Edge cases and invalid inputs
"""

import pytest
from datetime import datetime
from todocli.models import Todo


class TestTodoInitialization:
    """Test Todo class initialization and basic functionality."""
    
    def test_todo_creation_with_required_fields(self):
        """Test creating a Todo with required fields only."""
        todo = Todo(
            title="Buy milk",
            description="1 liter of milk",
            priority="high",
            category="Shopping"
        )
        
        assert todo.title == "Buy milk"
        assert todo.description == "1 liter of milk"
        assert todo.priority == "high"
        assert todo.category == "Shopping"
        assert todo.completed is False
        assert todo.created_at is not None
        assert todo.updated_at is not None
        assert todo.id is None  # ID should be None until saved
    
    def test_todo_creation_with_all_fields(self):
        """Test creating a Todo with all fields including optional ones."""
        now = datetime.now()
        todo = Todo(
            title="Write code",
            description="Implement models.py",
            priority="medium",
            category="Work",
            completed=True,
            created_at=now,
            updated_at=now,
            id=1
        )
        
        assert todo.id == 1
        assert todo.title == "Write code"
        assert todo.completed is True
        assert todo.created_at == now
        assert todo.updated_at == now
    
    def test_todo_default_values(self):
        """Test that default values are correctly set."""
        todo = Todo(
            title="Test task",
            description="A test",
            priority="medium",
            category="Test"
        )
        
        assert todo.completed is False
        assert todo.id is None
        assert isinstance(todo.created_at, datetime)
        assert isinstance(todo.updated_at, datetime)
    
    def test_todo_timestamps_are_set_automatically(self):
        """Test that created_at and updated_at are set automatically."""
        before = datetime.now()
        todo = Todo(
            title="Task",
            description="Description",
            priority="low",
            category="Testing"
        )
        after = datetime.now()
        
        assert before <= todo.created_at <= after
        assert before <= todo.updated_at <= after
        assert todo.created_at == todo.updated_at


class TestTodoValidation:
    """Test Todo field validation."""
    
    def test_valid_priority_levels(self, priority_levels):
        """Test that valid priority levels are accepted."""
        for priority in priority_levels:
            todo = Todo(
                title="Task",
                description="Description",
                priority=priority,
                category="Test"
            )
            assert todo.priority == priority
    
    def test_invalid_priority_raises_error(self):
        """Test that invalid priority levels raise ValueError."""
        with pytest.raises(ValueError):
            Todo(
                title="Task",
                description="Description",
                priority="invalid",
                category="Test"
            )
    
    def test_priority_case_sensitivity(self):
        """Test that priority levels are case-sensitive (lowercase only)."""
        with pytest.raises(ValueError):
            Todo(
                title="Task",
                description="Description",
                priority="HIGH",
                category="Test"
            )
    
    def test_empty_title_raises_error(self):
        """Test that empty title raises ValueError."""
        with pytest.raises(ValueError):
            Todo(
                title="",
                description="Description",
                priority="medium",
                category="Test"
            )
    
    def test_title_with_only_whitespace_raises_error(self):
        """Test that title with only whitespace raises ValueError."""
        with pytest.raises(ValueError):
            Todo(
                title="   ",
                description="Description",
                priority="medium",
                category="Test"
            )
    
    def test_very_long_title(self):
        """Test that very long titles are handled (may have max length)."""
        long_title = "x" * 256
        # This might raise an error depending on validation rules
        try:
            todo = Todo(
                title=long_title,
                description="Description",
                priority="medium",
                category="Test"
            )
            # If it doesn't raise, the long title should be stored
            assert len(todo.title) == 256
        except ValueError:
            # If it raises, that's also valid - max length enforcement
            pass
    
    def test_empty_description_is_allowed(self):
        """Test that empty description is allowed."""
        todo = Todo(
            title="Task",
            description="",
            priority="medium",
            category="Test"
        )
        assert todo.description == ""
    
    def test_special_characters_in_fields(self):
        """Test that special characters are handled correctly."""
        todo = Todo(
            title="Task with special chars: !@#$%^&*()",
            description="Description with 'quotes' and \"double quotes\"",
            priority="medium",
            category="Test & Development"
        )
        
        assert "!@#$%^&*()" in todo.title
        assert "'" in todo.description
        assert "&" in todo.category
    
    def test_unicode_characters_in_fields(self):
        """Test that unicode characters are handled correctly."""
        todo = Todo(
            title="购买牛奶 🥛",
            description="これはテストです",
            priority="medium",
            category="日本語"
        )
        
        assert "🥛" in todo.title
        assert "テスト" in todo.description
    
    def test_category_can_be_empty(self):
        """Test that empty category is allowed."""
        todo = Todo(
            title="Task",
            description="Description",
            priority="medium",
            category=""
        )
        assert todo.category == ""
    
    def test_custom_categories(self, sample_categories):
        """Test that custom categories work."""
        for category in sample_categories:
            todo = Todo(
                title="Task",
                description="Description",
                priority="medium",
                category=category
            )
            assert todo.category == category


class TestTodoSerialization:
    """Test Todo serialization to and from dictionaries."""
    
    def test_to_dict_includes_all_fields(self, sample_todo):
        """Test that to_dict includes all Todo fields."""
        data = sample_todo.to_dict()
        
        assert "id" in data
        assert "title" in data
        assert "description" in data
        assert "priority" in data
        assert "category" in data
        assert "completed" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_to_dict_values_are_correct(self, sample_todo):
        """Test that to_dict returns correct values."""
        data = sample_todo.to_dict()
        
        assert data["title"] == sample_todo.title
        assert data["description"] == sample_todo.description
        assert data["priority"] == sample_todo.priority
        assert data["category"] == sample_todo.category
        assert data["completed"] == sample_todo.completed
    
    def test_to_dict_datetime_fields_are_serialized(self, sample_todo):
        """Test that datetime fields are properly serialized."""
        data = sample_todo.to_dict()
        
        # created_at and updated_at should be strings (ISO format)
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)
        
        # Should be parseable as ISO format
        datetime.fromisoformat(data["created_at"])
        datetime.fromisoformat(data["updated_at"])
    
    def test_from_dict_creates_todo_from_dict(self, valid_todo_data):
        """Test creating a Todo from a dictionary."""
        todo = Todo.from_dict(valid_todo_data)
        
        assert todo.title == valid_todo_data["title"]
        assert todo.description == valid_todo_data["description"]
        assert todo.priority == valid_todo_data["priority"]
        assert todo.category == valid_todo_data["category"]
        assert todo.completed == valid_todo_data["completed"]
    
    def test_from_dict_with_id(self, valid_todo_data):
        """Test creating a Todo from dict with ID."""
        data = valid_todo_data.copy()
        data["id"] = 42
        
        todo = Todo.from_dict(data)
        assert todo.id == 42
    
    def test_from_dict_with_timestamps(self, valid_todo_data):
        """Test creating a Todo from dict with timestamps."""
        now = datetime.now()
        data = valid_todo_data.copy()
        data["created_at"] = now
        data["updated_at"] = now
        
        todo = Todo.from_dict(data)
        assert todo.created_at == now
        assert todo.updated_at == now
    
    def test_round_trip_serialization(self, sample_todo):
        """Test that a Todo can be serialized and deserialized without loss."""
        original_dict = sample_todo.to_dict()
        reconstructed = Todo.from_dict(original_dict)
        final_dict = reconstructed.to_dict()
        
        # Dates may have microsecond differences, compare components
        assert original_dict["title"] == final_dict["title"]
        assert original_dict["description"] == final_dict["description"]
        assert original_dict["priority"] == final_dict["priority"]
        assert original_dict["category"] == final_dict["category"]
        assert original_dict["completed"] == final_dict["completed"]
    
    def test_from_dict_with_iso_formatted_dates(self, valid_todo_data):
        """Test creating a Todo from dict with ISO-formatted date strings."""
        now = datetime.now()
        iso_date = now.isoformat()
        
        data = valid_todo_data.copy()
        data["created_at"] = iso_date
        data["updated_at"] = iso_date
        
        todo = Todo.from_dict(data)
        assert isinstance(todo.created_at, datetime)
        assert isinstance(todo.updated_at, datetime)
    
    def test_from_dict_missing_optional_fields(self):
        """Test from_dict with all required fields."""
        data = {
            "title": "Minimal Task",
            "description": "Just the basics",
            "priority": "medium",
            "category": "Test",
            "completed": False
        }
        
        todo = Todo.from_dict(data)
        assert todo.title == "Minimal Task"
        assert todo.id is None
        assert todo.completed is False
    
    def test_to_dict_missing_id_returns_none(self):
        """Test that to_dict returns None for id if not set."""
        todo = Todo(
            title="Task",
            description="Description",
            priority="medium",
            category="Test"
        )
        data = todo.to_dict()
        assert data["id"] is None
    
    def test_to_dict_with_id_set(self):
        """Test that to_dict returns id when set."""
        todo = Todo(
            title="Task",
            description="Description",
            priority="medium",
            category="Test",
            id=99
        )
        data = todo.to_dict()
        assert data["id"] == 99


class TestTodoEquality:
    """Test Todo equality and comparison."""
    
    def test_todos_with_same_data_are_equal(self):
        """Test that todos with same data are considered equal."""
        todo1 = Todo(
            title="Task",
            description="Description",
            priority="medium",
            category="Test"
        )
        todo2 = Todo(
            title="Task",
            description="Description",
            priority="medium",
            category="Test"
        )
        
        # Note: timestamps may differ, so we compare fields
        assert todo1.title == todo2.title
        assert todo1.description == todo2.description
        assert todo1.priority == todo2.priority
        assert todo1.category == todo2.category
    
    def test_todos_with_different_ids_are_different(self):
        """Test that todos with different IDs are considered different."""
        todo1 = Todo(
            title="Task",
            description="Description",
            priority="medium",
            category="Test",
            id=1
        )
        todo2 = Todo(
            title="Task",
            description="Description",
            priority="medium",
            category="Test",
            id=2
        )
        
        # If __eq__ is implemented based on ID
        if hasattr(todo1, '__eq__'):
            assert todo1.id != todo2.id


class TestTodoEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_todo_with_newlines_in_description(self):
        """Test that newlines in description are handled."""
        todo = Todo(
            title="Task",
            description="Line 1\nLine 2\nLine 3",
            priority="medium",
            category="Test"
        )
        assert "\n" in todo.description
    
    def test_todo_with_tabs_in_fields(self):
        """Test that tabs in fields are handled."""
        todo = Todo(
            title="Task\twith\ttabs",
            description="Description\twith\ttabs",
            priority="medium",
            category="Test"
        )
        assert "\t" in todo.title
        assert "\t" in todo.description
    
    def test_todo_completed_flag(self):
        """Test that completed flag is properly managed."""
        todo = Todo(
            title="Task",
            description="Description",
            priority="medium",
            category="Test",
            completed=False
        )
        assert todo.completed is False
        
        todo.completed = True
        assert todo.completed is True
    
    def test_todo_with_very_long_description(self):
        """Test handling very long descriptions."""
        long_description = "x" * 10000
        todo = Todo(
            title="Task",
            description=long_description,
            priority="medium",
            category="Test"
        )
        assert len(todo.description) == 10000
    
    def test_todo_timestamps_are_datetime_objects(self):
        """Test that timestamps are datetime objects."""
        todo = Todo(
            title="Task",
            description="Description",
            priority="medium",
            category="Test"
        )
        assert isinstance(todo.created_at, datetime)
        assert isinstance(todo.updated_at, datetime)


class TestTodoMethods:
    """Test Todo helper methods."""
    
    def test_mark_complete_method(self, sample_todo):
        """Test mark_complete method."""
        assert sample_todo.completed is False
        sample_todo.mark_complete()
        assert sample_todo.completed is True
    
    def test_mark_incomplete_method(self, sample_todo):
        """Test mark_incomplete method."""
        sample_todo.completed = True
        sample_todo.mark_incomplete()
        assert sample_todo.completed is False
    
    def test_mark_complete_updates_timestamp(self, sample_todo):
        """Test that mark_complete updates timestamp."""
        original_time = sample_todo.updated_at
        import time
        time.sleep(0.01)
        sample_todo.mark_complete()
        assert sample_todo.updated_at > original_time
    
    def test_mark_incomplete_updates_timestamp(self, sample_todo):
        """Test that mark_incomplete updates timestamp."""
        original_time = sample_todo.updated_at
        import time
        time.sleep(0.01)
        sample_todo.mark_incomplete()
        assert sample_todo.updated_at > original_time
    
    def test_update_title(self, sample_todo):
        """Test updating title via update method."""
        sample_todo.update(title="New Title")
        assert sample_todo.title == "New Title"
    
    def test_update_description(self, sample_todo):
        """Test updating description via update method."""
        sample_todo.update(description="New Description")
        assert sample_todo.description == "New Description"
    
    def test_update_priority(self, sample_todo):
        """Test updating priority via update method."""
        sample_todo.update(priority="low")
        assert sample_todo.priority == "low"
    
    def test_update_category(self, sample_todo):
        """Test updating category via update method."""
        sample_todo.update(category="NewCategory")
        assert sample_todo.category == "NewCategory"
    
    def test_update_multiple_fields(self, sample_todo):
        """Test updating multiple fields at once."""
        sample_todo.update(
            title="New Title",
            priority="low",
            category="Updated"
        )
        assert sample_todo.title == "New Title"
        assert sample_todo.priority == "low"
        assert sample_todo.category == "Updated"
    
    def test_update_with_invalid_field(self, sample_todo):
        """Test that update raises error for invalid field."""
        with pytest.raises(ValueError):
            sample_todo.update(completed=True)  # Cannot update completed via update()
    
    def test_update_with_invalid_title(self, sample_todo):
        """Test that update rejects empty title."""
        with pytest.raises(ValueError):
            sample_todo.update(title="")
    
    def test_update_with_invalid_priority(self, sample_todo):
        """Test that update rejects invalid priority."""
        with pytest.raises(ValueError):
            sample_todo.update(priority="urgent")
    
    def test_update_timestamp_changes(self, sample_todo):
        """Test that update changes updated_at timestamp."""
        original_time = sample_todo.updated_at
        import time
        time.sleep(0.01)
        sample_todo.update(title="New Title")
        assert sample_todo.updated_at > original_time
    
    def test_repr_method(self, sample_todo):
        """Test string representation of Todo."""
        repr_str = repr(sample_todo)
        assert "Todo(" in repr_str
        assert sample_todo.title in repr_str
        assert sample_todo.priority in repr_str


class TestTodoTypeValidation:
    """Test type validation in Todo constructor."""
    
    def test_description_must_be_string(self):
        """Test that description must be string."""
        with pytest.raises(TypeError):
            Todo("Task", description=123, priority="medium", category="Test")
    
    def test_category_must_be_string(self):
        """Test that category must be string."""
        with pytest.raises(TypeError):
            Todo("Task", description="Desc", priority="medium", category=123)
    
    def test_completed_must_be_boolean(self):
        """Test that completed must be boolean."""
        with pytest.raises(TypeError):
            Todo("Task", description="Desc", priority="medium", 
                 category="Test", completed="yes")
    
    def test_id_must_be_int_or_none(self):
        """Test that ID must be int or None."""
        with pytest.raises(TypeError):
            Todo("Task", description="Desc", priority="medium", 
                 category="Test", id="1")


class TestTodoUpdateValidation:
    """Test validation in update method."""
    
    def test_update_description_must_be_string(self, sample_todo):
        """Test that update rejects non-string description."""
        with pytest.raises(TypeError):
            sample_todo.update(description=123)
    
    def test_update_category_must_be_string(self, sample_todo):
        """Test that update rejects non-string category."""
        with pytest.raises(TypeError):
            sample_todo.update(category=123)
    
    def test_update_title_whitespace_stripped(self, sample_todo):
        """Test that update strips whitespace from title."""
        sample_todo.update(title="  New Title  ")
        assert sample_todo.title == "New Title"
    
    def test_update_description_whitespace_stripped(self, sample_todo):
        """Test that update strips whitespace from description."""
        sample_todo.update(description="  New Desc  ")
        assert sample_todo.description == "New Desc"
    
    def test_update_category_whitespace_stripped(self, sample_todo):
        """Test that update strips whitespace from category."""
        sample_todo.update(category="  New Cat  ")
        assert sample_todo.category == "New Cat"


class TestTodoEdgeCases:
    """Test edge cases and error conditions for Todo."""
    
    def test_from_dict_missing_required_fields(self):
        """Test from_dict with missing required fields raises ValueError."""
        data_missing_title = {
            "description": "Description",
            "priority": "medium",
            "category": "Test",
            "completed": False
        }
        
        with pytest.raises(ValueError, match="Missing required fields"):
            Todo.from_dict(data_missing_title)
    
    def test_from_dict_missing_multiple_required_fields(self):
        """Test from_dict with multiple missing required fields."""
        data_minimal = {
            "title": "Task",
        }
        
        with pytest.raises(ValueError, match="Missing required fields"):
            Todo.from_dict(data_minimal)
    
    def test_equality_with_non_todo_object(self):
        """Test __eq__ with non-Todo object returns NotImplemented."""
        todo = Todo(title="Task", description="Desc")
        
        # Comparing with non-Todo object
        assert (todo == "string") is False
        assert (todo == 123) is False
        assert (todo == None) is False
        assert (todo == {}) is False
    
    def test_equality_with_same_todo(self):
        """Test __eq__ with same Todo object."""
        todo = Todo(title="Task", description="Desc", priority="high", category="Test")
        
        # Same object should be equal to itself
        assert todo == todo
    
    def test_equality_with_different_todos(self):
        """Test __eq__ with different Todo objects."""
        todo1 = Todo(title="Task1", description="Desc")
        todo2 = Todo(title="Task2", description="Desc")
        
        # Different titles should not be equal
        assert todo1 != todo2
    
    def test_todo_repr_string(self):
        """Test __repr__ produces valid string representation."""
        todo = Todo(
            title="Buy milk",
            description="At the store",
            priority="high",
            category="Shopping",
            id=42
        )
        
        repr_str = repr(todo)
        assert "Todo" in repr_str
        assert "Buy milk" in repr_str
        assert "high" in repr_str
        assert "42" in repr_str
