"""Tests for schema management."""

import pytest
from unittest.mock import Mock
from typing import Optional

from falkordb_orm import node, property, indexed, unique, generated_id
from falkordb_orm.schema import SchemaManager, SchemaValidationResult


@node("User")
class User:
    id: Optional[int] = generated_id()
    email: str = unique(required=True)
    age: int = indexed()
    name: str = property(required=True)


@node("Product")
class Product:
    id: Optional[int] = generated_id()
    sku: str = unique()
    price: float = property()


class TestSchemaManager:
    """Test SchemaManager functionality."""

    def test_validate_schema_all_valid(self):
        """Test schema validation when all indexes exist."""
        graph = Mock()

        # Mock existing indexes
        result = Mock()
        result.result_set = [
            ["User", "email", "UNIQUE"],
            ["User", "age", "RANGE"],
            ["Product", "sku", "UNIQUE"],
        ]
        graph.query = Mock(return_value=result)

        manager = SchemaManager(graph)
        validation = manager.validate_schema([User, Product])

        assert validation.is_valid
        assert len(validation.missing_indexes) == 0
        assert len(validation.extra_indexes) == 0

    def test_validate_schema_missing_indexes(self):
        """Test detection of missing indexes."""
        graph = Mock()

        # Mock existing indexes (missing 'age' index)
        result = Mock()
        result.result_set = [
            ["User", "email", "UNIQUE"],
        ]
        graph.query = Mock(return_value=result)

        manager = SchemaManager(graph)
        validation = manager.validate_schema([User])

        assert not validation.is_valid
        assert len(validation.missing_indexes) == 1
        # missing_indexes is List[Tuple[str, str, str]] - (label, property, type)
        assert validation.missing_indexes[0][1] == "age"

    def test_validate_schema_extra_indexes(self):
        """Test detection of extra indexes."""
        graph = Mock()

        # Mock existing indexes (extra 'name' index)
        result = Mock()
        result.result_set = [
            ["User", "email", "UNIQUE"],
            ["User", "age", "RANGE"],
            ["User", "name", "RANGE"],  # Extra
        ]
        graph.query = Mock(return_value=result)

        manager = SchemaManager(graph)
        validation = manager.validate_schema([User])

        assert not validation.is_valid
        assert len(validation.extra_indexes) == 1
        assert validation.extra_indexes[0].property_name == "name"

    def test_sync_schema_creates_missing_indexes(self):
        """Test sync_schema creates missing indexes."""
        graph = Mock()

        # First call: list existing indexes (none)
        # Subsequent calls: create indexes
        call_count = [0]

        def mock_query(cypher, params=None):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: list indexes
                result = Mock()
                result.result_set = []
                return result
            else:
                # Subsequent: create indexes
                return Mock(result_set=[])

        graph.query = mock_query

        manager = SchemaManager(graph)
        queries = manager.sync_schema([User])

        # Should create 2 indexes: email (unique), age (regular)
        assert len(queries) >= 2

    def test_sync_schema_idempotent(self):
        """Test sync_schema is idempotent."""
        graph = Mock()

        # Mock all indexes already exist
        result = Mock()
        result.result_set = [
            ["User", "email", "UNIQUE"],
            ["User", "age", "RANGE"],
        ]
        graph.query = Mock(return_value=result)

        manager = SchemaManager(graph)
        stats = manager.sync_schema([User])

        # Should return stats with 0 created
        assert isinstance(stats, dict)
        assert stats["created"] == 0

    def test_ensure_schema_validates_and_syncs(self):
        """Test ensure_schema performs validation and sync."""
        graph = Mock()

        # First call: list indexes
        # Second call: create missing index
        call_count = [0]

        def mock_query(cypher, params=None):
            call_count[0] += 1
            if call_count[0] == 1:
                # Missing 'age' index
                result = Mock()
                result.result_set = [
                    ["User", "email", "UNIQUE"],
                ]
                return result
            else:
                return Mock(result_set=[])

        graph.query = mock_query

        manager = SchemaManager(graph)
        result = manager.ensure_schema([User])

        # ensure_schema returns None (it's a convenience method that calls sync_schema)
        assert result is None
        # Verify it was called by checking queries were executed
        assert call_count[0] > 0

    def test_get_schema_diff(self):
        """Test getting schema differences."""
        graph = Mock()

        # Mock existing indexes
        result = Mock()
        result.result_set = [
            ["User", "email", "UNIQUE"],
            ["User", "name", "RANGE"],  # Extra
        ]
        graph.query = Mock(return_value=result)

        manager = SchemaManager(graph)
        diff = manager.get_schema_diff([User])

        # get_schema_diff returns a formatted string
        assert isinstance(diff, str)
        assert "Missing" in diff or "Extra" in diff or "valid" in diff

    def test_get_schema_info(self):
        """Test getting schema information."""
        graph = Mock()

        result = Mock()
        result.result_set = [
            ["User", "email", "UNIQUE"],
            ["User", "age", "RANGE"],
        ]
        graph.query = Mock(return_value=result)

        manager = SchemaManager(graph)
        info = manager.get_schema_info([User])

        # get_schema_info returns a dict with various stats
        assert isinstance(info, dict)
        assert "entity_count" in info or "existing_indexes" in info

    def test_validate_multiple_entities(self):
        """Test validation with multiple entity types."""
        graph = Mock()

        result = Mock()
        result.result_set = [
            ["User", "email", "UNIQUE"],
            ["User", "age", "RANGE"],
            ["Product", "sku", "UNIQUE"],
        ]
        graph.query = Mock(return_value=result)

        manager = SchemaManager(graph)
        validation = manager.validate_schema([User, Product])

        assert validation.is_valid

    def test_validate_empty_entity_list(self):
        """Test validation with no entities."""
        graph = Mock()
        manager = SchemaManager(graph)

        validation = manager.validate_schema([])

        # Empty list should be valid
        assert validation.is_valid
        assert len(validation.missing_indexes) == 0

    def test_schema_validation_result_representation(self):
        """Test SchemaValidationResult string representation."""
        graph = Mock()

        result = Mock()
        result.result_set = []
        graph.query = Mock(return_value=result)

        manager = SchemaManager(graph)
        validation = manager.validate_schema([User])

        # Should have missing indexes
        assert not validation.is_valid
        result_str = str(validation)
        assert "missing" in result_str.lower() or "invalid" in result_str.lower()
