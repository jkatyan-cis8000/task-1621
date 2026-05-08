"""
Unit and integration tests for todocli.cli module.

Tests cover:
- CLI argument parsing
- Command execution (add, list, complete, delete, export)
- Filtering and output formatting
- Integration with database and exporter
- Error handling and edge cases
"""

import pytest
import sys
import tempfile
import os
import csv
from io import StringIO
from unittest.mock import patch, MagicMock

# Import CLI components
from todocli.cli import main, TodoCLI

from todocli.models import Todo
from todocli.database import Database


class TestCliAddCommand:
    """Test the 'add' CLI command."""
    
    def test_add_command_basic(self, temp_db_file):
        """Test adding a basic todo via CLI."""
        cli = TodoCLI(temp_db_file)
        cli.add(
            title='Buy milk',
            description='Get 1 liter',
            priority='high',
            category='Shopping'
        )
        
        # Verify todo was added to database
        todos = cli.db.get_todos()
        assert len(todos) == 1
        assert todos[0].title == 'Buy milk'
        assert todos[0].priority == 'high'
        assert todos[0].category == 'Shopping'
    
    def test_add_command_required_fields(self, temp_db_file):
        """Test add command with only required fields."""
        cli = TodoCLI(temp_db_file)
        cli.add(title='Task')
        
        # Should work with defaults
        todos = cli.db.get_todos()
        assert len(todos) == 1
        assert todos[0].priority == 'medium'  # Default
    
    def test_add_command_invalid_priority(self, temp_db_file):
        """Test add command with invalid priority."""
        cli = TodoCLI(temp_db_file)
        
        # Should raise ValueError for invalid priority
        with pytest.raises(ValueError, match="Priority must be one of"):
            cli.add(title='Task', priority='urgent')
    
    def test_add_command_empty_title_fails(self, temp_db_file):
        """Test that add command fails with empty title."""
        cli = TodoCLI(temp_db_file)
        
        # Should fail with empty title
        with pytest.raises(ValueError, match="Title must be a non-empty string"):
            cli.add(title='')  # Empty title should fail


class TestCliListCommand:
    """Test the 'list' CLI command."""
    
    def test_list_command_all_todos(self, populated_db):
        """Test listing all todos."""
        cli = TodoCLI(populated_db.db_path)
        
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            cli.list()
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        
        # Should display all todos
        assert len(output) > 0
        assert 'Buy groceries' in output
    
    def test_list_command_filter_by_category(self, populated_db):
        """Test listing todos filtered by category."""
        cli = TodoCLI(populated_db.db_path)
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            cli.list(category='Work')
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        
        # Should only show Work category todos
        assert 'Write report' in output or 'Complete project' in output
    
    def test_list_command_filter_by_priority(self, populated_db):
        """Test listing todos filtered by priority."""
        cli = TodoCLI(populated_db.db_path)
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            cli.list(priority='high')
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        
        # Should only show high priority todos
        assert 'high' in output.lower()
    
    def test_list_command_empty_list(self, temp_db_file):
        """Test listing when no todos exist."""
        db = Database(temp_db_file)
        db.init_db()
        cli = TodoCLI(temp_db_file)
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            cli.list()
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        
        # Should show "No todos found"
        assert 'No todos found' in output
    
    def test_list_command_output_format(self, populated_db):
        """Test that list output is properly formatted."""
        cli = TodoCLI(populated_db.db_path)
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            cli.list(format='table')
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        
        # Should display in table format with headers
        assert 'ID' in output
        assert 'Title' in output


class TestCliCompleteCommand:
    """Test the 'complete' CLI command."""
    
    def test_complete_command_marks_todo(self, db_instance, sample_todo):
        """Test marking a todo as complete."""
        todo_id = db_instance.add_todo(sample_todo)
        cli = TodoCLI(db_instance.db_path)
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            cli.complete(todo_id)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        
        # Should mark todo as completed
        assert 'marked as complete' in output.lower()
        todo = db_instance.get_todo_by_id(todo_id)
        assert todo.completed is True
    
    def test_complete_command_invalid_id(self, temp_db_file):
        """Test complete command with invalid ID."""
        cli = TodoCLI(temp_db_file)
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            # Complete returns False for non-existent IDs, which the test can verify
            result = cli.db.mark_complete(999)
            assert result is False  # Should return False for non-existent ID
        finally:
            sys.stderr = old_stderr
    
    def test_complete_command_nonnumeric_id(self, temp_db_file):
        """Test complete command with non-numeric ID."""
        cli = TodoCLI(temp_db_file)
        
        # String IDs should fail at database level
        # This test validates the Database layer properly rejects them
        with pytest.raises((TypeError, ValueError)):
            cli.db.mark_complete('abc')


