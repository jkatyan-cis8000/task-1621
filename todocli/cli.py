"""
Command-line interface for the Todo CLI application.

Implements commands for managing todos: add, list, complete, delete, export.
Supports filtering by category and priority, with formatted output.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from todocli.database import Database
from todocli.models import Todo


class TodoCLI:
    """Command-line interface for managing todos."""
    
    DEFAULT_DB_PATH = "todos.db"
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """
        Initialize the CLI with a database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db = Database(db_path)
        self.db.init_db()
    
    def add(self, title: str, description: str = "", priority: str = "medium", 
            category: str = "") -> None:
        """
        Add a new todo to the database.
        
        Args:
            title: The todo title
            description: Optional detailed description
            priority: Priority level (high, medium, low)
            category: Optional category/tag
        """
        try:
            todo = Todo(
                title=title,
                description=description,
                priority=priority,
                category=category
            )
            todo_id = self.db.add_todo(todo)
            print(f"✓ Todo added with ID: {todo_id}")
            print(f"  Title: {title}")
            if category:
                print(f"  Category: {category}")
            print(f"  Priority: {priority}")
        except ValueError as e:
            print(f"✗ Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def list(self, category: Optional[str] = None, priority: Optional[str] = None,
             completed: Optional[bool] = None, format: str = "table") -> None:
        """
        List todos with optional filtering.
        
        Args:
            category: Filter by category (optional)
            priority: Filter by priority level (optional)
            completed: Filter by completion status (optional)
            format: Output format ('table' or 'simple')
        """
        filters = {}
        if category is not None:
            filters["category"] = category
        if priority is not None:
            filters["priority"] = priority
        if completed is not None:
            filters["completed"] = completed
        
        try:
            todos = self.db.get_todos(filters)
            
            if not todos:
                print("No todos found.")
                return
            
            if format == "table":
                self._print_table(todos)
            else:
                self._print_simple(todos)
        
        except ValueError as e:
            print(f"✗ Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def complete(self, todo_id: int) -> None:
        """
        Mark a todo as completed.
        
        Args:
            todo_id: ID of the todo to mark complete
        """
        try:
            if self.db.mark_complete(todo_id):
                print(f"✓ Todo {todo_id} marked as complete")
            else:
                print(f"✗ Todo {todo_id} not found", file=sys.stderr)
                sys.exit(1)
        except ValueError as e:
            print(f"✗ Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def delete(self, todo_id: int) -> None:
        """
        Delete a todo from the database.
        
        Args:
            todo_id: ID of the todo to delete
        """
        try:
            if self.db.delete_todo(todo_id):
                print(f"✓ Todo {todo_id} deleted")
            else:
                print(f"✗ Todo {todo_id} not found", file=sys.stderr)
                sys.exit(1)
        except ValueError as e:
            print(f"✗ Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def export(self, filepath: str, category: Optional[str] = None) -> None:
        """
        Export todos to a CSV file.
        
        Args:
            filepath: Path where to save the CSV file
            category: Optional - export only todos from this category
        """
        try:
            # Import here to avoid circular imports
            from todocli.exporter import export_to_csv, export_by_category
            
            todos = self.db.get_todos({"category": category} if category else None)
            
            if not todos:
                print("No todos to export.")
                return
            
            if category:
                export_by_category(todos, category, filepath)
            else:
                export_to_csv(todos, filepath)
            
            print(f"✓ Exported {len(todos)} todos to {filepath}")
        
        except FileNotFoundError as e:
            print(f"✗ Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"✗ Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def _print_table(self, todos: List[Todo]) -> None:
        """
        Print todos in a formatted table.
        
        Args:
            todos: List of Todo instances to print
        """
        # Header
        print(f"{'ID':<4} {'Status':<8} {'Priority':<8} {'Title':<30} {'Category':<15}")
        print("-" * 75)
        
        # Rows
        for todo in todos:
            status = "✓" if todo.completed else " "
            title = todo.title[:30] if len(todo.title) <= 30 else todo.title[:27] + "..."
            category = todo.category[:15] if todo.category else "-"
            category = category if len(category) <= 15 else category[:12] + "..."
            
            print(f"{todo.id:<4} {status:<8} {todo.priority:<8} {title:<30} {category:<15}")
    
    def _print_simple(self, todos: List[Todo]) -> None:
        """
        Print todos in a simple format (one per line).
        
        Args:
            todos: List of Todo instances to print
        """
        for todo in todos:
            status = "✓" if todo.completed else "○"
            category_str = f" [{todo.category}]" if todo.category else ""
            print(f"{status} {todo.id}: {todo.title} ({todo.priority}){category_str}")


def main(args: Optional[List[str]] = None) -> None:
    """
    Main entry point for the CLI.
    
    Parses command-line arguments and executes the appropriate command.
    
    Args:
        args: Command-line arguments (for testing; defaults to sys.argv[1:])
    """
    parser = argparse.ArgumentParser(
        description="A modular Python CLI todo manager with SQLite persistence and CSV export",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  todocli add "Buy groceries" -d "Milk, eggs, bread" -p high -c shopping
  todocli list
  todocli list -c shopping -p high
  todocli list --completed
  todocli complete 1
  todocli delete 1
  todocli export todos.csv
  todocli export todos.csv -c shopping
        """
    )
    
    # Global options
    parser.add_argument(
        "--db",
        default=TodoCLI.DEFAULT_DB_PATH,
        help=f"Path to the SQLite database (default: {TodoCLI.DEFAULT_DB_PATH})"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new todo")
    add_parser.add_argument("title", help="Title of the todo")
    add_parser.add_argument(
        "-d", "--description",
        default="",
        help="Detailed description (optional)"
    )
    add_parser.add_argument(
        "-p", "--priority",
        default="medium",
        choices=["high", "medium", "low"],
        help="Priority level (default: medium)"
    )
    add_parser.add_argument(
        "-c", "--category",
        default="",
        help="Category/tag (optional)"
    )
    
    # List command
    list_parser = subparsers.add_parser("list", help="List todos")
    list_parser.add_argument(
        "-c", "--category",
        help="Filter by category"
    )
    list_parser.add_argument(
        "-p", "--priority",
        choices=["high", "medium", "low"],
        help="Filter by priority"
    )
    list_parser.add_argument(
        "--completed",
        action="store_true",
        help="Show only completed todos"
    )
    list_parser.add_argument(
        "--incomplete",
        action="store_true",
        help="Show only incomplete todos"
    )
    list_parser.add_argument(
        "-f", "--format",
        choices=["table", "simple"],
        default="table",
        help="Output format (default: table)"
    )
    
    # Complete command
    complete_parser = subparsers.add_parser("complete", help="Mark a todo as complete")
    complete_parser.add_argument("id", type=int, help="ID of the todo to mark complete")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a todo")
    delete_parser.add_argument("id", type=int, help="ID of the todo to delete")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export todos to CSV")
    export_parser.add_argument("filepath", help="Path to save the CSV file")
    export_parser.add_argument(
        "-c", "--category",
        help="Export only todos from this category"
    )
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    # Create CLI instance
    cli = TodoCLI(parsed_args.db)
    
    # Execute command
    if parsed_args.command == "add":
        cli.add(
            title=parsed_args.title,
            description=parsed_args.description,
            priority=parsed_args.priority,
            category=parsed_args.category
        )
    elif parsed_args.command == "list":
        completed = None
        if parsed_args.completed:
            completed = True
        elif parsed_args.incomplete:
            completed = False
        
        cli.list(
            category=parsed_args.category,
            priority=parsed_args.priority,
            completed=completed,
            format=parsed_args.format
        )
    elif parsed_args.command == "complete":
        cli.complete(parsed_args.id)
    elif parsed_args.command == "delete":
        cli.delete(parsed_args.id)
    elif parsed_args.command == "export":
        cli.export(parsed_args.filepath, parsed_args.category)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
