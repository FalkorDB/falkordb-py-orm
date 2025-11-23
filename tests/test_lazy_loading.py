"""Tests for lazy loading of relationships."""

import pytest
from typing import List, Optional
from unittest.mock import Mock, MagicMock

from falkordb_orm.decorators import node, generated_id, relationship
from falkordb_orm.relationships import LazyList, LazySingle, create_lazy_proxy
from falkordb_orm.metadata import RelationshipMetadata, get_entity_metadata
from falkordb_orm.mapper import EntityMapper
from falkordb_orm.query_builder import QueryBuilder


@node("Person")
class Person:
    id: Optional[int] = generated_id()
    name: str
    friends: List["Person"] = relationship("KNOWS", target="Person")


@node("Company")
class Company:
    id: Optional[int] = generated_id()
    name: str


@node("Employee")
class Employee:
    id: Optional[int] = generated_id()
    name: str
    company: Optional[Company] = relationship("WORKS_FOR", target=Company)


class TestLazyList:
    """Tests for LazyList proxy."""

    def test_lazy_list_creation(self):
        """Test creating a LazyList proxy."""
        graph = Mock()
        mapper = Mock()
        query_builder = Mock()

        rel_meta = RelationshipMetadata(
            python_name="friends",
            relationship_type="KNOWS",
            direction="OUTGOING",
            target_class=Person,
            is_collection=True,
            lazy=True,
        )

        lazy_list = LazyList(
            graph=graph,
            source_id=1,
            relationship_meta=rel_meta,
            entity_class=Person,
            mapper=mapper,
            query_builder=query_builder,
        )

        assert lazy_list._loaded is False
        assert len(lazy_list._items) == 0

    def test_lazy_list_loads_on_iteration(self):
        """Test that LazyList loads data on first iteration."""
        graph = Mock()
        mapper = Mock()
        query_builder = Mock()

        # Setup mock data
        mock_record = Mock()
        mock_result = Mock()
        mock_result.result_set = [mock_record]
        graph.query.return_value = mock_result

        # Mock person
        mock_person = Person(name="Alice")
        mock_person.id = 2
        mapper.map_from_record.return_value = mock_person

        query_builder.build_relationship_load_query.return_value = (
            "MATCH (source)-[:KNOWS]->(target:Person) WHERE id(source) = $source_id RETURN target",
            {"source_id": 1},
        )

        rel_meta = RelationshipMetadata(
            python_name="friends",
            relationship_type="KNOWS",
            direction="OUTGOING",
            target_class=Person,
            is_collection=True,
            lazy=True,
        )

        lazy_list = LazyList(
            graph=graph,
            source_id=1,
            relationship_meta=rel_meta,
            entity_class=Person,
            mapper=mapper,
            query_builder=query_builder,
        )

        # Before iteration, not loaded
        assert lazy_list._loaded is False

        # Iterate
        items = list(lazy_list)

        # After iteration, loaded
        assert lazy_list._loaded is True
        assert len(items) == 1
        assert items[0].name == "Alice"

        # Query should be called once
        query_builder.build_relationship_load_query.assert_called_once()
        graph.query.assert_called_once()

    def test_lazy_list_caches_results(self):
        """Test that LazyList caches loaded data."""
        graph = Mock()
        mapper = Mock()
        query_builder = Mock()

        # Setup mock data
        mock_result = Mock()
        mock_result.result_set = []
        graph.query.return_value = mock_result

        query_builder.build_relationship_load_query.return_value = (
            "MATCH (source)-[:KNOWS]->(target:Person) WHERE id(source) = $source_id RETURN target",
            {"source_id": 1},
        )

        rel_meta = RelationshipMetadata(
            python_name="friends",
            relationship_type="KNOWS",
            direction="OUTGOING",
            target_class=Person,
            is_collection=True,
            lazy=True,
        )

        lazy_list = LazyList(
            graph=graph,
            source_id=1,
            relationship_meta=rel_meta,
            entity_class=Person,
            mapper=mapper,
            query_builder=query_builder,
        )

        # Load twice
        list(lazy_list)
        list(lazy_list)

        # Query should only be called once (cached)
        assert graph.query.call_count == 1

    def test_lazy_list_len(self):
        """Test LazyList __len__ method."""
        graph = Mock()
        mapper = Mock()
        query_builder = Mock()

        # Setup mock data with 2 records
        mock_record1 = Mock()
        mock_record2 = Mock()
        mock_result = Mock()
        mock_result.result_set = [mock_record1, mock_record2]
        graph.query.return_value = mock_result

        mock_person1 = Person(name="Alice")
        mock_person1.id = 2
        mock_person2 = Person(name="Bob")
        mock_person2.id = 3

        mapper.map_from_record.side_effect = [mock_person1, mock_person2]

        query_builder.build_relationship_load_query.return_value = (
            "MATCH (source)-[:KNOWS]->(target:Person) WHERE id(source) = $source_id RETURN target",
            {"source_id": 1},
        )

        rel_meta = RelationshipMetadata(
            python_name="friends",
            relationship_type="KNOWS",
            direction="OUTGOING",
            target_class=Person,
            is_collection=True,
            lazy=True,
        )

        lazy_list = LazyList(
            graph=graph,
            source_id=1,
            relationship_meta=rel_meta,
            entity_class=Person,
            mapper=mapper,
            query_builder=query_builder,
        )

        assert len(lazy_list) == 2

    def test_lazy_list_getitem(self):
        """Test LazyList __getitem__ method."""
        graph = Mock()
        mapper = Mock()
        query_builder = Mock()

        # Setup mock data
        mock_record = Mock()
        mock_result = Mock()
        mock_result.result_set = [mock_record]
        graph.query.return_value = mock_result

        mock_person = Person(name="Alice")
        mock_person.id = 2
        mapper.map_from_record.return_value = mock_person

        query_builder.build_relationship_load_query.return_value = (
            "MATCH (source)-[:KNOWS]->(target:Person) WHERE id(source) = $source_id RETURN target",
            {"source_id": 1},
        )

        rel_meta = RelationshipMetadata(
            python_name="friends",
            relationship_type="KNOWS",
            direction="OUTGOING",
            target_class=Person,
            is_collection=True,
            lazy=True,
        )

        lazy_list = LazyList(
            graph=graph,
            source_id=1,
            relationship_meta=rel_meta,
            entity_class=Person,
            mapper=mapper,
            query_builder=query_builder,
        )

        item = lazy_list[0]
        assert item.name == "Alice"


