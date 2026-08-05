"""Tests for Issue #7 - custom/property-based IDs and query building/mapping."""

from typing import Optional

from falkordb_orm import node, generated_id
from falkordb_orm.metadata import get_entity_metadata
from falkordb_orm.query_builder import QueryBuilder
from falkordb_orm.mapper import EntityMapper


@node("CustomIDPerson")
class CustomIDPerson:
    """Test entity with a manually assigned property-based string ID."""

    id: str
    name: str


@node("AutoIDPerson")
class AutoIDPerson:
    """Test entity with an auto-generated internal integer ID."""

    id: Optional[int] = generated_id()
    name: str


def test_metadata_is_generated_flag():
    """Test that is_generated flag is correctly populated for ID fields."""
    custom_meta = get_entity_metadata(CustomIDPerson)
    assert custom_meta is not None
    assert custom_meta.id_property is not None
    assert custom_meta.id_property.is_id is True
    # Should be False because we didn't use generated_id()
    assert custom_meta.id_property.is_generated is False

    auto_meta = get_entity_metadata(AutoIDPerson)
    assert auto_meta is not None
    assert auto_meta.id_property is not None
    assert auto_meta.id_property.is_id is True
    # Should be True because we used generated_id()
    assert auto_meta.id_property.is_generated is True


def test_query_builder_for_custom_id():
    """Test that query builder generates property-based queries for custom ID."""
    builder = QueryBuilder()
    custom_meta = get_entity_metadata(CustomIDPerson)

    # 1. Match by ID Query
    cypher, params = builder.build_match_by_id_query(custom_meta, "user_abc")
    assert "id(n)" not in cypher
    assert "{id: $id}" in cypher
    assert params == {"id": "user_abc"}

    # 2. Delete by ID Query
    cypher, params = builder.build_delete_by_id_query(custom_meta, "user_abc")
    assert "id(n)" not in cypher
    assert "{id: $id}" in cypher
    assert params == {"id": "user_abc"}

    # 3. Exists by ID Query
    cypher, params = builder.build_exists_by_id_query(custom_meta, "user_abc")
    assert "id(n)" not in cypher
    assert "{id: $id}" in cypher
    assert params == {"id": "user_abc"}

    # 4. Eager Loading Query
    cypher, params = builder.build_eager_loading_query(custom_meta, "user_abc", [])
    assert "id(n)" not in cypher
    assert "n.id = $id" in cypher


def test_query_builder_for_auto_id():
    """Test that query builder generates internal node ID queries for auto ID."""
    builder = QueryBuilder()
    auto_meta = get_entity_metadata(AutoIDPerson)

    # 1. Match by ID Query
    cypher, params = builder.build_match_by_id_query(auto_meta, 123)
    assert "id(n) = $id" in cypher
    assert "{id: $id}" not in cypher

    # 2. Delete by ID Query
    cypher, params = builder.build_delete_by_id_query(auto_meta, 123)
    assert "id(n) = $id" in cypher
    assert "{id: $id}" not in cypher

    # 3. Exists by ID Query
    cypher, params = builder.build_exists_by_id_query(auto_meta, 123)
    assert "id(n) = $id" in cypher
    assert "{id: $id}" not in cypher

    # 4. Eager Loading Query
    cypher, params = builder.build_eager_loading_query(auto_meta, 123, [])
    assert "id(n) = $id" in cypher


def test_mapper_does_not_overwrite_custom_id_with_internal_id():
    """Test that map_from_node does not overwrite custom ID property with internal system node ID."""

    class MockNode:
        def __init__(self):
            self.id = 999  # Internal system node ID
            self.properties = {"id": "user_abc", "name": "Alice"}

    mapper = EntityMapper()
    node_obj = MockNode()

    # Map the node to CustomIDPerson
    entity = mapper.map_from_node(node_obj, CustomIDPerson)
    assert entity.id == "user_abc"  # Must preserve user's custom string ID!
    assert entity.name == "Alice"
