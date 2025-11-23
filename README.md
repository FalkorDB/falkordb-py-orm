# FalkorDB Python ORM

> **Object-Graph Mapping for FalkorDB with Spring Data-inspired patterns**

[![Python Version](https://img.shields.io/badge/Python-3.8+-brightgreen.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![FalkorDB](https://img.shields.io/badge/FalkorDB-Compatible-red.svg)](https://falkordb.com)

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

### Production Features

- **📚 Comprehensive Documentation**: Complete API reference and migration guides
- **🧠 Enhanced Exceptions**: Contextual error messages with structured error information
- **🚀 CI/CD Workflows**: Automated testing, linting, and publishing
- **💾 Memory Optimization**: Interned strings for repeated values with `@interned` decorator

### 📋 Future Enhancements (Optional)

- **⚡ Transaction Support**: Context managers for transactional operations
- **🗂️ Index Management**: Decorator-based index and constraint creation
- **📦 Migration System**: Schema version management
- **🔍 Query Caching**: Result caching for performance

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

### Interned Strings for Memory Optimization (Phase 6)

```python
from falkordb_orm import node, interned
from typing import Optional

@node("User")
class User:
    id: Optional[int] = None
    name: str
    email: str
    
    # Interned properties - deduplicated for memory savings
    country: str = interned()  # "United States" stored once for all US users
    city: str = interned()     # "New York" stored once for all NYC users  
    status: str = interned()   # "Active", "Inactive" stored once each
    
# Memory benefit: Repeated values stored only once!
# Perfect for: countries, cities, status fields, categories, tags
```

### Getting Started

For a complete walkthrough, see [QUICKSTART.md](QUICKSTART.md).

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
- **[Migration Guide](docs/MIGRATION_GUIDE.md)** - Migrating from raw FalkorDB client
- **[Examples](examples/)** - Complete working examples
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