class TestLazySingle:
    """Tests for LazySingle proxy."""

    def test_lazy_single_creation(self):
        """Test creating a LazySingle proxy."""
        graph = Mock()
        mapper = Mock()
        query_builder = Mock()

        rel_meta = RelationshipMetadata(
            python_name="company",
            relationship_type="WORKS_FOR",
            direction="OUTGOING",
            target_class=Company,
            is_collection=False,
            lazy=True,
        )

        lazy_single = LazySingle(
            graph=graph,
            source_id=1,
            relationship_meta=rel_meta,
            entity_class=Company,
            mapper=mapper,
            query_builder=query_builder,
        )

        assert lazy_single._loaded is False
        assert lazy_single._item is None

    def test_lazy_single_loads_on_access(self):
        """Test that LazySingle loads data on first access."""
        graph = Mock()
        mapper = Mock()
        query_builder = Mock()

        # Setup mock data
        mock_record = Mock()
        mock_result = Mock()
        mock_result.result_set = [mock_record]
        graph.query.return_value = mock_result

        mock_company = Company(name="Acme Corp")
        mock_company.id = 2
        mapper.map_from_record.return_value = mock_company

        query_builder.build_relationship_load_query.return_value = (
            "MATCH (source)-[:WORKS_FOR]->(target:Company) WHERE id(source) = $source_id RETURN target",
            {"source_id": 1},
        )

        rel_meta = RelationshipMetadata(
            python_name="company",
            relationship_type="WORKS_FOR",
            direction="OUTGOING",
            target_class=Company,
            is_collection=False,
            lazy=True,
        )

        lazy_single = LazySingle(
            graph=graph,
            source_id=1,
            relationship_meta=rel_meta,
            entity_class=Company,
            mapper=mapper,
            query_builder=query_builder,
        )

        # Before access, not loaded
        assert lazy_single._loaded is False

        # Access
        item = lazy_single.get()

        # After access, loaded
        assert lazy_single._loaded is True
        assert item is not None
        assert item.name == "Acme Corp"

        # Query should be called once
        query_builder.build_relationship_load_query.assert_called_once()
        graph.query.assert_called_once()

    def test_lazy_single_caches_result(self):
        """Test that LazySingle caches loaded data."""
        graph = Mock()
        mapper = Mock()
        query_builder = Mock()

        # Setup mock data
        mock_record = Mock()
        mock_result = Mock()
        mock_result.result_set = [mock_record]
        graph.query.return_value = mock_result

        mock_company = Company(name="Acme Corp")
        mock_company.id = 2
        mapper.map_from_record.return_value = mock_company

        query_builder.build_relationship_load_query.return_value = (
            "MATCH (source)-[:WORKS_FOR]->(target:Company) WHERE id(source) = $source_id RETURN target",
            {"source_id": 1},
        )

        rel_meta = RelationshipMetadata(
            python_name="company",
            relationship_type="WORKS_FOR",
            direction="OUTGOING",
            target_class=Company,
            is_collection=False,
            lazy=True,
        )

        lazy_single = LazySingle(
            graph=graph,
            source_id=1,
            relationship_meta=rel_meta,
            entity_class=Company,
            mapper=mapper,
            query_builder=query_builder,
        )

        # Load twice
        lazy_single.get()
        lazy_single.get()

        # Query should only be called once (cached)
        assert graph.query.call_count == 1

    def test_lazy_single_empty_result(self):
        """Test LazySingle with no related entity."""
        graph = Mock()
        mapper = Mock()
        query_builder = Mock()

        # Setup empty result
        mock_result = Mock()
        mock_result.result_set = []
        graph.query.return_value = mock_result

        query_builder.build_relationship_load_query.return_value = (
            "MATCH (source)-[:WORKS_FOR]->(target:Company) WHERE id(source) = $source_id RETURN target",
            {"source_id": 1},
        )

        rel_meta = RelationshipMetadata(
            python_name="company",
            relationship_type="WORKS_FOR",
            direction="OUTGOING",
            target_class=Company,
            is_collection=False,
            lazy=True,
        )

        lazy_single = LazySingle(
            graph=graph,
            source_id=1,
            relationship_meta=rel_meta,
            entity_class=Company,
            mapper=mapper,
            query_builder=query_builder,
        )

        item = lazy_single.get()
        assert item is None
        assert bool(lazy_single) is False

    def test_lazy_single_bool(self):
        """Test LazySingle __bool__ method."""
        graph = Mock()
        mapper = Mock()
        query_builder = Mock()

        # Setup mock data
        mock_record = Mock()
        mock_result = Mock()
        mock_result.result_set = [mock_record]
        graph.query.return_value = mock_result

        mock_company = Company(name="Acme Corp")
        mock_company.id = 2
        mapper.map_from_record.return_value = mock_company

        query_builder.build_relationship_load_query.return_value = (
            "MATCH (source)-[:WORKS_FOR]->(target:Company) WHERE id(source) = $source_id RETURN target",
            {"source_id": 1},
        )

        rel_meta = RelationshipMetadata(
            python_name="company",
            relationship_type="WORKS_FOR",
            direction="OUTGOING",
            target_class=Company,
            is_collection=False,
            lazy=True,
        )

        lazy_single = LazySingle(
            graph=graph,
            source_id=1,
            relationship_meta=rel_meta,
            entity_class=Company,
            mapper=mapper,
            query_builder=query_builder,
        )

        assert bool(lazy_single) is True


