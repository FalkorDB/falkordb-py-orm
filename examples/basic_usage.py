"""Basic usage example for falkordb-orm."""

from typing import Optional
from falkordb import FalkorDB
from falkordb_orm import node, property, Repository, generated_id


# Define entity classes
@node("Person")
class Person:
    """Person entity with auto-generated ID."""
    id: Optional[int] = generated_id()
    name: str
    email: str
    age: int


@node("Company")
class Company:
    """Company entity with manual ID."""
    id: Optional[str] = None
    name: str
    industry: str


def main():
    """Main function demonstrating basic ORM operations."""
    
    # Connect to FalkorDB
    print("Connecting to FalkorDB...")
    db = FalkorDB(host='localhost', port=6379)
    graph = db.select_graph('social')
    
    # Create repositories
    person_repo = Repository(graph, Person)
    company_repo = Repository(graph, Company)
    
    # Clear existing data for clean example
    print("\nClearing existing data...")
    person_repo.delete_all()
    company_repo.delete_all()
    
    # Create and save entities
    print("\n=== Creating Entities ===")
    
    alice = Person(id=None, name="Alice", email="alice@example.com", age=30)
    print(f"Created: {alice.name} (age {alice.age})")
    
    bob = Person(id=None, name="Bob", email="bob@example.com", age=25)
    print(f"Created: {bob.name} (age {bob.age})")
    
    company = Company(id="tech-corp", name="TechCorp", industry="Technology")
    print(f"Created company: {company.name}")
    
    # Save entities
    print("\n=== Saving Entities ===")
    saved_alice = person_repo.save(alice)
    print(f"Saved: {saved_alice.name} with ID: {saved_alice.id}")
    
    saved_bob = person_repo.save(bob)
    print(f"Saved: {saved_bob.name} with ID: {saved_bob.id}")
    
    saved_company = company_repo.save(company)
    print(f"Saved company: {saved_company.name} with ID: {saved_company.id}")
    
    # Find by ID
    print("\n=== Finding by ID ===")
    found_alice = person_repo.find_by_id(saved_alice.id)
    if found_alice:
        print(f"Found: {found_alice.name} - {found_alice.email}")
    
    found_company = company_repo.find_by_id("tech-corp")
    if found_company:
        print(f"Found company: {found_company.name} in {found_company.industry}")
    
    # Find all
    print("\n=== Finding All ===")
    all_people = person_repo.find_all()
    print(f"Found {len(all_people)} people:")
    for person in all_people:
        print(f"  - {person.name} (age {person.age})")
    
    # Count
    print("\n=== Counting ===")
    person_count = person_repo.count()
    print(f"Total people: {person_count}")
    
    # Update entity
    print("\n=== Updating Entity ===")
    found_alice.age = 31
    updated_alice = person_repo.save(found_alice)
    print(f"Updated {updated_alice.name}'s age to {updated_alice.age}")
    
    # Verify update
    verified = person_repo.find_by_id(updated_alice.id)
    print(f"Verified: {verified.name} is now {verified.age} years old")
    
    # Check existence
    print("\n=== Checking Existence ===")
    exists = person_repo.exists_by_id(saved_alice.id)
    print(f"Alice exists: {exists}")
    
    # Delete entity
    print("\n=== Deleting Entity ===")
    person_repo.delete(saved_bob)
    print(f"Deleted {saved_bob.name}")
    
    # Verify deletion
    remaining = person_repo.find_all()
    print(f"Remaining people: {len(remaining)}")
    
    # Clean up
    print("\n=== Cleanup ===")
    person_repo.delete_all()
    company_repo.delete_all()
    print("All data deleted")
    
    print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
