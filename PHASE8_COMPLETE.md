# Phase 8: Index Management - Complete

**Status:** ✅ Complete  
**Version:** 1.1.0  
**Date:** November 29, 2025

## Overview

Phase 8 adds comprehensive index management capabilities to the FalkorDB ORM, including declarative index definitions, programmatic index operations, and schema validation.

## Features Implemented

### 1. Declarative Index Decorators

```python
from falkordb_orm import node, indexed, unique, generated_id

@node("User")
class User:
    id: Optional[int] = generated_id()
    email: str = unique(required=True)       # Unique constraint
    username: str = unique()                  # Unique constraint
    age: int = indexed()                      # Regular index
    bio: str = indexed(index_type="FULLTEXT") # Full-text search
    embedding: list = indexed(index_type="VECTOR")  # Vector search
```

**Supported Index Types:**
- `RANGE` (default) - Standard B-tree index
- `FULLTEXT` - Full-text search index
- `VECTOR` - Vector similarity search index

### 2. IndexManager

Programmatic index management:

```python
from falkordb_orm import IndexManager

# Create manager
manager = IndexManager(graph)

# Create all indexes for entity
queries = manager.create_indexes(User, if_not_exists=True)

# Drop indexes
manager.drop_indexes(User)

# Ensure indexes exist (idempotent)
manager.ensure_indexes(User)

# List existing indexes
indexes = manager.list_indexes(User)
for idx in indexes:
    print(f"{idx.label}.{idx.property_name} ({idx.index_type})")

# Create specific index
manager.create_index_for_property("User", "last_name")
manager.create_index_for_property("User", "ssn", unique=True)

# Drop specific index
manager.drop_index_for_property("User", "temp_field")
```

### 3. SchemaManager

Schema validation and synchronization:

```python
from falkordb_orm import SchemaManager

# Create manager
schema_manager = SchemaManager(graph)

# Validate schema
result = schema_manager.validate_schema([User, Product, Order])

if not result.is_valid:
    print(f"Missing indexes: {len(result.missing_indexes)}")
    for idx in result.missing_indexes:
        print(f"  - {idx.label}.{idx.property_name}")
    
    print(f"Extra indexes: {len(result.extra_indexes)}")
    for idx in result.extra_indexes:
        print(f"  - {idx.label}.{idx.property_name}")

# Synchronize schema (create missing indexes)
queries = schema_manager.sync_schema([User, Product])
print(f"Created {len(queries)} indexes")

# Ensure schema is correct (validate + sync)
result = schema_manager.ensure_schema([User, Product])

# Get schema differences
missing, extra = schema_manager.get_schema_diff([User])

# Get schema information
info = schema_manager.get_schema_info([User, Product])
```

## API Reference

### @indexed Decorator

```python
def indexed(
    index_type: str = "RANGE",
    required: bool = False
) -> PropertyDescriptor:
    """
    Mark a property as indexed.
    
    Args:
        index_type: Type of index ("RANGE", "FULLTEXT", "VECTOR")
        required: Whether the field is required
    
    Returns:
        PropertyDescriptor with index metadata
    """
```

### @unique Decorator

```python
def unique(
    required: bool = False
) -> PropertyDescriptor:
    """
    Mark a property with unique constraint.
    
    Args:
        required: Whether the field is required
    
    Returns:
        PropertyDescriptor with unique constraint metadata
    """
```

### IndexManager Methods

| Method | Description |
|--------|-------------|
| `create_indexes(entity_class, if_not_exists=False)` | Create all indexes for entity |
| `drop_indexes(entity_class)` | Drop all indexes for entity |
| `ensure_indexes(entity_class)` | Create indexes if they don't exist |
| `list_indexes(entity_class)` | List existing indexes |
| `create_index_for_property(label, property, unique=False)` | Create specific index |
| `drop_index_for_property(label, property)` | Drop specific index |

### SchemaManager Methods

| Method | Description |
|--------|-------------|
| `validate_schema(entity_classes)` | Validate schema against entities |
| `sync_schema(entity_classes)` | Synchronize schema (create missing) |
| `ensure_schema(entity_classes)` | Validate and sync in one operation |
| `get_schema_diff(entity_classes)` | Get missing and extra indexes |
| `get_schema_info(entity_classes)` | Get current schema information |

## Usage Examples

### Example 1: Basic Index Declaration

```python
@node("Product")
class Product:
    id: Optional[int] = generated_id()
    sku: str = unique(required=True)
    name: str = indexed()
    description: str = indexed(index_type="FULLTEXT")
    price: float = property()
    
# Indexes created automatically or via manager
manager = IndexManager(graph)
manager.create_indexes(Product, if_not_exists=True)
```

### Example 2: Schema Validation

```python
# Define entities
entities = [User, Product, Order, Category]

# Validate schema
schema_manager = SchemaManager(graph)
result = schema_manager.validate_schema(entities)

if not result.is_valid:
    # Automatically fix schema
    schema_manager.sync_schema(entities)
```