class TestCreateLazyProxy:
    """Tests for create_lazy_proxy helper function."""

    def test_create_lazy_proxy_for_collection(self):
        """Test creating proxy for collection relationship."""
        graph = Mock()
        mapper = Mock()
        query_builder = Mock()

        rel_meta = RelationshipMetadata(
            python_name="friends",
            relationship_type="KNOWS",
            direction="OUTGOING",
            target_class=Person,
            is_collection=True,
            lazy=True,
        )

        proxy = create_lazy_proxy(
            graph=graph,
            source_id=1,
            relationship_meta=rel_meta,
            entity_class=Person,
            mapper=mapper,
            query_builder=query_builder,
        )

        assert isinstance(proxy, LazyList)

    def test_create_lazy_proxy_for_single(self):
        """Test creating proxy for single relationship."""
        graph = Mock()
        mapper = Mock()
        query_builder = Mock()

        rel_meta = RelationshipMetadata(
            python_name="company",
            relationship_type="WORKS_FOR",
            direction="OUTGOING",
            target_class=Company,
            is_collection=False,
            lazy=True,
        )

        proxy = create_lazy_proxy(
            graph=graph,
            source_id=1,
            relationship_meta=rel_meta,
            entity_class=Company,
            mapper=mapper,
            query_builder=query_builder,
        )

        assert isinstance(proxy, LazySingle)
