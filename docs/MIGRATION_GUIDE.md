# Migration Guide: From Raw FalkorDB Client to ORM

This guide helps you migrate from using the raw FalkorDB Python client to using the FalkorDB ORM.

## Table of Contents

1. [Why Migrate?](#why-migrate)
2. [Installation](#installation)
3. [Basic Concepts](#basic-concepts)
4. [Migration Patterns](#migration-patterns)
5. [Common Scenarios](#common-scenarios)
6. [Performance Considerations](#performance-considerations)
7. [Best Practices](#best-practices)

---

## Why Migrate?

### Benefits of Using the ORM

- **Type Safety**: Full type hints and IDE support
- **Less Boilerplate**: No manual Cypher query writing for common operations
- **Automatic Mapping**: Objects automatically mapped to/from graph structures
- **Relationship Management**: Lazy/eager loading, cascade operations
- **Query Derivation**: Auto-generate queries from method names
- **Better Testing**: Easier to mock and test

### When to Use Raw Client

- **Complex graph algorithms**: When you need specific Cypher features not supported by ORM
- **Performance critical paths**: When you need absolute control over queries
- **One-off operations**: For simple scripts or admin tasks

**Note**: You can mix both approaches! The ORM and raw client can coexist in the same project.

---

## Installation

```bash
# Install the ORM (includes falkordb client as dependency)
pip install falkordb-orm

# Or with poetry
poetry add falkordb-orm
```

---

## Basic Concepts

### Raw Client Approach

```python
from falkordb import FalkorDB

db = FalkorDB(host='localhost', port=6379)
g = db.select_graph('social')

# Manual query
result = g.query('''
    CREATE (p:Person {name: $name, age: $age})
    RETURN p, id(p)
''', {'name': 'Alice', 'age': 25})

# Manual result processing
for record in result.result_set:
    node = record[0]
    node_id = record[1]
    print(f"Created {node.properties['name']} with ID {node_id}")
```

### ORM Approach

```python
from falkordb import FalkorDB
from falkordb_orm import node, Repository
from typing import Optional

@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    age: int

db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('social')
repo = Repository(graph, Person)

# Type-safe creation
person = Person(name="Alice", age=25)
saved = repo.save(person)
print(f"Created {saved.name} with ID {saved.id}")
```

---

## Migration Patterns

### Pattern 1: CREATE (Insert)

#### Before (Raw Client)

```python
result = g.query('''
    CREATE (p:Person {name: $name, email: $email, age: $age})
    RETURN p, id(p)
''', {'name': 'Alice', 'email': 'alice@example.com', 'age': 25})

person_id = result.result_set[0][1]
```

#### After (ORM)

```python
@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    email: str
    age: int

person = Person(name="Alice", email="alice@example.com", age=25)
saved = repo.save(person)
person_id = saved.id
```

---

### Pattern 2: MATCH (Find by ID)

#### Before (Raw Client)

```python
result = g.query('''
    MATCH (p:Person)
    WHERE id(p) = $id
    RETURN p
''', {'id': 123})

if result.result_set:
    node = result.result_set[0][0]
    person = {
        'id': node.id,
        'name': node.properties['name'],
        'email': node.properties['email'],
        'age': node.properties['age']
    }
```

#### After (ORM)

```python
person = repo.find_by_id(123)
# person is a fully typed Person object
if person:
    print(person.name)  # IDE autocomplete works!
```

---

### Pattern 3: MATCH with WHERE (Find by Property)

#### Before (Raw Client)

```python
result = g.query('''
    MATCH (p:Person)
    WHERE p.age > $min_age
    RETURN p
''', {'min_age': 18})

people = []
for record in result.result_set:
    node = record[0]
    people.append({
        'id': node.id,
        'name': node.properties.get('name'),
        'age': node.properties.get('age')
    })
```

#### After (ORM)

```python
# Derived query - automatically implemented
people = repo.find_by_age_greater_than(18)
# Returns List[Person], fully typed
```

---

### Pattern 4: UPDATE

#### Before (Raw Client)

```python
g.query('''
    MATCH (p:Person)
    WHERE id(p) = $id
    SET p.age = $age, p.email = $email
''', {'id': 123, 'age': 26, 'email': 'newemail@example.com'})
```

#### After (ORM)

```python
person = repo.find_by_id(123)
if person:
    person.age = 26
    person.email = 'newemail@example.com'
    repo.save(person)  # Automatically generates UPDATE
```

---

### Pattern 5: DELETE

#### Before (Raw Client)

```python
g.query('''
    MATCH (p:Person)
    WHERE id(p) = $id
    DELETE p
''', {'id': 123})
```

#### After (ORM)

```python
# Option 1: Delete by ID
repo.delete_by_id(123)

# Option 2: Delete entity
person = repo.find_by_id(123)
if person:
    repo.delete(person)
```

---

### Pattern 6: CREATE Relationship

#### Before (Raw Client)

```python
g.query('''
    MATCH (a:Person), (b:Person)
    WHERE id(a) = $person1_id AND id(b) = $person2_id
    CREATE (a)-[:KNOWS]->(b)
''', {'person1_id': 1, 'person2_id': 2})
```

#### After (ORM)

```python
from typing import List

@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    friends: List["Person"] = relationship(type="KNOWS", direction="OUTGOING", cascade=True)

alice = repo.find_by_id(1)
bob = repo.find_by_id(2)
alice.friends = [bob]
repo.save(alice)  # Creates relationship automatically
```

---

### Pattern 7: MATCH with Relationship

#### Before (Raw Client)

```python
result = g.query('''
    MATCH (p:Person)-[:KNOWS]->(friend:Person)
    WHERE id(p) = $person_id
    RETURN friend
''', {'person_id': 1})

friends = []
for record in result.result_set:
    node = record[0]
    friends.append({
        'id': node.id,
        'name': node.properties['name']
    })
```

#### After (ORM)

```python
person = repo.find_by_id(1)
# Lazy loading - loads on first access
for friend in person.friends:
    print(friend.name)

# Or eager loading - single query
person = repo.find_by_id(1, fetch=["friends"])
```

---

### Pattern 8: COUNT

#### Before (Raw Client)

```python
result = g.query('''
    MATCH (p:Person)
    WHERE p.age > $min_age
    RETURN count(p)
''', {'min_age': 18})

count = result.result_set[0][0]
```

#### After (ORM)

```python
# Total count
count = repo.count()

# Conditional count (derived query)
count = repo.count_by_age_greater_than(18)
```

---

### Pattern 9: Aggregations

#### Before (Raw Client)

```python
result = g.query('''
    MATCH (p:Person)
    RETURN avg(p.age), max(p.age), min(p.age)
''')

avg_age = result.result_set[0][0]
max_age = result.result_set[0][1]
min_age = result.result_set[0][2]
```

#### After (ORM)

```python
avg_age = repo.avg("age")
max_age = repo.max("age")
min_age = repo.min("age")
```

---

## Common Scenarios

### Scenario 1: User Registration System

#### Before (Raw Client)

```python
def create_user(name: str, email: str, password_hash: str):
    result = g.query('''
        CREATE (u:User {name: $name, email: $email, password: $password, created_at: timestamp()})
        RETURN id(u)
    ''', {'name': name, 'email': email, 'password': password_hash})
    return result.result_set[0][0]

def find_user_by_email(email: str):
    result = g.query('''
        MATCH (u:User) WHERE u.email = $email RETURN u
    ''', {'email': email})
    
    if result.result_set:
        node = result.result_set[0][0]
        return {
            'id': node.id,
            'name': node.properties['name'],
            'email': node.properties['email'],
            'password': node.properties['password']
        }
    return None
```

#### After (ORM)

```python
from datetime import datetime

@node("User")
class User:
    id: Optional[int] = None
    name: str
    email: str
    password: str
    created_at: datetime = datetime.now()

repo = Repository(graph, User)

def create_user(name: str, email: str, password_hash: str):
    user = User(name=name, email=email, password=password_hash)
    return repo.save(user)

def find_user_by_email(email: str):
    # Derived query - automatically implemented
    users = repo.find_by_email(email)
    return users[0] if users else None
```

---

### Scenario 2: Social Network Queries

#### Before (Raw Client)

```python
def get_friends_of_friends(person_id: int):
    result = g.query('''
        MATCH (p:Person)-[:KNOWS]->(friend:Person)-[:KNOWS]->(fof:Person)
        WHERE id(p) = $person_id AND id(fof) <> $person_id
        RETURN DISTINCT fof
    ''', {'person_id': person_id})
    
    return [{'id': record[0].id, 'name': record[0].properties['name']} 
            for record in result.result_set]
```

#### After (ORM)

```python
from falkordb_orm import query

class PersonRepository(Repository[Person]):
    @query('''
        MATCH (p:Person)-[:KNOWS]->(friend:Person)-[:KNOWS]->(fof:Person)
        WHERE id(p) = $person_id AND id(fof) <> $person_id
        RETURN DISTINCT fof
    ''', returns=Person)
    def get_friends_of_friends(self, person_id: int) -> List[Person]:
        pass

# Usage
repo = PersonRepository(graph, Person)
fof = repo.get_friends_of_friends(1)
```

---

### Scenario 3: Cascade Operations

#### Before (Raw Client)

```python
def create_person_with_company(person_name: str, company_name: str):
    # Create company
    result = g.query('''
        CREATE (c:Company {name: $company_name})
        RETURN id(c)
    ''', {'company_name': company_name})
    company_id = result.result_set[0][0]
    
    # Create person
    result = g.query('''
        CREATE (p:Person {name: $person_name})
        RETURN id(p)
    ''', {'person_name': person_name})
    person_id = result.result_set[0][0]
    
    # Create relationship
    g.query('''
        MATCH (p:Person), (c:Company)
        WHERE id(p) = $person_id AND id(c) = $company_id
        CREATE (p)-[:WORKS_FOR]->(c)
    ''', {'person_id': person_id, 'company_id': company_id})
    
    return person_id
```

#### After (ORM)

```python
@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    company: Optional["Company"] = relationship(
        type="WORKS_FOR",
        direction="OUTGOING",
        cascade=True  # Automatically save company
    )

@node("Company")
class Company:
    id: Optional[int] = None
    name: str

# One operation saves everything
person = Person(name="Alice", company=Company(name="Acme Corp"))
saved = repo.save(person)  # Company saved automatically
```

---

## Performance Considerations

### 1. N+1 Query Problem

#### Before (Raw Client)

```python
# Get all people
result = g.query('MATCH (p:Person) RETURN p')
people = [record[0] for record in result.result_set]

# For each person, get their company (N+1 queries!)
for person in people:
    result = g.query('''
        MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
        WHERE id(p) = $id
        RETURN c
    ''', {'id': person.id})
```

#### After (ORM)

```python
# Solution: Eager loading
people = repo.find_all(fetch=["company"])
for person in people:
    print(person.company.name)  # No additional queries!
```

### 2. Bulk Operations

For bulk inserts, the raw client may still be faster for very large datasets:

```python
# For 1000+ entities, consider using raw client with batching
nodes = [{'name': f'User{i}', 'age': 20+i} for i in range(10000)]

# Raw client with UNWIND (faster for bulk)
g.query('''
    UNWIND $nodes as node
    CREATE (p:Person)
    SET p = node
''', {'nodes': nodes})

# ORM (simpler but potentially slower for bulk)
for data in nodes:
    person = Person(**data)
    repo.save(person)
```

### 3. Complex Queries

For complex queries with specific Cypher features, use `@query` decorator:

```python
class PersonRepository(Repository[Person]):
    @query('''
        MATCH path = shortestPath((p1:Person)-[:KNOWS*]-(p2:Person))
        WHERE id(p1) = $start_id AND id(p2) = $end_id
        RETURN p2
    ''', returns=Person)
    def find_shortest_path(self, start_id: int, end_id: int) -> Optional[Person]:
        pass
```

---

## Best Practices

### 1. Gradual Migration

You don't need to migrate everything at once:

```python
# Mix ORM and raw client
from falkordb import FalkorDB
from falkordb_orm import node, Repository

db = FalkorDB()
graph = db.select_graph('mydb')

# Use ORM for standard CRUD
repo = Repository(graph, Person)
person = repo.find_by_name("Alice")[0]

# Use raw client for complex queries
result = graph.query('''
    MATCH path = (p:Person)-[:KNOWS*3..5]->(friend)
    WHERE id(p) = $id
    RETURN friend
''', {'id': person.id})
```

### 2. Start with Entities

Begin by defining your entity classes:

```python
# 1. Define entities
@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    email: str

# 2. Migrate simple CRUD operations
repo = Repository(graph, Person)

# 3. Add relationships later
class Person:
    friends: List["Person"] = relationship(type="KNOWS")

# 4. Add custom queries as needed
class PersonRepository(Repository[Person]):
    @query("...")
    def custom_method(self): pass
```

### 3. Testing Strategy

```python
# ORM makes testing easier with mocking
from unittest.mock import Mock

def test_user_service():
    mock_repo = Mock(spec=Repository)
    mock_repo.find_by_email.return_value = [User(id=1, email="test@example.com")]
    
    service = UserService(mock_repo)
    user = service.get_user("test@example.com")
    
    assert user.id == 1
```

### 4. Use Type Hints

```python
# Good - type safety
def get_adult_users(repo: Repository[Person]) -> List[Person]:
    return repo.find_by_age_greater_than_or_equal(18)

# Less ideal - no type safety
def get_adult_users(repo):
    return repo.find_by_age_greater_than_or_equal(18)
```

---

## Troubleshooting

### "Entity not found" after migration

**Problem**: Raw queries use string property names, ORM uses Python attributes.

```python
# Before
g.query('CREATE (p:Person {full_name: $name})', {'name': 'Alice'})

# After - use property() to map
@node("Person")
class Person:
    id: Optional[int] = None
    name: str = property("full_name")  # Maps to 'full_name' in graph
```

### Performance slower than raw client

**Solution**: Use eager loading, check generated queries, consider raw client for bulk operations.

```python
# Check what query is generated (for debugging)
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable query logging in your code
```

### Type errors with relationships

**Problem**: Circular imports with forward references.

```python
# Solution: Use string literals
@node("Person")
class Person:
    friends: List["Person"] = relationship(type="KNOWS")  # String literal
```

---

## Summary

| Feature | Raw Client | ORM |
|---------|------------|-----|
| Type Safety | ❌ Manual | ✅ Built-in |
| Boilerplate | ❌ High | ✅ Low |
| Learning Curve | Medium | Low-Medium |
| Flexibility | ✅ Complete | ✅ Good (with @query) |
| Performance | ✅ Maximum control | ✅ Good (with optimizations) |
| Testability | Medium | ✅ Easy |
| IDE Support | ❌ Limited | ✅ Excellent |

**Recommendation**: Use the ORM for 90% of your code, raw client for the remaining 10% where you need specific Cypher features or maximum performance.

---

## Next Steps

1. Review the [Quickstart Guide](../QUICKSTART.md)
2. Explore [API Reference](api/README.md)
3. Check out [Example Projects](../examples/)
4. Join the [FalkorDB Community](https://github.com/FalkorDB)

Happy migrating! 🚀
