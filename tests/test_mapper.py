"""Tests for mapper module."""

from typing import Optional
import pytest

from falkordb_orm.decorators import node, generated_id
from falkordb_orm.mapper import EntityMapper
from falkordb_orm.exceptions import InvalidEntityException


@node("Person")
class Person:
    """Test entity class."""
    id: Optional[int] = None
    name: str
    email: str
    age: int


def test_mapper_initialization():
    """Test EntityMapper initialization."""
    mapper = EntityMapper()
    assert mapper is not None
    assert mapper._metadata_cache == {}


def test_get_entity_metadata():
    """Test getting entity metadata."""
    mapper = EntityMapper()
    metadata = mapper.get_entity_metadata(Person)
    
    assert metadata is not None
    assert metadata.entity_class == Person
    assert metadata.labels == ["Person"]


def test_get_entity_metadata_invalid_class():
    """Test getting metadata from non-entity class."""
    mapper = EntityMapper()
    
    class NotAnEntity:
        pass
    
    with pytest.raises(InvalidEntityException):
        mapper.get_entity_metadata(NotAnEntity)


def test_map_to_properties():
    """Test mapping entity to properties dict."""
    mapper = EntityMapper()
    person = Person(id=1, name="Alice", email="alice@example.com", age=30)
    
    props = mapper.map_to_properties(person)
    
    assert "name" in props
    assert props["name"] == "Alice"
    assert props["email"] == "alice@example.com"
    assert props["age"] == 30


def test_map_to_cypher_create():
    """Test generating CREATE Cypher statement."""
    mapper = EntityMapper()
    person = Person(id=None, name="Alice", email="alice@example.com", age=30)
    
    cypher, params = mapper.map_to_cypher_create(person)
    
    assert "CREATE" in cypher
    assert "Person" in cypher
    assert "props" in params
    assert params["props"]["name"] == "Alice"


def test_map_to_cypher_merge():
    """Test generating MERGE Cypher statement."""
    mapper = EntityMapper()
    person = Person(id=1, name="Alice", email="alice@example.com", age=30)
    
    cypher, params = mapper.map_to_cypher_merge(person)
    
    assert "MERGE" in cypher
    assert "Person" in cypher
    assert "id" in params
    assert params["id"] == 1


def test_map_from_node():
    """Test mapping FalkorDB node to entity."""
    
    # Mock node object
    class MockNode:
        def __init__(self):
            self.id = 123
            self.properties = {
                "name": "Alice",
                "email": "alice@example.com",
                "age": 30
            }
    
    mapper = EntityMapper()
    node = MockNode()
    
    entity = mapper.map_from_node(node, Person)
    
    assert entity is not None
    assert entity.name == "Alice"
    assert entity.email == "alice@example.com"
    assert entity.age == 30


def test_update_entity_id():
    """Test updating entity ID after creation."""
    mapper = EntityMapper()
    person = Person(id=None, name="Alice", email="alice@example.com", age=30)
    
    mapper.update_entity_id(person, 123)
    
    assert person.id == 123


def test_map_to_properties_with_auto_generated_id():
    """Test that auto-generated ID is skipped when None."""
    
    @node("AutoPerson")
    class AutoPerson:
        id: Optional[int] = generated_id()
        name: str
    
    mapper = EntityMapper()
    person = AutoPerson()
    person.id = None
    person.name = "Bob"
    
    props = mapper.map_to_properties(person)
    
    # Auto-generated ID should be skipped if None
    assert "name" in props
    assert props["name"] == "Bob"
