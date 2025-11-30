# FalkorDB Python ORM

> **Object-Graph Mapping for FalkorDB with Spring Data-inspired patterns**

[![Python Version](https://img.shields.io/badge/Python-3.9+-brightgreen.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![FalkorDB](https://img.shields.io/badge/FalkorDB-Compatible-red.svg)](https://falkordb.com)
[![PyPI](https://img.shields.io/pypi/v/falkordb-orm.svg)](https://pypi.org/project/falkordb-orm/)

FalkorDB Python ORM provides intuitive, annotation-based object-graph mapping for [FalkorDB](https://falkordb.com), enabling developers to work with graph databases using familiar ORM patterns inspired by Spring Data.

## 🎯 Project Status

**Production Ready! ✅** The FalkorDB Python ORM is fully implemented, tested, and documented.

## 🚀 Features

### Core Capabilities

- **🏷️ Decorator-based Entity Mapping**: Use `@node` and `property` decorators for intuitive object-graph mapping
- **📦 Repository Pattern**: Complete CRUD operations with type-safe `Repository[T]`
- **🔑 ID Management**: Auto-generated or manual IDs with `generated_id()`
- **🔄 Type Conversion**: Built-in converters for common Python types
- **🎯 Multiple Labels**: Support for multiple node labels per entity
- **🎨 Type Safety**: Full type hints and generic repositories for IDE support

### Query Features

- **🔍 Derived Query Methods**: Auto-generate queries from method names (e.g., `find_by_name()`, `count_by_age_greater_than()`)
- **📊 Comparison Operators**: 14+ operators (equals, greater_than, less_than, between, in, etc.)
- **🔗 Logical Operators**: AND/OR combinations in queries
- **📝 String Operations**: CONTAINS, STARTS WITH, ENDS WITH, regex patterns
- **📊 Sorting & Limiting**: ORDER BY multiple fields, first/top_N result limiting
- **⚡ Query Caching**: Automatic QuerySpec caching for performance
- **📝 Custom Cypher Queries**: `@query` decorator with parameter binding
- **📊 Aggregation Methods**: Built-in `sum()`, `avg()`, `min()`, `max()` functions

### Relationships

- **🔗 Relationship Declaration**: `relationship()` decorator with full type support
- **💤 Lazy Loading**: Relationships loaded on-demand with automatic caching
- **⚡ Eager Loading**: Solve N+1 queries with `fetch=['rel1', 'rel2']` parameter
- **🔄 Cascade Operations**: Auto-save related entities with `cascade=True`
- **↔️ Bidirectional Relationships**: Full support for complex relationship graphs
- **🔙 Reverse Relationships**: `direction='INCOMING'` for inverse traversal
- **🔁 Circular Reference Handling**: Safe handling of circular relationships

### Async Support

- **⚡ AsyncRepository**: Full async/await support for all CRUD operations
- **🔄 Async Relationships**: Async lazy loading with `AsyncLazyList` and `AsyncLazySingle`
- **📊 Async Derived Queries**: Auto-generated async query methods
- **🌐 Framework Ready**: Perfect for FastAPI, aiohttp, and async Python applications

### Advanced Features (v1.1.0)

- **⚡ Transaction Support**: Context managers with identity map and change tracking
- **🗂️ Index Management**: `@indexed` and `@unique` decorators with schema validation
- **📄 Pagination**: Full pagination with sorting and navigation (`Pageable`, `Page[T]`)
- **🔄 Relationship Updates**: Automatic deletion of old edges when relationships change

### Security Features (v1.2.0 NEW! 🔒)

- **🔐 Role-Based Access Control (RBAC)**: Enterprise-grade security with fine-grained permissions
- **👥 User & Role Management**: Built-in user, role, and privilege entities
- **🛡️ Declarative Security**: `@secured` decorator for entity-level access control
- **🔑 Property-Level Security**: Control access to individual properties
- **🔒 SecureSession**: Security-aware sessions with automatic permission enforcement
- **👨‍💼 Admin API**: Comprehensive RBACManager for runtime administration
- **📝 Audit Logging**: Complete audit trail for all security operations
- **🎭 Impersonation**: Test permissions safely with context managers
- **⚡ Performance**: <10ms overhead with intelligent privilege caching

### Production Features

- **📚 Comprehensive Documentation**: Complete API reference and migration guides
- **🧠 Enhanced Exceptions**: Contextual error messages with structured error information
- **🚀 CI/CD Workflows**: Automated testing, linting, and publishing
- **💾 Memory Optimization**: Interned strings for repeated values with `@interned` decorator
- **🧪 Integration Tests**: Full end-to-end tests with real FalkorDB

### 📋 Future Enhancements (Optional)

- **📦 Migration System**: Schema version management and migrations
- **🔍 Query Result Caching**: Result caching for performance
- **⚙️ Batch Optimization**: UNWIND-based bulk operations

## 📜 Usage

### Entity Definition

```python
from falkordb_orm import node, property, relationship, Repository
from typing import Optional, List

@node(labels=["Person", "Individual"])
class Person:
    id: Optional[int] = None
    name: str = property("full_name")  # Maps to 'full_name' in graph
    email: str
    age: int
    
    friends: List["Person"] = relationship(type="KNOWS", direction="OUTGOING")
    company: Optional["Company"] = relationship(type="WORKS_FOR", direction="OUTGOING")

@node("Company")
class Company:
    id: Optional[int] = None
    name: str
    employees: List[Person] = relationship(type="WORKS_FOR", direction="INCOMING")
```

### Repository Usage

```python
from falkordb import FalkorDB

# Connect to FalkorDB
db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('social')

# Create repository
repo = Repository(graph, Person)

# Create and save
person = Person(name="Alice", email="alice@example.com", age=25)
saved = repo.save(person)

# Derived queries (auto-implemented)
adults = repo.find_by_age_greater_than(18)
alice = repo.find_by_name("Alice")
count = repo.count_by_age(25)
exists = repo.exists_by_email("alice@example.com")

# Eager loading relationships (prevents N+1 queries)
person_with_friends = repo.find_by_id(1, fetch=["friends", "company"])
all_with_friends = repo.find_all(fetch=["friends"])  # Single query!

# Cascade save (auto-saves related entities)
company = Company(name="Acme Corp")
employee = Employee(name="Bob", company=company)
repo.save(employee)  # Company automatically saved!
```

### Async Usage (Phase 5)

```python
import asyncio
from falkordb.asyncio import FalkorDB
from falkordb_orm import node, AsyncRepository
from typing import Optional

@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    age: int

async def main():
    # Connect to FalkorDB with async client
    from redis.asyncio import BlockingConnectionPool
    pool = BlockingConnectionPool(max_connections=16, timeout=None, decode_responses=True)
    db = FalkorDB(connection_pool=pool)
    graph = db.select_graph('social')
    
    # Create async repository
    repo = AsyncRepository(graph, Person)
    
    # All operations are async
    person = Person(name="Alice", age=25)
    saved = await repo.save(person)
    
    # Async derived queries
    adults = await repo.find_by_age_greater_than(18)
    count = await repo.count()
    
    # Async eager loading
    person_with_friends = await repo.find_by_id(1, fetch=["friends"])
    
    print(f"Found {count} people")

asyncio.run(main())
```

### Transaction Support (v1.1.0 NEW!)

```python
from falkordb_orm import Session

# Use session for transactions with identity map
with Session(graph) as session:
    # Get entity (cached in identity map)
    person = session.get(Person, 1)
    person.age = 31
    session._dirty.add(person)  # Mark as modified
    
    # Add new entities
    new_person = Person(name="Bob", age=25)
    session.add(new_person)
    
    # Auto-commit on success, auto-rollback on error
    session.commit()
```

### Index Management (v1.1.0 NEW!)

```python
from falkordb_orm import node, indexed, unique, IndexManager

@node("User")
class User:
    email: str = unique(required=True)       # Unique constraint
    age: int = indexed()                      # Regular index
    bio: str = indexed(index_type="FULLTEXT") # Full-text search

# Create indexes
manager = IndexManager(graph)
manager.create_indexes(User, if_not_exists=True)

# Schema validation
from falkordb_orm import SchemaManager
schema_manager = SchemaManager(graph)
result = schema_manager.validate_schema([User, Product])
if not result.is_valid:
    schema_manager.sync_schema([User, Product])
```

### Pagination (v1.1.0 NEW!)

```python
from falkordb_orm import Pageable

# Create pageable (page 0, 10 items, sorted by age)
pageable = Pageable(page=0, size=10, sort_by="age", direction="ASC")

# Get paginated results
page = repo.find_all_paginated(pageable)

print(f"Page {page.page_number + 1} of {page.total_pages}")
print(f"Total: {page.total_elements} items")

for person in page.content:
    print(person.name)

# Navigate pages
if page.has_next():
    next_page = repo.find_all_paginated(pageable.next())
```

### Getting Started

For a complete walkthrough, see [QUICKSTART.md](QUICKSTART.md).

### Security Quick Start (v1.2.0)

Define a secured entity:

```python
from falkordb_orm import node, generated_id
from falkordb_orm.security import secured

@node("Person")
@secured(
    read=["reader", "admin"],
    write=["editor", "admin"],
    deny_read_properties={
        "ssn": ["*"],   # Nobody can read
        "salary": ["reader"]  # Readers cannot read salary
    }
)
class Person:
    id: int | None = generated_id()
    name: str
    email: str
    ssn: str
    salary: float
```

Create roles, users, and grant privileges:

```python
from datetime import datetime
from falkordb_orm.repository import Repository
from falkordb_orm.security import Role, User, SecurityPolicy

role_repo = Repository(graph, Role)
user_repo = Repository(graph, User)

reader = Role(name="reader", description="Read-only", created_at=datetime.now())
editor = Role(name="editor", description="Edit", created_at=datetime.now())
role_repo.save(reader)
role_repo.save(editor)

alice = User(username="alice", email="alice@example.com", created_at=datetime.now())
alice.roles = [reader]
user_repo.save(alice)

policy = SecurityPolicy(graph)
policy.grant("READ", "Person", to="reader")
policy.grant("WRITE", "Person", to="editor")
policy.deny("READ", "Person.ssn", to="reader")
```

Use SecureSession:

```python
from falkordb_orm.security import SecureSession

session = SecureSession(graph, alice)
repo = session.get_repository(Person)

p = repo.find_by_id(1)
print(p.name)     # ✓ Allowed
print(p.ssn)      # None (filtered)
```

Admin API example:

```python
from falkordb_orm.security import RBACManager

admin_session = SecureSession(graph, admin_user)
rbac = RBACManager(graph, admin_session.security_context)

rbac.create_user("bob", "bob@example.com", roles=["editor"])  # create
rbac.assign_role("alice", "editor")                              # assign
rbac.grant_privilege("editor", "WRITE", "NODE", "Document")     # grant
logs = rbac.query_audit_logs(limit=10)                            # audit
```

### Custom Queries (Phase 4)

```python
from falkordb_orm import query

class PersonRepository(Repository[Person]):
    @query(
        "MATCH (p:Person)-[:KNOWS]->(f:Person) WHERE p.name = $name RETURN f",
        returns=Person
    )
    def find_friends(self, name: str) -> List[Person]:
        pass
    
    @query(
        "MATCH (p:Person) WHERE p.age BETWEEN $min AND $max RETURN p",
        returns=Person
    )
    def find_by_age_range(self, min: int, max: int) -> List[Person]:
        pass
```


## 📋 Comparison with Current Approach

### Before (Raw Cypher)

```python
from falkordb import FalkorDB

db = FalkorDB(host='localhost', port=6379)
g = db.select_graph('social')

# Create manually
g.query('''
    CREATE (p:Person {name: $name, email: $email, age: $age})
    RETURN p, id(p)
''', {'name': 'Alice', 'email': 'alice@example.com', 'age': 25})

# Query manually
result = g.query('''
    MATCH (p:Person) WHERE p.age > $min_age RETURN p
''', {'min_age': 18})

# Manual result processing
for record in result.result_set:
    person = record[0]
    print(person.properties['name'])
```

### After (ORM - Planned)

```python
from falkordb import FalkorDB
from falkordb_orm import node, Repository

@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    email: str
    age: int

db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('social')
repo = Repository(graph, Person)

# Create with ORM
person = Person(name="Alice", email="alice@example.com", age=25)
saved = repo.save(person)

# Query with derived method
adults = repo.find_by_age_greater_than(18)

# Automatic object mapping
for person in adults:
    print(person.name)
```


## 📚 Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get started in minutes
- **[Design Document](DESIGN.md)** - Comprehensive design and architecture
- **[API Reference](docs/api/)** - Complete API documentation
  - [Decorators](docs/api/decorators.md) - `@node`, `property()`, `relationship()`
  - [Repository](docs/api/repository.md) - `Repository` and `AsyncRepository`
- **[Security Module](falkordb_orm/security/README.md)** - Complete RBAC security guide (v1.2.0)
- **[Migration Guide](docs/MIGRATION_GUIDE.md)** - Migrating from raw FalkorDB client
- **[Examples](examples/)** - Complete working examples
  - [Security Examples](examples/security/) - RBAC and admin API examples
- **[Contributing](CONTRIBUTING.md)** - Contribution guidelines

## 🤝 Comparison with Spring Data FalkorDB

This project is inspired by [Spring Data FalkorDB](https://github.com/FalkorDB/spring-data-falkordb), bringing similar patterns to Python:

| Feature | Spring Data FalkorDB | falkordb-orm |
|---------|---------------------|--------------|
| Entity Mapping | `@Node` annotation | `@node` decorator |
| Property Mapping | `@Property` | `property()` function |
| Relationships | `@Relationship` | `relationship()` function |
| Repository | `FalkorDBRepository<T, ID>` | `Repository[T]` |
| Query Methods | Method name derivation | Method name derivation |
| Custom Queries | `@Query` annotation | `@query` decorator |
| Transactions | `@Transactional` | `Session` (unit of work) |
| Async Support | ❌ | ✅ Planned |

## 🎯 Goals

1. **Developer Productivity**: Reduce boilerplate code and manual Cypher writing
2. **Type Safety**: Leverage Python type hints for better IDE support
3. **Familiarity**: Use patterns developers know from SQLAlchemy, Django ORM, Spring Data
4. **Performance**: Optimize queries, support batching, implement lazy loading
5. **Flexibility**: Support both simple and complex use cases

## 🔧 Technology Stack

- **Python**: 3.8+
- **FalkorDB Client**: [falkordb-py](https://github.com/FalkorDB/falkordb-py)
- **Type Hints**: For IDE support and validation
- **Decorators**: For entity and query definition
- **Generics**: For type-safe repositories

## 📦 Installation

```bash
pip install falkordb-orm
```

Or install from source:

```bash
git clone https://github.com/FalkorDB/falkordb-py-orm.git
cd falkordb-py-orm
pip install -e .
```

## 💡 Design Principles

1. **Convention over Configuration**: Sensible defaults with customization options
2. **Explicit is Better**: Clear, readable API over implicit magic
3. **Performance Matters**: Optimize for common use cases
4. **Pythonic**: Follow Python idioms and best practices
5. **Compatibility**: Work seamlessly with existing falkordb-py code


## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Inspired by [Spring Data FalkorDB](https://github.com/FalkorDB/spring-data-falkordb)
- Built on top of [falkordb-py](https://github.com/FalkorDB/falkordb-py)
- Follows patterns from SQLAlchemy and Django ORM

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📦 Resources

- **FalkorDB**: [falkordb.com](https://falkordb.com)
- **Discord**: [FalkorDB Community](https://discord.gg/falkordb)
- **GitHub**: [FalkorDB Organization](https://github.com/FalkorDB)
