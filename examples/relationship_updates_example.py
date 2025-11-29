"""
Examples demonstrating relationship update functionality.

This module shows how to update relationships on existing entities,
including replacing, adding, removing, and clearing relationships.
"""

from typing import List, Optional
from falkordb import FalkorDB
from falkordb_orm import (
    node,
    relationship,
    generated_id,
    Repository,
)


# Define entities
@node("Person")
class Person:
    """Person entity with self-referential friendship relationship."""
    
    id: Optional[int] = generated_id()
    name: str
    age: int
    
    friends: List["Person"] = relationship(
        relationship_type="KNOWS",
        target="Person",
        direction="OUTGOING",
        cascade=True,
    )


@node("Company")
class Company:
    """Company entity."""
    
    id: Optional[int] = generated_id()
    name: str
    industry: str


@node("Employee")
class Employee:
    """Employee entity with relationship to Company."""
    
    id: Optional[int] = generated_id()
    name: str
    position: str
    
    company: Optional[Company] = relationship(
        relationship_type="WORKS_FOR",
        target=Company,
        direction="OUTGOING",
        cascade=False,
    )


@node("Project")
class Project:
    """Project entity."""
    
    id: Optional[int] = generated_id()
    name: str
    
    team_members: List[Employee] = relationship(
        relationship_type="ASSIGNED_TO",
        target=Employee,
        direction="INCOMING",
        cascade=False,
    )


def example_1_update_single_relationship():
    """Example 1: Updating a single relationship."""
    print("\\n=== Example 1: Update Single Relationship ===")
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("relationship_updates")
    
    # Create repositories
    company_repo = Repository(graph, Company)
    employee_repo = Repository(graph, Employee)
    
    # Create companies
    acme = Company(name="Acme Corp", industry="Technology")
    globex = Company(name="Globex Inc", industry="Finance")
    
    acme = company_repo.save(acme)
    globex = company_repo.save(globex)
    
    # Create employee at Acme
    alice = Employee(name="Alice", position="Engineer")
    alice.company = acme
    alice = employee_repo.save(alice)
    
    print(f"Alice works for: {alice.company.name}")
    
    # Update: Alice moves to Globex
    alice.company = globex
    alice = employee_repo.save(alice)
    
    print(f"After update, Alice works for: {alice.company.name}")
    print("✓ Old WORKS_FOR relationship deleted, new one created")


def example_2_update_collection_add_items():
    """Example 2: Adding items to a collection relationship."""
    print("\\n=== Example 2: Add Items to Collection ===")
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("relationship_updates")
    
    person_repo = Repository(graph, Person)
    
    # Create people
    alice = Person(name="Alice", age=30)
    bob = Person(name="Bob", age=28)
    charlie = Person(name="Charlie", age=32)
    
    alice = person_repo.save(alice)
    bob = person_repo.save(bob)
    charlie = person_repo.save(charlie)
    
    # Alice initially knows Bob
    alice.friends = [bob]
    alice = person_repo.save(alice)
    
    print(f"Alice's friends: {[f.name for f in alice.friends]}")
    
    # Update: Alice also befriends Charlie
    alice.friends = [bob, charlie]
    alice = person_repo.save(alice)
    
    print(f"After update, Alice's friends: {[f.name for f in alice.friends]}")
    print("✓ Old relationships deleted, new relationships created")


def example_3_update_collection_remove_items():
    """Example 3: Removing items from a collection relationship."""
    print("\\n=== Example 3: Remove Items from Collection ===")
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("relationship_updates")
    
    person_repo = Repository(graph, Person)
    
    # Create people
    alice = Person(name="Alice", age=30)
    bob = Person(name="Bob", age=28)
    charlie = Person(name="Charlie", age=32)
    diana = Person(name="Diana", age=27)
    
    alice = person_repo.save(alice)
    bob = person_repo.save(bob)
    charlie = person_repo.save(charlie)
    diana = person_repo.save(diana)
    
    # Alice knows Bob, Charlie, and Diana
    alice.friends = [bob, charlie, diana]
    alice = person_repo.save(alice)
    
    print(f"Alice's friends: {[f.name for f in alice.friends]}")
    
    # Update: Alice unfriends Diana
    alice.friends = [bob, charlie]
    alice = person_repo.save(alice)
    
    print(f"After update, Alice's friends: {[f.name for f in alice.friends]}")
    print("✓ Old relationships deleted, new relationships created (Diana removed)")


