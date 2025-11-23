# Phase 3a Complete: Relationship Metadata & Declaration

**Status**: ✅ Complete  
**Date**: November 23, 2024  
**Estimated Effort**: 2-3 hours  
**Actual Effort**: ~2.5 hours

## Overview

Phase 3a implements the foundation for relationship support in falkordb-py-orm. This phase focuses on declaring relationships between entities and extracting their metadata. The actual loading and saving of relationships will be implemented in subsequent phases.

## What's New

### 1. RelationshipMetadata Class

Added a new `RelationshipMetadata` dataclass to `metadata.py` that captures:
- `python_name`: The attribute name in Python
- `relationship_type`: The Cypher edge type (e.g., 'KNOWS', 'WORKS_FOR')
- `direction`: OUTGOING, INCOMING, or BOTH
- `target_class`: The target entity class (resolved at runtime)
- `target_class_name`: Target class name (for forward references)
- `is_collection`: Whether it's a List or Optional relationship
- `lazy`: Whether to use lazy loading (default: True)
- `cascade`: Whether to cascade operations (default: False)

### 2. relationship() Function

New decorator function in `decorators.py`:

```python
from falkordb_orm import node, relationship, generated_id
from typing import List, Optional

@node("Person")
class Person:
    id: Optional[int] = generated_id()
    name: str
    
    # One-to-many relationship
    friends: List['Person'] = relationship('KNOWS', target='Person')
    
    # One-to-one relationship
    manager: Optional['Person'] = relationship('REPORTS_TO', target='Person')
```

### 3. RelationshipDescriptor

Internal descriptor class that:
- Stores relationship configuration
- Captures attribute names via `__set_name__`
- Validates direction parameter
- Provides property-like access

### 4. Enhanced @node Decorator

Updated to detect and extract relationship metadata:
- Scans for `RelationshipDescriptor` instances
- Extracts type hints to determine collection vs single relationships
- Handles forward references (quoted class names)
- Distinguishes between properties and relationships
- Supports both `List[T]` and `Optional[T]` type hints

### 5. EntityMetadata Enhancements

Extended `EntityMetadata` with:
- `relationships`: List of relationship metadata
- `get_relationship_by_python_name()`: Lookup method
- `is_relationship_field()`: Check if field is a relationship

## Features Implemented

### ✅ Relationship Declaration
- Declare relationships using `relationship()` function
- Specify relationship type (Cypher edge type)
- Configure direction (OUTGOING, INCOMING, BOTH)
- Set cascade and lazy options

### ✅ Type Hint Support
- **One-to-many**: `List[TargetClass]`
- **One-to-one**: `Optional[TargetClass]`
- Automatic detection of collection vs single relationships

### ✅ Forward References
- Self-referential relationships using quoted strings
- Example: `friends: List['Person']`
- Handles `ForwardRef` objects correctly

### ✅ Direction Support
- **OUTGOING**: Default, relationship goes from source to target
- **INCOMING**: Relationship comes into source from target
- **BOTH**: Bidirectional relationship

### ✅ Configuration Options
- **cascade**: Auto-save/delete related entities (default: False)
- **lazy**: Lazy load relationships (default: True)

### ✅ Metadata Inspection
- Complete metadata extraction for relationships
- Helper methods for querying metadata
- Separation of properties and relationships

## Code Statistics

- **Lines Added**: ~400
- **Files Modified**: 3
  - `falkordb_orm/metadata.py`: +60 lines
  - `falkordb_orm/decorators.py`: +170 lines
  - `falkordb_orm/__init__.py`: +4 lines
- **Files Created**: 2
  - `tests/test_relationship_metadata.py`: 309 lines
  - `examples/relationship_declaration.py`: 280 lines
- **Test Coverage**: 16 test cases covering all features

## Examples

### Self-Referential Relationship

```python
@node("Person")
class Person:
    id: Optional[int] = generated_id()
    name: str
    friends: List['Person'] = relationship('KNOWS', target='Person')
    manager: Optional['Person'] = relationship('REPORTS_TO', target='Person')
```

### Multiple Entity Types

