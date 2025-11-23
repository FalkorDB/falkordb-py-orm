"""Tests for relationship metadata extraction."""

from typing import List, Optional
import pytest

from falkordb_orm.decorators import node, generated_id, relationship
from falkordb_orm.metadata import get_entity_metadata, RelationshipMetadata


def test_one_to_many_relationship_with_forward_reference():
    """Test one-to-many relationship using forward reference."""
    @node("Person")
    class Person:
        id: Optional[int] = generated_id()
        name: str
        friends: List['Person'] = relationship('KNOWS', target='Person')
    
    metadata = get_entity_metadata(Person)
    assert metadata is not None
    assert len(metadata.relationships) == 1
    
    friends_rel = metadata.get_relationship_by_python_name('friends')
    assert friends_rel is not None
    assert friends_rel.relationship_type == 'KNOWS'
    assert friends_rel.direction == 'OUTGOING'
    assert friends_rel.is_collection is True
    assert friends_rel.target_class_name == 'Person'
    assert friends_rel.lazy is True
    assert friends_rel.cascade is False


def test_one_to_one_relationship():
    """Test one-to-one relationship with Optional."""
    @node("Company")
    class Company:
        id: Optional[int] = generated_id()
        name: str
    
    @node("Person")
    class Person:
        id: Optional[int] = generated_id()
        name: str
        company: Optional[Company] = relationship('WORKS_FOR', target=Company)
    
    metadata = get_entity_metadata(Person)
    assert metadata is not None
    assert len(metadata.relationships) == 1
    
    company_rel = metadata.get_relationship_by_python_name('company')
    assert company_rel is not None
    assert company_rel.relationship_type == 'WORKS_FOR'
    assert company_rel.direction == 'OUTGOING'
    assert company_rel.is_collection is False
    assert company_rel.target_class == Company
    assert company_rel.target_class_name == 'Company'


def test_relationship_with_incoming_direction():
    """Test relationship with incoming direction."""
    @node("Person")
    class Person:
        id: Optional[int] = generated_id()
        name: str
        followers: List['Person'] = relationship('FOLLOWS', direction='INCOMING', target='Person')
    
    metadata = get_entity_metadata(Person)
    followers_rel = metadata.get_relationship_by_python_name('followers')
    
    assert followers_rel is not None
    assert followers_rel.direction == 'INCOMING'


def test_relationship_with_both_direction():
    """Test relationship with bidirectional (BOTH) direction."""
    @node("Person")
    class Person:
        id: Optional[int] = generated_id()
        name: str
        connections: List['Person'] = relationship('CONNECTED', direction='BOTH', target='Person')
    
    metadata = get_entity_metadata(Person)
    connections_rel = metadata.get_relationship_by_python_name('connections')
    
    assert connections_rel is not None
    assert connections_rel.direction == 'BOTH'


def test_relationship_with_cascade():
    """Test relationship with cascade enabled."""
    @node("Address")
    class Address:
        id: Optional[int] = generated_id()
        street: str
    
    @node("Person")
    class Person:
        id: Optional[int] = generated_id()
        name: str
        address: Optional[Address] = relationship('HAS_ADDRESS', target=Address, cascade=True)
    
    metadata = get_entity_metadata(Person)
    address_rel = metadata.get_relationship_by_python_name('address')
    
    assert address_rel is not None
    assert address_rel.cascade is True


def test_relationship_with_lazy_false():
    """Test relationship with lazy loading disabled."""
    @node("Team")
    class Team:
        id: Optional[int] = generated_id()
        name: str
    
    @node("Person")
    class Person:
        id: Optional[int] = generated_id()
        name: str
        team: Optional[Team] = relationship('MEMBER_OF', target=Team, lazy=False)
    
    metadata = get_entity_metadata(Person)
    team_rel = metadata.get_relationship_by_python_name('team')
    
    assert team_rel is not None
    assert team_rel.lazy is False


def test_multiple_relationships():
    """Test entity with multiple relationships."""
    @node("Company")
    class Company:
        id: Optional[int] = generated_id()
        name: str
    
    @node("Person")
    class Person:
        id: Optional[int] = generated_id()
        name: str
        friends: List['Person'] = relationship('KNOWS', target='Person')
        company: Optional[Company] = relationship('WORKS_FOR', target=Company)
        followers: List['Person'] = relationship('FOLLOWS', direction='INCOMING', target='Person')
    
    metadata = get_entity_metadata(Person)
    assert metadata is not None
    assert len(metadata.relationships) == 3
    
    # Check that all relationships are captured
    rel_names = [r.python_name for r in metadata.relationships]
    assert 'friends' in rel_names
    assert 'company' in rel_names
    assert 'followers' in rel_names


