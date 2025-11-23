"""
Example demonstrating async repository usage with AsyncRepository.

This example shows how to use the async ORM for non-blocking database operations.
Perfect for async frameworks like FastAPI, aiohttp, etc.
"""

import asyncio
from typing import Optional, List

# Note: These imports require falkordb-py with async support
from falkordb.asyncio import FalkorDB
from redis.asyncio import BlockingConnectionPool

from falkordb_orm import node, relationship, AsyncRepository, generated_id


@node("Person")
class Person:
    """Person entity with relationships."""
    id: Optional[int] = generated_id()
    name: str
    email: str
    age: int
    
    friends: List["Person"] = relationship(type="KNOWS", direction="OUTGOING")
    company: Optional["Company"] = relationship(type="WORKS_FOR", direction="OUTGOING")


@node("Company")
class Company:
    """Company entity."""
    id: Optional[int] = generated_id()
    name: str
    industry: str
    
    employees: List[Person] = relationship(type="WORKS_FOR", direction="INCOMING")


async def basic_async_operations():
    """Demonstrate basic async CRUD operations."""
    print("\n=== Basic Async Operations ===\n")
    
    # Connect to FalkorDB with async client
    pool = BlockingConnectionPool(
        max_connections=16, 
        timeout=None, 
        decode_responses=True,
        host='localhost',
        port=6379
    )
    db = FalkorDB(connection_pool=pool)
    graph = db.select_graph('async_example')
    
    # Create async repository
    person_repo = AsyncRepository(graph, Person)
    company_repo = AsyncRepository(graph, Company)
    
    # Clean up from previous runs
    await person_repo.delete_all()
    await company_repo.delete_all()
    
    # Create and save entities
    print("Creating entities...")
    alice = Person(name="Alice", email="alice@example.com", age=30)
    bob = Person(name="Bob", email="bob@example.com", age=25)
    
    saved_alice = await person_repo.save(alice)
    saved_bob = await person_repo.save(bob)
    
    print(f"✓ Saved Alice with ID: {saved_alice.id}")
    print(f"✓ Saved Bob with ID: {saved_bob.id}")
    
    # Find by ID
    print("\nFinding by ID...")
    found = await person_repo.find_by_id(saved_alice.id)
    print(f"✓ Found: {found.name} ({found.email})")
    
    # Count
    count = await person_repo.count()
    print(f"\n✓ Total people: {count}")
    
    # Find all
    print("\nFinding all...")
    all_people = await person_repo.find_all()
    for person in all_people:
        print(f"  - {person.name} (age {person.age})")
    
    # Update
    print("\nUpdating entity...")
    alice.age = 31
    await person_repo.save(alice)
    updated = await person_repo.find_by_id(alice.id)
    print(f"✓ Updated Alice's age to: {updated.age}")


async def async_derived_queries():
    """Demonstrate async derived query methods."""
    print("\n=== Async Derived Queries ===\n")
    
    # Connect to FalkorDB
    pool = BlockingConnectionPool(
        max_connections=16, 
        timeout=None, 
        decode_responses=True,
        host='localhost',
        port=6379
    )
    db = FalkorDB(connection_pool=pool)
    graph = db.select_graph('async_example')
    
    person_repo = AsyncRepository(graph, Person)
    
    # Derived queries work exactly like sync version, but are awaitable
    print("Finding adults (age > 21)...")
    adults = await person_repo.find_by_age_greater_than(21)
    print(f"✓ Found {len(adults)} adults")
    for person in adults:
        print(f"  - {person.name}, age {person.age}")
    
    # Count with condition
    print("\nCounting people named Alice...")
    count = await person_repo.count_by_name("Alice")
    print(f"✓ Count: {count}")
    
    # Exists check
    print("\nChecking if email exists...")
    exists = await person_repo.exists_by_email("alice@example.com")
    print(f"✓ Email exists: {exists}")


