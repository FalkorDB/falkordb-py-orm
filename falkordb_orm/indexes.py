"""Index management for FalkorDB entities."""

from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass

from .metadata import get_entity_metadata, PropertyMetadata
from .exceptions import QueryException


@dataclass
class IndexInfo:
    """Information about a database index."""

    label: str
    """The node label the index is on."""

    property_name: str
    """The property name the index is on."""

    index_type: str
    """Type of index (RANGE, FULLTEXT, VECTOR, etc.)."""

    is_unique: bool
    """Whether this is a unique constraint index."""


class IndexManager:
    """
    Manages indexes for FalkorDB entities.

    Provides methods to create, drop, and list indexes based on entity metadata.
    Supports RANGE, FULLTEXT, and VECTOR indexes, as well as unique constraints.

    Example:
        >>> from falkordb_orm import IndexManager
        >>>
        >>> manager = IndexManager(graph)
        >>>
        >>> # Create all indexes for an entity
        >>> manager.create_indexes(Person)
        >>>
        >>> # Ensure indexes exist (create if missing)
        >>> manager.ensure_indexes(Person)
        >>>
        >>> # List all indexes for an entity
        >>> indexes = manager.list_indexes(Person)
    """

    def __init__(self, graph: Any):
        """
        Initialize index manager.

        Args:
            graph: FalkorDB graph instance
        """
        self.graph = graph

    def create_indexes(self, entity_class: Type, if_not_exists: bool = False) -> List[str]:
        """
        Create indexes for all indexed properties in an entity.

        Args:
            entity_class: Entity class with metadata
            if_not_exists: Whether to skip if index already exists (default: False)

        Returns:
            List of Cypher queries executed

        Raises:
            QueryException: If index creation fails

        Example:
            >>> manager.create_indexes(Person)
            ['CREATE INDEX FOR (n:Person) ON (n.email)', ...]
        """
        metadata = get_entity_metadata(entity_class)
        if not metadata:
            raise ValueError(f"{entity_class.__name__} is not a decorated entity")

        queries = []
        label = metadata.primary_label

        for prop in metadata.properties:
            if prop.unique:
                # Create unique constraint (also creates an index)
                query = self._build_unique_constraint_query(label, prop.graph_name)
                queries.append(query)

                try:
                    self.graph.query(query)
                except Exception as e:
                    if not if_not_exists:
                        raise QueryException(f"Failed to create unique constraint: {e}") from e
                    # Ignore if constraint already exists

            elif prop.indexed:
                # Create regular index
                query = self._build_index_query(label, prop.graph_name, prop.index_type)
                queries.append(query)

                try:
                    self.graph.query(query)
                except Exception as e:
                    if not if_not_exists:
                        raise QueryException(f"Failed to create index: {e}") from e
                    # Ignore if index already exists

        return queries

    def drop_indexes(self, entity_class: Type) -> List[str]:
        """
        Drop all indexes for an entity.

        Args:
            entity_class: Entity class with metadata

        Returns:
            List of Cypher queries executed

        Raises:
            QueryException: If index dropping fails

        Example:
            >>> manager.drop_indexes(Person)
            ['DROP INDEX ON :Person(email)', ...]
        """
        metadata = get_entity_metadata(entity_class)
        if not metadata:
            raise ValueError(f"{entity_class.__name__} is not a decorated entity")

        queries = []
        label = metadata.primary_label

        for prop in metadata.properties:
            if prop.indexed or prop.unique:
                # Drop index
                query = f"DROP INDEX ON :{label}({prop.graph_name})"
                queries.append(query)

                try:
                    self.graph.query(query)
                except Exception as e:
                    # Ignore if index doesn't exist
                    pass

        return queries

    def ensure_indexes(self, entity_class: Type) -> List[str]:
        """
        Ensure indexes exist, creating them if missing.

        This is a safe operation that won't fail if indexes already exist.

        Args:
            entity_class: Entity class with metadata

        Returns:
            List of Cypher queries executed

        Example:
            >>> manager.ensure_indexes(Person)
        """
        return self.create_indexes(entity_class, if_not_exists=True)

    def list_indexes(self, entity_class: Optional[Type] = None) -> List[IndexInfo]:
        """
        List all indexes, optionally filtered by entity.

        Args:
            entity_class: Optional entity class to filter by

        Returns:
            List of IndexInfo objects

        Example:
            >>> indexes = manager.list_indexes(Person)
            >>> for idx in indexes:
            ...     print(f"{idx.label}.{idx.property_name}: {idx.index_type}")
        """
        # Get indexes using CALL db.indexes()
        try:
            result = self.graph.query("CALL db.indexes()")

            indexes = []
            label_filter = None

            if entity_class:
                metadata = get_entity_metadata(entity_class)
                if metadata:
                    label_filter = metadata.primary_label

            # Parse index results
            # FalkorDB returns: label, property, type
            for record in result.result_set:
                # Extract index information
                # Format varies by FalkorDB version, handle both
                if len(record) >= 3:
                    label = str(record[0])
                    prop_name = str(record[1])
                    idx_type = str(record[2]) if record[2] else "RANGE"

                    # Check if this is a unique constraint
                    is_unique = "UNIQUE" in idx_type.upper() if idx_type else False

                    # Filter by label if specified
                    if label_filter and label != label_filter:
                        continue

                    indexes.append(
                        IndexInfo(
                            label=label,
                            property_name=prop_name,
                            index_type=idx_type,
                            is_unique=is_unique,
                        )
                    )

            return indexes

        except Exception as e:
            # If db.indexes() not available, return empty list
            return []

    def _build_index_query(self, label: str, property_name: str, index_type: Optional[str]) -> str:
        """
        Build Cypher query to create an index.

        Args:
            label: Node label
            property_name: Property name
            index_type: Type of index (RANGE, FULLTEXT, VECTOR, or None for default)

        Returns:
            Cypher CREATE INDEX query
        """
        if index_type and index_type.upper() == "FULLTEXT":
            # Full-text index
            return f"CALL db.idx.fulltext.createNodeIndex('{label}', '{property_name}')"
        elif index_type and index_type.upper() == "VECTOR":
            # Vector index (requires dimension specification, using default 1536 for now)
            return f"CALL db.idx.vector.createNodeIndex('{label}', '{property_name}')"
        else:
            # Default RANGE index
            return f"CREATE INDEX FOR (n:{label}) ON (n.{property_name})"

    def _build_unique_constraint_query(self, label: str, property_name: str) -> str:
        """
        Build Cypher query to create a unique constraint.

        Args:
            label: Node label
            property_name: Property name

        Returns:
            Cypher CREATE CONSTRAINT query
        """
        # FalkorDB unique constraint syntax
        return f"CREATE CONSTRAINT ON (n:{label}) ASSERT n.{property_name} IS UNIQUE"

    def create_index_for_property(
        self,
        label: str,
        property_name: str,
        index_type: Optional[str] = None,
        unique: bool = False,
    ) -> str:
        """
        Create an index for a specific property (without entity metadata).

        Args:
            label: Node label
            property_name: Property name
            index_type: Type of index (RANGE, FULLTEXT, VECTOR, or None)
            unique: Whether to create a unique constraint

        Returns:
            Cypher query executed

        Example:
            >>> manager.create_index_for_property("Person", "email", unique=True)
        """
        if unique:
            query = self._build_unique_constraint_query(label, property_name)
        else:
            query = self._build_index_query(label, property_name, index_type)

        try:
            self.graph.query(query)
            return query
        except Exception as e:
            raise QueryException(f"Failed to create index: {e}") from e

    def drop_index_for_property(self, label: str, property_name: str) -> str:
        """
        Drop an index for a specific property.

        Args:
            label: Node label
            property_name: Property name

        Returns:
            Cypher query executed

        Example:
            >>> manager.drop_index_for_property("Person", "email")
        """
        query = f"DROP INDEX ON :{label}({property_name})"

        try:
            self.graph.query(query)
            return query
        except Exception as e:
            # Ignore if index doesn't exist
            return query
