"""Metadata structures for entity mapping."""

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    pass  # For forward reference resolution


@dataclass
class PropertyMetadata:
    """Metadata for a single entity property."""

    python_name: str
    """The name of the attribute in Python class."""

    graph_name: str
    """The name of the property in the graph database."""

    python_type: Type
    """The Python type of the property."""

    converter: Optional[Callable] = None
    """Optional type converter for custom conversion."""

    required: bool = False
    """Whether this property is required."""

    is_id: bool = False
    """Whether this property is the ID field."""

    id_generator: Optional[Callable] = None
    """Optional ID generator function for auto-generated IDs."""

    interned: bool = False
    """Whether this string property should use FalkorDB's intern() function for deduplication."""

    indexed: bool = False
    """Whether this property should have an index."""

    unique: bool = False
    """Whether this property should have a unique constraint."""

    index_type: Optional[str] = None
    """Type of index (e.g., 'RANGE', 'FULLTEXT', 'VECTOR'). None means default RANGE index."""


@dataclass
class RelationshipMetadata:
    """Metadata for a relationship between entities."""

    python_name: str
    """The name of the relationship attribute in Python class."""

    relationship_type: str
    """The type of the relationship edge in the graph (e.g., 'KNOWS', 'WORKS_FOR')."""

    direction: str
    """Direction of the relationship: 'OUTGOING', 'INCOMING', or 'BOTH'."""

    target_class: Optional[Type] = None
    """The target entity class (resolved at runtime)."""

    target_class_name: Optional[str] = None
    """The target class name (for forward references)."""

    is_collection: bool = False
    """Whether the relationship is a collection (List) or single (Optional)."""

    lazy: bool = True
    """Whether to use lazy loading for this relationship."""

    cascade: bool = False
    """Whether to cascade save/delete operations to related entities."""


@dataclass
class EntityMetadata:
    """Metadata for an entity class."""

    entity_class: Type
    """The Python class representing the entity."""

    labels: List[str]
    """List of node labels in the graph."""

    primary_label: str
    """The primary label for the node."""

    properties: List[PropertyMetadata] = field(default_factory=list)
    """List of property metadata."""

    id_property: Optional[PropertyMetadata] = None
    """Metadata for the ID property, if present."""

    relationships: List[RelationshipMetadata] = field(default_factory=list)
    """List of relationship metadata."""

    def get_property_by_python_name(self, name: str) -> Optional[PropertyMetadata]:
        """Get property metadata by Python attribute name."""
        for prop in self.properties:
            if prop.python_name == name:
                return prop
        return None

    def get_property_by_graph_name(self, name: str) -> Optional[PropertyMetadata]:
        """Get property metadata by graph property name."""
        for prop in self.properties:
            if prop.graph_name == name:
                return prop
        return None

    def get_relationship_by_python_name(self, name: str) -> Optional[RelationshipMetadata]:
        """Get relationship metadata by Python attribute name."""
        for rel in self.relationships:
            if rel.python_name == name:
                return rel
        return None

    def is_relationship_field(self, name: str) -> bool:
        """Check if a field is a relationship."""
        return any(rel.python_name == name for rel in self.relationships)


def get_entity_metadata(entity_class: Type) -> Optional[EntityMetadata]:
    """
    Extract entity metadata from a decorated class.

    Args:
        entity_class: The entity class to extract metadata from

    Returns:
        EntityMetadata if the class is decorated with @node, None otherwise
    """
    return getattr(entity_class, "__node_metadata__", None)


def has_entity_metadata(entity_class: Type) -> bool:
    """
    Check if a class has entity metadata (is decorated with @node).

    Args:
        entity_class: The class to check

    Returns:
        True if the class has entity metadata, False otherwise
    """
    return hasattr(entity_class, "__node_metadata__")
