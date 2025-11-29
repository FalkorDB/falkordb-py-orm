"""Tests for index management."""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Optional

from falkordb_orm import node, property, indexed, unique, generated_id
from falkordb_orm.indexes import IndexManager, IndexInfo
from falkordb_orm.exceptions import QueryException


@node("TestPerson")
class TestPerson:
    id: Optional[int] = generated_id()
    email: str = unique(required=True)
    age: int = indexed()
    name: str = property()


@node("TestProduct")
class TestProduct:
    id: Optional[int] = generated_id()
    sku: str = unique()
    category: str = indexed()
    price: float = indexed()
    name: str = property()


class TestIndexManager:
    """Test IndexManager functionality."""

    def test_create_indexes_for_entity(self):
        """Test creating all indexes for an entity."""
        graph = Mock()
        graph.query = Mock(return_value=Mock(result_set=[]))

        manager = IndexManager(graph)
        queries = manager.create_indexes(TestPerson, if_not_exists=True)

        # Should create indexes for email (unique) and age (indexed)
        assert len(queries) >= 2
        assert any("email" in q for q in queries)
        assert any("age" in q for q in queries)

    def test_create_unique_constraint(self):
        """Test unique constraint creation."""
        graph = Mock()
        graph.query = Mock(return_value=Mock(result_set=[]))

        manager = IndexManager(graph)
        queries = manager.create_indexes(TestPerson, if_not_exists=True)

        # Check that unique constraint query is generated
        unique_query = [q for q in queries if "UNIQUE" in q and "email" in q]
        assert len(unique_query) == 1
        assert "CONSTRAINT" in unique_query[0]

    def test_create_regular_index(self):
        """Test regular index creation."""
        graph = Mock()
        graph.query = Mock(return_value=Mock(result_set=[]))

        manager = IndexManager(graph)
        queries = manager.create_indexes(TestPerson, if_not_exists=True)

        # Check that regular index query is generated
        index_query = [q for q in queries if "age" in q and "UNIQUE" not in q]
        assert len(index_query) >= 1

    def test_drop_indexes(self):
        """Test dropping indexes."""
        graph = Mock()
        graph.query = Mock(return_value=Mock(result_set=[]))

        manager = IndexManager(graph)
        queries = manager.drop_indexes(TestPerson)

        # Should drop both email and age indexes
        assert len(queries) >= 2
        assert all("DROP INDEX" in q for q in queries)

    def test_ensure_indexes_idempotent(self):
        """Test ensure_indexes is idempotent."""
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params=None):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call succeeds
                return Mock(result_set=[])
            else:
                # Second call would fail (index exists) but is ignored
                raise Exception("Index already exists")

        graph.query = mock_query

        manager = IndexManager(graph)

        # First call should succeed
        queries1 = manager.ensure_indexes(TestPerson)
        assert len(queries1) >= 2

        # Second call should not raise error
        queries2 = manager.ensure_indexes(TestPerson)
        assert len(queries2) >= 2

    def test_list_indexes(self):
        """Test listing indexes."""
        graph = Mock()

        # Mock db.indexes() result
        result = Mock()
        result.result_set = [
            ["TestPerson", "email", "UNIQUE"],
            ["TestPerson", "age", "RANGE"],
        ]
        graph.query = Mock(return_value=result)

        manager = IndexManager(graph)
        indexes = manager.list_indexes(TestPerson)

        assert len(indexes) == 2
        assert any(idx.property_name == "email" and idx.is_unique for idx in indexes)
        assert any(idx.property_name == "age" and not idx.is_unique for idx in indexes)

    def test_list_indexes_filters_by_entity(self):
        """Test list_indexes filters by entity class."""
        graph = Mock()

        # Mock result with multiple entities
        result = Mock()
        result.result_set = [
            ["TestPerson", "email", "UNIQUE"],
            ["TestProduct", "sku", "UNIQUE"],
        ]
        graph.query = Mock(return_value=result)

        manager = IndexManager(graph)
        indexes = manager.list_indexes(TestPerson)

        # Should only return TestPerson indexes
        assert len(indexes) == 1
        assert indexes[0].label == "TestPerson"

    def test_create_index_for_property_manual(self):
        """Test manual index creation for specific property."""
        graph = Mock()
        graph.query = Mock(return_value=Mock(result_set=[]))

        manager = IndexManager(graph)
        query = manager.create_index_for_property("Person", "last_name")

        assert "Person" in query
        assert "last_name" in query
        assert graph.query.called

    def test_create_unique_constraint_manual(self):
        """Test manual unique constraint creation."""
        graph = Mock()
        graph.query = Mock(return_value=Mock(result_set=[]))

        manager = IndexManager(graph)
        query = manager.create_index_for_property("Person", "ssn", unique=True)

        assert "Person" in query
        assert "ssn" in query
        assert "UNIQUE" in query

    def test_drop_index_for_property(self):
        """Test dropping specific index."""
        graph = Mock()
        graph.query = Mock(return_value=Mock(result_set=[]))

        manager = IndexManager(graph)
        query = manager.drop_index_for_property("Person", "email")

        assert "DROP INDEX" in query
        assert "Person" in query
        assert "email" in query

    def test_index_creation_failure(self):
        """Test error handling in index creation."""
        graph = Mock()
        graph.query = Mock(side_effect=Exception("Index creation failed"))

        manager = IndexManager(graph)

        with pytest.raises(QueryException):
            manager.create_indexes(TestPerson, if_not_exists=False)

    def test_multiple_indexes_per_entity(self):
        """Test entity with multiple indexed properties."""
        graph = Mock()
        graph.query = Mock(return_value=Mock(result_set=[]))

        manager = IndexManager(graph)
        queries = manager.create_indexes(TestProduct, if_not_exists=True)

        # TestProduct has 3 indexed fields: sku (unique), category, price
        assert len(queries) >= 3

    def test_no_indexes_for_non_decorated_class(self):
        """Test error when class is not decorated."""
        graph = Mock()
        manager = IndexManager(graph)

        class NotAnEntity:
            name: str

        with pytest.raises(ValueError, match="not a decorated entity"):
            manager.create_indexes(NotAnEntity)
