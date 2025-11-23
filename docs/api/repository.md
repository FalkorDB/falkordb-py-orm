# Repository API Reference

Complete documentation for the `Repository` and `AsyncRepository` classes, which provide the primary interface for database operations.

## Repository[T]

Generic repository for performing CRUD operations and derived queries on entities.

### Signature

```python
class Repository(Generic[T]):
    def __init__(self, graph: Graph, entity_class: Type[T])
```

### Parameters

- **graph** (`Graph`): FalkorDB graph instance
- **entity_class** (`Type[T]`): The entity class this repository manages

### Example

```python
from falkordb import FalkorDB
from falkordb_orm import node, Repository

@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    age: int

db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('social')
repo = Repository(graph, Person)
```

---

## Core CRUD Methods

### save()

Save an entity to the database.

#### Signature

```python
def save(self, entity: T) -> T
```

#### Parameters

- **entity** (`T`): The entity to save

#### Returns

The saved entity with its ID populated.

#### Behavior

- If entity has no ID: Creates new node (INSERT)
- If entity has ID: Updates existing node (UPDATE)
- If `cascade=True` on relationships: Saves related entities first
- Creates relationship edges if relationships are set

#### Example

```python
# Create new
person = Person(name="Alice", age=25)
saved = repo.save(person)
print(saved.id)  # ID populated

# Update existing
saved.age = 26
updated = repo.save(saved)
```

#### Errors

- `InvalidEntityException`: If entity is invalid
- `QueryException`: If database operation fails

---

### find_by_id()

Find an entity by its ID.

#### Signature

```python
def find_by_id(
    self,
    entity_id: int,
    fetch: Optional[List[str]] = None
) -> Optional[T]
```

#### Parameters

- **entity_id** (`int`): The entity ID
- **fetch** (`List[str]`, optional): Relationships to eager load

#### Returns

The entity if found, `None` otherwise.

#### Example

```python
# Basic
person = repo.find_by_id(1)

# Eager load relationships
person = repo.find_by_id(1, fetch=["friends", "company"])
for friend in person.friends:  # No additional query
    print(friend.name)
```

---

### find_all()

Find all entities of this type.

#### Signature

```python
def find_all(self, fetch: Optional[List[str]] = None) -> List[T]
```

#### Parameters

- **fetch** (`List[str]`, optional): Relationships to eager load

#### Returns

List of all entities.

#### Example

```python
# Get all
people = repo.find_all()

# With relationships
people = repo.find_all(fetch=["company"])
```

#### Warning

This loads all entities into memory. Use with caution on large datasets.

---

### delete()

Delete an entity from the database.

#### Signature

```python
def delete(self, entity: T) -> None
```

#### Parameters

- **entity** (`T`): The entity to delete

#### Behavior

- Removes the node from the graph
- Relationships to/from this node are also removed
- Does NOT cascade delete related entities

#### Example

```python
person = repo.find_by_id(1)
repo.delete(person)
```

---

### delete_by_id()

Delete an entity by its ID.

#### Signature

```python
def delete_by_id(self, entity_id: int) -> None
```

#### Parameters

- **entity_id** (`int`): The ID of the entity to delete

#### Example

```python
repo.delete_by_id(1)
```

---

### count()

Count all entities of this type.

#### Signature

```python
def count(self) -> int
```

#### Returns

Total count of entities.

#### Example

```python
total = repo.count()
print(f"Total people: {total}")
```

---

### exists()

Check if an entity with the given ID exists.

#### Signature

```python
def exists(self, entity_id: int) -> bool
```

#### Parameters

- **entity_id** (`int`): The entity ID to check

#### Returns

`True` if exists, `False` otherwise.

#### Example

```python
if repo.exists(1):
    print("Person 1 exists")
```

---

## Derived Query Methods

The repository automatically implements query methods based on method names.

### Pattern

```
{action}_by_{field}[_{operator}][_and_{field}[_{operator}]]*
```

### Actions

- `find_by` - Returns List[T]
- `find_first_by` - Returns Optional[T]
- `count_by` - Returns int
- `exists_by` - Returns bool
- `delete_by` - Returns None

### Examples

```python
# Find by exact match
people = repo.find_by_name("Alice")
people = repo.find_by_age(25)

# Comparison operators
adults = repo.find_by_age_greater_than(18)
seniors = repo.find_by_age_greater_than_or_equal(65)
young = repo.find_by_age_less_than(18)
children = repo.find_by_age_less_than_or_equal(12)

# Range queries
people = repo.find_by_age_between(18, 65)

# IN queries
people = repo.find_by_name_in(["Alice", "Bob", "Charlie"])
people = repo.find_by_age_not_in([18, 19, 20])

# String operations
people = repo.find_by_name_containing("ali")  # Case insensitive
people = repo.find_by_name_starting_with("A")
people = repo.find_by_name_ending_with("son")

# Negation
people = repo.find_by_name_not("Alice")
people = repo.find_by_age_not(25)

# Logical operators
people = repo.find_by_name_and_age("Alice", 25)
people = repo.find_by_age_greater_than_and_name("18", "Alice")
people = repo.find_by_name_or_email("Alice", "alice@example.com")

# Counting
count = repo.count_by_age(25)
count = repo.count_by_age_greater_than(18)

# Existence
exists = repo.exists_by_name("Alice")
exists = repo.exists_by_email("alice@example.com")

# Deletion
repo.delete_by_name("Alice")
repo.delete_by_age_less_than(18)

# First result
person = repo.find_first_by_name("Alice")  # Returns Optional[Person]
```