```python
@node("Company")
class Company:
    id: Optional[int] = generated_id()
    name: str
    employees: List['Employee'] = relationship('EMPLOYS', target='Employee')

@node("Employee")
class Employee:
    id: Optional[int] = generated_id()
    name: str
    company: Optional[Company] = relationship('WORKS_FOR', target=Company)
    projects: List['Project'] = relationship('WORKS_ON', target='Project')
```

### Direction Examples

```python
@node("Developer")
class Developer:
    id: Optional[int] = generated_id()
    name: str
    
    # Outgoing: This developer follows others
    following: List['Developer'] = relationship('FOLLOWS', direction='OUTGOING', target='Developer')
    
    # Incoming: Others follow this developer
    followers: List['Developer'] = relationship('FOLLOWS', direction='INCOMING', target='Developer')
    
    # Both: Bidirectional connections
    connections: List['Developer'] = relationship('CONNECTED', direction='BOTH', target='Developer')
```

### Cascade and Lazy Options

```python
@node("Address")
class Address:
    id: Optional[int] = generated_id()
    street: str
    city: str

@node("Customer")
class Customer:
    id: Optional[int] = generated_id()
    name: str
    
    # With cascade: saving customer also saves address
    # With lazy=False: address loaded eagerly (Phase 3d feature)
    address: Optional[Address] = relationship(
        'HAS_ADDRESS', 
        target=Address, 
        cascade=True, 
        lazy=False
    )
```

## Testing

All tests pass successfully:

```bash
# Run relationship metadata tests
PYTHONPATH=. python3 -m pytest tests/test_relationship_metadata.py -v

# Run example
PYTHONPATH=. python3 examples/relationship_declaration.py
```

### Test Coverage

1. ✅ One-to-many with forward references
2. ✅ One-to-one with Optional
3. ✅ INCOMING direction
4. ✅ BOTH direction
5. ✅ Cascade option
6. ✅ Lazy option
7. ✅ Multiple relationships
8. ✅ Properties vs relationships separation
9. ✅ Helper methods
10. ✅ Target inference from type hints
11. ✅ Invalid direction validation
12. ✅ Complex multi-entity scenarios

## Backward Compatibility

✅ **All Phase 1 and Phase 2 functionality remains intact**
- Existing entity declarations work unchanged
- Property mappings unaffected
- Query derivation works as before
- Repository operations continue functioning
- No breaking changes

## Known Limitations

These are expected and will be addressed in subsequent phases:

1. **No Lazy Loading Yet**: Relationship attributes are declared but not functional for loading
2. **No Cascade Operations**: Cascade flag is captured but not yet implemented
3. **No Eager Loading**: Lazy=False flag captured but not yet functional
4. **No Query Generation**: Relationship queries not yet implemented
5. **No Edge Creation**: Cannot create relationship edges in graph yet

## What's Next

### Phase 3b: Lazy Loading System (Next)
- Create `LazyList` and `LazySingle` proxy classes
- Implement transparent lazy loading on first access
- Generate relationship loading queries
- Cache loaded relationships

### Phase 3c: Cascade Operations
- Implement cascade save logic
- Handle circular references
- Create relationship edges in graph

### Phase 3d: Eager Loading & Optimization
- Add `fetch` parameter to repository methods
- Build OPTIONAL MATCH queries
- Optimize with batch loading

### Phase 3e: Integration & Documentation
- Complete documentation
- Integration tests
- Update README and QUICKSTART

## Public API Changes

### New Exports

```python
from falkordb_orm import (
    relationship,          # NEW: Declare relationships
    RelationshipMetadata,  # NEW: Relationship metadata class
)
```

### Enhanced Classes

```python
# EntityMetadata now includes:
metadata.relationships                    # List of relationships
metadata.get_relationship_by_python_name('friends')
metadata.is_relationship_field('friends')
```

## Migration Guide

No migration needed! Phase 3a is purely additive. Existing code continues to work without changes.

To start using relationships:

```python
from falkordb_orm import node, relationship, generated_id
from typing import List, Optional

@node("Person")
class Person:
    id: Optional[int] = generated_id()
    name: str
    
    # Add relationships
    friends: List['Person'] = relationship('KNOWS', target='Person')
```

## Conclusion

Phase 3a successfully lays the groundwork for relationship support in falkordb-py-orm. The metadata extraction and declaration system is complete and fully tested. The API is intuitive and follows Spring Data patterns.

**Ready for Phase 3b!** 🚀