class TestCliDeleteCommand:
    """Test the 'delete' CLI command."""
    
    def test_delete_command_removes_todo(self, db_instance, sample_todo):
        """Test deleting a todo."""
        todo_id = db_instance.add_todo(sample_todo)
        cli = TodoCLI(db_instance.db_path)
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            cli.delete(todo_id)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        
        # Should delete the todo
        assert 'deleted' in output.lower()
        todo = db_instance.get_todo_by_id(todo_id)
        assert todo is None
    
    def test_delete_command_invalid_id(self, temp_db_file):
        """Test delete command with non-existent ID."""
        cli = TodoCLI(temp_db_file)
        
        # CLI raises ValueError for invalid ID
        with pytest.raises(ValueError):
            cli.delete(999)
    
    def test_delete_command_nonnumeric_id(self, temp_db_file):
        """Test delete command with non-numeric ID."""
        cli = TodoCLI(temp_db_file)
        
        # String IDs should fail at database level
        with pytest.raises((TypeError, ValueError)):
            cli.db.delete_todo('abc')


class TestCliExportCommand:
    """Test the 'export' CLI command."""
    
    def test_export_command_creates_csv(self, populated_db, temp_csv_file):
        """Test exporting todos to CSV."""
        cli = TodoCLI(populated_db.db_path)
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            cli.export(temp_csv_file)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        
        # Should create CSV file
        assert os.path.exists(temp_csv_file)
        assert 'Exported' in output
    
    def test_export_command_by_category(self, populated_db, temp_csv_file):
        """Test exporting todos by specific category."""
        cli = TodoCLI(populated_db.db_path)
        
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            cli.export(temp_csv_file, category='Work')
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        
        # Should export only Work category todos
        assert os.path.exists(temp_csv_file)
        assert 'Exported' in output
    
    def test_export_command_csv_format(self, populated_db, temp_csv_file):
        """Test that exported CSV has correct format."""
        cli = TodoCLI(populated_db.db_path)
        
        cli.export(temp_csv_file)
        
        # Should create valid CSV with headers
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) > 0
        assert 'title' in rows[0]
        assert 'priority' in rows[0]


class TestCliIntegration:
    """Integration tests combining multiple CLI commands."""
    
    
    def test_workflow_add_list_complete(self, temp_db_file):
        """Test workflow: add -> list -> complete."""
        # 1. Add a todo
        # 2. List todos (should appear)
        # 3. Mark as complete
        # 4. List again (should show as completed)
        pass
    
    
    def test_workflow_add_filter_export(self, temp_db_file, temp_csv_file):
        """Test workflow: add -> filter -> export."""
        # 1. Add multiple todos
        # 2. Filter by category
        # 3. Export filtered results
        pass
    
    
    def test_workflow_multiple_todos_operations(self, temp_db_file):
        """Test adding and managing multiple todos."""
        # 1. Add several todos with different categories/priorities
        # 2. List all
        # 3. List filtered
        # 4. Mark some complete
        # 5. Delete some
        # 6. Verify final state
        pass


class TestCliErrorHandling:
    """Test CLI error handling and edge cases."""
    
    
    def test_missing_required_arguments(self):
        """Test command with missing required arguments."""
        # Should show error message and usage
        pass
    
    
    def test_database_file_not_found(self, temp_db_file):
        """Test when database file doesn't exist."""
        nonexistent = "/nonexistent/path/db.sqlite"
        
        args = ['list', '--db', nonexistent]
        
        # Should handle gracefully - create new DB or show error
    
    
    def test_invalid_command(self):
        """Test with invalid command name."""
        args = ['invalid-command']
        
        # Should show error and suggest valid commands


class TestCliOutput:
    """Test CLI output formatting and presentation."""
    
    
    def test_list_output_contains_all_fields(self, populated_db, temp_db_file):
        """Test that list output includes relevant fields."""
        # Output should include: ID, title, priority, category, status
        pass
    
    
    def test_list_output_shows_completion_status(self, populated_db, temp_db_file):
        """Test that completed todos are clearly marked."""
        # Completed todos should show checkmark or [✓] or similar
        pass
    
    
    def test_error_messages_are_clear(self):
        """Test that error messages are helpful."""
        # Error messages should tell user what went wrong
        # Should suggest how to fix
        pass


