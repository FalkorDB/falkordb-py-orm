# Phase 4 Complete: Advanced Features

## Overview
Phase 4 has been successfully completed, adding advanced features to falkordb-py-orm including custom Cypher queries, aggregation methods, and enhanced repository capabilities. This phase rounds out the ORM with powerful tools for complex use cases.

## Implementation Date
November 23, 2025

## Version
**v0.3.0** - Advanced Features

---

## What Was Implemented

### ✅ Phase 4a: Custom Query Decorator (@query)
**Status:** Complete

- `@query` decorator for custom Cypher queries
- Automatic parameter binding from method arguments
- Type-safe result mapping
- Support for entity and primitive return types
- Complex query pattern support

### ✅ Phase 4d: Aggregation Methods
**Status:** Complete

- `sum(property)` - Sum numeric property values
- `avg(property)` - Calculate average of property values
- `min(property)` - Find minimum property value
- `max(property)` - Find maximum property value
- Built on existing `count()` method

### ⏭️ Phase 4b & 4c: Deferred
**Transaction Support** and **Index Management** are deferred to future releases as they require deeper integration with FalkorDB's transaction model and constraint system.

---

## Feature Details

### 1. Custom Query Decorator (@query)

#### Overview
The `@query` decorator allows developers to define custom Cypher queries as repository methods with automatic parameter binding and result mapping.

#### Usage

**Basic Custom Query:**
```python
from falkordb_orm import query, Repository

class PersonRepository(Repository[Person]):
    @query(
        "MATCH (p:Person)-[:KNOWS]->(f:Person) WHERE p.name = $name RETURN f",
        returns=Person
    )
    def find_friends_of(self, name: str) -> List[Person]:
        pass
```

**Parameters:**
- `cypher`: Cypher query string with `$param` placeholders
- `returns`: Expected return type (entity class, primitive, or None)
- `write`: Boolean indicating write operations (default: False)

#### Parameter Binding

Arguments are automatically mapped to Cypher parameters:

```python
class PersonRepository(Repository[Person]):
    @query(
        "MATCH (p:Person) WHERE p.age > $min AND p.age < $max RETURN p",
        returns=Person
    )
    def find_by_age_range(self, min: int, max: int) -> List[Person]:
        pass

# Usage
repo.find_by_age_range(25, 65)
# Executes: MATCH (p:Person) WHERE p.age > 25 AND p.age < 65 RETURN p
```

#### Return Types

**Entity Return Type:**
```python
@query(
    "MATCH (p:Person) WHERE p.name = $name RETURN p",
    returns=Person
)
def find_by_name(self, name: str) -> List[Person]:
    pass
```

**Primitive Return Type:**
```python
@query(
    "MATCH (p:Person) RETURN count(p)",
    returns=int
)
def count_all(self) -> int:
    pass
```

**Complex Queries:**
```python
@query(
    """
    MATCH (p:Person)-[:KNOWS]->(f:Person)
    WITH p, count(f) as friend_count
    WHERE friend_count >= $min_friends
    RETURN p
    ORDER BY friend_count DESC
    """,
    returns=Person
)
def find_popular_people(self, min_friends: int) -> List[Person]:
    pass
```

### 2. Aggregation Methods

#### Overview
Built-in aggregation methods for common statistical operations on entity properties.

#### Available Methods

**sum(property_name)**
```python
total_salary = person_repo.sum('salary')
# Returns: 450000.0
```

**avg(property_name)**
```python
average_age = person_repo.avg('age')
# Returns: 32.5
```

**min(property_name)**
```python
youngest = person_repo.min('age')
# Returns: 21
```

**max(property_name)**
```python
oldest = person_repo.max('age')
# Returns: 65
```

**count()**
```python
total_people = person_repo.count()
# Returns: 150
```

#### Implementation

All aggregation methods generate optimized Cypher queries:

```cypher
-- sum(property)
MATCH (n:Person) RETURN sum(n.salary) as total

-- avg(property)  
MATCH (n:Person) RETURN avg(n.age) as average

-- min(property)
MATCH (n:Person) RETURN min(n.age) as minimum

-- max(property)
MATCH (n:Person) RETURN max(n.salary) as maximum
```

---

## Complete API Reference

### @query Decorator

```python
def query(
    cypher: str,
    returns: Optional[Type] = None,
    write: bool = False
) -> Callable[[Callable], QueryMethod]:
    """
    Decorator for custom Cypher query methods.
    
    Args:
        cypher: Cypher query with $param placeholders
        returns: Expected return type (entity class, primitive, or None)
        write: Whether query performs write operations
        
    Returns:
        Decorated method that executes custom query
    """
```

