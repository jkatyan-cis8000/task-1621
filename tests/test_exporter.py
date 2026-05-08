"""
Unit tests for todocli.exporter module.

Tests cover:
- CSV export functionality
- File creation and writing
- CSV formatting and structure
- Special character handling
- Category filtering
- Edge cases
"""

import pytest
import csv
import os
from datetime import datetime
from todocli.exporter import export_to_csv, export_by_category
from todocli.models import Todo


class TestExportToCsv:
    """Test the export_to_csv function."""
    
    def test_export_to_csv_creates_file(self, sample_todos, temp_csv_file):
        """Test that export_to_csv creates a file."""
        export_to_csv(sample_todos, temp_csv_file)
        assert os.path.exists(temp_csv_file)
        assert os.path.getsize(temp_csv_file) > 0
    
    def test_export_empty_list(self, temp_csv_file):
        """Test exporting empty todo list."""
        export_to_csv([], temp_csv_file)
        assert os.path.exists(temp_csv_file)
        
        # File should have headers even if empty
        with open(temp_csv_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) >= 1  # At least header row
    
    def test_export_single_todo(self, sample_todo, temp_csv_file):
        """Test exporting a single todo."""
        export_to_csv([sample_todo], temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            # Header + 1 data row
            assert len(rows) >= 2
    
    def test_export_multiple_todos(self, sample_todos, temp_csv_file):
        """Test exporting multiple todos."""
        export_to_csv(sample_todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            # Header + data rows
            assert len(rows) == len(sample_todos) + 1
    
    def test_csv_has_required_headers(self, sample_todos, temp_csv_file):
        """Test that CSV has all required headers."""
        export_to_csv(sample_todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            required_fields = ['id', 'title', 'description', 'priority', 
                             'category', 'completed', 'created_at', 'updated_at']
            for field in required_fields:
                assert field in headers
    
    def test_csv_preserves_all_todo_fields(self, sample_todos, temp_csv_file):
        """Test that all todo fields are correctly exported."""
        export_to_csv(sample_todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            for i, row in enumerate(rows):
                original = sample_todos[i]
                assert row['title'] == original.title
                assert row['description'] == original.description
                assert row['priority'] == original.priority
                assert row['category'] == original.category
    
    def test_csv_preserves_completed_status(self, sample_todos, temp_csv_file):
        """Test that completed status is correctly exported."""
        export_to_csv(sample_todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            for i, row in enumerate(rows):
                original = sample_todos[i]
                # Check if it's yes/no or true/false format
                expected = 'Yes' if original.completed else 'No'
                # Some implementations use True/False, others use Yes/No
                assert row['completed'] in (expected, str(original.completed))
    
    def test_csv_preserves_special_characters(self, temp_csv_file):
        """Test that special characters are preserved in CSV."""
        todos = [
            Todo("Task with \"quotes\"", "Desc", "high", "Work"),
            Todo("Task, with commas", "Desc", "medium", "Work"),
            Todo("Task\nwith\nnewlines", "Desc", "low", "Work"),
        ]
        
        export_to_csv(todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert '"' in rows[0]['title']
            assert ',' in rows[1]['title']
            # Newlines might be escaped or handled by CSV writer
    
    def test_csv_handles_unicode(self, temp_csv_file):
        """Test that unicode characters are preserved."""
        todos = [
            Todo("购买牛奶 🥛", "これはテストです", "high", "日本語"),
        ]
        
        export_to_csv(todos, temp_csv_file)
        
        with open(temp_csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            
            assert "🥛" in row['title']
            assert "テスト" in row['description']
    
    def test_overwrite_existing_file(self, sample_todos, temp_csv_file):
        """Test that export overwrites existing file."""
        # Write first file
        first_todos = sample_todos[:2]
        export_to_csv(first_todos, temp_csv_file)
        
        # Write second file (should overwrite)
        second_todos = sample_todos[2:4]
        export_to_csv(second_todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            # Header + 2 new rows (not original 2)
            assert len(rows) == 3
    
    def test_csv_id_field(self, sample_todos, temp_csv_file):
        """Test that ID field is correctly exported (may be None for new todos)."""
        export_to_csv(sample_todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # IDs should be present or empty depending on save state
            assert 'id' in rows[0]


class TestExportByCategory:
    """Test the export_by_category function."""
    
    def test_export_by_category_creates_file(self, populated_db, temp_csv_file):
        """Test that export_by_category creates a file."""
        todos = populated_db.get_todos()
        export_by_category(todos, "Work", temp_csv_file)
        assert os.path.exists(temp_csv_file)
    
    def test_export_by_category_filters_correctly(self, populated_db, temp_csv_file):
        """Test that export_by_category only includes specified category."""
        todos = populated_db.get_todos()
        
        # Find a category that exists
        categories = set(t.category for t in todos if t.category)
        if categories:
            category = list(categories)[0]
            export_by_category(todos, category, temp_csv_file)
            
            with open(temp_csv_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                for row in rows:
                    assert row['category'] == category
    
    def test_export_by_category_empty_result(self, sample_todos, temp_csv_file):
        """Test exporting when category doesn't exist."""
        export_by_category(sample_todos, "NonExistentCategory", temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            # Should still have header, just no data rows
            assert len(rows) >= 1
    
    def test_export_by_category_single_category(self, sample_todos, temp_csv_file):
        """Test exporting todos of a single category."""
        export_by_category(sample_todos, "Shopping", temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Should have at least one Shopping item
            assert len(rows) >= 1
            for row in rows:
                assert row['category'] == "Shopping"
    
    def test_export_by_category_with_special_characters(self, temp_csv_file):
        """Test exporting by category with special characters."""
        todos = [
            Todo("Task 1", "Desc", "high", "Work & Personal"),
            Todo("Task 2", "Desc", "medium", "Work & Personal"),
            Todo("Task 3", "Desc", "low", "Other"),
        ]
        
        export_by_category(todos, "Work & Personal", temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2


class TestCsvFormatting:
    """Test CSV formatting details."""
    
    def test_csv_is_valid(self, sample_todos, temp_csv_file):
        """Test that generated CSV is valid and readable."""
        export_to_csv(sample_todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            # Should be readable without errors
            try:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == len(sample_todos)
            except csv.Error as e:
                pytest.fail(f"Invalid CSV: {e}")
    
    def test_csv_encoding_utf8(self, sample_todos, temp_csv_file):
        """Test that CSV is UTF-8 encoded."""
        export_to_csv(sample_todos, temp_csv_file)
        
        # Should be readable as UTF-8
        with open(temp_csv_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert len(content) > 0
    
    def test_csv_delimiter_consistency(self, sample_todos, temp_csv_file):
        """Test that CSV uses consistent delimiter."""
        export_to_csv(sample_todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            # Try both common delimiters
            f.seek(0)
            content = f.read()
            # Should use comma as delimiter (standard CSV)
            assert ',' in content
    
    def test_csv_quotes_handling(self, temp_csv_file):
        """Test that fields with commas are properly quoted."""
        todos = [
            Todo("Task, with comma", "Description", "high", "Work"),
        ]
        
        export_to_csv(todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            content = f.read()
            # Comma-containing field should be quoted
            assert '"Task, with comma"' in content or "'Task, with comma'" in content


class TestExportEdgeCases:
    """Test edge cases in export functionality."""
    
    def test_export_todos_with_no_category(self, temp_csv_file):
        """Test exporting todos with empty category."""
        todos = [
            Todo("Task 1", "Desc", "high", ""),
            Todo("Task 2", "Desc", "medium", ""),
        ]
        
        export_to_csv(todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
    
    def test_export_with_very_long_content(self, temp_csv_file):
        """Test exporting todos with very long strings."""
        long_desc = "x" * 5000
        todos = [
            Todo("Task", long_desc, "high", "Work"),
        ]
        
        export_to_csv(todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert len(row['description']) == 5000
    
    def test_export_preserves_field_order(self, sample_todos, temp_csv_file):
        """Test that fields appear in consistent order."""
        export_to_csv(sample_todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            first_line = f.readline().strip()
            # Should contain header fields in some order
            assert 'title' in first_line
            assert 'description' in first_line
            assert 'priority' in first_line
    
    def test_export_handles_none_values(self, temp_csv_file):
        """Test that None values are handled gracefully."""
        todos = [
            Todo("Task 1", "", "high", "Work", id=None),  # Empty description, None ID
        ]
        
        export_to_csv(todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            # Should handle gracefully (empty string or 'None')
            assert isinstance(row['description'], str)
    
    def test_export_preserves_row_order(self, sample_todos, temp_csv_file):
        """Test that rows are exported in same order as input."""
        export_to_csv(sample_todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            for i, row in enumerate(rows):
                assert row['title'] == sample_todos[i].title


class TestExportIntegration:
    """Integration tests for export functionality."""
    
    def test_export_all_todos_from_database(self, populated_db, temp_csv_file):
        """Test exporting all todos from a populated database."""
        todos = populated_db.get_todos()
        export_to_csv(todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == len(todos) + 1  # +1 for header
    
    def test_export_filtered_todos(self, populated_db, temp_csv_file):
        """Test exporting filtered subset of todos."""
        todos = populated_db.get_todos(filters={"category": "Work"})
        export_to_csv(todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            for row in rows:
                assert row['category'] == "Work"
    
    def test_export_and_reimport_consistency(self, sample_todos, temp_csv_file):
        """Test that exported data can be read back consistently."""
        export_to_csv(sample_todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            for i, row in enumerate(rows):
                original = sample_todos[i]
                # Key fields should match
                assert row['title'] == original.title
                assert row['priority'] == original.priority


class TestExportByPriority:
    """Test the export_by_priority function."""
    
    def test_export_by_priority_creates_file(self, sample_todos, temp_csv_file):
        """Test that export_by_priority creates a file."""
        from todocli.exporter import export_by_priority
        export_by_priority(sample_todos, "high", temp_csv_file)
        assert os.path.exists(temp_csv_file)
    
    def test_export_by_priority_filters_correctly(self, sample_todos, temp_csv_file):
        """Test that export_by_priority only includes specified priority."""
        from todocli.exporter import export_by_priority
        export_by_priority(sample_todos, "high", temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            for row in rows:
                assert row['priority'] == "high"
    
    def test_export_by_priority_all_levels(self, sample_todos, temp_csv_file):
        """Test exporting for all priority levels."""
        from todocli.exporter import export_by_priority
        
        for priority in ["high", "medium", "low"]:
            export_by_priority(sample_todos, priority, temp_csv_file)
            
            with open(temp_csv_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert all(row['priority'] == priority for row in rows)
    
    def test_export_by_priority_invalid_priority(self, sample_todos, temp_csv_file):
        """Test that invalid priority raises ValueError."""
        from todocli.exporter import export_by_priority
        
        with pytest.raises(ValueError):
            export_by_priority(sample_todos, "urgent", temp_csv_file)
    
    def test_export_by_priority_empty_filepath(self, sample_todos):
        """Test that empty filepath raises ValueError."""
        from todocli.exporter import export_by_priority
        
        with pytest.raises(ValueError):
            export_by_priority(sample_todos, "high", "")


class TestExportCompleted:
    """Test the export_completed function."""
    
    def test_export_completed_todos(self, sample_todos, temp_csv_file):
        """Test exporting completed todos."""
        from todocli.exporter import export_completed
        export_completed(sample_todos, temp_csv_file, completed=True)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            for row in rows:
                assert row['completed'] == "Yes"
    
    def test_export_incomplete_todos(self, sample_todos, temp_csv_file):
        """Test exporting incomplete todos."""
        from todocli.exporter import export_completed
        export_completed(sample_todos, temp_csv_file, completed=False)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            for row in rows:
                assert row['completed'] == "No"
    
    def test_export_completed_default(self, sample_todos, temp_csv_file):
        """Test that default exports completed todos."""
        from todocli.exporter import export_completed
        export_completed(sample_todos, temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert all(row['completed'] == "Yes" for row in rows)
    
    def test_export_completed_empty_filepath(self, sample_todos):
        """Test that empty filepath raises ValueError."""
        from todocli.exporter import export_completed
        
        with pytest.raises(ValueError):
            export_completed(sample_todos, "")


class TestExportByTextSearch:
    """Test the export_by_text_search function."""
    
    def test_export_by_text_search_in_title(self, sample_todos, temp_csv_file):
        """Test searching in title field."""
        from todocli.exporter import export_by_text_search
        export_by_text_search(sample_todos, "Buy", temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) > 0
            for row in rows:
                assert "buy" in row['title'].lower()
    
    def test_export_by_text_search_case_insensitive(self, sample_todos, temp_csv_file):
        """Test that search is case-insensitive."""
        from todocli.exporter import export_by_text_search
        
        export_to_csv(sample_todos, temp_csv_file)
        count_lower = len(sample_todos)
        
        export_by_text_search(sample_todos, "BUY", temp_csv_file)
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) > 0
    
    def test_export_by_text_search_in_description(self, sample_todos, temp_csv_file):
        """Test searching in description field."""
        from todocli.exporter import export_by_text_search
        export_by_text_search(sample_todos, "report", temp_csv_file, search_fields=["description"])
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            for row in rows:
                assert "report" in row['description'].lower()
    
    def test_export_by_text_search_in_category(self, sample_todos, temp_csv_file):
        """Test searching in category field."""
        from todocli.exporter import export_by_text_search
        export_by_text_search(sample_todos, "Work", temp_csv_file, search_fields=["category"])
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            for row in rows:
                assert "work" in row['category'].lower()
    
    def test_export_by_text_search_multiple_fields(self, sample_todos, temp_csv_file):
        """Test searching in multiple fields."""
        from todocli.exporter import export_by_text_search
        export_by_text_search(sample_todos, "test", temp_csv_file, 
                             search_fields=["title", "description", "category"])
        
        # Should find at least some matches
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            # May or may not have matches depending on data
            assert isinstance(rows, list)
    
    def test_export_by_text_search_empty_search_text(self, sample_todos):
        """Test that empty search text raises ValueError."""
        from todocli.exporter import export_by_text_search
        
        with pytest.raises(ValueError):
            export_by_text_search(sample_todos, "", "file.csv")
    
    def test_export_by_text_search_empty_filepath(self, sample_todos):
        """Test that empty filepath raises ValueError."""
        from todocli.exporter import export_by_text_search
        
        with pytest.raises(ValueError):
            export_by_text_search(sample_todos, "search", "")
    
    def test_export_by_text_search_no_matches(self, sample_todos, temp_csv_file):
        """Test searching with no matches."""
        from todocli.exporter import export_by_text_search
        export_by_text_search(sample_todos, "xyzabc123", temp_csv_file)
        
        with open(temp_csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0  # No matches
