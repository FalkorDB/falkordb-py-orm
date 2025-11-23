"""
Example demonstrating lazy loading of relationships.

This example shows how relationships are loaded on-demand when accessed,
rather than being loaded immediately when the entity is fetched.
"""

from typing import List, Optional
from falkordb import FalkorDB
from falkordb_orm import node, generated_id, relationship, Repository


# Define entities with relationships
@node("Person")
class Person:
    id: Optional[int] = generated_id()
    name: str
    age: int
    friends: List['Person'] = relationship('KNOWS', target='Person')


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
    company: Optional[Company] = relationship('WORKS_FOR', target=Company)


def demonstrate_lazy_loading():
    """Demonstrate lazy loading behavior."""
    
    # Connect to FalkorDB
    db = FalkorDB(host='localhost', port=6379)
    graph = db.select_graph('lazy_loading_demo')
    
    # Create repositories
    person_repo = Repository(graph, Person)
    company_repo = Repository(graph, Company)
    employee_repo = Repository(graph, Employee)
    
    # Clean up previous data
    person_repo.delete_all()
    company_repo.delete_all()
    employee_repo.delete_all()
    
    print("=" * 60)
    print("Lazy Loading Example")
    print("=" * 60)
    
    # Create and save a company
    print("\n1. Creating a company...")
    acme = Company(name="Acme Corp", industry="Technology")
    acme = company_repo.save(acme)
    print(f"   Created: {acme.name} (ID: {acme.id})")
    
    # Create and save employees
    print("\n2. Creating employees...")
    alice = Employee(name="Alice", position="Engineer")
    alice = employee_repo.save(alice)
    print(f"   Created: {alice.name} (ID: {alice.id})")
    
    bob = Employee(name="Bob", position="Manager")
    bob = employee_repo.save(bob)
    print(f"   Created: {bob.name} (ID: {bob.id})")
    
    # Manually create relationships (Phase 3c will automate this)
    print("\n3. Creating relationships manually...")
    graph.query(
        "MATCH (e:Employee), (c:Company) WHERE id(e) = $emp_id AND id(c) = $comp_id "
        "CREATE (e)-[:WORKS_FOR]->(c)",
        {'emp_id': alice.id, 'comp_id': acme.id}
    )
    graph.query(
        "MATCH (e:Employee), (c:Company) WHERE id(e) = $emp_id AND id(c) = $comp_id "
        "CREATE (e)-[:WORKS_FOR]->(c)",
        {'emp_id': bob.id, 'comp_id': acme.id}
    )
    print("   Relationships created")
    
    # Create people with friendships
    print("\n4. Creating people with friendships...")
    person1 = Person(name="John", age=30)
    person1 = person_repo.save(person1)
    
    person2 = Person(name="Jane", age=28)
    person2 = person_repo.save(person2)
    
    person3 = Person(name="Jack", age=32)
    person3 = person_repo.save(person3)
    
    # Create friendship relationships
    graph.query(
        "MATCH (p1:Person), (p2:Person) WHERE id(p1) = $id1 AND id(p2) = $id2 "
        "CREATE (p1)-[:KNOWS]->(p2)",
        {'id1': person1.id, 'id2': person2.id}
    )
    graph.query(
        "MATCH (p1:Person), (p2:Person) WHERE id(p1) = $id1 AND id(p2) = $id2 "
        "CREATE (p1)-[:KNOWS]->(p2)",
        {'id1': person1.id, 'id2': person3.id}
    )
    print(f"   Created: {person1.name}, {person2.name}, {person3.name}")
    print("   Friendship relationships created")
    
    # Demonstrate lazy loading
    print("\n" + "=" * 60)
    print("Demonstrating Lazy Loading")
    print("=" * 60)
    
    # Fetch employee
    print("\n5. Fetching employee by ID...")
    fetched_alice = employee_repo.find_by_id(alice.id)
    print(f"   Fetched: {fetched_alice.name} (Position: {fetched_alice.position})")
    print(f"   Company relationship: {fetched_alice.company}")
    print("   ^ Notice: LazyProxy shows '<not loaded>' - no query executed yet")
    
    # Access company - triggers lazy load
    print("\n6. Accessing employee's company (triggers lazy load)...")
    print(f"   Accessing fetched_alice.company...")
    company = fetched_alice.company.get()
    print(f"   Company loaded: {company.name} (Industry: {company.industry})")
    print("   ^ Query was executed when we called .get()")
    
    # Access again - uses cached data
    print("\n7. Accessing company again (uses cache, no query)...")
    company_again = fetched_alice.company.get()
    print(f"   Company: {company_again.name}")
    print("   ^ No query executed - data was cached")
    
    # Fetch person with multiple friends
    print("\n8. Fetching person by ID...")
    fetched_john = person_repo.find_by_id(person1.id)
    print(f"   Fetched: {fetched_john.name} (Age: {fetched_john.age})")
    print(f"   Friends relationship: {fetched_john.friends}")
    print("   ^ LazyList shows '<not loaded>'")
    
    # Iterate friends - triggers lazy load
    print("\n9. Iterating over friends (triggers lazy load)...")
    print("   Friends:")
    for friend in fetched_john.friends:
        print(f"     - {friend.name} (Age: {friend.age})")
    print("   ^ Query was executed when we started iterating")
    
    # Access friends again - uses cached data
    print("\n10. Checking friend count (uses cache)...")
    friend_count = len(fetched_john.friends)
    print(f"   Friend count: {friend_count}")
    print("   ^ No query executed - data was cached")
    
    # Check empty relationships
    print("\n11. Fetching person with no friends...")
    person4 = Person(name="Loner", age=25)
    person4 = person_repo.save(person4)
    
    fetched_loner = person_repo.find_by_id(person4.id)
    print(f"   Fetched: {fetched_loner.name}")
    print(f"   Friends: {list(fetched_loner.friends)}")
    print("   ^ Empty list - relationship exists but has no connected nodes")
    
    print("\n" + "=" * 60)
    print("Key Takeaways:")
    print("=" * 60)
    print("1. Relationships are represented by lazy proxies (LazyList/LazySingle)")
    print("2. No query is executed until the relationship is accessed")
    print("3. Once loaded, data is cached - subsequent accesses don't query DB")
    print("4. Empty relationships return empty list or None")
    print("5. This avoids the N+1 query problem for unused relationships")
    print("=" * 60)
    
    # Cleanup
    print("\nCleaning up...")
    person_repo.delete_all()
    company_repo.delete_all()
    employee_repo.delete_all()
    print("Done!")


if __name__ == "__main__":
    demonstrate_lazy_loading()