async def async_aggregations():
    """Demonstrate async aggregation methods."""
    print("\n=== Async Aggregations ===\n")
    
    pool = BlockingConnectionPool(
        max_connections=16, 
        timeout=None, 
        decode_responses=True,
        host='localhost',
        port=6379
    )
    db = FalkorDB(connection_pool=pool)
    graph = db.select_graph('async_example')
    
    person_repo = AsyncRepository(graph, Person)
    
    # Aggregation methods
    print("Computing statistics on age...")
    avg_age = await person_repo.avg('age')
    min_age = await person_repo.min('age')
    max_age = await person_repo.max('age')
    
    print(f"✓ Average age: {avg_age:.1f}")
    print(f"✓ Minimum age: {min_age}")
    print(f"✓ Maximum age: {max_age}")


async def async_relationships():
    """Demonstrate async relationship operations."""
    print("\n=== Async Relationships ===\n")
    
    pool = BlockingConnectionPool(
        max_connections=16, 
        timeout=None, 
        decode_responses=True,
        host='localhost',
        port=6379
    )
    db = FalkorDB(connection_pool=pool)
    graph = db.select_graph('async_example')
    
    person_repo = AsyncRepository(graph, Person)
    company_repo = AsyncRepository(graph, Company)
    
    # Create company and person with relationship
    print("Creating company and employee with cascade save...")
    company = Company(name="TechCorp", industry="Technology")
    employee = Person(name="Charlie", email="charlie@tech.com", age=28)
    employee.company = company
    
    # Cascade save (company will be saved automatically)
    await person_repo.save(employee)
    print(f"✓ Saved Charlie (ID: {employee.id})")
    print(f"✓ Saved TechCorp (ID: {company.id})")
    
    # Eager loading with relationships
    print("\nFinding person with eager loaded company...")
    charlie = await person_repo.find_by_id(employee.id, fetch=["company"])
    print(f"✓ Found: {charlie.name}")
    if charlie.company:
        print(f"  - Works at: {charlie.company.name} ({charlie.company.industry})")
    
    # Lazy loading (async)
    print("\nFinding person with lazy loaded company...")
    charlie_lazy = await person_repo.find_by_id(employee.id)
    print(f"✓ Found: {charlie_lazy.name}")
    # To access lazy relationships, you need to explicitly load them
    if hasattr(charlie_lazy.company, 'get'):
        loaded_company = await charlie_lazy.company.get()
        if loaded_company:
            print(f"  - Works at: {loaded_company.name}")


async def concurrent_operations():
    """Demonstrate concurrent async operations."""
    print("\n=== Concurrent Operations ===\n")
    
    pool = BlockingConnectionPool(
        max_connections=16, 
        timeout=None, 
        decode_responses=True,
        host='localhost',
        port=6379
    )
    db = FalkorDB(connection_pool=pool)
    graph = db.select_graph('async_example')
    
    person_repo = AsyncRepository(graph, Person)
    
    # Create multiple entities concurrently
    print("Creating multiple entities concurrently...")
    
    people = [
        Person(name=f"Person{i}", email=f"person{i}@example.com", age=20+i)
        for i in range(5)
    ]
    
    # Save all concurrently using asyncio.gather
    saved_people = await asyncio.gather(*[
        person_repo.save(person)
        for person in people
    ])
    
    print(f"✓ Saved {len(saved_people)} people concurrently")
    for person in saved_people:
        print(f"  - {person.name} (ID: {person.id})")
    
    # Query multiple operations concurrently
    print("\nRunning multiple queries concurrently...")
    results = await asyncio.gather(
        person_repo.count(),
        person_repo.avg('age'),
        person_repo.find_by_age_greater_than(22)
    )
    
    count, avg_age, adults = results
    print(f"✓ Count: {count}")
    print(f"✓ Average age: {avg_age:.1f}")
    print(f"✓ Adults (>22): {len(adults)}")


async def main():
    """Run all async examples."""
    print("="*60)
    print("FalkorDB ORM - Async Repository Examples")
    print("="*60)
    
    try:
        await basic_async_operations()
        await async_derived_queries()
        await async_aggregations()
        await async_relationships()
        await concurrent_operations()
        
        print("\n" + "="*60)
        print("All async examples completed successfully!")
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Note: This requires FalkorDB running on localhost:6379
    # Run: docker run -p 6379:6379 falkordb/falkordb
    asyncio.run(main())
