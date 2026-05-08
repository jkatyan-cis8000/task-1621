"""
Data models for the Todo CLI application.

Defines the Todo class with validation, serialization, and deserialization.
"""

from datetime import datetime
from typing import Dict, Any, Optional


class Todo:
    """
    Represents a single todo item.
    
    Attributes:
        id: Unique identifier (None for new todos before database insertion)
        title: Short title/name of the todo
        description: Detailed description of the todo
        priority: Priority level (high, medium, low)
        category: User-defined category (free-form string)
        completed: Whether the todo is marked as complete
        created_at: Timestamp when the todo was created
        updated_at: Timestamp when the todo was last updated
    """
    
    VALID_PRIORITIES = {"high", "medium", "low"}
    
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
    ):
        """
        Initialize a Todo instance.
        
        Args:
            title: Required todo title
            description: Optional detailed description
            priority: Priority level (high, medium, low). Defaults to "medium"
            category: Optional category/tag. Defaults to empty string
            completed: Whether todo is completed. Defaults to False
            id: Database ID (typically None for new todos)
            created_at: Creation timestamp. Auto-set if None
            updated_at: Last update timestamp. Auto-set if None
            
        Raises:
            ValueError: If title is empty or priority is invalid
            TypeError: If fields are of wrong type
        """
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Title must be a non-empty string")
        
        if not isinstance(description, str):
            raise TypeError("Description must be a string")
        
        if not isinstance(priority, str) or priority not in self.VALID_PRIORITIES:
            raise ValueError(f"Priority must be one of {self.VALID_PRIORITIES}")
        
        if not isinstance(category, str):
            raise TypeError("Category must be a string")
        
        if not isinstance(completed, bool):
            raise TypeError("Completed must be a boolean")
        
        if id is not None and not isinstance(id, int):
            raise TypeError("ID must be an integer or None")
        
        self.id = id
        self.title = title.strip()
        self.description = description.strip()
        self.priority = priority
        self.category = category.strip()
        self.completed = completed
        
        # Set timestamps - use current time if not provided
        now = datetime.now()
        self.created_at = created_at if created_at is not None else now
        self.updated_at = updated_at if updated_at is not None else now
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Todo instance to a dictionary.
        
        Timestamps are converted to ISO format strings for serialization.
        
        Returns:
            Dictionary representation of the todo with all fields
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "completed": self.completed,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Todo":
        """
        Create a Todo instance from a dictionary.
        
        Handles ISO format datetime strings and converts them back to datetime objects.
        Validates all required fields are present.
        
        Args:
            data: Dictionary containing todo fields
            
        Returns:
            New Todo instance
            
        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If field types are incorrect
        """
        required_fields = {"title", "description", "priority", "category", "completed"}
        missing_fields = required_fields - set(data.keys())
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Parse ISO format timestamps if they're strings
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            title=data["title"],
            description=data["description"],
            priority=data["priority"],
            category=data["category"],
            completed=data["completed"],
            id=data.get("id"),
            created_at=created_at,
            updated_at=updated_at,
        )
    
    def __repr__(self) -> str:
        """
        Return a string representation of the Todo.
        
        Format: Todo(id=X, title="...", priority=Y, completed=Z)
        """
        return (
            f"Todo(id={self.id}, title={self.title!r}, priority={self.priority}, "
            f"completed={self.completed})"
        )
    
    def __eq__(self, other: object) -> bool:
        """
        Check equality between two Todo instances.
        
        Compares all fields except timestamps (which may vary slightly).
        """
        if not isinstance(other, Todo):
            return NotImplemented
        
        return (
            self.id == other.id
            and self.title == other.title
            and self.description == other.description
            and self.priority == other.priority
            and self.category == other.category
            and self.completed == other.completed
        )
    
    def mark_complete(self) -> None:
        """
        Mark this todo as completed and update the timestamp.
        """
        self.completed = True
        self.updated_at = datetime.now()
    
    def mark_incomplete(self) -> None:
        """
        Mark this todo as incomplete and update the timestamp.
        """
        self.completed = False
        self.updated_at = datetime.now()
    
    def update(self, **kwargs) -> None:
        """
        Update multiple fields of the todo.
        
        Only allows updating specific fields: title, description, priority, category.
        Automatically updates the updated_at timestamp.
        
        Args:
            **kwargs: Fields to update (title, description, priority, category)
            
        Raises:
            ValueError: If an invalid field is provided or value is invalid
        """
        allowed_fields = {"title", "description", "priority", "category"}
        invalid_fields = set(kwargs.keys()) - allowed_fields
        
        if invalid_fields:
            raise ValueError(f"Cannot update fields: {invalid_fields}")
        
        if "title" in kwargs:
            if not isinstance(kwargs["title"], str) or not kwargs["title"].strip():
                raise ValueError("Title must be a non-empty string")
            self.title = kwargs["title"].strip()
        
        if "description" in kwargs:
            if not isinstance(kwargs["description"], str):
                raise TypeError("Description must be a string")
            self.description = kwargs["description"].strip()
        
        if "priority" in kwargs:
            if kwargs["priority"] not in self.VALID_PRIORITIES:
                raise ValueError(f"Priority must be one of {self.VALID_PRIORITIES}")
            self.priority = kwargs["priority"]
        
        if "category" in kwargs:
            if not isinstance(kwargs["category"], str):
                raise TypeError("Category must be a string")
            self.category = kwargs["category"].strip()
        
        # Update the timestamp whenever any field is modified
        self.updated_at = datetime.now()
