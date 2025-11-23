# Decorators API Reference

This document provides comprehensive documentation for the decorator functions used to define entities and their properties in FalkorDB ORM.

## @node

The `@node` decorator is used to mark a class as a graph entity (node).

### Signature

```python
def node(
    labels: Union[str, List[str]],
    *,
    id_field: str = "id",
    id_generator: Optional[Callable[[], Any]] = None
) -> Callable[[Type[T]], Type[T]]
```

### Parameters

- **labels** (`str` or `List[str]`): The label(s) to assign to the node in the graph
  - Single label: `@node("Person")`
  - Multiple labels: `@node(["Person", "Individual"])`
  
- **id_field** (`str`, optional): The name of the field that stores the entity ID
  - Default: `"id"`
  - Must be annotated with `Optional[int]` type hint
  
- **id_generator** (`Callable`, optional): Function to generate IDs
  - Default: `None` (uses FalkorDB's internal ID)
  - Use `generated_id()` for auto-generated IDs

### Returns

The decorated class with metadata attached.

### Examples

#### Basic Node

```python
from falkordb_orm import node
from typing import Optional

@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    age: int
```

#### Multiple Labels

```python
@node(labels=["Person", "Individual", "User"])
class Person:
    id: Optional[int] = None
    name: str
    email: str
```

#### Custom ID Field

```python
@node("Person", id_field="person_id")
class Person:
    person_id: Optional[int] = None
    name: str
```

#### Auto-Generated ID

```python
from falkordb_orm import node, generated_id

@node("Person", id_generator=generated_id())
class Person:
    id: Optional[int] = None
    name: str
```

### Validation

The decorator validates that:
- The class has a field matching `id_field` name
- The ID field is annotated with `Optional[int]`
- All required type hints are present

### Errors

Raises `MetadataException` if:
- ID field is missing
- ID field has wrong type annotation
- Class is improperly configured

---

## property()

The `property()` function is used to map a Python attribute to a different property name in the graph.

### Signature

```python
def property(
    graph_name: str,
    *,
    converter: Optional[TypeConverter] = None,
    required: bool = False
) -> Any
```

### Parameters

- **graph_name** (`str`): The name of the property in the graph database
  
- **converter** (`TypeConverter`, optional): Custom type converter for this property
  - Default: Uses built-in converter based on type hint
  
- **required** (`bool`, optional): Whether the property is required
  - Default: `False`
  - If `True`, validation will fail if value is `None`

### Returns

A property descriptor that handles the mapping.

### Examples

#### Basic Property Mapping

```python
from falkordb_orm import node, property

@node("Person")
class Person:
    id: Optional[int] = None
    name: str = property("full_name")  # Maps to 'full_name' in graph
    email: str  # Maps to 'email' (same name)
```

#### Required Property

```python
@node("Person")
class Person:
    id: Optional[int] = None
    name: str = property("full_name", required=True)
    email: str = property("email_address", required=True)
```

#### Custom Converter

```python
from datetime import datetime
from falkordb_orm import node, property, TypeConverter

class DateConverter(TypeConverter):
    def to_graph(self, value: datetime) -> int:
        return int(value.timestamp())
    
    def from_graph(self, value: int) -> datetime:
        return datetime.fromtimestamp(value)

@node("Event")
class Event:
    id: Optional[int] = None
    name: str
    created_at: datetime = property("created", converter=DateConverter())
```

### Built-in Type Conversion

The ORM automatically converts between Python and graph types:

| Python Type | Graph Type | Example |
|-------------|------------|---------|
| `int` | Integer | `42` |
| `float` | Float | `3.14` |
| `str` | String | `"hello"` |
| `bool` | Boolean | `True` |
| `list` | Array | `[1, 2, 3]` |
| `dict` | Map | `{"key": "value"}` |
| `datetime` | String (ISO) | `"2024-01-01T00:00:00"` |
| `date` | String | `"2024-01-01"` |
| `Enum` | String | `"ACTIVE"` |

---

## relationship()

The `relationship()` function defines a relationship between entities.

### Signature

```python
def relationship(
    type: str,
    *,
    direction: Literal["OUTGOING", "INCOMING", "BOTH"] = "OUTGOING",
    target: Optional[Type] = None,
    lazy: bool = True,
    cascade: bool = False
) -> Any
```

### Parameters

- **type** (`str`): The relationship type in the graph (e.g., "KNOWS", "WORKS_FOR")
  
- **direction** (`str`, optional): The direction of the relationship
  - `"OUTGOING"`: This entity → target entity (default)
  - `"INCOMING"`: Target entity → this entity
  - `"BOTH"`: Bidirectional relationship
  
- **target** (`Type`, optional): The target entity class
  - Usually inferred from type hint
  - Required for forward references
  
- **lazy** (`bool`, optional): Whether to load relationships lazily
  - Default: `True` (load on first access)
  - `False`: Must be explicitly fetched with `fetch` parameter
  
- **cascade** (`bool`, optional): Whether to cascade save operations
  - Default: `False`
  - `True`: Automatically save related entities when saving this entity

### Returns

A relationship descriptor that handles the relationship.

### Examples

#### One-to-Many Relationship

```python
from falkordb_orm import node, relationship
from typing import Optional, List

@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    friends: List["Person"] = relationship(type="KNOWS", direction="OUTGOING")
```

#### Many-to-One Relationship

```python
@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    company: Optional["Company"] = relationship(type="WORKS_FOR", direction="OUTGOING")

@node("Company")
class Company:
    id: Optional[int] = None
    name: str
```

#### Bidirectional Relationships

```python
@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    company: Optional["Company"] = relationship(type="WORKS_FOR", direction="OUTGOING")

@node("Company")
class Company:
    id: Optional[int] = None
    name: str
    employees: List[Person] = relationship(type="WORKS_FOR", direction="INCOMING")
```

#### Cascade Save

```python
@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    company: Optional["Company"] = relationship(
        type="WORKS_FOR",
        direction="OUTGOING",
        cascade=True  # Saves company automatically
    )

# Create and save
person = Person(name="Alice", company=Company(name="Acme Corp"))
repo.save(person)  # Both person and company are saved
```

#### Eager Loading

```python
@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    friends: List["Person"] = relationship(type="KNOWS", lazy=False)

# Must use fetch parameter
person = repo.find_by_id(1, fetch=["friends"])
```

### Type Annotations

Relationship fields must use proper type annotations:

- **One-to-One**: `Optional[TargetType]`
- **One-to-Many**: `List[TargetType]`
- **Forward References**: Use string literals for circular dependencies

```python
# Forward reference (same class)
@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    friends: List["Person"] = relationship(type="KNOWS")
    
# Forward reference (not yet defined)
@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    company: Optional["Company"] = relationship(type="WORKS_FOR")

# Define later
@node("Company")
class Company:
    id: Optional[int] = None
    name: str
```

### Lazy Loading Behavior

When `lazy=True` (default):

```python
person = repo.find_by_id(1)
# Relationship not loaded yet

for friend in person.friends:  # Triggers load on first access
    print(friend.name)

# Subsequent access uses cached data (no additional query)
print(len(person.friends))
```

### Errors

Raises `RelationshipException` if:
- Invalid direction specified
- Target type cannot be resolved
- Circular relationship causes infinite loop

Raises `ConfigurationException` if:
- Type annotation is missing or invalid
- Relationship metadata is improperly configured

---

## interned()

The `interned()` function marks a string property to use FalkorDB's `intern()` function for memory optimization through string deduplication.

### Signature

```python
def interned(
    name: Optional[str] = None,
    required: bool = False
) -> Any
```

### Parameters

- **name** (`str`, optional): The name of the property in the graph database
  - Default: Uses the Python attribute name
  
- **required** (`bool`, optional): Whether the property is required
  - Default: `False`

### Returns

A property descriptor configured for string interning.

### Description

<cite index="2-1,2-10">String interning deduplicates strings by storing a single internal copy across the database. It is especially useful for repeated string values—like country names, email domains, or tags—in large graphs.</cite> <cite index="2-12">Interned strings can be stored as node or relationship properties, and behave identically to regular strings in queries, with the added benefit of reduced memory usage.</cite>

### When to Use

Use `interned()` for string properties that have:
- Limited unique values (e.g., countries, cities)
- High repetition across entities (e.g., status fields)
- Categorical data (e.g., tags, categories, departments)

**Examples of good candidates**:
- Country names: "United States", "United Kingdom", "Canada" (repeated thousands of times)
- Status fields: "Active", "Inactive", "Pending" (repeated frequently)
- Email domains: "gmail.com", "outlook.com" (many users per domain)
- Categories: "Electronics", "Books", "Clothing" (limited set)

**Not recommended for**:
- Unique strings (e.g., user-specific descriptions)
- Strings that rarely repeat
- Very long text fields

### Examples

#### Basic Usage

```python
from falkordb_orm import node, interned
from typing import Optional

@node("User")
class User:
    id: Optional[int] = None
    name: str
    email: str
    country: str = interned()  # Deduplicated string
    city: str = interned()
```

#### Custom Property Name

```python
@node("User")
class User:
    id: Optional[int] = None
    name: str
    status: str = interned("user_status")  # Maps to 'user_status' in graph
```

#### Required Interned Property

```python
@node("Product")
class Product:
    id: Optional[int] = None
    name: str
    category: str = interned(required=True)  # Required and deduplicated
    brand: str = interned()
```

#### Using property() with interned Flag

Alternatively, you can use the `property()` function with `interned=True`:

```python
from falkordb_orm import node, property

@node("User")
class User:
    id: Optional[int] = None
    name: str
    country: str = property(interned=True)  # Equivalent to interned()
    city: str = property("user_city", interned=True)
```

#### Real-World Example

```python
from falkordb_orm import node, interned
from typing import Optional

@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    email: str
    
    # Interned properties for memory optimization
    country: str = interned()      # "United States" stored once for all US users
    city: str = interned()         # "New York" stored once for all NYC users
    status: str = interned()       # "Active", "Inactive" stored once each
    email_domain: str = interned() # "gmail.com" stored once for all Gmail users
    
    # Regular property - unique per user
    bio: str  # Not interned - each user has unique bio

# When you save multiple users:
user1 = Person(name="Alice", country="United States", city="New York", 
               status="Active", email_domain="gmail.com")
user2 = Person(name="Bob", country="United States", city="New York",
               status="Active", email_domain="gmail.com")

# "United States", "New York", "Active", "gmail.com" are stored only ONCE in memory
# Both users reference the same interned string copies
```

### Memory Benefits

For a dataset with 1 million users:

**Without interning**:
- "United States" stored 500,000 times
- "Active" stored 900,000 times
- Total: Significant memory waste

**With interning**:
- "United States" stored once
- "Active" stored once
- Total: Massive memory savings

### Performance

- **Memory**: Dramatically reduced for repeated values
- **Comparison**: Faster (uses reference equality instead of string comparison)
- **Queries**: No performance impact - works like regular strings

### Technical Details

When you use `interned()`, the ORM automatically wraps the value with FalkorDB's `intern()` function:

```cypher
-- Without interned()
CREATE (u:User {country: "United States"})

-- With interned()
CREATE (u:User) SET u.country = intern("United States")
```

### Errors

Raises `ConfigurationException` if:
- Used on non-string properties
- Property name conflicts with existing property

---

## generated_id()

Helper function to create an ID generator.

### Signature

```python
def generated_id() -> Callable[[], int]
```

### Returns

A callable that generates unique IDs.

### Example

```python
from falkordb_orm import node, generated_id

@node("Person", id_generator=generated_id())
class Person:
    id: Optional[int] = None
    name: str
```

### Note

In most cases, you should use FalkorDB's internal node IDs (the default) rather than generating your own.

---

## Best Practices

### 1. Always Use Type Hints

```python
# Good
@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    age: int

# Bad
@node("Person")
class Person:
    id = None
    name = ""
    age = 0
```

### 2. Use Descriptive Labels

```python
# Good
@node("Person")
@node(["Person", "User", "Individual"])

# Less ideal
@node("P")
```

### 3. Use Cascade Sparingly

Only use `cascade=True` when you want to automatically save related entities. Be aware of performance implications.

### 4. Prefer Lazy Loading

Use `lazy=True` (default) unless you know you'll always need the relationship. Use eager loading with `fetch` when needed.

### 5. Document Relationships

```python
@node("Person")
class Person:
    id: Optional[int] = None
    name: str
    
    # Friends that this person knows
    friends: List["Person"] = relationship(type="KNOWS", direction="OUTGOING")
    
    # Friends who know this person
    followers: List["Person"] = relationship(type="KNOWS", direction="INCOMING")
```

---

## See Also

- [Repository API](repository.md)
- [Query Methods](query_methods.md)
- [Relationships Guide](relationships.md)
- [Custom Queries](custom_queries.md)