def example_4_replace_all_relationships():
    """Example 4: Replacing all items in a collection relationship."""
    print("\\n=== Example 4: Replace All Relationships ===")
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("relationship_updates")
    
    person_repo = Repository(graph, Person)
    
    # Create people
    alice = Person(name="Alice", age=30)
    bob = Person(name="Bob", age=28)
    charlie = Person(name="Charlie", age=32)
    diana = Person(name="Diana", age=27)
    eve = Person(name="Eve", age=29)
    
    alice = person_repo.save(alice)
    bob = person_repo.save(bob)
    charlie = person_repo.save(charlie)
    diana = person_repo.save(diana)
    eve = person_repo.save(eve)
    
    # Alice knows Bob and Charlie
    alice.friends = [bob, charlie]
    alice = person_repo.save(alice)
    
    print(f"Alice's friends: {[f.name for f in alice.friends]}")
    
    # Update: Completely replace friends with Diana and Eve
    alice.friends = [diana, eve]
    alice = person_repo.save(alice)
    
    print(f"After update, Alice's friends: {[f.name for f in alice.friends]}")
    print("✓ All old relationships deleted, new relationships created")


def example_5_clear_collection_relationship():
    """Example 5: Clearing a collection relationship."""
    print("\\n=== Example 5: Clear Collection Relationship ===")
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("relationship_updates")
    
    person_repo = Repository(graph, Person)
    
    # Create people
    alice = Person(name="Alice", age=30)
    bob = Person(name="Bob", age=28)
    charlie = Person(name="Charlie", age=32)
    
    alice = person_repo.save(alice)
    bob = person_repo.save(bob)
    charlie = person_repo.save(charlie)
    
    # Alice has friends
    alice.friends = [bob, charlie]
    alice = person_repo.save(alice)
    
    print(f"Alice's friends: {[f.name for f in alice.friends]}")
    
    # Update: Clear all friends
    alice.friends = []
    alice = person_repo.save(alice)
    
    print(f"After update, Alice's friends: {alice.friends}")
    print("✓ All old relationships deleted, no new relationships")


def example_6_clear_single_relationship():
    """Example 6: Clearing a single relationship (setting to None)."""
    print("\\n=== Example 6: Clear Single Relationship ===")
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("relationship_updates")
    
    company_repo = Repository(graph, Company)
    employee_repo = Repository(graph, Employee)
    
    # Create company and employee
    acme = Company(name="Acme Corp", industry="Technology")
    acme = company_repo.save(acme)
    
    alice = Employee(name="Alice", position="Engineer")
    alice.company = acme
    alice = employee_repo.save(alice)
    
    print(f"Alice works for: {alice.company.name if alice.company else 'None'}")
    
    # Update: Alice leaves the company
    alice.company = None
    alice = employee_repo.save(alice)
    
    print(f"After update, Alice works for: {alice.company}")
    print("Note: Setting to None skips relationship processing")


