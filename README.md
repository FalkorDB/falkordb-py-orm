# FalkorDB Python ORM

> **Object-Graph Mapping for FalkorDB with Spring Data-inspired patterns**

[![Python Version](https://img.shields.io/badge/Python-3.8+-brightgreen.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![FalkorDB](https://img.shields.io/badge/FalkorDB-Compatible-red.svg)](https://falkordb.com)

FalkorDB Python ORM provides intuitive, annotation-based object-graph mapping for [FalkorDB](https://falkordb.com), enabling developers to work with graph databases using familiar ORM patterns inspired by Spring Data.

## 🎯 Project Status

**Phase 6 Complete! ✅ Production Ready!** The ORM is now fully documented, tested, and ready for PyPI release.

- ✅ Phase 1: Foundation (Core entity mapping and basic CRUD) - **COMPLETE**
- ✅ Phase 2: Query Derivation (Automatic query generation) - **COMPLETE**
- ✅ Phase 3: Relationships (Lazy/eager loading, cascade operations) - **COMPLETE**
- ✅ Phase 4: Advanced Features (Custom queries, aggregations) - **COMPLETE**
- ✅ Phase 5: Async Support (AsyncRepository with full async/await) - **COMPLETE**
- ✅ Phase 6: Polish & Documentation (Production-ready, CI/CD, comprehensive docs) - **COMPLETE**

See [PHASE6_COMPLETE.md](PHASE6_COMPLETE.md) for the latest updates, including comprehensive API documentation, migration guide, and CI/CD setup. Check [QUICKSTART.md](QUICKSTART.md) to get started.

**Phase 6** adds production-ready features: comprehensive API docs, migration guide from raw FalkorDB client, CI/CD workflows, enhanced exception handling, and all package distribution files.

## 🚀 Features

### ✅ Implemented

**Phase 1 - Foundation:**
- **🏷️ Decorator-based Entity Mapping**: Use `@node` and `property` decorators
- **📦 Repository Pattern**: CRUD operations with `Repository[T]`
- **🔑 ID Management**: Auto-generated or manual IDs with `generated_id()`
- **🔄 Type Conversion**: Built-in converters for common types
- **🎯 Multiple Labels**: Support for multiple node labels
- **🎨 Type Safety**: Full type hints and generic repositories

**Phase 2 - Query Derivation:**
- **🔍 Derived Query Methods**: Auto-generate queries from method names (e.g., `find_by_name()`, `count_by_age_greater_than()`)
- **📊 Comparison Operators**: Support for 14 operators (equals, greater_than, less_than, between, in, etc.)
- **🔗 Logical Operators**: AND/OR combinations in queries
- **📝 String Operations**: CONTAINS, STARTS WITH, ENDS WITH, regex patterns
- **📊 Sorting**: Single and multiple field ORDER BY
- **🎯 Limiting**: first/top_N result limiting
- **⚡ Query Caching**: Automatic QuerySpec caching for performance

**Phase 3 - Relationships:**
- **🔗 Relationship Declaration**: `relationship()` decorator with full type support
- **💤 Lazy Loading**: Relationships loaded on-demand with automatic caching
- **⚡ Eager Loading**: Solve N+1 queries with `fetch=['rel1', 'rel2']` parameter
- **🔄 Cascade Operations**: Auto-save related entities with `cascade=True`
- **↔️ Bidirectional Relationships**: Full support for complex relationship graphs
- **🔙 Reverse Relationships**: `direction='INCOMING'` for inverse traversal
- **🔁 Circular Reference Handling**: Safe handling of circular relationships

**Phase 4 - Advanced Features:**
- **📝 Custom Cypher Queries**: `@query` decorator with parameter binding
- **📊 Aggregation Methods**: Built-in `sum()`, `avg()`, `min()`, `max()` functions
- **🎯 Type-Safe Results**: Automatic mapping of query results to entities
- **🔧 Complex Patterns**: Support for WITH clauses, CTEs, and advanced Cypher

**Phase 5 - Async Support:**
- **⚡ AsyncRepository**: Full async/await support for all CRUD operations
- **🔄 Async Relationships**: Async lazy loading with `AsyncLazyList` and `AsyncLazySingle`
- **📊 Async Derived Queries**: Auto-generated async query methods
- **🌐 Framework Ready**: Perfect for FastAPI, aiohttp, and async Python applications

**Phase 6 - Polish & Documentation:**
- **📚 Comprehensive API Docs**: Complete reference for decorators, repository, and query methods
- **🔄 Migration Guide**: Step-by-step guide from raw FalkorDB client to ORM
- **🧠 Enhanced Exceptions**: Contextual error messages with structured error information
- **🚀 CI/CD Workflows**: Automated testing, linting, and PyPI publishing
- **📦 Distribution Ready**: LICENSE, CHANGELOG, CONTRIBUTING, and complete package metadata
- **💾 Interned Strings**: Memory optimization for repeated string values with `@interned` decorator

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

### Session Management (Coming in Phase 4)

```python
from falkordb_orm import Session

with Session(graph) as session:
    # Add new entities
    alice = Person(name="Alice", age=25)
    bob = Person(name="Bob", age=30)
    
    session.add(alice)
    session.add(bob)
    
    # Modify existing
    existing = session.get(Person, 1)
    existing.age = 26
    
    # All changes persisted on commit
    session.commit()
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

## 🗺️ Implementation Plan

### Phase 1: Foundation (Week 1-2)
- Core entity mapping with `@node` decorator
- Basic property mapping
- Simple `Repository` with CRUD operations
- `save()` and `find_by_id()` methods

### Phase 2: Query Derivation (Week 3-4)
- Parse method names into Cypher queries
- Support comparison operators (`greater_than`, `less_than`, etc.)
- Support logical operators (`and`, `or`)
- String operations (`containing`, `starting_with`, etc.)

### Phase 3: Relationships (Week 5-6)
- `@relationship` decorator
- Relationship persistence (cascade)
- Lazy loading with proxies
- Eager loading with fetch hints

### Phase 4: Advanced Features (Week 7-8)
- `Session` with unit of work pattern
- Identity map for entity tracking
- `@query` decorator for custom Cypher
- Pagination support

### Phase 5: Async Support (Week 9)
- `AsyncRepository` implementation
- `AsyncSession` implementation
- Async query methods

### Phase 6: Polish & Documentation (Week 10)
- Comprehensive documentation
- Example projects
- Performance optimization
- Package publishing

## 📚 Documentation

- [Design Document](DESIGN.md) - Comprehensive design and architecture
- Getting Started Guide (Coming soon)
- API Reference (Coming soon)
- Examples (Coming soon)

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

## 📦 Planned Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.8"
falkordb = "^1.2.0"
typing-extensions = "^4.0"
```

## 💡 Design Principles

1. **Convention over Configuration**: Sensible defaults with customization options
2. **Explicit is Better**: Clear, readable API over implicit magic
3. **Performance Matters**: Optimize for common use cases
4. **Pythonic**: Follow Python idioms and best practices
5. **Compatibility**: Work seamlessly with existing falkordb-py code

## 🚀 Getting Started

```bash
# Clone and install
git clone https://github.com/FalkorDB/falkordb-py-orm.git
cd falkordb-py-orm
pip install -e .

# Quick start
from falkordb import FalkorDB
from falkordb_orm import node, Repository

@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    age: int

db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('mydb')
repo = Repository(graph, Person)

person = Person(name="Alice", age=25)
saved = repo.save(person)
```

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Inspired by [Spring Data FalkorDB](https://github.com/FalkorDB/spring-data-falkordb)
- Built on top of [falkordb-py](https://github.com/FalkorDB/falkordb-py)
- Follows patterns from SQLAlchemy and Django ORM

## 📞 Contact & Contributing

Contributions and feedback are welcome!

- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Design Document**: [DESIGN.md](DESIGN.md)
- **Phase 2 Complete**: [PHASE2_COMPLETE.md](PHASE2_COMPLETE.md)
- **Phase 1 Complete**: [PHASE1_COMPLETE.md](PHASE1_COMPLETE.md)
- **FalkorDB**: [falkordb.com](https://falkordb.com)
- **Discord**: [FalkorDB Community](https://discord.gg/falkordb)

---

**Status**: ✅ Phase 1, 2, 3, 4 & 5 Complete

For implementation details, see phase completion documents: [PHASE4_COMPLETE.md](PHASE4_COMPLETE.md), [PHASE3_COMPLETE.md](PHASE3_COMPLETE.md), [PHASE2_COMPLETE.md](PHASE2_COMPLETE.md), and [PHASE1_COMPLETE.md](PHASE1_COMPLETE.md).