def test_properties_and_relationships_separate():
    """Test that properties and relationships are kept separate."""
    @node("Person")
    class Person:
        id: Optional[int] = generated_id()
        name: str
        age: int
        friends: List['Person'] = relationship('KNOWS', target='Person')
    
    metadata = get_entity_metadata(Person)
    
    # Check properties
    assert len(metadata.properties) == 3
    prop_names = [p.python_name for p in metadata.properties]
    assert 'id' in prop_names
    assert 'name' in prop_names
    assert 'age' in prop_names
    assert 'friends' not in prop_names
    
    # Check relationships
    assert len(metadata.relationships) == 1
    assert metadata.relationships[0].python_name == 'friends'


def test_is_relationship_field_method():
    """Test the is_relationship_field method."""
    @node("Person")
    class Person:
        id: Optional[int] = generated_id()
        name: str
        friends: List['Person'] = relationship('KNOWS', target='Person')
    
    metadata = get_entity_metadata(Person)
    
    assert metadata.is_relationship_field('friends') is True
    assert metadata.is_relationship_field('name') is False
    assert metadata.is_relationship_field('id') is False
    assert metadata.is_relationship_field('nonexistent') is False


def test_get_relationship_by_python_name():
    """Test retrieving relationship metadata by name."""
    @node("Person")
    class Person:
        id: Optional[int] = generated_id()
        name: str
        friends: List['Person'] = relationship('KNOWS', target='Person')
    
    metadata = get_entity_metadata(Person)
    
    friends_rel = metadata.get_relationship_by_python_name('friends')
    assert friends_rel is not None
    assert friends_rel.relationship_type == 'KNOWS'
    
    none_rel = metadata.get_relationship_by_python_name('nonexistent')
    assert none_rel is None


def test_relationship_without_explicit_target():
    """Test that target can be inferred from type hint."""
    @node("Company")
    class Company:
        id: Optional[int] = generated_id()
        name: str
    
    @node("Person")
    class Person:
        id: Optional[int] = generated_id()
        name: str
        company: Optional[Company] = relationship('WORKS_FOR')
    
    metadata = get_entity_metadata(Person)
    company_rel = metadata.get_relationship_by_python_name('company')
    
    assert company_rel is not None
    assert company_rel.target_class == Company
    assert company_rel.target_class_name == 'Company'


def test_invalid_direction_raises_error():
    """Test that invalid direction raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        relationship('KNOWS', direction='INVALID')
    
    assert 'Invalid direction' in str(exc_info.value)


def test_relationship_descriptor_set_name():
    """Test that RelationshipDescriptor captures attribute name."""
    @node("Person")
    class Person:
        id: Optional[int] = generated_id()
        name: str
        friends: List['Person'] = relationship('KNOWS', target='Person')
    
    # Get the descriptor from the class
    descriptor = Person.__dict__['friends']
    assert descriptor._python_name == 'friends'


def test_complex_relationship_scenario():
    """Test a complex scenario with multiple entity types and relationships."""
    @node("Project")
    class Project:
        id: Optional[int] = generated_id()
        name: str
    
    @node("Department")
    class Department:
        id: Optional[int] = generated_id()
        name: str
    
    @node("Company")
    class Company:
        id: Optional[int] = generated_id()
        name: str
        departments: List[Department] = relationship('HAS_DEPARTMENT', target=Department, cascade=True)
    
    @node("Employee")
    class Employee:
        id: Optional[int] = generated_id()
        name: str
        email: str
        company: Optional[Company] = relationship('WORKS_FOR', target=Company)
        department: Optional[Department] = relationship('MEMBER_OF', target=Department)
        projects: List[Project] = relationship('WORKS_ON', target=Project)
        manager: Optional['Employee'] = relationship('REPORTS_TO', target='Employee')
        direct_reports: List['Employee'] = relationship('REPORTS_TO', direction='INCOMING', target='Employee')
    
    # Verify Employee metadata
    emp_metadata = get_entity_metadata(Employee)
    assert len(emp_metadata.properties) == 3  # id, name, email
    assert len(emp_metadata.relationships) == 5
    
    # Verify each relationship
    company_rel = emp_metadata.get_relationship_by_python_name('company')
    assert company_rel.is_collection is False
    assert company_rel.target_class == Company
    
    projects_rel = emp_metadata.get_relationship_by_python_name('projects')
    assert projects_rel.is_collection is True
    assert projects_rel.target_class == Project
    
    manager_rel = emp_metadata.get_relationship_by_python_name('manager')
    assert manager_rel.target_class_name == 'Employee'
    assert manager_rel.direction == 'OUTGOING'
    
    reports_rel = emp_metadata.get_relationship_by_python_name('direct_reports')
    assert reports_rel.direction == 'INCOMING'
    assert reports_rel.is_collection is True
    
    # Verify Company metadata
    company_metadata = get_entity_metadata(Company)
    assert len(company_metadata.relationships) == 1
    dept_rel = company_metadata.get_relationship_by_python_name('departments')
    assert dept_rel.cascade is True
