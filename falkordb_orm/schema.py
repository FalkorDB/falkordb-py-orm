"""Schema management and validation for FalkorDB entities."""

from typing import Any, Dict, List, Set, Type, Tuple
from dataclasses import dataclass

from .metadata import get_entity_metadata
from .indexes import IndexManager, IndexInfo


@dataclass
class SchemaValidationResult:
    """Result of schema validation."""

    is_valid: bool
    """Whether the schema is valid."""

    missing_indexes: List[Tuple[str, str, str]]
    """List of missing indexes as (label, property, type) tuples."""

    extra_indexes: List[IndexInfo]
    """List of extra indexes not defined in metadata."""

    errors: List[str]
    """List of validation errors."""

    def __str__(self) -> str:
        """String representation of validation result."""
        if self.is_valid:
            return "Schema is valid ✓"

        lines = ["Schema validation failed:"]

        if self.missing_indexes:
            lines.append(f"\nMissing {len(self.missing_indexes)} index(es):")
            for label, prop, idx_type in self.missing_indexes:
                lines.append(f"  - {label}.{prop} ({idx_type})")

        if self.extra_indexes:
            lines.append(f"\nExtra {len(self.extra_indexes)} index(es):")
            for idx in self.extra_indexes:
                lines.append(f"  - {idx.label}.{idx.property_name} ({idx.index_type})")

        if self.errors:
            lines.append("\nErrors:")
            for error in self.errors:
                lines.append(f"  - {error}")

        return "\n".join(lines)


