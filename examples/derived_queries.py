"""Example demonstrating derived query methods in falkordb-orm."""

from typing import Optional
from falkordb import FalkorDB
from falkordb_orm import node, Repository, generated_id


# Define entity
@node("Person")
class Person:
    """Person entity for demonstration."""
    id: Optional[int] = generated_id()
    name: str
    email: str
    age: int
    city: str


def main():
    """Main function demonstrating derived queries."""
    
    # Connect to FalkorDB
    print("Connecting to FalkorDB...")
    db = FalkorDB(host='localhost', port=6379)
    graph = db.select_graph('derived_queries_demo')
    
    # Create repository
    repo = Repository(graph, Person)
    
    # Clear existing data
    print("\nClearing existing data...")
    repo.delete_all()
    
    # Create sample data
    print("\n=== Creating Sample Data ===")
    people = [
        Person(id=None, name="Alice", email="alice@example.com", age=30, city="New York"),
        Person(id=None, name="Bob", email="bob@example.com", age=25, city="San Francisco"),
        Person(id=None, name="Charlie", email="charlie@example.com", age=35, city="New York"),
        Person(id=None, name="David", email="david@example.com", age=28, city="Boston"),
        Person(id=None, name="Eve", email="eve@example.com", age=32, city="San Francisco"),
        Person(id=None, name="Frank", email="frank@example.com", age=45, city="New York"),
        Person(id=None, name="Grace", email="grace@example.com", age=22, city="Boston"),
        Person(id=None, name="Heidi", email="heidi@example.com", age=38, city="San Francisco"),
    ]
    
    saved_people = repo.save_all(people)
    print(f"Created {len(saved_people)} people")
    
    # Simple find_by queries
    print("\n=== Simple Find By ===")
    alice = repo.find_by_name("Alice")
    print(f"find_by_name('Alice'): {alice[0].name if alice else 'Not found'}")
    
    ny_people = repo.find_by_city("New York")
    print(f"find_by_city('New York'): {len(ny_people)} people")
    
    # Comparison operators
    print("\n=== Comparison Operators ===")
    adults = repo.find_by_age_greater_than(30)
    print(f"find_by_age_greater_than(30): {len(adults)} people")
    for p in adults:
        print(f"  - {p.name} (age {p.age})")
    
    young = repo.find_by_age_less_than(30)
    print(f"find_by_age_less_than(30): {len(young)} people")
    
    middle_aged = repo.find_by_age_between(28, 35)
    print(f"find_by_age_between(28, 35): {len(middle_aged)} people")
    
    # String operations
    print("\n=== String Operations ===")
    names_with_a = repo.find_by_name_containing("a")
    print(f"find_by_name_containing('a'): {len(names_with_a)} people")
    for p in names_with_a:
        print(f"  - {p.name}")
    
    names_starting_with_a = repo.find_by_name_starting_with("A")
    print(f"find_by_name_starting_with('A'): {len(names_starting_with_a)} people")
    
    emails_ending_with_com = repo.find_by_email_ending_with("@example.com")
    print(f"find_by_email_ending_with('@example.com'): {len(emails_ending_with_com)} people")
    
    # Logical operators
    print("\n=== Logical Operators (AND) ===")
    ny_adults = repo.find_by_city_and_age_greater_than("New York", 30)
    print(f"find_by_city_and_age_greater_than('New York', 30): {len(ny_adults)} people")
    for p in ny_adults:
        print(f"  - {p.name} (age {p.age}, {p.city})")
    
    print("\n=== Logical Operators (OR) ===")
    alice_or_bob = repo.find_by_name_or_email("Alice", "bob@example.com")
    print(f"find_by_name_or_email('Alice', 'bob@example.com'): {len(alice_or_bob)} people")
    for p in alice_or_bob:
        print(f"  - {p.name}")
    
    # Sorting
    print("\n=== Sorting ===")
    sorted_by_age = repo.find_by_city_order_by_age_asc("New York")
    print(f"find_by_city_order_by_age_asc('New York'):")
    for p in sorted_by_age:
        print(f"  - {p.name} (age {p.age})")
    
    sorted_desc = repo.find_by_age_greater_than_order_by_age_desc(25)
    print(f"find_by_age_greater_than_order_by_age_desc(25) [first 3]:")
    for p in sorted_desc[:3]:
        print(f"  - {p.name} (age {p.age})")
    
    # Multiple sort fields
    sorted_multi = repo.find_by_age_greater_than_order_by_city_asc_age_desc(25)
    print(f"find_by_age_greater_than_order_by_city_asc_age_desc(25):")
    for p in sorted_multi:
        print(f"  - {p.name} (age {p.age}, {p.city})")
    
    # Limiting results
    print("\n=== Limiting Results ===")
    first_person = repo.find_first_by_city("San Francisco")
    print(f"find_first_by_city('San Francisco'): {first_person[0].name if first_person else 'None'}")
    
    top_3_oldest = repo.find_top_3_by_age_greater_than_order_by_age_desc(20)
    print(f"find_top_3_by_age_greater_than_order_by_age_desc(20):")
    for p in top_3_oldest:
        print(f"  - {p.name} (age {p.age})")
    
    # Count queries
    print("\n=== Count Queries ===")
    total_adults = repo.count_by_age_greater_than(30)
    print(f"count_by_age_greater_than(30): {total_adults}")
    
    ny_count = repo.count_by_city("New York")
    print(f"count_by_city('New York'): {ny_count}")
    
    # Exists queries
    print("\n=== Exists Queries ===")
    alice_exists = repo.exists_by_name("Alice")
    print(f"exists_by_name('Alice'): {alice_exists}")
    
    john_exists = repo.exists_by_name("John")
    print(f"exists_by_name('John'): {john_exists}")
    
    # Complex queries
    print("\n=== Complex Queries ===")
    complex_result = repo.find_by_age_between_and_city("25", "35", "New York")
    print(f"find_by_age_between_and_city(25, 35, 'New York'): {len(complex_result)} people")
    for p in complex_result:
        print(f"  - {p.name} (age {p.age})")
    
    # IN operator
    print("\n=== IN Operator ===")
    cities = ["New York", "Boston"]
    in_cities = repo.find_by_city_in(cities)
    print(f"find_by_city_in(['New York', 'Boston']): {len(in_cities)} people")
    for p in in_cities:
        print(f"  - {p.name} ({p.city})")
    
    # Delete queries
    print("\n=== Delete Queries ===")
    before_count = repo.count()
    print(f"Total people before delete: {before_count}")
    
    # Delete young people (age < 23)
    repo.delete_by_age_less_than(23)
    
    after_count = repo.count()
    print(f"Total people after delete_by_age_less_than(23): {after_count}")
    
    # Clean up
    print("\n=== Cleanup ===")
    repo.delete_all()
    print("All data deleted")
    
    print("\n✅ Derived queries example completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