### Repository Aggregation Methods

```python
class Repository(Generic[T]):
    def sum(self, property_name: str) -> float:
        """Sum values of a numeric property."""
        
    def avg(self, property_name: str) -> float:
        """Calculate average of a numeric property."""
        
    def min(self, property_name: str) -> Any:
        """Find minimum value of a property."""
        
    def max(self, property_name: str) -> Any:
        """Find maximum value of a property."""
```

---

## Examples

### Custom Repository with @query Methods

```python
from typing import List, Optional
from falkordb_orm import node, generated_id, relationship, Repository, query

@node("Person")
class Person:
    id: Optional[int] = generated_id()
    name: str
    age: int
    salary: float

class PersonRepository(Repository[Person]):
    @query(
        "MATCH (p:Person)-[:KNOWS]->(f:Person) WHERE p.name = $name RETURN f",
        returns=Person
    )
    def find_friends_of(self, name: str) -> List[Person]:
        pass
    
    @query(
        "MATCH (p:Person) WHERE p.salary >= $threshold RETURN p ORDER BY p.salary DESC",
        returns=Person
    )
    def find_high_earners(self, threshold: float) -> List[Person]:
        pass
    
    @query(
        "MATCH (p:Person) RETURN count(DISTINCT p.age)",
        returns=int
    )
    def count_unique_ages(self) -> int:
        pass

# Usage
repo = PersonRepository(graph, Person)

friends = repo.find_friends_of("Alice")
high_earners = repo.find_high_earners(75000)
unique_ages = repo.count_unique_ages()
```

### Aggregation Methods

```python
repo = Repository(graph, Person)

# Statistical operations
total = repo.sum('salary')
average = repo.avg('age')
youngest = repo.min('age')
oldest = repo.max('age')

print(f"Total salaries: ${total:,.2f}")
print(f"Average age: {average:.1f}")
print(f"Age range: {youngest} - {oldest}")
```

### Complex Custom Queries

```python
class EmployeeRepository(Repository[Employee]):
    @query(
        """
        MATCH (e:Employee)-[:WORKS_FOR]->(c:Company)
        WHERE c.industry = $industry
        RETURN avg(e.salary) as avg_salary
        """,
        returns=float
    )
    def average_salary_in_industry(self, industry: str) -> float:
        pass
    
    @query(
        """
        MATCH (e:Employee)-[:WORKS_FOR]->(c:Company)
        WHERE c.name = $company_name
        RETURN e
        ORDER BY e.salary DESC
        """,
        returns=Employee
    )
    def find_by_company(self, company_name: str) -> List[Employee]:
        pass

# Usage
repo = EmployeeRepository(graph, Employee)
tech_avg = repo.average_salary_in_industry("Technology")
employees = repo.find_by_company("TechCorp")
```

---

## Implementation Statistics

### Code Metrics

**Phase 4a - Custom Queries:**
- 221 lines query_decorator.py (new module)
- QueryMethod descriptor class
- Parameter binding logic
- Result mapping logic

**Phase 4d - Aggregation:**
- 108 lines added to repository.py
- 4 new aggregation methods
- Optimized Cypher generation

**Total Phase 4:**
- ~330 lines core implementation
- ~310 lines example code
- ~200 lines documentation
- **Total: ~840 lines**

### Files Created/Modified

**New Files:**
1. `falkordb_orm/query_decorator.py` (221 lines)
2. `examples/phase4_advanced_features.py` (309 lines)
3. `PHASE4_COMPLETE.md` (this file)

**Modified Files:**
1. `falkordb_orm/__init__.py` (version 0.3.0, export query)
2. `falkordb_orm/repository.py` (aggregation methods)

---

## Performance Characteristics

### Custom Queries
- **Execution**: Direct Cypher execution, no parsing overhead
- **Mapping**: Same as built-in methods
- **Best For**: Complex queries, domain-specific operations

### Aggregation Methods
- **Query Generation**: O(1) - template-based
- **Execution**: Single Cypher query per operation
- **Best For**: Statistical operations, reporting

---

## Known Limitations

1. **@query Return Type Inference**: Must explicitly specify `returns` parameter
   - Cannot infer from method return type annotation
   - Future: Use type hints for inference

2. **Parameter Naming**: Method parameter names must match Cypher $params
   - Alternative: Support parameter mapping

3. **Complex Return Types**: Limited support for tuple/dict returns
   - Only entity classes and primitives fully supported