### Example 3: Manual Index Management

```python
manager = IndexManager(graph)

# Create indexes for specific properties
manager.create_index_for_property("Customer", "email", unique=True)
manager.create_index_for_property("Customer", "city")
manager.create_index_for_property("Product", "tags", index_type="FULLTEXT")

# List all indexes
indexes = manager.list_indexes(Customer)
for idx in indexes:
    print(f"{idx.property_name}: {idx.index_type}, unique={idx.is_unique}")
```

### Example 4: Application Startup

```python
def initialize_app(graph):
    """Initialize application with schema validation."""
    # Define all entity classes
    entities = [User, Product, Order, Customer, Review]
    
    # Ensure schema is correct
    schema_manager = SchemaManager(graph)
    result = schema_manager.ensure_schema(entities)
    
    if not result.is_valid:
        print("WARNING: Schema was out of sync, indexes created")
    else:
        print("Schema validation passed")
```

## Performance Considerations

### Index Creation Time

- **Range indexes**: Fast (milliseconds)
- **Fulltext indexes**: Moderate (seconds for large datasets)
- **Vector indexes**: Slow (minutes for large datasets)
- **Recommendation**: Create indexes during deployment, not at runtime

### Query Performance

**Without Indexes:**
```cypher
MATCH (u:User) WHERE u.email = 'alice@example.com' RETURN u
// O(n) - Full table scan
```

**With Unique Index:**
```cypher
MATCH (u:User) WHERE u.email = 'alice@example.com' RETURN u
// O(log n) - Index lookup
```

**Improvement:** 10x-100x faster for queries on indexed properties

### Best Practices

1. **Index selective properties**: Properties used in WHERE clauses
2. **Unique constraints for identifiers**: Email, username, SKU
3. **Avoid over-indexing**: Each index costs write performance
4. **Use fulltext for search**: Better than LIKE queries
5. **Batch index creation**: Create all indexes at once during deployment

## Integration with ORM

### Automatic Index Creation

```python
# Option 1: Explicit creation
manager = IndexManager(graph)
manager.create_indexes(User, if_not_exists=True)

# Option 2: Schema synchronization
schema_manager = SchemaManager(graph)
schema_manager.sync_schema([User, Product])
```

### Repository Usage

```python
# Indexes improve these operations:
user_repo = Repository(graph, User)

# Fast lookups (uses unique index on email)
user = user_repo.find_by_email("alice@example.com")

# Fast range queries (uses index on age)
adults = user_repo.find_by_age_greater_than(18)

# Fast fulltext search (uses fulltext index)
results = user_repo.graph.query(
    "MATCH (u:User) WHERE u.bio =~ $pattern RETURN u",
    {"pattern": ".*engineer.*"}
)
```

## Migration Guide

### Adding Indexes to Existing Entities

```python
# 1. Add index decorators to entity
@node("User")
class User:
    email: str = unique()  # NEW
    age: int = indexed()   # NEW
    
# 2. Create indexes
manager = IndexManager(graph)
manager.create_indexes(User, if_not_exists=True)

# 3. Verify
indexes = manager.list_indexes(User)
print(f"Created {len(indexes)} indexes")
```

### Removing Indexes

```python
# 1. Remove decorator from entity
@node("User")
class User:
    temp_field: str = property()  # No longer indexed
    
# 2. Drop index manually
manager = IndexManager(graph)
manager.drop_index_for_property("User", "temp_field")
```

## Limitations

1. **No automatic migrations**: Indexes not created/dropped automatically
2. **No composite indexes**: Only single-property indexes supported
3. **No index options**: Cannot configure index parameters (e.g., case sensitivity)
4. **Manual synchronization**: Must explicitly call `sync_schema()` or `create_indexes()`

## Testing

Tests provided in:
- `tests/test_indexes.py` - Unit tests for IndexManager (15 test cases)
- `tests/test_schema.py` - Unit tests for SchemaManager (12 test cases)
- `tests/integration/test_full_workflow.py` - Integration tests

Run tests:
```bash
python3 -m pytest tests/test_indexes.py -v
python3 -m pytest tests/test_schema.py -v
python3 -m pytest tests/integration/ -v
```

## Examples

Complete examples in:
- `examples/indexes_example.py` - 9 comprehensive scenarios

Run example:
```bash
python3 examples/indexes_example.py
```

## Future Enhancements

Potential future improvements:
- Composite indexes (multiple properties)
- Index statistics and monitoring
- Automatic index recommendations
- Index rebuild/optimization commands
- Conditional indexes (partial indexes)

## Conclusion

Phase 8 provides production-ready index management with:
- ✅ Declarative index definitions
- ✅ Programmatic index operations
- ✅ Schema validation and synchronization
- ✅ Support for RANGE, FULLTEXT, and VECTOR indexes
- ✅ Comprehensive testing and examples

For more examples, see `examples/indexes_example.py`.
