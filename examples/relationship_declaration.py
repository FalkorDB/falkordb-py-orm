"""
Example demonstrating relationship declaration in Phase 3a.

This example shows:
1. How to declare relationships using the relationship() function
2. One-to-many relationships with List type hints
3. One-to-one relationships with Optional type hints
4. Forward references for self-referential relationships
5. Different relationship directions (OUTGOING, INCOMING, BOTH)
6. Cascade and lazy loading options
7. How to inspect relationship metadata

Note: This is Phase 3a - only relationship *declaration* is implemented.
Actual relationship loading and saving will be implemented in later phases.
"""

from typing import List, Optional

from falkordb_orm.decorators import node, generated_id, relationship
from falkordb_orm.metadata import get_entity_metadata


# Example 1: Self-referential relationship (social network)
@node("Person")
class Person:
    """Person entity with self-referential relationships."""
    id: Optional[int] = generated_id()
    name: str
    email: str
    
    # One-to-many: A person can have many friends
    friends: List['Person'] = relationship('KNOWS', target='Person')
    
    # One-to-many with INCOMING direction: People who follow this person
    followers: List['Person'] = relationship('FOLLOWS', direction='INCOMING', target='Person')
    
    # One-to-one: A person can have one manager
    manager: Optional['Person'] = relationship('REPORTS_TO', target='Person')


# Example 2: Company and Employee relationship
@node("Company")
class Company:
    """Company entity."""
    id: Optional[int] = generated_id()
    name: str
    industry: str
    
    # One-to-many: A company has many employees
    # Using cascade=True means saving the company will also save its employees
    employees: List['Employee'] = relationship(
        'EMPLOYS', 
        direction='OUTGOING',
        target='Employee',
        cascade=True
    )


@node("Employee")
class Employee:
    """Employee entity with multiple relationships."""
    id: Optional[int] = generated_id()
    name: str
    position: str
    
    # Many-to-one: An employee works for one company
    company: Optional[Company] = relationship('WORKS_FOR', target=Company)
    
    # Many-to-many: An employee can work on multiple projects
    projects: List['Project'] = relationship('WORKS_ON', target='Project')
    
    # Self-referential: Manager relationship
    manager: Optional['Employee'] = relationship('MANAGES', direction='INCOMING', target='Employee')
    
    # Self-referential: Direct reports
    direct_reports: List['Employee'] = relationship('MANAGES', direction='OUTGOING', target='Employee')


@node("Project")
class Project:
    """Project entity."""
    id: Optional[int] = generated_id()
    name: str
    description: str
    
    # Many-to-many: A project has multiple team members
    team_members: List[Employee] = relationship(
        'WORKS_ON', 
        direction='INCOMING',
        target=Employee
    )


# Example 3: Bidirectional relationship
@node("User")
class User:
    """User entity with bidirectional connections."""
    id: Optional[int] = generated_id()
    username: str
    
    # Bidirectional relationship (BOTH direction)
    connections: List['User'] = relationship(
        'CONNECTED', 
        direction='BOTH',
        target='User'
    )


# Example 4: Cascade and eager loading options
@node("Address")
class Address:
    """Address entity."""
    id: Optional[int] = generated_id()
    street: str
    city: str
    country: str


@node("Customer")
class Customer:
    """Customer entity with cascade and lazy options."""
    id: Optional[int] = generated_id()
    name: str
    email: str
    
    # Cascade: Saving customer will also save addresses
    # Lazy=False: Address will be eagerly loaded (Phase 3d feature)
    shipping_address: Optional[Address] = relationship(
        'HAS_SHIPPING_ADDRESS',
        target=Address,
        cascade=True,
        lazy=False
    )
    
    billing_address: Optional[Address] = relationship(
        'HAS_BILLING_ADDRESS',
        target=Address,
        cascade=True
    )


