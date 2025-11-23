"""Tests for query builder module."""

from typing import Optional

from falkordb_orm.decorators import node, generated_id
from falkordb_orm.query_builder import QueryBuilder
from falkordb_orm.metadata import get_entity_metadata


@node("Person")
class Person:
    """Test entity class."""

    id: Optional[int] = None
    name: str
    age: int


@node("AutoPerson")
class AutoPerson:
    """Test entity with auto-generated ID."""

    id: Optional[int] = generated_id()
    name: str


def test_query_builder_initialization():
    """Test QueryBuilder initialization."""
    builder = QueryBuilder()
    assert builder is not None


def test_build_match_by_id_query():
    """Test building MATCH by ID query."""
    builder = QueryBuilder()
    metadata = get_entity_metadata(Person)

    cypher, params = builder.build_match_by_id_query(metadata, 123)

    assert "MATCH" in cypher
    assert "Person" in cypher
    assert "id" in params
    assert params["id"] == 123


def test_build_match_by_id_query_with_auto_id():
    """Test building MATCH by ID query with auto-generated ID."""
    builder = QueryBuilder()
    metadata = get_entity_metadata(AutoPerson)

    cypher, params = builder.build_match_by_id_query(metadata, 123)

    assert "MATCH" in cypher
    assert "AutoPerson" in cypher
    # With generated_id(), uses internal id(n) function in WHERE clause
    assert "WHERE id(n)" in cypher or "id(n) =" in cypher
    assert params["id"] == 123


def test_build_match_all_query():
    """Test building MATCH all query."""
    builder = QueryBuilder()
    metadata = get_entity_metadata(Person)

    cypher, params = builder.build_match_all_query(metadata)

    assert "MATCH" in cypher
    assert "Person" in cypher
    assert "RETURN n" in cypher


def test_build_count_query():
    """Test building COUNT query."""
    builder = QueryBuilder()
    metadata = get_entity_metadata(Person)

    cypher, params = builder.build_count_query(metadata)

    assert "MATCH" in cypher
    assert "Person" in cypher
    assert "count(n)" in cypher


def test_build_delete_by_id_query():
    """Test building DELETE by ID query."""
    builder = QueryBuilder()
    metadata = get_entity_metadata(Person)

    cypher, params = builder.build_delete_by_id_query(metadata, 123)

    assert "MATCH" in cypher
    assert "DELETE" in cypher
    assert "Person" in cypher
    assert params["id"] == 123


def test_build_delete_all_query():
    """Test building DELETE all query."""
    builder = QueryBuilder()
    metadata = get_entity_metadata(Person)

    cypher, params = builder.build_delete_all_query(metadata)

    assert "MATCH" in cypher
    assert "DELETE" in cypher
    assert "Person" in cypher


def test_build_exists_by_id_query():
    """Test building EXISTS by ID query."""
    builder = QueryBuilder()
    metadata = get_entity_metadata(Person)

    cypher, params = builder.build_exists_by_id_query(metadata, 123)

    assert "MATCH" in cypher
    assert "Person" in cypher
    assert "count(n) > 0" in cypher
    assert params["id"] == 123
