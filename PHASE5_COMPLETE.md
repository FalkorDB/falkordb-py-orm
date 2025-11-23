# Phase 5 Complete: Async Support ✅

**Status**: ✅ COMPLETE  
**Date**: November 2025  
**Goal**: Full async/await support for non-blocking database operations

---

## Overview

Phase 5 implements complete async/await support for the FalkorDB ORM, enabling non-blocking database operations in modern Python applications. This makes the ORM perfect for use with async frameworks like FastAPI, aiohttp, Quart, and others.

## What Was Implemented

### 1. AsyncRepository ✅

A fully async version of Repository with all CRUD operations:

```python
from falkordb.asyncio import FalkorDB
from falkordb_orm import AsyncRepository, node
from typing import Optional

@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    age: int

# Connect with async client
from redis.asyncio import BlockingConnectionPool
pool = BlockingConnectionPool(max_connections=16, timeout=None, decode_responses=True)
db = FalkorDB(connection_pool=pool)
graph = db.select_graph('social')

# Create async repository
repo = AsyncRepository(graph, Person)

# All operations are async
person = Person(name="Alice", age=25)
saved = await repo.save(person)
found = await repo.find_by_id(saved.id)
all_people = await repo.find_all()
count = await repo.count()
await repo.delete(person)
```

**Implemented Methods:**
- `async def save(entity: T) -> T`
- `async def save_all(entities: Iterable[T]) -> List[T]`
- `async def find_by_id(entity_id: Any, fetch: Optional[List[str]] = None) -> Optional[T]`
- `async def find_all(fetch: Optional[List[str]] = None) -> List[T]`
- `async def find_all_by_id(ids: Iterable[Any]) -> List[T]`
- `async def exists_by_id(entity_id: Any) -> bool`
- `async def count() -> int`
- `async def sum(property_name: str) -> float`
- `async def avg(property_name: str) -> float`
- `async def min(property_name: str) -> Any`
- `async def max(property_name: str) -> Any`
- `async def delete(entity: T) -> None`
- `async def delete_by_id(entity_id: Any) -> None`
- `async def delete_all(entities: Optional[Iterable[T]] = None) -> None`

### 2. Async Derived Queries ✅

All derived query methods work with async/await:

```python
# Derived queries are automatically async
adults = await repo.find_by_age_greater_than(18)
alices = await repo.find_by_name("Alice")
count = await repo.count_by_age(25)
exists = await repo.exists_by_email("alice@example.com")
await repo.delete_by_age_less_than(18)

# All Phase 2 query operators work
people = await repo.find_by_name_containing("Ali")
seniors = await repo.find_by_age_between(60, 80)
sorted_people = await repo.find_all_order_by_age_desc()
```

### 3. AsyncEntityMapper ✅

Async mapper for entity conversion:

```python
class AsyncEntityMapper:
    async def map_from_node(self, node: Any, entity_class: Type[T]) -> T
    async def map_from_record(self, record: Any, entity_class: Type[T], var_name: str = 'n') -> T
    async def map_with_relationships(self, record: Any, entity_class: Type[T], fetch_hints: List[str], var_name: str = 'n') -> T
    async def _initialize_lazy_relationships(self, entity: T, entity_id: int) -> None
```

**Features:**
- Reuses synchronous mapping logic where possible (property conversion, Cypher generation)
- Async methods for database interactions
- Async lazy relationship initialization

### 4. Async Relationships ✅

Full async support for relationship loading:

#### AsyncLazyList

```python
class AsyncLazyList(Generic[T]):
    async def load(self) -> List[T]
    async def __aiter__(self)  # Async iteration
```

**Usage:**
```python
person = await repo.find_by_id(1)

# Explicit async loading
friends = await person.friends.load()

# Async iteration
async for friend in person.friends:
    print(friend.name)
```

#### AsyncLazySingle

```python
class AsyncLazySingle(Generic[T]):
    async def get(self) -> Optional[T]
```

**Usage:**
```python
person = await repo.find_by_id(1)

# Async loading of single relationship
company = await person.company.get()
if company:
    print(company.name)
```

### 5. AsyncRelationshipManager ✅

Async cascade operations:

```python
class AsyncRelationshipManager:
    async def save_relationships(source_entity: Any, source_id: int, metadata: Any) -> None
    async def _get_or_save_related_entity(entity: Any, rel_meta: RelationshipMetadata) -> Optional[int]
    async def _create_relationship_edge(source_id: int, target_id: int, rel_meta: RelationshipMetadata) -> None
```

**Features:**
- Async cascade save
- Async relationship edge creation
- Entity tracking to prevent infinite loops
- Works with both collections and single relationships

### 6. Async Eager Loading ✅

Eager loading works with async operations:

```python
# Eager load relationships
person = await repo.find_by_id(1, fetch=["friends", "company"])

# Access relationships without additional queries
print(person.name)
for friend in person.friends:
    print(friend.name)
if person.company:
    print(person.company.name)

# Eager load for all entities
all_people = await repo.find_all(fetch=["company"])
for person in all_people:
    if person.company:
        print(f"{person.name} works at {person.company.name}")
```

## File Structure

```
falkordb_orm/
├── async_repository.py          # AsyncRepository implementation
├── async_mapper.py               # AsyncEntityMapper
├── async_relationships.py        # AsyncLazyList, AsyncLazySingle, AsyncRelationshipManager
└── __init__.py                   # Export AsyncRepository

examples/
└── async_usage.py                # Comprehensive async examples
```

## Key Design Decisions

### 1. Separate Async Classes

Created separate async classes (`AsyncRepository`, `AsyncEntityMapper`, etc.) rather than trying to make sync classes work in both modes:
- Cleaner separation of concerns
- Avoids complex "sync or async" logic
- Better type hints and IDE support
- Users explicitly choose sync or async

### 2. Code Reuse