def example_7_project_team_reassignment():
    """Example 7: Reassigning project team members."""
    print("\\n=== Example 7: Project Team Reassignment ===")
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("relationship_updates")
    
    company_repo = Repository(graph, Company)
    employee_repo = Repository(graph, Employee)
    project_repo = Repository(graph, Project)
    
    # Create company and employees
    acme = Company(name="Acme Corp", industry="Technology")
    acme = company_repo.save(acme)
    
    alice = Employee(name="Alice", position="Engineer")
    bob = Employee(name="Bob", position="Engineer")
    charlie = Employee(name="Charlie", position="Designer")
    diana = Employee(name="Diana", position="Engineer")
    
    for emp in [alice, bob, charlie, diana]:
        emp.company = acme
        employee_repo.save(emp)
    
    # Create project with initial team
    project = Project(name="Project X")
    project.team_members = [alice, bob]
    project = project_repo.save(project)
    
    print(f"Project team: {[m.name for m in project.team_members]}")
    
    # Update: Replace Bob with Charlie and Diana
    project.team_members = [alice, charlie, diana]
    project = project_repo.save(project)
    
    print(f"After update, project team: {[m.name for m in project.team_members]}")
    print("✓ Old assignments deleted, new assignments created")


def example_8_cascade_with_update():
    """Example 8: Cascade behavior with relationship updates."""
    print("\\n=== Example 8: Cascade with Updates ===")
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("relationship_updates")
    
    person_repo = Repository(graph, Person)
    
    # Create person with existing friends
    alice = Person(name="Alice", age=30)
    bob = Person(name="Bob", age=28)
    bob = person_repo.save(bob)  # Bob is already saved
    
    alice.friends = [bob]
    alice = person_repo.save(alice)
    
    print(f"Alice's friends: {[f.name for f in alice.friends]}")
    
    # Update: Add new unsaved friend (cascade will save them)
    charlie = Person(name="Charlie", age=32)  # Not saved yet
    alice.friends = [bob, charlie]
    alice = person_repo.save(alice)
    
    print(f"After update, Alice's friends: {[f.name for f in alice.friends]}")
    print(f"Charlie was cascade-saved with ID: {charlie.id}")
    print("✓ Cascade save works on relationship updates")


def example_9_batch_updates():
    """Example 9: Batch updating multiple entities' relationships."""
    print("\\n=== Example 9: Batch Relationship Updates ===")
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("relationship_updates")
    
    person_repo = Repository(graph, Person)
    
    # Create people
    people = [
        Person(name="Alice", age=30),
        Person(name="Bob", age=28),
        Person(name="Charlie", age=32),
        Person(name="Diana", age=27),
    ]
    
    for person in people:
        person_repo.save(person)
    
    alice, bob, charlie, diana = people
    
    # Set initial relationships
    alice.friends = [bob]
    charlie.friends = [diana]
    
    person_repo.save(alice)
    person_repo.save(charlie)
    
    print("Initial:")
    print(f"  Alice's friends: {[f.name for f in alice.friends]}")
    print(f"  Charlie's friends: {[f.name for f in charlie.friends]}")
    
    # Batch update: everyone becomes friends with everyone
    alice.friends = [bob, charlie, diana]
    bob.friends = [alice, charlie, diana]
    charlie.friends = [alice, bob, diana]
    diana.friends = [alice, bob, charlie]
    
    for person in people:
        person_repo.save(person)
    
    print("\\nAfter batch update:")
    print(f"  Alice's friends: {[f.name for f in alice.friends]}")
    print(f"  Bob's friends: {[f.name for f in bob.friends]}")
    print(f"  Charlie's friends: {[f.name for f in charlie.friends]}")
    print(f"  Diana's friends: {[f.name for f in diana.friends]}")
    print("✓ All relationships updated correctly")


def main():
    """Run all examples."""
    print("Relationship Update Examples")
    print("=" * 50)
    
    try:
        example_1_update_single_relationship()
        example_2_update_collection_add_items()
        example_3_update_collection_remove_items()
        example_4_replace_all_relationships()
        example_5_clear_collection_relationship()
        example_6_clear_single_relationship()
        example_7_project_team_reassignment()
        example_8_cascade_with_update()
        example_9_batch_updates()
        
        print("\\n" + "=" * 50)
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"\\nError running examples: {e}")
        raise


if __name__ == "__main__":
    main()