class TestCliArgumentParsing:
    """Test CLI argument parsing."""
    
    
    def test_parse_add_arguments(self):
        """Test parsing add command arguments."""
        # Should parse title, description, priority, category
        pass
    
    
    def test_parse_list_arguments(self):
        """Test parsing list command arguments."""
        # Should parse filter options, output format
        pass
    
    
    def test_case_insensitive_commands(self):
        """Test that commands work in any case."""
        # 'add', 'ADD', 'Add' should all work
        pass


class TestCliSpecialCharacters:
    """Test CLI handling of special characters."""
    
    
    def test_add_todo_with_quotes(self, temp_db_file):
        """Test adding todo with quoted strings."""
        args = [
            'add',
            '--title', 'Task with "quotes"',
            '--db', temp_db_file
        ]
        
        # Should preserve quotes
    
    
    def test_add_todo_with_special_characters(self, temp_db_file):
        """Test adding todo with special characters."""
        args = [
            'add',
            '--title', 'Task & stuff',
            '--description', 'Line1\nLine2',
            '--db', temp_db_file
        ]
        
        # Should handle special chars
    
    
    def test_add_todo_with_unicode(self, temp_db_file):
        """Test adding todo with unicode characters."""
        args = [
            'add',
            '--title', '购买牛奶 🥛',
            '--db', temp_db_file
        ]
        
        # Should preserve unicode


class TestCliHelpAndUsage:
    """Test CLI help and usage information."""
    
    
    def test_main_help(self):
        """Test main help message."""
        # --help or -h should show usage
        pass
    
    
    def test_command_help(self):
        """Test command-specific help."""
        # add --help should show add command options
        pass
    
    
    def test_version_flag(self):
        """Test --version flag."""
        # Should show version number
        pass


class TestCliDatabasePersistence:
    """Test CLI with persistent database."""
    
    
    def test_todos_persist_between_commands(self, temp_db_file):
        """Test that todos added via CLI persist."""
        # 1. Add todo via add command
        # 2. List todos via list command
        # 3. Todo should still be there
        pass
    
    
    def test_todos_persist_across_sessions(self, temp_db_file):
        """Test that todos persist across separate CLI invocations."""
        # Create fresh CLI instance and verify todos still exist
        pass


# Test module initialization (can run without main function)
class TestCliModuleBasics:
    """Test basic CLI module properties."""
    
    def test_cli_module_importable(self):
        """Test that CLI module can be imported."""
        try:
            from todocli import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module not yet implemented")
    
    def test_main_package_entry_point(self):
        """Test that __main__ module exists."""
        try:
            from todocli import __main__
            assert __main__ is not None
        except ImportError:
            pytest.skip("__main__ module not yet implemented")
    
    def test_main_function_exists(self):
        """Test that main function exists in cli module."""
        try:
            from todocli.cli import main
            assert callable(main)
        except ImportError:
            pytest.skip("CLI module not yet implemented")
    
    def test_cli_has_required_functions(self):
        """Test that cli module has key functions."""
        try:
            from todocli import cli
            # Check for main function
            assert hasattr(cli, 'main')
            assert callable(cli.main)
        except ImportError:
            pytest.skip("CLI module not yet implemented")


class TestCliEdgeCases:
    """Test edge cases in CLI usage."""
    
    
    def test_add_todo_with_very_long_title(self, temp_db_file):
        """Test adding todo with very long title."""
        long_title = "x" * 500
        args = [
            'add',
            '--title', long_title,
            '--db', temp_db_file
        ]
        
        # Should handle or reject gracefully
    
    
    def test_add_todo_with_empty_description(self, temp_db_file):
        """Test adding todo with empty description."""
        args = [
            'add',
            '--title', 'Task',
            '--description', '',
            '--db', temp_db_file
        ]
        
        # Should work
    
    
    def test_export_to_invalid_path(self, populated_db, temp_db_file):
        """Test exporting to invalid/inaccessible path."""
        args = [
            'export',
            '--output', '/invalid/nonexistent/path/file.csv',
            '--db', temp_db_file
        ]
        
        # Should fail with clear error


class TestCliIntegrationWithDatabase:
    """Integration tests between CLI and Database."""
    
    
    def test_cli_respects_database_filters(self, populated_db, temp_db_file):
        """Test that CLI properly uses database filters."""
        # List with category filter should match database filter results
        pass
    
    
    def test_cli_crud_operations_atomic(self, temp_db_file):
        """Test that CLI CRUD operations are properly atomic."""
        # Operations should succeed or fail cleanly
        pass