class SchemaManager:
    """
    Manages database schema for FalkorDB entities.

    Provides schema validation, synchronization, and migration capabilities.

    Example:
        >>> from falkordb_orm import SchemaManager
        >>>
        >>> manager = SchemaManager(graph)
        >>>
        >>> # Validate schema against entities
        >>> result = manager.validate_schema([Person, Company])
        >>> print(result)
        >>>
        >>> # Synchronize schema (create missing indexes)
        >>> manager.sync_schema([Person, Company])
        >>>
        >>> # Get schema differences
        >>> diff = manager.get_schema_diff([Person, Company])
    """

    def __init__(self, graph: Any):
        """
        Initialize schema manager.

        Args:
            graph: FalkorDB graph instance
        """
        self.graph = graph
        self.index_manager = IndexManager(graph)

    def validate_schema(self, entity_classes: List[Type]) -> SchemaValidationResult:
        """
        Validate database schema against entity definitions.

        Checks if all declared indexes exist and reports discrepancies.

        Args:
            entity_classes: List of entity classes to validate

        Returns:
            SchemaValidationResult with validation details

        Example:
            >>> result = manager.validate_schema([Person, Company])
            >>> if not result.is_valid:
            ...     print(result)
        """
        missing_indexes = []
        extra_indexes = []
        errors = []

        # Get all defined indexes from metadata
        defined_indexes: Set[Tuple[str, str]] = set()
        for entity_class in entity_classes:
            metadata = get_entity_metadata(entity_class)
            if not metadata:
                errors.append(f"{entity_class.__name__} is not a decorated entity")
                continue

            label = metadata.primary_label
            for prop in metadata.properties:
                if prop.indexed or prop.unique:
                    defined_indexes.add((label, prop.graph_name))

        # Get all existing indexes from database
        existing_indexes = self.index_manager.list_indexes()
        existing_index_set: Set[Tuple[str, str]] = set()

        for idx in existing_indexes:
            existing_index_set.add((idx.label, idx.property_name))

        # Find missing indexes
        for label, prop_name in defined_indexes:
            if (label, prop_name) not in existing_index_set:
                # Determine index type from metadata
                idx_type = "RANGE"  # default
                for entity_class in entity_classes:
                    metadata = get_entity_metadata(entity_class)
                    if metadata and metadata.primary_label == label:
                        for p in metadata.properties:
                            if p.graph_name == prop_name:
                                if p.unique:
                                    idx_type = "UNIQUE"
                                elif p.index_type:
                                    idx_type = p.index_type
                                break
                        break

                missing_indexes.append((label, prop_name, idx_type))

        # Find extra indexes
        for idx in existing_indexes:
            if (idx.label, idx.property_name) not in defined_indexes:
                # Check if this is an index for an entity we're managing
                is_managed = False
                for entity_class in entity_classes:
                    metadata = get_entity_metadata(entity_class)
                    if metadata and metadata.primary_label == idx.label:
                        is_managed = True
                        break

                if is_managed:
                    extra_indexes.append(idx)

        is_valid = len(missing_indexes) == 0 and len(extra_indexes) == 0 and len(errors) == 0

        return SchemaValidationResult(
            is_valid=is_valid,
            missing_indexes=missing_indexes,
            extra_indexes=extra_indexes,
            errors=errors,
        )

    def sync_schema(self, entity_classes: List[Type], drop_extra: bool = False) -> Dict[str, int]:
        """
        Synchronize database schema with entity definitions.

        Creates missing indexes and optionally drops extra indexes.

        Args:
            entity_classes: List of entity classes to sync
            drop_extra: Whether to drop extra indexes (default: False)

        Returns:
            Dictionary with counts: {'created': N, 'dropped': M}

        Example:
            >>> stats = manager.sync_schema([Person, Company])
            >>> print(f"Created {stats['created']} indexes")
        """
        created = 0
        dropped = 0

        # Validate first to get differences
        result = self.validate_schema(entity_classes)

        # Create missing indexes
        for label, prop_name, idx_type in result.missing_indexes:
            try:
                unique = idx_type == "UNIQUE"
                self.index_manager.create_index_for_property(
                    label, prop_name, idx_type if not unique else None, unique
                )
                created += 1
            except Exception:
                # Log error but continue
                pass

        # Drop extra indexes if requested
        if drop_extra:
            for idx in result.extra_indexes:
                try:
                    self.index_manager.drop_index_for_property(idx.label, idx.property_name)
                    dropped += 1
                except Exception:
                    # Log error but continue
                    pass

        return {"created": created, "dropped": dropped}

    def get_schema_diff(self, entity_classes: List[Type]) -> str:
        """
        Get human-readable schema differences.

        Args:
            entity_classes: List of entity classes to compare

        Returns:
            Formatted string describing schema differences

        Example:
            >>> print(manager.get_schema_diff([Person, Company]))
        """
        result = self.validate_schema(entity_classes)
        return str(result)

    def ensure_schema(self, entity_classes: List[Type]) -> None:
        """
        Ensure schema is synchronized (convenience method).

        Creates all missing indexes without dropping extras.

        Args:
            entity_classes: List of entity classes to ensure

        Example:
            >>> manager.ensure_schema([Person, Company])
        """
        self.sync_schema(entity_classes, drop_extra=False)

    def get_schema_info(self, entity_classes: List[Type]) -> Dict[str, Any]:
        """
        Get detailed schema information.

        Args:
            entity_classes: List of entity classes to analyze

        Returns:
            Dictionary with schema details

        Example:
            >>> info = manager.get_schema_info([Person, Company])
            >>> print(f"Total entities: {info['entity_count']}")
            >>> print(f"Total indexes: {info['total_indexes']}")
        """
        total_properties = 0
        indexed_properties = 0
        unique_properties = 0

        for entity_class in entity_classes:
            metadata = get_entity_metadata(entity_class)
            if metadata:
                total_properties += len(metadata.properties)
                for prop in metadata.properties:
                    if prop.indexed:
                        indexed_properties += 1
                    if prop.unique:
                        unique_properties += 1

        # Get existing indexes
        existing_indexes = self.index_manager.list_indexes()

        return {
            "entity_count": len(entity_classes),
            "total_properties": total_properties,
            "indexed_properties": indexed_properties,
            "unique_properties": unique_properties,
            "total_indexes": len(existing_indexes),
            "existing_indexes": existing_indexes,
        }
