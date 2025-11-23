"""Tests for decorators module."""

from typing import Optional
import pytest

from falkordb_orm.decorators import node, property, generated_id
from falkordb_orm.metadata import get_entity_metadata


def test_node_decorator_with_string_label():
    """Test @node decorator with string label."""

    @node("Person")
    class Person:
        id: Optional[int] = None
        name: str
        age: int

    metadata = get_entity_metadata(Person)
    assert metadata is not None
    assert metadata.labels == ["Person"]
    assert metadata.primary_label == "Person"
    assert len(metadata.properties) == 3


def test_node_decorator_with_list_labels():
    """Test @node decorator with multiple labels."""

    @node(labels=["Person", "Individual"])
    class Person:
        id: Optional[int] = None
        name: str

    metadata = get_entity_metadata(Person)
    assert metadata is not None
    assert metadata.labels == ["Person", "Individual"]
    assert metadata.primary_label == "Person"


def test_node_decorator_without_label():
    """Test @node decorator without explicit label (uses class name)."""

    @node()
    class User:
        id: Optional[int] = None
        username: str

    metadata = get_entity_metadata(User)
    assert metadata is not None
    assert metadata.labels == ["User"]
    assert metadata.primary_label == "User"


def test_node_decorator_with_primary_label():
    """Test @node decorator with explicit primary label."""

    @node(labels=["Person", "Individual"], primary_label="Individual")
    class Person:
        id: Optional[int] = None
        name: str

    metadata = get_entity_metadata(Person)
    assert metadata is not None
    assert metadata.primary_label == "Individual"


def test_property_descriptor():
    """Test property descriptor with custom name."""

    @node("Person")
    class Person:
        id: Optional[int] = None
        name: str = property("full_name")
        age: int

    metadata = get_entity_metadata(Person)
    name_prop = metadata.get_property_by_python_name("name")

    assert name_prop is not None
    assert name_prop.graph_name == "full_name"
    assert name_prop.python_name == "name"


def test_generated_id_descriptor():
    """Test generated_id descriptor."""

    @node("Person")
    class Person:
        id: Optional[int] = generated_id()
        name: str

    metadata = get_entity_metadata(Person)
    id_prop = metadata.id_property

    assert id_prop is not None
    assert id_prop.python_name == "id"
    assert id_prop.is_id is True
    assert id_prop.id_generator is None


def test_id_property_detection():
    """Test automatic detection of 'id' field."""

    @node("Person")
    class Person:
        id: Optional[int] = None
        name: str

    metadata = get_entity_metadata(Person)
    id_prop = metadata.id_property

    assert id_prop is not None
    assert id_prop.python_name == "id"
    assert id_prop.is_id is True


def test_property_metadata_extraction():
    """Test extraction of all properties."""

    @node("Person")
    class Person:
        id: Optional[int] = None
        name: str
        email: str
        age: int

    metadata = get_entity_metadata(Person)

    assert len(metadata.properties) == 4
    prop_names = [p.python_name for p in metadata.properties]
    assert "id" in prop_names
    assert "name" in prop_names
    assert "email" in prop_names
    assert "age" in prop_names


def test_entity_instantiation():
    """Test that decorated classes can still be instantiated normally."""

    @node("Person")
    class Person:
        def __init__(self, id: Optional[int], name: str, age: int):
            self.id = id
            self.name = name
            self.age = age

    person = Person(id=1, name="Alice", age=30)
    assert person.id == 1
    assert person.name == "Alice"
    assert person.age == 30

    metadata = get_entity_metadata(Person)
    assert metadata is not None
