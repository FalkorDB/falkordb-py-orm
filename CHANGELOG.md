# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-11-23

### Initial Release 🎉

First production-ready release of FalkorDB Python ORM with comprehensive features for object-graph mapping.

#### Core Features
- **Entity Mapping**: `@node` decorator for defining entities with full type safety
- **Repository Pattern**: Generic `Repository[T]` with type-safe CRUD operations
- **Query Derivation**: Automatic query generation from method names (e.g., `find_by_name_and_age_greater_than()`)
- **Relationships**: Lazy/eager loading, cascade operations, bidirectional support
- **Custom Queries**: `@query` decorator for custom Cypher with parameter binding
- **Async Support**: Full async/await with `AsyncRepository` for modern Python applications
- **Type System**: Built-in converters for common Python types with extensibility

#### Polish & Documentation
- Complete API reference documentation for all decorators and methods
- Migration guide from raw FalkorDB client to ORM
- CI/CD workflows (GitHub Actions) for testing, linting, and publishing
- Enhanced exception handling with contextual error messages
- Comprehensive examples for all features
- Memory optimization with interned string support (`@interned` decorator)

#### Breaking Changes
- Python 3.8 is no longer supported (EOL October 2024). Minimum version is now Python 3.9

## [0.1.0-alpha] - 2024-11-23

### Phase 5 - Async Support
#### Added
- `AsyncRepository` class with full async/await support
- `AsyncMapper` for async entity mapping
- `AsyncLazyList` and `AsyncLazySingle` for async relationship loading
- Async derived query methods
- Support for concurrent operations with `asyncio.gather()`
- Async aggregation methods (sum, avg, min, max)
- Comprehensive async examples and documentation

#### Documentation
- PHASE5_COMPLETE.md with detailed async usage guide
- Async usage examples in README
- Migration guide for converting sync to async code

### Phase 4 - Advanced Features
#### Added
- `@query` decorator for custom Cypher queries
- Parameter binding support for custom queries
- Aggregation methods: `sum()`, `avg()`, `min()`, `max()`
- Support for complex Cypher patterns (WITH clauses, CTEs)
- Automatic result mapping for custom queries
- Type-safe custom query results

#### Documentation
- PHASE4_COMPLETE.md with custom query examples
- Advanced query patterns documentation
- Aggregation usage examples

### Phase 3 - Relationships
#### Added
- `relationship()` function for declaring entity relationships
- `RelationshipMetadata` for storing relationship configuration
- Lazy loading system with `LazyList` and `LazySingle` proxies
- Eager loading with `fetch` parameter
- Cascade save operations for related entities
- Bidirectional relationship support
- Circular reference handling
- `RelationshipManager` for relationship persistence

#### Documentation
- PHASE3_COMPLETE.md comprehensive guide
- PHASE3_BREAKDOWN.md detailed implementation plan
- PHASE3_QUICK_GUIDE.md for quick reference
- Phase-specific completion docs (3A, 3B, 3CD)

#### Examples
- relationship_declaration.py
- lazy_loading_example.py
- cascade_save_example.py
- relationships_complete.py

### Phase 2 - Query Derivation
#### Added
- Automatic query method generation from method names
- `QueryParser` for parsing method names into query specifications
- `QueryBuilder` for generating Cypher queries
- Support for 14 comparison operators:
  - equals, not, greater_than, greater_than_or_equal
  - less_than, less_than_or_equal, between
  - in, not_in, containing, starting_with, ending_with
- Logical operators: AND, OR
- Query actions: find_by, find_first_by, count_by, exists_by, delete_by
- ORDER BY support for single and multiple fields
- LIMIT support with top_N and first
- Query specification caching for performance

#### Documentation
- PHASE2_COMPLETE.md with comprehensive examples
- Query method patterns documentation

#### Examples
- derived_queries.py demonstrating all query patterns

### Phase 1 - Foundation
#### Added
- Core `@node` decorator for entity definition
- `property()` function for custom property mapping
- `EntityMetadata` and `PropertyMetadata` for storing entity configuration
- `EntityMapper` for converting between entities and graph nodes
- `Repository` class with basic CRUD operations:
  - `save()` - create/update entities
  - `find_by_id()` - retrieve by ID
  - `find_all()` - retrieve all entities
  - `delete()`, `delete_by_id()` - remove entities
  - `count()` - count entities
  - `exists()` - check existence
- Type conversion system for common Python types
- Multiple node label support
- ID generation and management
- Generic repository with type safety

#### Documentation
- PHASE1_COMPLETE.md implementation summary
- DESIGN.md comprehensive design document
- QUICKSTART.md getting started guide
- README.md with project overview

#### Examples
- basic_usage.py demonstrating core CRUD operations

## Project Structure

```
falkordb-py-orm/
├── falkordb_orm/           # Core ORM package
│   ├── __init__.py
│   ├── decorators.py       # @node, property(), relationship()
│   ├── metadata.py         # Entity and relationship metadata
│   ├── mapper.py           # Entity ↔ Node mapping
│   ├── async_mapper.py     # Async entity mapping
│   ├── repository.py       # Sync repository implementation
│   ├── async_repository.py # Async repository implementation
│   ├── query_parser.py     # Method name → QuerySpec
│   ├── query_builder.py    # QuerySpec → Cypher
│   ├── query_decorator.py  # @query decorator
│   ├── relationships.py    # Relationship management
│   ├── async_relationships.py  # Async relationship loading
│   ├── types.py           # Type converters
│   └── exceptions.py      # Custom exceptions
├── tests/                 # Test suite
├── examples/              # Usage examples
├── docs/                  # Documentation
│   ├── api/              # API reference
│   └── MIGRATION_GUIDE.md
├── DESIGN.md
├── QUICKSTART.md
├── README.md
└── pyproject.toml
```

## Compatibility

- Python: 3.9+ (3.8 reached EOL in October 2024)
- FalkorDB: 1.0.0+
- Redis (for FalkorDB): 6.0+

## Contributors

- FalkorDB Team

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

For migration guides, see [MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md)

For API documentation, see [docs/api/](docs/api/)

For examples, see [examples/](examples/)