Maximized code reuse between sync and async implementations:
- `AsyncEntityMapper` delegates to `EntityMapper` for non-async operations
- Both use the same `QueryBuilder` and `QueryParser` (they don't need to be async)
- Share metadata and type conversion logic
- Same decorators (`@node`, `@relationship`) work for both

### 3. Lazy Loading Approach

Async lazy relationships use explicit methods:
- `AsyncLazyList.load()` - explicitly load list
- `AsyncLazySingle.get()` - explicitly load single entity
- `async for` iteration support for lists
- Cannot use property access (Python limitation with async)

### 4. FalkorDB Client Integration

Leverages existing FalkorDB async client:
- Uses `falkordb.asyncio.FalkorDB`
- Requires `redis.asyncio.BlockingConnectionPool`
- All graph queries use `await graph.query()`

## Examples

### Basic Async CRUD

```python
import asyncio
from falkordb.asyncio import FalkorDB
from redis.asyncio import BlockingConnectionPool
from falkordb_orm import node, AsyncRepository
from typing import Optional

@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    age: int

async def main():
    # Connect
    pool = BlockingConnectionPool(max_connections=16, timeout=None, decode_responses=True)
    db = FalkorDB(connection_pool=pool)
    graph = db.select_graph('social')
    
    # Create repository
    repo = AsyncRepository(graph, Person)
    
    # CRUD operations
    person = Person(name="Alice", age=25)
    saved = await repo.save(person)
    found = await repo.find_by_id(saved.id)
    count = await repo.count()
    await repo.delete(person)

asyncio.run(main())
```

### Concurrent Operations

```python
async def concurrent_example():
    # Create multiple entities concurrently
    people = [Person(name=f"Person{i}", age=20+i) for i in range(5)]
    saved_people = await asyncio.gather(*[repo.save(p) for p in people])
    
    # Run multiple queries concurrently
    count, avg_age, adults = await asyncio.gather(
        repo.count(),
        repo.avg('age'),
        repo.find_by_age_greater_than(22)
    )
```

### With FastAPI

```python
from fastapi import FastAPI, Depends
from falkordb.asyncio import FalkorDB
from falkordb_orm import AsyncRepository, node
from typing import Optional, List

app = FastAPI()

@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    age: int

# Dependency injection
async def get_person_repo():
    pool = BlockingConnectionPool(max_connections=16, timeout=None, decode_responses=True)
    db = FalkorDB(connection_pool=pool)
    graph = db.select_graph('social')
    return AsyncRepository(graph, Person)

@app.get("/people")
async def list_people(repo: AsyncRepository = Depends(get_person_repo)) -> List[Person]:
    return await repo.find_all()

@app.get("/people/{person_id}")
async def get_person(person_id: int, repo: AsyncRepository = Depends(get_person_repo)) -> Optional[Person]:
    return await repo.find_by_id(person_id)

@app.post("/people")
async def create_person(person: Person, repo: AsyncRepository = Depends(get_person_repo)) -> Person:
    return await repo.save(person)
```

## Testing

Run the async example:

```bash
# Start FalkorDB
docker run -p 6379:6379 falkordb/falkordb

# Run async examples
python examples/async_usage.py
```

## Performance Benefits

Async support enables:

1. **Concurrent Database Operations**: Run multiple queries simultaneously
2. **Non-blocking I/O**: Application remains responsive during database operations
3. **Better Resource Utilization**: Handle more requests with same resources
4. **Framework Integration**: Perfect for FastAPI, aiohttp, Quart, etc.

## Comparison: Sync vs Async

### Synchronous (Phase 1-4)

```python
from falkordb import FalkorDB
from falkordb_orm import Repository

db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('social')
repo = Repository(graph, Person)

# Blocking operations
person = repo.save(Person(name="Alice", age=25))
found = repo.find_by_id(person.id)
all_people = repo.find_all()
```

### Asynchronous (Phase 5)

```python
from falkordb.asyncio import FalkorDB
from redis.asyncio import BlockingConnectionPool
from falkordb_orm import AsyncRepository

pool = BlockingConnectionPool(max_connections=16, timeout=None, decode_responses=True)
db = FalkorDB(connection_pool=pool)
graph = db.select_graph('social')
repo = AsyncRepository(graph, Person)

# Non-blocking operations
person = await repo.save(Person(name="Alice", age=25))
found = await repo.find_by_id(person.id)
all_people = await repo.find_all()

# Can run concurrently
results = await asyncio.gather(
    repo.save(person1),
    repo.save(person2),
    repo.find_all()
)
```

## Limitations & Future Work

### Current Limitations

1. **Lazy Loading Syntax**: Async lazy relationships require explicit `.load()` or `.get()` calls (Python async limitation)
2. **No AsyncSession**: Session/Unit of Work pattern not yet implemented for async (planned for future)
3. **Connection Pooling**: Users must manage connection pools themselves

### Future Enhancements

- AsyncSession for transaction management
- Async query caching
- Connection pool helpers
- Async bulk operations optimization
- Streaming query results

## Migration Guide

### From Sync to Async

1. Change imports:
```python
# Before
from falkordb import FalkorDB
from falkordb_orm import Repository

# After
from falkordb.asyncio import FalkorDB
from redis.asyncio import BlockingConnectionPool
from falkordb_orm import AsyncRepository
```

2. Update repository creation:
```python
# Before
db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('social')
repo = Repository(graph, Person)

# After
pool = BlockingConnectionPool(max_connections=16, timeout=None, decode_responses=True)
db = FalkorDB(connection_pool=pool)
graph = db.select_graph('social')
repo = AsyncRepository(graph, Person)
```

3. Add `await` to all repository operations:
```python
# Before
person = repo.save(person)
found = repo.find_by_id(1)

# After
person = await repo.save(person)
found = await repo.find_by_id(1)
```

4. Update lazy relationship access:
```python
# Before (sync)
for friend in person.friends:
    print(friend.name)

# After (async)
friends = await person.friends.load()
for friend in friends:
    print(friend.name)

# Or use async iteration
async for friend in person.friends:
    print(friend.name)
```

## Conclusion

Phase 5 successfully implements complete async/await support for the FalkorDB ORM. The implementation:

✅ Maintains API consistency with sync version  
✅ Enables non-blocking database operations  
✅ Supports concurrent query execution  
✅ Integrates seamlessly with async frameworks  
✅ Reuses code where possible  
✅ Provides comprehensive examples  

The ORM is now ready for production use in both synchronous and asynchronous Python applications!

---

**Next Steps**: Phase 6 (Polish & Documentation) or additional features like AsyncSession, transaction support, and advanced query caching.
