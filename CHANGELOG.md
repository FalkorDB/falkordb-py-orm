# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.1] - 2025-11-29

### Fixed
- **Critical**: Fixed generated ID detection in query builder - entities with `generated_id()` now correctly use FalkorDB's internal `id()` function instead of property-based matching
- **Critical**: Fixed entity ID mapping in mapper - retrieved entities now have their IDs properly set from the internal node ID
- **Enhancement**: Implemented forward reference resolution for relationships - self-referential relationships (e.g., `Person` → `Person`) now work correctly
- All relationship loading operations (lazy and eager) now function as expected

### Technical Details
- Changed ID type detection from `id_generator is not None` to `hasattr(property, 'id_generator')` to properly identify generated ID fields
- Added registry-based forward reference resolution in `_initialize_lazy_relationships()`
- Fixes apply to `query_builder.py` (3 locations) and `mapper.py` (2 locations)

## [1.1.0] - 2025-11-29

### 🎉 Major Release - Advanced Features

This release adds transaction support, index management, pagination, and relationship update functionality, bringing the ORM to ~90% feature completion.

### Added - Phase 7: Transaction Support
- **Session Management**: `Session` class with identity map and change tracking
  - Identity map prevents duplicate entity loads within session
  - Automatic change tracking with dirty checking
  - Context manager support with auto-commit on success
  - Automatic rollback on exceptions
- **Session Methods**: `add()`, `delete()`, `get()`, `flush()`, `commit()`, `rollback()`, `close()`
- **Session Properties**: `is_active` and `has_pending_changes`
- **Async Support**: `AsyncSession` with full async/await support
- **Tests**: 608 lines, 40+ comprehensive test cases
- **Examples**: `examples/transaction_example.py` with 9 scenarios
- **Documentation**: Complete transaction guide in `PHASE7_COMPLETE.md`

### Added - Phase 8: Index Management
- **Declarative Indexes**: `@indexed` decorator for property-level indexes
- **Unique Constraints**: `@unique` decorator for unique constraints
- **Index Types**: Support for RANGE, FULLTEXT, and VECTOR indexes
- **IndexManager**: Programmatic index creation, deletion, and listing
  - `create_indexes()`, `drop_indexes()`, `ensure_indexes()`
  - `list_indexes()`, `create_index_for_property()`, `drop_index_for_property()`
- **SchemaManager**: Schema validation and synchronization
  - `validate_schema()`, `sync_schema()`, `ensure_schema()`
  - `get_schema_diff()`, `get_schema_info()`
- **Data Classes**: `IndexInfo` and `SchemaValidationResult`
- **Tests**: 27 test cases (454 lines) in `test_indexes.py` and `test_schema.py`
- **Examples**: `examples/indexes_example.py` with 9 comprehensive scenarios
- **Documentation**: Complete index guide in `PHASE8_COMPLETE.md`

### Added - Phase 9: Pagination
- **Pageable Class**: Pagination parameters with sorting support
  - Page number (0-indexed), page size, sort_by, direction
  - Navigation methods: `next()`, `previous()`, `first()`
- **Page Class**: Generic `Page[T]` with content and metadata
  - Total elements, total pages, navigation helpers
  - `has_next()`, `has_previous()`, `is_first()`, `is_last()`
- **Repository Integration**: `find_all_paginated(pageable: Pageable)` method
- **Query Builder**: Pagination query support with SKIP/LIMIT
- **Tests**: 364 lines, 30+ test cases in `test_pagination.py`
- **Documentation**: Complete pagination guide in `PHASE9_COMPLETE.md`

### Added - Relationship Updates (New Feature)
- **Automatic Edge Deletion**: Old relationship edges deleted when relationships updated
- **Query Builder**: `build_relationship_delete_query()` method
- **RelationshipManager**: Enhanced with `is_update` flag and edge deletion
- **Examples**: `examples/relationship_updates_example.py` with 9 scenarios
- **Tests**: Updated `test_relationship_updates.py` with verification tests

### Added - Integration Testing
- **Integration Test Suite**: `tests/integration/test_full_workflow.py` (507 lines)
  - End-to-end tests with real FalkorDB instance
  - Tests for CRUD, relationships, transactions, pagination, indexes
  - Complex workflow scenarios (social network, company-employees)
  - 50+ integration test cases

### Changed
- **Repository**: Enhanced `save()` to pass `is_update` flag for relationship tracking
- **RelationshipManager**: Now deletes old edges before creating new ones on updates
- **Query Builder**: Extended with pagination and relationship deletion support

### Fixed
- **Relationship Updates**: Old edges now properly deleted when relationships change
- **Cascade Save**: Verified working correctly with integration tests

### Documentation
- **PHASE7_COMPLETE.md**: Transaction support guide (623 lines)
- **PHASE8_COMPLETE.md**: Index management guide (375 lines)
- **PHASE9_COMPLETE.md**: Pagination guide (183 lines)
- **PHASE8_TESTS_AND_REL_UPDATES_COMPLETE.md**: Implementation summary
- **IMPLEMENTATION_REVIEW_NOV_29_2025.md**: Comprehensive status review
- **README.md**: Updated with v1.1.0 features and examples

### Statistics
- **Code Added**: ~5,000 lines of production code
- **Tests Added**: ~1,500 lines of test code
- **Documentation**: ~1,500 lines of guides
- **Total**: ~8,000 lines across all files
- **Completion**: ~90% feature complete

## [1.0.1] - 2024-11-29

### Fixed
- Enhanced query result record mapping to support both list-based and dict-based formats
- Added header-based column resolution for accurate variable name mapping in query results
- Improved backward compatibility with fallback to first column when header unavailable
- Fixed potential column mismatch issues in `map_from_record()` and `map_with_relationships()`

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