def inspect_metadata():
    """Inspect and print relationship metadata for all entities."""
    print("=" * 80)
    print("RELATIONSHIP METADATA INSPECTION")
    print("=" * 80)
    print()
    
    # Inspect Person entity
    print("Person Entity:")
    print("-" * 80)
    person_meta = get_entity_metadata(Person)
    print(f"  Label: {person_meta.primary_label}")
    print(f"  Properties: {len(person_meta.properties)}")
    print(f"  Relationships: {len(person_meta.relationships)}")
    print()
    
    for rel in person_meta.relationships:
        print(f"  Relationship: {rel.python_name}")
        print(f"    Type: {rel.relationship_type}")
        print(f"    Direction: {rel.direction}")
        print(f"    Target: {rel.target_class_name}")
        print(f"    Is Collection: {rel.is_collection}")
        print(f"    Lazy: {rel.lazy}")
        print(f"    Cascade: {rel.cascade}")
        print()
    
    # Inspect Employee entity
    print("Employee Entity:")
    print("-" * 80)
    emp_meta = get_entity_metadata(Employee)
    print(f"  Label: {emp_meta.primary_label}")
    print(f"  Properties: {len(emp_meta.properties)}")
    print(f"  Relationships: {len(emp_meta.relationships)}")
    print()
    
    for rel in emp_meta.relationships:
        print(f"  Relationship: {rel.python_name}")
        print(f"    Type: {rel.relationship_type}")
        print(f"    Direction: {rel.direction}")
        print(f"    Target: {rel.target_class_name}")
        print(f"    Is Collection: {rel.is_collection}")
        print()
    
    # Inspect Customer entity (with cascade and lazy options)
    print("Customer Entity (with cascade and lazy options):")
    print("-" * 80)
    customer_meta = get_entity_metadata(Customer)
    print(f"  Label: {customer_meta.primary_label}")
    print(f"  Relationships: {len(customer_meta.relationships)}")
    print()
    
    for rel in customer_meta.relationships:
        print(f"  Relationship: {rel.python_name}")
        print(f"    Type: {rel.relationship_type}")
        print(f"    Cascade: {rel.cascade}")
        print(f"    Lazy: {rel.lazy}")
        print()
    
    # Test helper methods
    print("Helper Methods:")
    print("-" * 80)
    print(f"  Is 'friends' a relationship? {person_meta.is_relationship_field('friends')}")
    print(f"  Is 'name' a relationship? {person_meta.is_relationship_field('name')}")
    print()
    
    friends_rel = person_meta.get_relationship_by_python_name('friends')
    print(f"  Get 'friends' relationship: {friends_rel.relationship_type if friends_rel else 'None'}")
    print()


def demonstrate_entity_creation():
    """Demonstrate that entities can still be created normally."""
    print("=" * 80)
    print("ENTITY CREATION")
    print("=" * 80)
    print()
    
    # Create a person (relationships are not yet functional in Phase 3a)
    person = Person()
    person.id = 1
    person.name = "Alice Smith"
    person.email = "alice@example.com"
    
    print(f"Created Person:")
    print(f"  ID: {person.id}")
    print(f"  Name: {person.name}")
    print(f"  Email: {person.email}")
    print()
    
    # Create a company
    company = Company()
    company.id = 100
    company.name = "Tech Corp"
    company.industry = "Software"
    
    print(f"Created Company:")
    print(f"  ID: {company.id}")
    print(f"  Name: {company.name}")
    print(f"  Industry: {company.industry}")
    print()
    
    print("Note: Relationship attributes are declared but not yet functional.")
    print("They will be implemented in Phase 3b (Lazy Loading) and Phase 3c (Cascade).")
    print()


if __name__ == "__main__":
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "PHASE 3a: RELATIONSHIP DECLARATION" + " " * 24 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    # Show metadata inspection
    inspect_metadata()
    
    # Show entity creation
    demonstrate_entity_creation()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("Phase 3a Complete! ✓")
    print()
    print("What's working:")
    print("  ✓ Declare relationships using relationship() function")
    print("  ✓ Support for List[T] (one-to-many) and Optional[T] (one-to-one)")
    print("  ✓ Forward references for self-referential relationships")
    print("  ✓ Direction support: OUTGOING, INCOMING, BOTH")
    print("  ✓ Cascade and lazy options")
    print("  ✓ Metadata extraction and inspection")
    print()
    print("Coming in later phases:")
    print("  • Phase 3b: Lazy loading of relationships")
    print("  • Phase 3c: Cascade save/delete operations")
    print("  • Phase 3d: Eager loading optimization")
    print("  • Phase 3e: Complete documentation")
    print()
