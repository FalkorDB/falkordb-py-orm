"""Entity mapper for converting between Python objects and graph structures."""

from typing import Any, Dict, List, Tuple, Type, TypeVar

from .exceptions import InvalidEntityException, MappingException
from .metadata import EntityMetadata, get_entity_metadata
from .types import get_type_registry

T = TypeVar("T")


class EntityMapper:
    """Handles bidirectional conversion between Python objects and FalkorDB graph structures."""

    def __init__(self, graph: Any = None, query_builder: Any = None) -> None:
        self._metadata_cache: Dict[Type, EntityMetadata] = {}
        self._type_registry = get_type_registry()
        self._graph = graph
        self._query_builder = query_builder

    def get_entity_metadata(self, entity_class: Type[T]) -> EntityMetadata:
        """
        Get entity metadata from a class, using cache.

        Args:
            entity_class: The entity class

        Returns:
            EntityMetadata for the class

        Raises:
            InvalidEntityException: If the class is not a valid entity
        """
        if entity_class not in self._metadata_cache:
            metadata = get_entity_metadata(entity_class)
            if metadata is None:
                raise InvalidEntityException(
                    f"Class {entity_class.__name__} is not decorated with @node"
                )
            self._metadata_cache[entity_class] = metadata

        return self._metadata_cache[entity_class]

    def _is_relationship_field(self, field_name: str, metadata: EntityMetadata) -> bool:
        """
        Check if a field is a relationship.

        Args:
            field_name: Name of the field
            metadata: Entity metadata

        Returns:
            True if field is a relationship, False otherwise
        """
        return metadata.is_relationship_field(field_name)

    def map_to_properties(self, entity: Any) -> Dict[str, Any]:
        """
        Extract properties from entity for graph storage.

        Args:
            entity: Python entity instance

        Returns:
            Dictionary of property names to values (graph format)
        """
        metadata = self.get_entity_metadata(type(entity))
        properties: Dict[str, Any] = {}

        for prop in metadata.properties:
            # Skip relationship fields - they're not regular properties
            if self._is_relationship_field(prop.python_name, metadata):
                continue

            # Skip ID property if it's auto-generated and None
            if prop.is_id and prop.id_generator is not None:
                value = getattr(entity, prop.python_name, None)
                if value is None:
                    continue

            value = getattr(entity, prop.python_name, None)

            if value is not None:
                # Use custom converter if provided
                if prop.converter:
                    graph_value = prop.converter.to_graph(value)
                else:
                    graph_value = self._type_registry.convert_to_graph(value, prop.python_type)

                properties[prop.graph_name] = graph_value

        return properties

    def map_to_cypher_create(self, entity: Any) -> Tuple[str, Dict[str, Any]]:
        """
        Generate Cypher CREATE statement for entity.

        Args:
            entity: Python entity instance

        Returns:
            Tuple of (cypher_query, parameters)
        """
        metadata = self.get_entity_metadata(type(entity))
        properties = self.map_to_properties(entity)

        # Build labels string
        labels_str = ":".join(metadata.labels)

        # Handle interned properties by wrapping with intern() function
        set_clauses = []
        params: Dict[str, Any] = {}

        for prop in metadata.properties:
            if prop.python_name in properties or prop.graph_name in properties:
                value = properties.get(prop.graph_name, properties.get(prop.python_name))
                param_name = f"prop_{prop.graph_name}"

                if prop.interned and isinstance(value, str):
                    # Use intern() function for interned string properties
                    set_clauses.append(f"n.{prop.graph_name} = intern(${param_name})")
                else:
                    set_clauses.append(f"n.{prop.graph_name} = ${param_name}")

                params[param_name] = value

        # Generate Cypher
        if set_clauses:
            set_statement = ", ".join(set_clauses)
            cypher = f"CREATE (n:{labels_str}) SET {set_statement} RETURN n, id(n) as node_id"
        else:
            cypher = f"CREATE (n:{labels_str}) RETURN n, id(n) as node_id"

        return cypher, params

    def map_to_cypher_merge(self, entity: Any) -> Tuple[str, Dict[str, Any]]:
        """
        Generate Cypher MERGE statement for entity (update or create).

        Args:
            entity: Python entity instance

        Returns:
            Tuple of (cypher_query, parameters)

        Raises:
            MappingException: If entity doesn't have an ID
        """
        metadata = self.get_entity_metadata(type(entity))

        if metadata.id_property is None:
            raise MappingException(f"Entity {metadata.entity_class.__name__} has no ID property")

        entity_id = getattr(entity, metadata.id_property.python_name, None)
        if entity_id is None:
            raise MappingException(f"Entity {metadata.entity_class.__name__} has no ID value")

        properties = self.map_to_properties(entity)

        # Build labels string
        labels_str = ":".join(metadata.labels)

        # Handle interned properties by wrapping with intern() function
        set_clauses = []
        params: Dict[str, Any] = {"id": entity_id}

        for prop in metadata.properties:
            if prop.is_id:
                continue  # Skip ID property as it's in the MERGE clause

            if prop.python_name in properties or prop.graph_name in properties:
                value = properties.get(prop.graph_name, properties.get(prop.python_name))
                param_name = f"prop_{prop.graph_name}"

                if prop.interned and isinstance(value, str):
                    # Use intern() function for interned string properties
                    set_clauses.append(f"n.{prop.graph_name} = intern(${param_name})")
                else:
                    set_clauses.append(f"n.{prop.graph_name} = ${param_name}")

                params[param_name] = value

        # Generate Cypher
        if set_clauses:
            set_statement = ", ".join(set_clauses)
            cypher = f"""
            MERGE (n:{labels_str} {{id: $id}})
            SET {set_statement}
            RETURN n, id(n) as node_id
            """
        else:
            cypher = f"""
            MERGE (n:{labels_str} {{id: $id}})
            RETURN n, id(n) as node_id
            """

        return cypher, params

    def _initialize_lazy_relationships(self, entity: T, entity_id: int) -> None:
        """
        Initialize lazy relationship proxies on an entity.

        Args:
            entity: Entity instance
            entity_id: Entity's internal ID
        """
        # Only initialize if we have graph and query_builder
        if self._graph is None or self._query_builder is None:
            return

        metadata = self.get_entity_metadata(type(entity))

        # Import here to avoid circular dependency
        from .relationships import create_lazy_proxy

        for rel_meta in metadata.relationships:
            # Determine target class
            target_class = rel_meta.target_class

            # If target_class is not resolved, try to resolve it
            if target_class is None and rel_meta.target_class_name:
                # Try to get from metadata cache or global namespace
                # For now, skip if not resolved - will be handled in Phase 3c
                continue

            if target_class is None:
                continue

            # Create lazy proxy
            proxy = create_lazy_proxy(
                graph=self._graph,
                source_id=entity_id,
                relationship_meta=rel_meta,
                entity_class=target_class,
                mapper=self,
                query_builder=self._query_builder,
            )

            # Set the proxy on the entity
            setattr(entity, rel_meta.python_name, proxy)

    def map_from_node(self, node: Any, entity_class: Type[T]) -> T:
        """
        Convert FalkorDB node to entity instance.

        Args:
            node: FalkorDB Node object
            entity_class: Target entity class

        Returns:
            Entity instance
        """
        metadata = self.get_entity_metadata(entity_class)
        kwargs: Dict[str, Any] = {}

        # Extract internal ID if present
        internal_id = getattr(node, "id", None)

        # Map properties
        node_properties = node.properties if hasattr(node, "properties") else {}

        for prop in metadata.properties:
            # Check if property exists in node
            if prop.graph_name in node_properties:
                graph_value = node_properties[prop.graph_name]

                # Use custom converter if provided
                if prop.converter:
                    python_value = prop.converter.from_graph(graph_value)
                else:
                    python_value = self._type_registry.convert_from_graph(
                        graph_value, prop.python_type
                    )

                kwargs[prop.python_name] = python_value
            elif prop.is_id and internal_id is not None and prop.id_generator is not None:
                # Use internal ID for auto-generated ID fields
                kwargs[prop.python_name] = internal_id
            else:
                # Set to None if not present
                kwargs[prop.python_name] = None

        # Create instance
        try:
            entity = entity_class(**kwargs)

            # Initialize lazy relationships if we have an ID
            if internal_id is not None:
                self._initialize_lazy_relationships(entity, internal_id)

            return entity
        except Exception as e:
            raise MappingException(
                f"Failed to create instance of {entity_class.__name__}: {e}"
            ) from e

    def map_from_record(
        self, record: Any, entity_class: Type[T], var_name: str = "n", header: Any = None
    ) -> T:
        """
        Convert FalkorDB query result record to entity instance.

        Args:
            record: FalkorDB result record (list or dict)
            entity_class: Target entity class
            var_name: Variable name in query (default: 'n')
            header: Optional header from query result for column name mapping

        Returns:
            Entity instance
        """
        # Handle both list-based (FalkorDB) and dict-based (custom) records
        if isinstance(record, list):
            # FalkorDB returns list format - need to find column index
            if header is not None:
                # Header format: [[column_id, column_name], ...]
                column_index = None
                for idx, header_item in enumerate(header):
                    # header_item is [column_id, column_name]
                    col_name = header_item[1] if isinstance(header_item, list) else header_item
                    if col_name == var_name:
                        column_index = idx
                        break

                if column_index is not None:
                    node = record[column_index]
                else:
                    # Fallback: assume first column if var_name not found
                    node = record[0]
            else:
                # No header provided, assume first column
                node = record[0]
        else:
            # Dictionary-based record (backward compatible)
            node = record[var_name]

        return self.map_from_node(node, entity_class)

    def update_entity_id(self, entity: Any, node_id: int) -> None:
        """
        Update entity's ID after creation.

        Args:
            entity: Entity instance
            node_id: Generated node ID
        """
        metadata = self.get_entity_metadata(type(entity))

        if metadata.id_property:
            setattr(entity, metadata.id_property.python_name, node_id)

    def map_with_relationships(
        self,
        record: Any,
        entity_class: Type[T],
        fetch_hints: List[str],
        var_name: str = "n",
        header: Any = None,
    ) -> T:
        """
        Convert FalkorDB query result record to entity with eagerly loaded relationships.

        Args:
            record: FalkorDB result record (list or dict)
            entity_class: Target entity class
            fetch_hints: List of relationship names that were eagerly loaded
            var_name: Variable name in query (default: 'n')
            header: Optional header from query result for column name mapping

        Returns:
            Entity instance with relationships populated
        """
        # Map main entity - handle both list and dict format
        if isinstance(record, list) and header is not None:
            # Find column index for var_name
            column_index = 0
            for idx, header_item in enumerate(header):
                col_name = header_item[1] if isinstance(header_item, list) else header_item
                if col_name == var_name:
                    column_index = idx
                    break
            node = record[column_index]
        elif isinstance(record, list):
            node = record[0]  # Fallback to first column
        else:
            node = record[var_name]  # Dictionary format

        entity = self.map_from_node(node, entity_class)

        # Get metadata
        metadata = self.get_entity_metadata(entity_class)

        # Map each eagerly loaded relationship
        for hint in fetch_hints:
            if hint not in record:
                continue

            # Get relationship metadata
            rel_meta = metadata.get_relationship_by_python_name(hint)
            if rel_meta is None:
                continue

            # Get related nodes from record
            related_nodes = record[hint]

            # Handle None or empty list
            if related_nodes is None:
                related_nodes = []

            # Filter out None values (from OPTIONAL MATCH)
            related_nodes = [n for n in related_nodes if n is not None]

            # Map nodes to entities
            if rel_meta.target_class:
                related_entities = [
                    self.map_from_node(node, rel_meta.target_class) for node in related_nodes
                ]

                # Set on entity based on relationship type
                if rel_meta.is_collection:
                    setattr(entity, rel_meta.python_name, related_entities)
                else:
                    # For single relationships, take first or None
                    value = related_entities[0] if related_entities else None
                    setattr(entity, rel_meta.python_name, value)

        return entity
