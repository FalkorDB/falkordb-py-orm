# FalkorDB Python ORM - Design Document

## Executive Summary

This document outlines the design for **falkordb-orm**, a Python Object-Graph Mapping (OGM) library for FalkorDB that provides Spring Data-like patterns and annotations for intuitive graph database interaction. The library will build on top of the existing `falkordb-py` client to provide declarative entity mapping, repository abstractions, and automatic query generation.

**Key Goals:**
- Provide intuitive, annotation-based entity mapping
- Implement repository pattern for CRUD operations
- Support derived query methods (method-name-based query generation)
- Enable relationship mapping with automatic persistence
- Maintain compatibility with both sync and async `falkordb-py` APIs

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Entity Mapping](#entity-mapping)
4. [Repository Pattern](#repository-pattern)
5. [Query Derivation](#query-derivation)
6. [Relationship Handling](#relationship-handling)
7. [Session Management](#session-management)
8. [Type System](#type-system)
9. [API Reference](#api-reference)
10. [Implementation Plan](#implementation-plan)
11. [Examples](#examples)

---

## 1. Architecture Overview

### 1.1 Layer Architecture

```
┌─────────────────────────────────────────┐
│   Application Code (Domain Models)      │
│   @node, @relationship decorators       │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│   Repository Layer                       │
│   - Repository[T]                        │
│   - Query Derivation                     │
│   - Custom Queries (@query)              │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│   ORM Core Layer                         │
│   - EntityMapper                         │
│   - Session                              │
│   - RelationshipManager                  │
│   - QueryBuilder                         │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│   FalkorDB Client (falkordb-py)         │
│   - Graph.query()                        │
│   - Node, Edge primitives                │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│   FalkorDB Server                        │
└─────────────────────────────────────────┘
```

### 1.2 Package Structure

```
falkordb-orm/
├── falkordb_orm/
│   ├── __init__.py              # Public API exports
│   ├── decorators.py            # @node, @property, @relationship
│   ├── mapper.py                # EntityMapper - object <-> Cypher
│   ├── repository.py            # Repository base class
│   ├── query_builder.py         # Cypher query generation
│   ├── query_parser.py          # Parse derived query method names
│   ├── session.py               # Session - unit of work pattern
│   ├── relationships.py         # Relationship loading/saving
│   ├── types.py                 # Type converters
│   ├── metadata.py              # Entity metadata management
│   ├── exceptions.py            # Custom exceptions
│   └── asyncio/
│       ├── __init__.py
│       ├── repository.py        # Async repository
│       └── session.py           # Async session
├── tests/
│   ├── test_decorators.py
│   ├── test_mapper.py
│   ├── test_repository.py
│   ├── test_query_parser.py
│   └── integration/
│       └── test_twitter_example.py
├── examples/
│   ├── basic_usage.py
│   ├── twitter_social_graph.py
│   └── async_example.py
├── docs/
│   ├── getting_started.md
│   ├── entity_mapping.md
│   ├── repository_guide.md
│   └── api_reference.md
├── pyproject.toml
├── README.md
└── DESIGN.md (this file)
```

### 1.3 Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.8"
falkordb = "^1.2.0"           # Core FalkorDB client
typing-extensions = "^4.0"     # For Python 3.8-3.9 compatibility
```

Optional dependencies:
- `pydantic` (for enhanced validation)
- `dataclasses-json` (for JSON serialization)

---

## 2. Core Components

### 2.1 EntityMapper

**Responsibility:** Bidirectional conversion between Python objects and FalkorDB graph structures.

**Key Methods:**
- `map_to_node(entity: T) -> (cypher: str, params: dict)`
- `map_from_record(record: Record, clazz: Type[T]) -> T`
- `get_entity_metadata(clazz: Type[T]) -> EntityMetadata`

**Design:**
```python
class EntityMapper:
    def __init__(self):
        self._metadata_cache: Dict[Type, EntityMetadata] = {}
    
    def map_to_node(self, entity: Any) -> Tuple[str, Dict[str, Any]]:
        """Convert entity to Cypher CREATE/MERGE statement"""
        metadata = self.get_entity_metadata(type(entity))
        properties = {}
        
        for field in metadata.properties:
            value = getattr(entity, field.python_name)
            if value is not None:
                properties[field.graph_name] = self._convert_to_graph_type(value)
        
        return self._build_cypher(metadata, properties)
    
    def map_from_record(self, record: Any, clazz: Type[T]) -> T:
        """Convert FalkorDB record to entity instance"""
        metadata = self.get_entity_metadata(clazz)
        node_data = record.get('n')  # Assuming variable 'n' in query
        
        kwargs = {}
        for field in metadata.properties:
            graph_value = node_data.properties.get(field.graph_name)
            kwargs[field.python_name] = self._convert_from_graph_type(
                graph_value, field.python_type
            )
        
        return clazz(**kwargs)
```

### 2.2 Repository

**Responsibility:** Data access abstraction with CRUD operations and query derivation.

**Key Features:**
- Type-safe operations using generics `Repository[T]`
- Automatic query generation from method names
- Support for custom Cypher queries via `@query` decorator
- Pagination and sorting

**Design:**
```python
class Repository(Generic[T]):
    def __init__(self, graph: Graph, entity_class: Type[T]):
        self.graph = graph
        self.entity_class = entity_class
        self.mapper = EntityMapper()
        self.query_builder = QueryBuilder()
    
    def save(self, entity: T) -> T:
        """Save or update entity"""
        pass
    
    def find_by_id(self, id: Any) -> Optional[T]:
        """Find entity by ID"""
        pass
    
    def find_all(self) -> List[T]:
        """Find all entities"""
        pass
    
    def delete(self, entity: T) -> None:
        """Delete entity"""
        pass
    
    def __getattr__(self, name: str):
        """Handle derived query methods dynamically"""
        if name.startswith(('find_by_', 'count_by_', 'exists_by_', 'delete_by_')):
            return self._create_derived_query_method(name)
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")
```

### 2.3 QueryBuilder

**Responsibility:** Generate Cypher queries from method specifications.

**Design:**
```python
class QueryBuilder:
    def build_create_query(self, metadata: EntityMetadata, properties: dict) -> str:
        """Generate CREATE query"""
        pass
    
    def build_match_query(self, metadata: EntityMetadata, conditions: List[Condition]) -> str:
        """Generate MATCH query with WHERE clause"""
        pass
    
    def build_relationship_query(self, 
                                 source_id: Any,
                                 rel_type: str,
                                 target_id: Any,
                                 direction: str) -> str:
        """Generate relationship creation query"""
        pass
```

### 2.4 Session

**Responsibility:** Unit of work pattern - track changes and batch operations.

**Design:**
```python
class Session:
    def __init__(self, graph: Graph):
        self.graph = graph
        self._identity_map: Dict[Tuple[Type, Any], Any] = {}
        self._new_entities: Set[Any] = set()
        self._dirty_entities: Set[Any] = set()
        self._deleted_entities: Set[Any] = set()
    
    def add(self, entity: Any) -> None:
        """Mark entity for insertion"""
        self._new_entities.add(entity)
    
    def delete(self, entity: Any) -> None:
        """Mark entity for deletion"""
        self._deleted_entities.add(entity)
    
    def commit(self) -> None:
        """Persist all changes to database"""
        # Generate batch operations
        pass
    
    def rollback(self) -> None:
        """Discard all pending changes"""
        pass
```

---

## 3. Entity Mapping

### 3.1 Node Decorator

**Purpose:** Mark a class as a graph node entity.

**Signature:**
```python
def node(
    labels: Union[str, List[str]] = None,
    primary_label: str = None
) -> Callable[[Type[T]], Type[T]]:
    """
    Decorator to mark a class as a FalkorDB node entity.
    
    Args:
        labels: Single label or list of labels for the node
        primary_label: Explicit primary label (defaults to first label or class name)
    
    Returns:
        Decorated class with entity metadata
    """
```

**Usage:**
```python
@node(labels=["Person", "Individual"])
class Person:
    pass

@node("Company")  # Single label shorthand
class Company:
    pass

@node()  # Use class name as label
class User:
    pass
```

**Implementation Details:**
- Store metadata in class attribute `__node_metadata__`
- If no labels provided, use class name as label
- Primary label is first label unless explicitly specified
- Support inheritance (subclass inherits parent labels)

### 3.2 Property Mapping

**Purpose:** Map Python attributes to graph properties.

**Signature:**
```python
def property(
    name: str = None,
    converter: Callable = None,
    required: bool = False
) -> Any:
    """
    Map a Python attribute to a graph property.
    
    Args:
        name: Property name in graph (defaults to attribute name)
        converter: Custom type converter function
        required: Whether property is required (validation)
    
    Returns:
        Property descriptor
    """
```

**Usage:**
```python
@node("Person")
class Person:
    id: Optional[int] = None
    name: str = property("full_name")  # Maps to 'full_name' in graph
    email: str = property(required=True)
    age: int
    created_at: datetime = property(converter=datetime_converter)
```

**Type Mapping:**

| Python Type | FalkorDB Type | Conversion |
|-------------|---------------|------------|
| `str` | String | Direct |
| `int` | Integer | Direct |
| `float` | Float | Direct |
| `bool` | Boolean | Direct |
| `datetime` | Integer (timestamp) | Convert to/from timestamp |
| `date` | String (ISO) | Convert to/from ISO format |
| `List[T]` | Array | Element-wise conversion |
| `Dict[str, Any]` | Map | Recursive conversion |
| `Enum` | String | Convert to/from name |

### 3.3 ID Field

**Purpose:** Mark the primary key field.

**Options:**
1. **Manual ID:** User assigns IDs
```python
@node("Person")
class Person:
    id: str  # User-assigned ID
    name: str
```

2. **Generated ID (FalkorDB internal):**
```python
@node("Person")
class Person:
    id: Optional[int] = generated_id()  # Uses id(n)
    name: str
```

3. **Generated ID (UUID):**
```python
@node("Person")
class Person:
    id: str = generated_id(generator=uuid_generator)
    name: str
```

**Implementation:**
```python
def generated_id(generator: Callable = None) -> Any:
    """
    Mark field as auto-generated ID.
    
    Args:
        generator: Custom ID generator function (defaults to FalkorDB internal ID)
    """
    pass
```

---

## 4. Repository Pattern

### 4.1 Base Repository

**Definition:**
```python
class Repository(Generic[T]):
    """
    Base repository for entity data access.
    
    Type Parameters:
        T: Entity type
    """
    
    # Basic CRUD
    def save(self, entity: T) -> T: ...
    def save_all(self, entities: Iterable[T]) -> List[T]: ...
    def find_by_id(self, id: Any) -> Optional[T]: ...
    def find_all(self) -> List[T]: ...
    def find_all_by_id(self, ids: Iterable[Any]) -> List[T]: ...
    def exists_by_id(self, id: Any) -> bool: ...
    def count(self) -> int: ...
    def delete(self, entity: T) -> None: ...
    def delete_by_id(self, id: Any) -> None: ...
    def delete_all(self, entities: Iterable[T]) -> None: ...
```

### 4.2 Custom Repository

**Usage:**
```python
class PersonRepository(Repository[Person]):
    """
    Custom repository with derived query methods.
    Methods starting with find_by_*, count_by_*, etc. are auto-implemented.
    """
    pass

# Usage
repo = PersonRepository(graph, Person)
person = repo.find_by_name("Alice")
count = repo.count_by_age_greater_than(18)
adults = repo.find_by_age_between(18, 65)
```

### 4.3 Custom Queries

**Purpose:** Define complex Cypher queries with automatic parameter binding.

**Signature:**
```python
def query(
    cypher: str,
    returns: Type = None,
    write: bool = False
) -> Callable:
    """
    Decorator for custom Cypher query methods.
    
    Args:
        cypher: Cypher query with $param placeholders
        returns: Expected return type (entity class or primitive)
        write: Whether query performs write operations
    """
```

**Usage:**
```python
class PersonRepository(Repository[Person]):
    @query(
        "MATCH (p:Person)-[:KNOWS]->(f:Person) WHERE p.name = $name RETURN f",
        returns=Person
    )
    def find_friends(self, name: str) -> List[Person]:
        pass
    
    @query(
        "MATCH (p:Person) WHERE p.age > $min_age AND p.age < $max_age RETURN p",
        returns=Person
    )
    def find_by_age_range(self, min_age: int, max_age: int) -> List[Person]:
        pass
    
    @query(
        "MATCH (p:Person)-[:WORKS_FOR]->(c:Company) WHERE c.name = $company RETURN count(p)",
        returns=int
    )
    def count_employees(self, company: str) -> int:
        pass
    
    @query(
        "MATCH (p:Person {id: $id}) SET p.last_login = $timestamp",
        write=True
    )
    def update_last_login(self, id: int, timestamp: datetime) -> None:
        pass
```

---

## 5. Query Derivation

### 5.1 Supported Query Patterns

**Query Keywords:**

| Pattern | Generated Cypher | Example |
|---------|------------------|---------|
| `find_by_<property>` | `MATCH (n) WHERE n.property = $value RETURN n` | `find_by_name("Alice")` |
| `find_by_<prop>_and_<prop>` | `MATCH (n) WHERE n.p1 = $v1 AND n.p2 = $v2 RETURN n` | `find_by_name_and_age("Alice", 25)` |
| `find_by_<prop>_or_<prop>` | `MATCH (n) WHERE n.p1 = $v1 OR n.p2 = $v2 RETURN n` | `find_by_name_or_email(...)` |
| `count_by_<property>` | `MATCH (n) WHERE n.property = $value RETURN count(n)` | `count_by_age(25)` |
| `exists_by_<property>` | `MATCH (n) WHERE n.property = $value RETURN count(n) > 0` | `exists_by_email("...")` |
| `delete_by_<property>` | `MATCH (n) WHERE n.property = $value DELETE n` | `delete_by_id(123)` |
| `find_first_by_<property>` | `MATCH (n) WHERE ... RETURN n LIMIT 1` | `find_first_by_age(25)` |
| `find_top_N_by_<property>` | `MATCH (n) WHERE ... RETURN n LIMIT N` | `find_top_10_by_age(25)` |

**Comparison Operators:**

| Suffix | Operator | Example |
|--------|----------|---------|
| (none) | `=` | `find_by_age(25)` → `age = 25` |
| `_not` | `<>` | `find_by_age_not(25)` → `age <> 25` |
| `_greater_than` | `>` | `find_by_age_greater_than(18)` → `age > 18` |
| `_greater_than_equal` | `>=` | `find_by_age_greater_than_equal(18)` |
| `_less_than` | `<` | `find_by_age_less_than(65)` |
| `_less_than_equal` | `<=` | `find_by_age_less_than_equal(65)` |
| `_between` | `>= AND <=` | `find_by_age_between(18, 65)` |
| `_in` | `IN` | `find_by_age_in([18, 25, 30])` |
| `_not_in` | `NOT IN` | `find_by_age_not_in([0, 1])` |
| `_is_null` | `IS NULL` | `find_by_email_is_null()` |
| `_is_not_null` | `IS NOT NULL` | `find_by_email_is_not_null()` |
| `_containing` | `CONTAINS` | `find_by_name_containing("ali")` |
| `_starting_with` | `STARTS WITH` | `find_by_name_starting_with("Al")` |
| `_ending_with` | `ENDS WITH` | `find_by_name_ending_with("ice")` |
| `_like` | `=~` (regex) | `find_by_name_like(".*ice$")` |

**Sorting:**
```python
repo.find_by_age_greater_than_order_by_name_asc(18)
# → MATCH (n) WHERE n.age > 18 RETURN n ORDER BY n.name ASC

repo.find_all_order_by_age_desc_name_asc()
# → MATCH (n) RETURN n ORDER BY n.age DESC, n.name ASC
```

**Pagination:**
```python
from falkordb_orm import Pageable, Page

pageable = Pageable(page=0, size=10, sort_by="name", direction="ASC")
page: Page[Person] = repo.find_by_age_greater_than(18, pageable)

print(f"Total: {page.total_elements}")
print(f"Pages: {page.total_pages}")
print(f"Content: {page.content}")
```

### 5.2 Query Parser Implementation

**Algorithm:**
```python
class QueryParser:
    def parse_method_name(self, method_name: str) -> QuerySpec:
        """
        Parse derived query method name into QuerySpec.
        
        Examples:
            find_by_name_and_age_greater_than
            count_by_email
            exists_by_username_containing
            delete_by_age_less_than
            find_top_10_by_age_order_by_name_desc
        """
        # 1. Extract operation (find, count, exists, delete)
        # 2. Extract limiting (first, top_N)
        # 3. Extract conditions (property + operator)
        # 4. Extract logical operators (and, or)
        # 5. Extract ordering (order_by)
        pass
```

**QuerySpec Structure:**
```python
@dataclass
class QuerySpec:
    operation: str  # 'find', 'count', 'exists', 'delete'
    conditions: List[Condition]
    logical_operator: str  # 'AND', 'OR'
    ordering: List[OrderClause]
    limit: Optional[int]
```

---

## 6. Relationship Handling

### 6.1 Relationship Decorator

**Signature:**
```python
def relationship(
    type: str,
    direction: str = "OUTGOING",
    target: Type = None,
    lazy: bool = True,
    cascade: bool = False
) -> Any:
    """
    Define a relationship to another entity.
    
    Args:
        type: Relationship type (e.g., "KNOWS", "WORKS_FOR")
        direction: "OUTGOING", "INCOMING", or "BOTH"
        target: Target entity class (inferred from type hint if not provided)
        lazy: Whether to load relationship lazily (default: True)
        cascade: Whether to cascade save/delete operations
    """
```

**Usage:**
```python
@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    
    # One-to-many: Person -> [Person]
    friends: List["Person"] = relationship(
        type="KNOWS",
        direction="OUTGOING"
    )
    
    # Many-to-one: Person -> Company
    company: Optional["Company"] = relationship(
        type="WORKS_FOR",
        direction="OUTGOING"
    )
    
    # Bidirectional
    followers: List["Person"] = relationship(
        type="FOLLOWS",
        direction="INCOMING"
    )
    following: List["Person"] = relationship(
        type="FOLLOWS",
        direction="OUTGOING"
    )

@node("Company")
class Company:
    id: Optional[int] = None
    name: str
    
    # Inverse relationship
    employees: List[Person] = relationship(
        type="WORKS_FOR",
        direction="INCOMING"
    )
```

### 6.2 Relationship Persistence

**Saving with Relationships:**
```python
# Cascade save
person = Person(name="Alice")
person.company = Company(name="TechCorp")
person.friends = [
    Person(name="Bob"),
    Person(name="Charlie")
]

repo.save(person)  # Saves person, company, and friends + relationships
```

**Generated Queries:**
```cypher
// 1. Save main entity
CREATE (p:Person {name: 'Alice'}) RETURN p, id(p)

// 2. Save related entities (if cascade=True)
CREATE (c:Company {name: 'TechCorp'}) RETURN c, id(c)
CREATE (f1:Person {name: 'Bob'}) RETURN f1, id(f1)
CREATE (f2:Person {name: 'Charlie'}) RETURN f2, id(f2)

// 3. Create relationships
MATCH (p:Person), (c:Company) WHERE id(p) = 1 AND id(c) = 2
CREATE (p)-[:WORKS_FOR]->(c)

MATCH (p:Person), (f:Person) WHERE id(p) = 1 AND id(f) = 3
CREATE (p)-[:KNOWS]->(f)

MATCH (p:Person), (f:Person) WHERE id(p) = 1 AND id(f) = 4
CREATE (p)-[:KNOWS]->(f)
```

### 6.3 Lazy Loading

**Implementation:**
```python
class LazyLoader:
    """Proxy for lazy relationship loading"""
    
    def __init__(self, source_id: Any, rel_metadata: RelationshipMetadata):
        self._source_id = source_id
        self._rel_metadata = rel_metadata
        self._loaded = False
        self._value = None
    
    def __iter__(self):
        if not self._loaded:
            self._load()
        return iter(self._value)
    
    def _load(self):
        # Generate and execute query to load relationships
        cypher = f"""
        MATCH (source)-[:{self._rel_metadata.type}]->(target:{self._rel_metadata.target_label})
        WHERE id(source) = $source_id
        RETURN target
        """
        # Execute and populate self._value
        self._loaded = True
```

**Usage:**
```python
person = repo.find_by_id(1)  # Loads person only

# First access triggers query
for friend in person.friends:  # Query executed here
    print(friend.name)

# Subsequent access uses cached value
for friend in person.friends:  # No query executed
    print(friend.name)
```

### 6.4 Eager Loading

**Explicit Loading:**
```python
# Load with specific relationships
person = repo.find_by_id(1, fetch=["friends", "company"])

# Load with nested relationships
person = repo.find_by_id(1, fetch=["friends.company", "company.employees"])
```

**Generated Query:**
```cypher
MATCH (p:Person)
WHERE id(p) = $id
OPTIONAL MATCH (p)-[:KNOWS]->(f:Person)
OPTIONAL MATCH (p)-[:WORKS_FOR]->(c:Company)
RETURN p, collect(distinct f) as friends, c as company
```

---

## 7. Session Management

### 7.1 Session API

**Basic Usage:**
```python
from falkordb_orm import Session

# Create session
session = Session(graph)

# Add new entity
person = Person(name="Alice", email="alice@example.com")
session.add(person)

# Modify entity
existing = session.find_by_id(Person, 1)
existing.age = 26

# Delete entity
session.delete(other_person)

# Persist all changes
session.commit()

# Or discard changes
session.rollback()
```

### 7.2 Context Manager

```python
with Session(graph) as session:
    person = Person(name="Alice")
    session.add(person)
    # Automatically commits on exit
# Or rolls back on exception
```

### 7.3 Identity Map

**Purpose:** Ensure single instance per entity ID within session.

```python
class Session:
    def __init__(self, graph: Graph):
        self._identity_map: Dict[Tuple[Type, Any], Any] = {}
    
    def get(self, entity_class: Type[T], id: Any) -> Optional[T]:
        """Get entity from identity map or load from database"""
        key = (entity_class, id)
        
        if key in self._identity_map:
            return self._identity_map[key]
        
        entity = self._load_from_db(entity_class, id)
        if entity:
            self._identity_map[key] = entity
        
        return entity
```

**Benefits:**
- Prevents duplicate instances of same entity
- Automatic change tracking
- Consistent object identity within transaction

### 7.4 Unit of Work

**Change Tracking:**
```python
class Session:
    def __init__(self, graph: Graph):
        self._new: Set[Any] = set()
        self._dirty: Set[Any] = set()
        self._deleted: Set[Any] = set()
    
    def add(self, entity: Any) -> None:
        """Track new entity"""
        self._new.add(entity)
    
    def _mark_dirty(self, entity: Any) -> None:
        """Track modified entity"""
        if entity not in self._new:
            self._dirty.add(entity)
    
    def delete(self, entity: Any) -> None:
        """Track deleted entity"""
        self._deleted.add(entity)
        self._new.discard(entity)
        self._dirty.discard(entity)
    
    def commit(self) -> None:
        """Persist all changes in optimal order"""
        # 1. INSERT new entities
        for entity in self._new:
            self._insert(entity)
        
        # 2. UPDATE dirty entities
        for entity in self._dirty:
            self._update(entity)
        
        # 3. DELETE removed entities
        for entity in self._deleted:
            self._delete(entity)
        
        self._clear_tracking()
```

---

## 8. Type System

### 8.1 Built-in Converters

```python
class TypeConverter(ABC):
    @abstractmethod
    def to_graph(self, value: Any) -> Any:
        """Convert Python value to graph-compatible type"""
        pass
    
    @abstractmethod
    def from_graph(self, value: Any) -> Any:
        """Convert graph value to Python type"""
        pass
```

**Standard Converters:**

| Python Type | Converter | To Graph | From Graph |
|-------------|-----------|----------|------------|
| `datetime` | `DateTimeConverter` | `int` (timestamp) | `datetime.fromtimestamp()` |
| `date` | `DateConverter` | `str` (ISO) | `date.fromisoformat()` |
| `Decimal` | `DecimalConverter` | `float` | `Decimal()` |
| `UUID` | `UUIDConverter` | `str` | `UUID()` |
| `Enum` | `EnumConverter` | `str` (name) | `EnumClass[name]` |
| `List[T]` | `ListConverter` | `list` (recursive) | `list` (recursive) |
| `Set[T]` | `SetConverter` | `list` | `set` |

### 8.2 Custom Converters

**Definition:**
```python
from falkordb_orm import TypeConverter

class PointConverter(TypeConverter):
    def to_graph(self, value: Point) -> dict:
        return {"lat": value.latitude, "lon": value.longitude}
    
    def from_graph(self, value: dict) -> Point:
        return Point(latitude=value["lat"], longitude=value["lon"])

# Register converter
register_converter(Point, PointConverter())
```

**Usage in Entity:**
```python
@node("Location")
class Location:
    id: Optional[int] = None
    name: str
    coordinates: Point = property(converter=PointConverter())
```

---

## 9. API Reference

### 9.1 Decorators

```python
# Node entity
@node(labels: Union[str, List[str]] = None, primary_label: str = None)

# Property mapping
def property(name: str = None, converter: TypeConverter = None, required: bool = False)

# Relationship
def relationship(
    type: str,
    direction: Literal["OUTGOING", "INCOMING", "BOTH"] = "OUTGOING",
    target: Type = None,
    lazy: bool = True,
    cascade: bool = False
)

# ID generation
def generated_id(generator: Callable = None)

# Custom query
def query(cypher: str, returns: Type = None, write: bool = False)
```

### 9.2 Repository

```python
class Repository(Generic[T]):
    def __init__(self, graph: Graph, entity_class: Type[T])
    
    # CRUD
    def save(self, entity: T) -> T
    def save_all(self, entities: Iterable[T]) -> List[T]
    def find_by_id(self, id: Any, fetch: List[str] = None) -> Optional[T]
    def find_all(self, pageable: Pageable = None) -> Union[List[T], Page[T]]
    def find_all_by_id(self, ids: Iterable[Any]) -> List[T]
    def exists_by_id(self, id: Any) -> bool
    def count(self) -> int
    def delete(self, entity: T) -> None
    def delete_by_id(self, id: Any) -> None
    def delete_all(self, entities: Iterable[T] = None) -> None
```

### 9.3 Session

```python
class Session:
    def __init__(self, graph: Graph)
    
    def add(self, entity: Any) -> None
    def get(self, entity_class: Type[T], id: Any) -> Optional[T]
    def query(self, entity_class: Type[T]) -> QueryBuilder
    def delete(self, entity: Any) -> None
    def commit(self) -> None
    def rollback(self) -> None
    def close(self) -> None
    
    # Context manager
    def __enter__(self) -> Session
    def __exit__(self, exc_type, exc_val, exc_tb) -> None
```

### 9.4 Pagination

```python
@dataclass
class Pageable:
    page: int = 0
    size: int = 20
    sort_by: str = None
    direction: Literal["ASC", "DESC"] = "ASC"

@dataclass
class Page(Generic[T]):
    content: List[T]
    page_number: int
    page_size: int
    total_elements: int
    total_pages: int
    
    def has_next(self) -> bool
    def has_previous(self) -> bool
```

---

## 10. Implementation Plan

### Phase 1: Foundation (Week 1-2)
**Goal:** Core entity mapping and basic CRUD

**Tasks:**
- [ ] Project setup (pyproject.toml, directory structure)
- [ ] Implement `@node` decorator
- [ ] Implement `property()` function
- [ ] Implement `EntityMetadata` and `PropertyMetadata`
- [ ] Implement `EntityMapper` (basic conversion)
- [ ] Implement basic `Repository` class
- [ ] Implement `save()` and `find_by_id()`
- [ ] Unit tests for decorators and mapper
- [ ] Basic documentation

**Deliverable:** Can define entities and perform basic CRUD operations.

### Phase 2: Query Derivation (Week 3-4)
**Goal:** Automatic query generation from method names

**Tasks:**
- [ ] Implement `QueryParser` (parse method names)
- [ ] Implement `QueryBuilder` (generate Cypher)
- [ ] Support basic operators (equals, not, greater_than, etc.)
- [ ] Support logical operators (and, or)
- [ ] Support string operations (containing, starting_with, etc.)
- [ ] Support count_by, exists_by, delete_by
- [ ] Implement `__getattr__` in Repository for dynamic methods
- [ ] Unit tests for query parsing and generation
- [ ] Integration tests with FalkorDB

**Deliverable:** Derived query methods work automatically.

### Phase 3: Relationships (Week 5-6)
**Goal:** Relationship mapping and persistence

**Tasks:**
- [ ] Implement `@relationship` decorator
- [ ] Implement `RelationshipMetadata`
- [ ] Implement relationship saving (cascade)
- [ ] Implement lazy loading with proxy objects
- [ ] Implement eager loading (fetch parameter)
- [ ] Handle bidirectional relationships
- [ ] Unit tests for relationship mapping
- [ ] Integration tests with complex graphs

**Deliverable:** Can define and persist relationships between entities.

### Phase 4: Advanced Features (Week 7-8)
**Goal:** Session management and custom queries

**Tasks:**
- [ ] Implement `Session` class
- [ ] Implement identity map
- [ ] Implement unit of work (change tracking)
- [ ] Implement `@query` decorator
- [ ] Implement pagination (`Pageable`, `Page`)
- [ ] Implement sorting and ordering
- [ ] Type converters (datetime, enum, etc.)
- [ ] Custom converter registration
- [ ] Integration tests for sessions

**Deliverable:** Full-featured ORM with session management.

### Phase 5: Async Support (Week 9)
**Goal:** Async/await support

**Tasks:**
- [ ] Implement `AsyncRepository`
- [ ] Implement `AsyncSession`
- [ ] Support async query methods
- [ ] Async integration tests
- [ ] Documentation for async usage

**Deliverable:** Full async/await support.

### Phase 6: Polish & Documentation (Week 10)
**Goal:** Production-ready library

**Tasks:**
- [ ] Comprehensive documentation
- [ ] API reference docs
- [ ] Migration guide from raw queries
- [ ] Performance optimization
- [ ] Error handling improvements
- [ ] Example projects (Twitter, blog, etc.)
- [ ] CI/CD setup
- [ ] Package publishing

**Deliverable:** Production-ready library with full documentation.

---

## 11. Examples

### 11.1 Basic Usage

```python
from falkordb import FalkorDB
from falkordb_orm import node, property, Repository

# Define entity
@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    email: str
    age: int

# Connect to FalkorDB
db = FalkorDB(host='localhost', port=6379)
graph = db.select_graph('social')

# Create repository
repo = Repository(graph, Person)

# Create and save
person = Person(name="Alice", email="alice@example.com", age=25)
saved = repo.save(person)
print(f"Saved person with ID: {saved.id}")

# Find by ID
found = repo.find_by_id(saved.id)
print(f"Found: {found.name}")

# Derived query
adults = repo.find_by_age_greater_than(18)
print(f"Found {len(adults)} adults")

# Count
count = repo.count_by_age(25)
print(f"People aged 25: {count}")

# Delete
repo.delete(person)
```

### 11.2 Relationships Example

```python
from falkordb_orm import node, relationship, Repository

@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    friends: List["Person"] = relationship(type="KNOWS", direction="OUTGOING")
    company: Optional["Company"] = relationship(type="WORKS_FOR", direction="OUTGOING")

@node("Company")
class Company:
    id: Optional[int] = None
    name: str
    employees: List[Person] = relationship(type="WORKS_FOR", direction="INCOMING")

# Create entities with relationships
alice = Person(name="Alice")
bob = Person(name="Bob")
company = Company(name="TechCorp")

alice.friends = [bob]
alice.company = company

# Save (cascades to related entities)
repo = Repository(graph, Person)
saved_alice = repo.save(alice)

# Access relationships (lazy loaded)
for friend in saved_alice.friends:
    print(f"Friend: {friend.name}")
```

### 11.3 Custom Queries

```python
from falkordb_orm import node, Repository, query

@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    age: int

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
    
    @query(
        "MATCH (p:Person) RETURN p ORDER BY p.age DESC LIMIT $limit",
        returns=Person
    )
    def find_oldest(self, limit: int = 10) -> List[Person]:
        pass

# Usage
repo = PersonRepository(graph, Person)
friends = repo.find_friends("Alice")
young_adults = repo.find_by_age_range(18, 30)
oldest = repo.find_oldest(5)
```

### 11.4 Session Example

```python
from falkordb_orm import Session

with Session(graph) as session:
    # Create new entities
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

### 11.5 Pagination Example

```python
from falkordb_orm import Repository, Pageable

repo = Repository(graph, Person)

# First page of 10 results, sorted by name
pageable = Pageable(page=0, size=10, sort_by="name", direction="ASC")
page = repo.find_by_age_greater_than(18, pageable)

print(f"Page {page.page_number + 1} of {page.total_pages}")
print(f"Total: {page.total_elements}")

for person in page.content:
    print(f"  - {person.name}")

# Next page
if page.has_next():
    next_pageable = Pageable(page=1, size=10, sort_by="name", direction="ASC")
    next_page = repo.find_by_age_greater_than(18, next_pageable)
```

### 11.6 Async Example

```python
import asyncio
from falkordb.asyncio import FalkorDB
from falkordb_orm.asyncio import AsyncRepository

@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    age: int

async def main():
    db = FalkorDB(host='localhost', port=6379)
    graph = db.select_graph('social')
    
    repo = AsyncRepository(graph, Person)
    
    # Async save
    person = Person(name="Alice", age=25)
    saved = await repo.save(person)
    
    # Async find
    found = await repo.find_by_id(saved.id)
    
    # Async derived query
    adults = await repo.find_by_age_greater_than(18)
    
    print(f"Found {len(adults)} adults")

asyncio.run(main())
```

### 11.7 Type Converters Example

```python
from datetime import datetime
from enum import Enum
from falkordb_orm import node, property, TypeConverter

class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

@node("User")
class User:
    id: Optional[int] = None
    username: str
    status: Status  # Auto-converted to/from string
    created_at: datetime  # Auto-converted to/from timestamp
    metadata: dict  # Auto-converted to/from map

# Usage
user = User(
    username="alice",
    status=Status.ACTIVE,
    created_at=datetime.now(),
    metadata={"role": "admin", "level": 5}
)

repo = Repository(graph, User)
saved = repo.save(user)

# Values automatically converted back
assert isinstance(saved.status, Status)
assert isinstance(saved.created_at, datetime)
assert isinstance(saved.metadata, dict)
```

---

## Appendix A: Comparison with Spring Data FalkorDB

| Feature | Spring Data FalkorDB | falkordb-orm (Proposed) |
|---------|---------------------|-------------------------|
| Entity Annotation | `@Node` | `@node` decorator |
| Property Mapping | `@Property` | `property()` function |
| Relationship Mapping | `@Relationship` | `relationship()` function |
| ID Generation | `@Id @GeneratedValue` | `generated_id()` |
| Repository Pattern | `FalkorDBRepository<T, ID>` | `Repository[T]` |
| Derived Queries | Method names | Method names (via `__getattr__`) |
| Custom Queries | `@Query` annotation | `@query` decorator |
| Transaction Support | `@Transactional` | `Session` (unit of work) |
| Lazy Loading | Automatic | Automatic (via proxies) |
| Async Support | ❌ | ✅ (via asyncio) |

---

## Appendix B: Performance Considerations

### Batch Operations

**Problem:** N+1 query problem when loading relationships.

**Solution:** Use batch loading with `UNWIND`:
```cypher
// Instead of N queries:
MATCH (p:Person)-[:KNOWS]->(f) WHERE id(p) = 1 RETURN f
MATCH (p:Person)-[:KNOWS]->(f) WHERE id(p) = 2 RETURN f
...

// Use one query:
UNWIND $ids AS id
MATCH (p:Person)-[:KNOWS]->(f)
WHERE id(p) = id
RETURN id, collect(f) as friends
```

### Query Optimization

1. **Use indexes:** Create indexes on frequently queried properties
2. **Limit relationships:** Use fetch hints to avoid loading unnecessary relationships
3. **Pagination:** Always use pagination for large result sets
4. **Projections:** Return only needed properties

### Caching Strategy

```python
class CachedRepository(Repository[T]):
    def __init__(self, graph: Graph, entity_class: Type[T], cache: Cache):
        super().__init__(graph, entity_class)
        self.cache = cache
    
    def find_by_id(self, id: Any) -> Optional[T]:
        # Check cache first
        cached = self.cache.get(f"{self.entity_class.__name__}:{id}")
        if cached:
            return cached
        
        # Load from database
        entity = super().find_by_id(id)
        if entity:
            self.cache.set(f"{self.entity_class.__name__}:{id}", entity)
        
        return entity
```

---

## Appendix C: Migration Guide

### From Raw Queries to ORM

**Before:**
```python
graph.query('''
    CREATE (p:Person {name: $name, email: $email, age: $age})
    RETURN p, id(p)
''', {'name': 'Alice', 'email': 'alice@example.com', 'age': 25})

result = graph.query('''
    MATCH (p:Person) WHERE p.age > $min_age RETURN p
''', {'min_age': 18})
```

**After:**
```python
@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    email: str
    age: int

repo = Repository(graph, Person)
person = Person(name="Alice", email="alice@example.com", age=25)
repo.save(person)

adults = repo.find_by_age_greater_than(18)
```

---

## Appendix D: Error Handling

```python
from falkordb_orm.exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
    InvalidQueryException,
    RelationshipException
)

try:
    person = repo.find_by_id(999)
    if person is None:
        raise EntityNotFoundException(f"Person with id 999 not found")
except EntityNotFoundException as e:
    print(f"Error: {e}")

try:
    repo.save(duplicate_person)
except DuplicateEntityException as e:
    print(f"Entity already exists: {e}")
```

---

## Conclusion

This design document outlines a comprehensive Python ORM for FalkorDB that provides:

1. **Intuitive API:** Spring Data-inspired patterns familiar to developers
2. **Type Safety:** Leveraging Python type hints and generics
3. **Performance:** Batch operations, lazy loading, and query optimization
4. **Flexibility:** Support for both simple and complex use cases
5. **Async Support:** First-class async/await support

The phased implementation plan ensures incremental delivery of value while maintaining code quality and test coverage. The resulting library will significantly improve developer productivity when working with FalkorDB in Python applications.
