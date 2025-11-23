# Quick Start Guide

Get started with falkordb-py-orm in 5 minutes!

## Installation

```bash
# Clone the repository
git clone https://github.com/FalkorDB/falkordb-py-orm.git
cd falkordb-py-orm

# Install dependencies
pip install -e .
```

## Prerequisites

- Python 3.8 or higher
- FalkorDB instance running (default: localhost:6379)

## Basic Usage

### 1. Define Your Entities

```python
from typing import Optional
from falkordb_orm import node, property, generated_id

@node("Person")
class Person:
    """A person entity with auto-generated ID."""
    id: Optional[int] = generated_id()
    name: str
    email: str
    age: int

@node("Company")
class Company:
    """A company entity with manual ID."""
    id: str
    name: str
    industry: str
```

### 2. Connect to FalkorDB

```python
from falkordb import FalkorDB

db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('myapp')
```

### 3. Create a Repository

```python
from falkordb_orm import Repository

person_repo = Repository(graph, Person)
company_repo = Repository(graph, Company)
```

### 4. Perform CRUD Operations

#### Create

```python
# Create a person
alice = Person(id=None, name="Alice", email="alice@example.com", age=30)
saved_alice = person_repo.save(alice)
print(f"Created person with ID: {saved_alice.id}")

# Create a company
company = Company(id="tech-corp", name="TechCorp", industry="Technology")
saved_company = company_repo.save(company)
```

#### Read

```python
# Find by ID
person = person_repo.find_by_id(saved_alice.id)
print(f"Found: {person.name}")

# Find all
all_people = person_repo.find_all()
for p in all_people:
    print(f"- {p.name} ({p.age} years old)")

# Check existence
exists = person_repo.exists_by_id(saved_alice.id)
print(f"Person exists: {exists}")

# Count entities
count = person_repo.count()
print(f"Total people: {count}")
```

#### Update

```python
# Update entity
alice.age = 31
updated = person_repo.save(alice)
print(f"Updated age to {updated.age}")
```

#### Delete

```python
# Delete by entity
person_repo.delete(alice)

# Delete by ID
person_repo.delete_by_id(123)

# Delete all
person_repo.delete_all()
```

## Advanced Features

### Relationships (Phase 3)

#### Declaring Relationships

```python
from typing import List, Optional
from falkordb_orm import node, generated_id, relationship

@node("Person")
class Person:
    id: Optional[int] = generated_id()
    name: str
    age: int
    # Collection relationship
    friends: List['Person'] = relationship('KNOWS', target='Person')
    # Single relationship with cascade
    company: Optional['Company'] = relationship(
        'WORKS_FOR', 
        target='Company',
        cascade=True  # Auto-save company
    )

@node("Company")
class Company:
    id: Optional[int] = generated_id()
    name: str
    # Reverse relationship
    employees: List[Person] = relationship(
        'WORKS_FOR',
        direction='INCOMING',
        target=Person
    )
```

#### Lazy Loading (Default)

```python
# Fetch person - relationships not loaded yet
person = person_repo.find_by_id(1)

# Access relationship - triggers load
for friend in person.friends:  # Query executed here
    print(friend.name)

# Subsequent access uses cache - no query
friend_count = len(person.friends)  # No query
```

#### Eager Loading (Solve N+1 Queries)

```python
# Load person with relationships in single query
person = person_repo.find_by_id(1, fetch=['friends', 'company'])

# No additional queries needed
for friend in person.friends:  # Already loaded!
    print(friend.name)

if person.company:
    print(person.company.get().name)  # Already loaded!

# Eager load for multiple entities
people = person_repo.find_all(fetch=['friends'])
for person in people:
    print(f"{person.name} has {len(person.friends)} friends")
# ^ Only 1 query instead of N+1!
```

#### Cascade Save

```python
# Create related entities without saving them first
company = Company(name="Acme Corp")
employee = Person(name="Alice", age=30)
employee.company = company  # Not saved yet!

# Save employee - company is automatically saved
employee = person_repo.save(employee)

print(f"Employee ID: {employee.id}")
print(f"Company ID: {company.id}")  # Auto-assigned!
```

#### Bidirectional Relationships

```python
# Create friendship in both directions
alice = person_repo.find_by_id(1)
bob = person_repo.find_by_id(2)

alice.friends = [bob]
alice = person_repo.save(alice)

bob.friends = [alice]
bob = person_repo.save(bob)

# Both can see each other as friends
```

### Custom Property Names

Map Python attributes to different graph property names:

```python
@node("Person")
class Person:
    id: Optional[int] = None
    name: str = property("full_name")  # Maps to 'full_name' in graph
    email: str
```

### Multiple Labels

Assign multiple labels to a node:

```python
@node(labels=["Person", "Employee", "Manager"])
class Manager:
    id: Optional[int] = None
    name: str
    department: str
```

### Custom Type Converters

Create custom converters for special types:

```python
from falkordb_orm import TypeConverter, register_converter

class Point:
    def __init__(self, lat: float, lon: float):
        self.latitude = lat
        self.longitude = lon

class PointConverter(TypeConverter):
    def to_graph(self, value: Point) -> dict:
        return {"lat": value.latitude, "lon": value.longitude}
    
    def from_graph(self, value: dict) -> Point:
        return Point(lat=value["lat"], lon=value["lon"])

# Register the converter
register_converter(Point, PointConverter())
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=falkordb_orm tests/

# Run specific test file
pytest tests/test_decorators.py
```

## Running the Example

```bash
# Make sure FalkorDB is running on localhost:6379
python examples/basic_usage.py
```

## Common Patterns

### Batch Operations

```python
# Save multiple entities at once
people = [
    Person(id=None, name="Alice", email="alice@example.com", age=30),
    Person(id=None, name="Bob", email="bob@example.com", age=25),
    Person(id=None, name="Charlie", email="charlie@example.com", age=35)
]

saved_people = person_repo.save_all(people)
print(f"Saved {len(saved_people)} people")
```

### Find Multiple by IDs

```python
ids = [1, 2, 3]
people = person_repo.find_all_by_id(ids)
```

### Conditional Delete

```python
# Find and delete
people = person_repo.find_all()
to_delete = [p for p in people if p.age < 18]
person_repo.delete_all(to_delete)
```

## Error Handling

```python
from falkordb_orm import (
    EntityNotFoundException,
    QueryException,
    InvalidEntityException
)

try:
    person = person_repo.find_by_id(999)
    if person is None:
        print("Person not found")
except QueryException as e:
    print(f"Query error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

1. **Use Type Hints**: Always add type hints to your entity classes for better IDE support
2. **Define ID Fields**: Always include an `id` field in your entities
3. **Use Repositories**: Access data through repositories, not direct queries
4. **Handle None Values**: Use `Optional[T]` for nullable fields
5. **Batch Operations**: Use `save_all()` and `delete_all()` for bulk operations

## Next Steps

- Read the [Design Document](DESIGN.md) for detailed architecture
- Check [Phase 1 Complete](PHASE1_COMPLETE.md) for implementation status
- Look at [examples/basic_usage.py](examples/basic_usage.py) for a complete example
- Explore the API documentation (coming soon)

## Getting Help

- Check the [README](README.md) for project overview
- Report issues on GitHub
- Join the FalkorDB Discord community

---

**Happy coding with falkordb-py-orm! 🚀**
