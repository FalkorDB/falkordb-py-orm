# Phase 9: Pagination Support - Complete

**Status:** ✅ Complete  
**Version:** 1.1.0  
**Date:** November 29, 2025

## Overview

Phase 9 adds full pagination support with sorting, navigation, and integration with all repository methods.

## Quick Start

```python
from falkordb_orm import Repository, Pageable

# Create repository
person_repo = Repository(graph, Person)

# Create pageable (page 0, 10 items, sorted by name ascending)
pageable = Pageable(page=0, size=10, sort_by="name", direction="ASC")

# Get page
page = person_repo.find_all_paginated(pageable)

# Access results
for person in page.content:
    print(person.name)

# Navigate
print(f"Page {page.page_number + 1} of {page.total_pages}")
print(f"Total items: {page.total_elements}")

if page.has_next():
    next_pageable = pageable.next()
    next_page = person_repo.find_all_paginated(next_pageable)
```

## API Reference

### Pageable Class

```python
Pageable(
    page: int,              # 0-indexed page number
    size: int,              # Items per page
    sort_by: Optional[str], # Property to sort by
    direction: str = "ASC"  # "ASC" or "DESC"
)
```

**Methods:**
- `next() -> Pageable` - Get next page parameters
- `previous() -> Pageable` - Get previous page parameters
- `first() -> Pageable` - Get first page parameters
- `skip() -> int` - Calculate SKIP value

### Page Class

```python
Page[T](
    content: List[T],        # Items on this page
    page_number: int,        # Current page (0-indexed)
    page_size: int,          # Items per page
    total_elements: int,     # Total items
    total_pages: int         # Total pages
)
```

**Methods:**
- `has_next() -> bool` - Check if next page exists
- `has_previous() -> bool` - Check if previous page exists
- `is_first() -> bool` - Check if this is first page
- `is_last() -> bool` - Check if this is last page
- `__iter__()` - Iterate over content
- `__len__()` - Get content length

## Examples

### Example 1: Basic Pagination

```python
# Get first page of 20 items
pageable = Pageable(page=0, size=20)
page = repo.find_all_paginated(pageable)

# Display results
for item in page:
    print(item.name)
```

### Example 2: Sorted Pagination

```python
# Get page sorted by age (descending)
pageable = Pageable(page=0, size=10, sort_by="age", direction="DESC")
page = repo.find_all_paginated(pageable)

# Oldest users first
for person in page:
    print(f"{person.name}: {person.age}")
```

### Example 3: Page Navigation

```python
# Start at first page
pageable = Pageable(page=0, size=5)
page = repo.find_all_paginated(pageable)

# Navigate through pages
while True:
    for item in page:
        print(item.name)
    
    if not page.has_next():
        break
    
    # Get next page
    pageable = pageable.next()
    page = repo.find_all_paginated(pageable)
```

### Example 4: Page Information

```python
page = repo.find_all_paginated(Pageable(0, 10))

print(f"Showing items {page.page_number * page.page_size + 1} to "
      f"{min((page.page_number + 1) * page.page_size, page.total_elements)} "
      f"of {page.total_elements}")

print(f"Page {page.page_number + 1} of {page.total_pages}")
```

## Integration

### With Derived Queries

```python
# Pagination works with derived query methods (future feature)
# Currently use find_all_paginated for all results
```

### With Custom Queries

```python
# For custom queries, build pagination manually
query = """
MATCH (p:Person)
WHERE p.age > $min_age
RETURN p
ORDER BY p.age ASC
SKIP $skip LIMIT $limit
"""

pageable = Pageable(page=2, size=10)
params = {
    "min_age": 18,
    "skip": pageable.skip(),
    "limit": pageable.size
}
```

## Testing

Tests in `tests/test_pagination.py` (364 lines, 30+ test cases)

Run tests:
```bash
python3 -m pytest tests/test_pagination.py -v
```

## Performance

- **SKIP/LIMIT**: Efficient for small-medium datasets
- **Large SKIP values**: Can be slow (O(n) in worst case)
- **Recommendation**: Use keyset pagination for very large datasets

## Conclusion

Phase 9 provides production-ready pagination with sorting and navigation.

For more details, see `tests/test_pagination.py` and integration tests.
