"""
Example demonstrating cascade save operations with relationships.

This example shows how cascade=True automatically saves related entities
and creates relationship edges in the graph.
"""

from typing import List, Optional
from falkordb import FalkorDB
from falkordb_orm import node, generated_id, relationship, Repository


# Define entities with cascade relationships
@node("Person")
class Person:
    id: Optional[int] = generated_id()
    name: str
    age: int
    # Non-cascade relationship - requires entities to be saved first
    friends: List['Person'] = relationship('KNOWS', target='Person', cascade=False)


@node("Company")
class Company:
    id: Optional[int] = generated_id()
    name: str
    industry: str


@node("Employee")
class Employee:
    id: Optional[int] = generated_id()
    name: str
    position: str
    # Cascade relationship - automatically saves company if not saved
    company: Optional[Company] = relationship('WORKS_FOR', target=Company, cascade=True)


@node("Project")
class Project:
    id: Optional[int] = generated_id()
    name: str
    description: str


@node("Team")
class Team:
    id: Optional[int] = generated_id()
    name: str
    # Cascade relationships for both members and projects
    members: List[Person] = relationship('HAS_MEMBER', target=Person, cascade=True)
    projects: List[Project] = relationship('WORKS_ON', target=Project, cascade=True)


def demonstrate_cascade_save():
    """Demonstrate cascade save operations."""
    
    # Connect to FalkorDB
    db = FalkorDB(host='localhost', port=6379)
    graph = db.select_graph('cascade_demo')
    
    # Create repositories
    person_repo = Repository(graph, Person)
    company_repo = Repository(graph, Company)
    employee_repo = Repository(graph, Employee)
    project_repo = Repository(graph, Project)
    team_repo = Repository(graph, Team)
    
    # Clean up previous data
    person_repo.delete_all()
    company_repo.delete_all()
    employee_repo.delete_all()
    project_repo.delete_all()
    team_repo.delete_all()
    
    print("=" * 60)
    print("Cascade Save Example")
    print("=" * 60)
    
    # Example 1: Non-cascade relationship (must save entities first)
    print("\n1. Non-Cascade Relationship (friends)")
    print("   Creating two people...")
    
    alice = Person(name="Alice", age=30)
    alice = person_repo.save(alice)
    print(f"   Saved: {alice.name} (ID: {alice.id})")
    
    bob = Person(name="Bob", age=28)
    bob = person_repo.save(bob)
    print(f"   Saved: {bob.name} (ID: {bob.id})")
    
    print("\n   Creating friendship (non-cascade)...")
    alice.friends = [bob]
    alice = person_repo.save(alice)
    print(f"   Friendship created: {alice.name} -> {bob.name}")
    print("   ^ Both entities were saved first, then relationship created")
    
    # Example 2: Cascade relationship (auto-saves related entity)
    print("\n2. Cascade Relationship (employee -> company)")
    print("   Creating employee with unsaved company...")
    
    acme = Company(name="Acme Corp", industry="Technology")
    charlie = Employee(name="Charlie", position="Engineer")
    charlie.company = acme  # Company not saved yet!
    
    print(f"   Before save - Company ID: {acme.id}")
    charlie = employee_repo.save(charlie)
    print(f"   After save - Employee ID: {charlie.id}")
    print(f"   After save - Company ID: {acme.id}")
    print("   ^ Company was automatically saved due to cascade=True!")
    
    # Verify the relationship was created
    fetched_charlie = employee_repo.find_by_id(charlie.id)
    company = fetched_charlie.company.get()
    print(f"   Verified: {fetched_charlie.name} works for {company.name}")
    
    # Example 3: Cascade with collections (team with members and projects)
    print("\n3. Cascade with Collections (team -> members + projects)")
    print("   Creating team with unsaved members and projects...")
    
    # Create unsaved team members
    diana = Person(name="Diana", age=32)
    evan = Person(name="Evan", age=29)
    
    # Create unsaved projects
    project1 = Project(name="Project Alpha", description="First project")
    project2 = Project(name="Project Beta", description="Second project")
    
    # Create team with unsaved entities
    dev_team = Team(name="Development Team")
    dev_team.members = [diana, evan]
    dev_team.projects = [project1, project2]
    
    print(f"   Before save - Team ID: {dev_team.id}")
    print(f"   Before save - Diana ID: {diana.id}")
    print(f"   Before save - Evan ID: {evan.id}")
    print(f"   Before save - Project Alpha ID: {project1.id}")
    print(f"   Before save - Project Beta ID: {project2.id}")
    
    dev_team = team_repo.save(dev_team)
    
    print(f"\n   After save - Team ID: {dev_team.id}")
    print(f"   After save - Diana ID: {diana.id}")
    print(f"   After save - Evan ID: {evan.id}")
    print(f"   After save - Project Alpha ID: {project1.id}")
    print(f"   After save - Project Beta ID: {project2.id}")
    print("   ^ All related entities automatically saved due to cascade=True!")
    
    # Verify relationships
    fetched_team = team_repo.find_by_id(dev_team.id)
    print(f"\n   Verified team members:")
    for member in fetched_team.members:
        print(f"     - {member.name} (Age: {member.age})")
    
    print(f"   Verified team projects:")
    for project in fetched_team.projects:
        print(f"     - {project.name}: {project.description}")
    
    # Example 4: Mixed scenario (some entities already saved)
    print("\n4. Mixed Scenario (some saved, some not)")
    print("   Creating employee for existing company...")
    
    # acme is already saved from example 2
    frank = Employee(name="Frank", position="Manager")
    frank.company = acme  # Already has ID
    
    frank = employee_repo.save(frank)
    print(f"   Saved: {frank.name} works for {acme.name}")
    print("   ^ Company already had ID, so it wasn't saved again")
    
    # Example 5: Circular references (handled safely)
    print("\n5. Circular References (safe handling)")
    print("   Creating bidirectional friendships...")
    
    grace = Person(name="Grace", age=27)
    henry = Person(name="Henry", age=31)
    
    # Save first person
    grace = person_repo.save(grace)
    henry = person_repo.save(henry)
    
    # Create bidirectional friendship
    grace.friends = [henry]
    henry.friends = [grace]
    
    grace = person_repo.save(grace)
    henry = person_repo.save(henry)
    
    print(f"   Created bidirectional friendship: {grace.name} <-> {henry.name}")
    print("   ^ Tracker prevents infinite loops in circular relationships")
    
    print("\n" + "=" * 60)
    print("Key Takeaways:")
    print("=" * 60)
    print("1. cascade=True automatically saves unsaved related entities")
    print("2. cascade=False requires entities to be saved manually first")
    print("3. Cascade works for both single and collection relationships")
    print("4. Already-saved entities (with IDs) are not re-saved")
    print("5. Circular references are handled safely with entity tracking")
    print("6. All relationship edges are created automatically")
    print("=" * 60)
    
    # Cleanup
    print("\nCleaning up...")
    person_repo.delete_all()
    company_repo.delete_all()
    employee_repo.delete_all()
    project_repo.delete_all()
    team_repo.delete_all()
    print("Done!")


if __name__ == "__main__":
    demonstrate_cascade_save()