### Supported Operators

| Operator | Example | Cypher |
|----------|---------|--------|
| (none) | `find_by_age(25)` | `age = 25` |
| `greater_than` | `find_by_age_greater_than(18)` | `age > 18` |
| `greater_than_or_equal` | `find_by_age_greater_than_or_equal(18)` | `age >= 18` |
| `less_than` | `find_by_age_less_than(18)` | `age < 18` |
| `less_than_or_equal` | `find_by_age_less_than_or_equal(18)` | `age <= 18` |
| `between` | `find_by_age_between(18, 65)` | `age >= 18 AND age <= 65` |
| `in` | `find_by_name_in(["Alice", "Bob"])` | `name IN ["Alice", "Bob"]` |
| `not_in` | `find_by_age_not_in([1, 2, 3])` | `NOT age IN [1, 2, 3]` |
| `containing` | `find_by_name_containing("ali")` | `toLower(name) CONTAINS "ali"` |
| `starting_with` | `find_by_name_starting_with("A")` | `name STARTS WITH "A"` |
| `ending_with` | `find_by_name_ending_with("son")` | `name ENDS WITH "son"` |
| `not` | `find_by_name_not("Alice")` | `name <> "Alice"` |

### Errors

- `QueryException`: If method name cannot be parsed
- `MetadataException`: If field name doesn't exist in entity

---

## Aggregation Methods

Perform aggregate calculations on entity properties.

### sum()

Calculate sum of a numeric property.

```python
def sum(self, property_name: str) -> float

total_age = repo.sum("age")
```

### avg()

Calculate average of a numeric property.

```python
def avg(self, property_name: str) -> float

average_age = repo.avg("age")
```

### min()

Find minimum value of a property.

```python
def min(self, property_name: str) -> Any

min_age = repo.min("age")
```

### max()

Find maximum value of a property.

```python
def max(self, property_name: str) -> Any

max_age = repo.max("age")
```

---

## AsyncRepository[T]

Async version of Repository for use with async/await.

### Signature

```python
class AsyncRepository(Generic[T]):
    def __init__(self, graph: AsyncGraph, entity_class: Type[T])
```

### Usage

All methods are identical to `Repository` but are async and must be awaited.

### Example

```python
import asyncio
from falkordb.asyncio import FalkorDB
from redis.asyncio import BlockingConnectionPool
from falkordb_orm import node, AsyncRepository

@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    age: int

async def main():
    pool = BlockingConnectionPool(max_connections=16, timeout=None, decode_responses=True)
    db = FalkorDB(connection_pool=pool)
    graph = db.select_graph('social')
    repo = AsyncRepository(graph, Person)
    
    # All operations are async
    person = Person(name="Alice", age=25)
    saved = await repo.save(person)
    
    found = await repo.find_by_id(saved.id)
    all_people = await repo.find_all()
    
    adults = await repo.find_by_age_greater_than(18)
    count = await repo.count()
    
    await repo.delete(saved)

asyncio.run(main())
```

### Concurrent Operations

```python
# Run multiple queries concurrently
results = await asyncio.gather(
    repo.find_by_name("Alice"),
    repo.find_by_age_greater_than(18),
    repo.count()
)
```

### Async Relationships

Async lazy loading requires explicit calls:

```python
person = await repo.find_by_id(1)

# Async iteration
async for friend in person.friends:
    print(friend.name)

# Or load all at once
friends = await person.friends.load()
```

---

## Best Practices

### 1. Reuse Repository Instances

```python
# Good - reuse
repo = Repository(graph, Person)
for data in user_data:
    person = Person(**data)
    repo.save(person)

# Avoid - creating new instance each time
for data in user_data:
    repo = Repository(graph, Person)  # Unnecessary
    repo.save(Person(**data))
```

### 2. Use Eager Loading to Avoid N+1

```python
# Bad - N+1 queries
people = repo.find_all()
for person in people:
    print(person.company.name)  # Triggers query for each person

# Good - Single query
people = repo.find_all(fetch=["company"])
for person in people:
    print(person.company.name)  # No additional queries
```

### 3. Use Derived Queries for Readability

```python
# Good - readable
adults = repo.find_by_age_greater_than_or_equal(18)

# Less ideal - custom query for simple case
@query("MATCH (p:Person) WHERE p.age >= $age RETURN p")
def find_adults(self, age: int) -> List[Person]:
    pass
```

### 4. Batch Operations When Possible

```python
# For bulk inserts, consider batching
people = [Person(name=f"User{i}", age=20+i) for i in range(100)]
for person in people:
    repo.save(person)
# Note: Current implementation doesn't support bulk operations
# This is a future enhancement
```

---

## See Also

- [Decorators API](decorators.md)
- [Query Methods](query_methods.md)
- [Custom Queries](custom_queries.md)
- [Relationships Guide](relationships.md)
