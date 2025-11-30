"""FalkorDB Python ORM - Object-Graph Mapping for FalkorDB."""

__version__ = "1.2.1"

# Decorators
from .decorators import node, property, generated_id, relationship, interned, indexed, unique
from .query_decorator import query

# Repository
from .repository import Repository
from .async_repository import AsyncRepository

# Exceptions
from .exceptions import (
    FalkorDBORMException,
    EntityNotFoundException,
    InvalidEntityException,
    MappingException,
    QueryException,
    MetadataException,
)

# Types
from .types import TypeConverter, register_converter

# Pagination
from .pagination import Page, Pageable

# Session management
from .session import Session
from .async_session import AsyncSession

# Index and schema management
from .indexes import IndexManager, IndexInfo
from .schema import SchemaManager, SchemaValidationResult

# Metadata (for advanced usage)
from .metadata import EntityMetadata, PropertyMetadata, RelationshipMetadata, get_entity_metadata

# Query parser (for advanced usage)
from .query_parser import (
    QueryParser,
    QuerySpec,
    Condition,
    OrderClause,
    Operation,
    Operator,
    LogicalOperator,
)

__all__ = [
    # Version
    "__version__",
    # Decorators
    "node",
    "property",
    "generated_id",
    "relationship",
    "interned",
    "indexed",
    "unique",
    "query",
    # Repository
    "Repository",
    "AsyncRepository",
    # Exceptions
    "FalkorDBORMException",
    "EntityNotFoundException",
    "InvalidEntityException",
    "MappingException",
    "QueryException",
    "MetadataException",
    # Types
    "TypeConverter",
    "register_converter",
    # Pagination
    "Page",
    "Pageable",
    # Session
    "Session",
    "AsyncSession",
    # Index management
    "IndexManager",
    "IndexInfo",
    "SchemaManager",
    "SchemaValidationResult",
    # Metadata
    "EntityMetadata",
    "PropertyMetadata",
    "RelationshipMetadata",
    "get_entity_metadata",
    # Query parser
    "QueryParser",
    "QuerySpec",
    "Condition",
    "OrderClause",
    "Operation",
    "Operator",
    "LogicalOperator",
]