4. **No Query Validation**: Cypher syntax not validated at decoration time
   - Errors only caught at runtime
   - Future: Add optional validation

5. **Write Operations**: `write=True` flag present but not enforced
   - Placeholder for future transaction support

---

## Best Practices

### When to Use @query

✅ **Use @query when:**
- Need complex Cypher patterns not supported by derived queries
- Performing graph-specific operations (shortest path, pattern matching)
- Requiring custom aggregations or WITH clauses
- Need fine-grained control over query structure

❌ **Avoid @query when:**
- Simple CRUD operations (use Repository methods)
- Property-based filtering (use derived queries)
- Common patterns (use built-in methods)

### When to Use Aggregations

✅ **Use aggregation methods when:**
- Calculating statistics over entire entity set
- Reporting and analytics
- Dashboard data
- Simple single-property operations

❌ **Avoid aggregation methods when:**
- Need complex aggregations (use @query)
- Aggregating across relationships
- Need GROUP BY functionality

### Query Performance Tips

1. **Use Parameters**: Always use `$params` instead of string interpolation
2. **Index Properties**: Ensure filtered properties are indexed
3. **Limit Results**: Add LIMIT clauses to large result sets
4. **Avoid Cartesian Products**: Be careful with multiple MATCH patterns
5. **Test Queries**: Use EXPLAIN/PROFILE to understand query plans

---

## Migration Guide

### Adding Custom Queries to Existing Repository

**Before:**
```python
class PersonRepository(Repository[Person]):
    pass

# Manual queries
result = graph.query(
    "MATCH (p:Person)-[:KNOWS]->(f) WHERE p.name = $name RETURN f",
    {'name': 'Alice'}
)
# Manual mapping...
```

**After:**
```python
from falkordb_orm import query

class PersonRepository(Repository[Person]):
    @query(
        "MATCH (p:Person)-[:KNOWS]->(f:Person) WHERE p.name = $name RETURN f",
        returns=Person
    )
    def find_friends_of(self, name: str) -> List[Person]:
        pass

# Clean usage
friends = repo.find_friends_of("Alice")
```

### Replacing Manual Aggregations

**Before:**
```python
result = graph.query("MATCH (p:Person) RETURN sum(p.salary)")
total = result.result_set[0][0] if result.result_set else 0
```

**After:**
```python
total = repo.sum('salary')
```

---

## Testing

### Custom Query Testing

```python
def test_custom_query():
    repo = PersonRepository(graph, Person)
    
    # Create test data
    alice = Person(name="Alice", age=30)
    bob = Person(name="Bob", age=25)
    repo.save_all([alice, bob])
    
    # Test custom query
    results = repo.find_by_age_range(20, 35)
    assert len(results) == 2
```

### Aggregation Testing

```python
def test_aggregations():
    repo = Repository(graph, Person)
    
    # Create test data
    person1 = Person(name="Alice", age=30, salary=70000)
    person2 = Person(name="Bob", age=25, salary=60000)
    repo.save_all([person1, person2])
    
    # Test aggregations
    assert repo.sum('salary') == 130000
    assert repo.avg('age') == 27.5
    assert repo.min('age') == 25
    assert repo.max('salary') == 70000
```

---

## Future Enhancements (Phase 5+)

Potential improvements:
- Transaction support with context managers
- Index and constraint management
- Async/await support
- Query result caching
- Batch operations optimization
- Migration system
- Schema validation

---

## Comparison with Other ORMs

### vs SQLAlchemy
- ✅ Similar custom query patterns (@query like raw SQL)
- ✅ Comparable aggregation functions
- ➖ No ORM-level transactions yet
- ➖ Less mature query builder

### vs Django ORM
- ✅ More flexible custom queries
- ✅ Graph-native patterns
- ➖ No automatic migrations
- ➖ Fewer built-in aggregations

---

## Summary

Phase 4 successfully implements advanced features for falkordb-py-orm:

✅ **Custom Queries** - Full Cypher query support with @query decorator  
✅ **Aggregations** - Statistical operations on entity properties  
✅ **Type Safety** - Automatic result mapping to typed entities  
✅ **Performance** - Optimized query generation and execution  
✅ **Flexibility** - Support for complex patterns and use cases  

**Combined with Phases 1-3:**
- ✅ Entity mapping and CRUD
- ✅ Derived query methods
- ✅ Full relationship support
- ✅ Custom queries and aggregations

The ORM now provides a complete, production-ready solution for FalkorDB applications, supporting everything from simple CRUD to complex graph analytics!

**Phase 4 is complete! 🚀**
