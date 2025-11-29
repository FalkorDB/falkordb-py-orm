"""Async entity mapper for converting between Python objects and graph structures."""

from typing import Any, Dict, List, Tuple, Type, TypeVar

from .exceptions import MappingException
from .metadata import EntityMetadata
from .types import get_type_registry
from .mapper import EntityMapper

T = TypeVar("T")


class AsyncEntityMapper:
    """Handles async bidirectional conversion between Python objects and FalkorDB graph structures."""

    def __init__(self, graph: Any = None, query_builder: Any = None) -> None:
        self._metadata_cache: Dict[Type, EntityMetadata] = {}
        self._type_registry = get_type_registry()
        self._graph = graph
        self._query_builder = query_builder
        # Reuse sync mapper for non-async operations
        self._sync_mapper = EntityMapper(graph=graph, query_builder=query_builder)

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
        return self._sync_mapper.get_entity_metadata(entity_class)

    def map_to_properties(self, entity: Any) -> Dict[str, Any]:
        """
        Extract properties from entity for graph storage.

        Args:
            entity: Python entity instance

        Returns:
            Dictionary of property names to values (graph format)
        """
        return self._sync_mapper.map_to_properties(entity)

    def map_to_cypher_create(self, entity: Any) -> Tuple[str, Dict[str, Any]]:
        """
        Generate Cypher CREATE statement for entity.

        Args:
            entity: Python entity instance

        Returns:
            Tuple of (cypher_query, parameters)
        """
        return self._sync_mapper.map_to_cypher_create(entity)

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
        return self._sync_mapper.map_to_cypher_merge(entity)

    async def _initialize_lazy_relationships(self, entity: T, entity_id: int) -> None:
        """
        Initialize async lazy relationship proxies on an entity.

        Args:
            entity: Entity instance
            entity_id: Entity's internal ID
        """
        # Only initialize if we have graph and query_builder
        if self._graph is None or self._query_builder is None:
            return

        metadata = self.get_entity_metadata(type(entity))

        # Import here to avoid circular dependency
        from .async_relationships import create_async_lazy_proxy

        for rel_meta in metadata.relationships:
            # Determine target class
            target_class = rel_meta.target_class

            # If target_class is not resolved, skip
            if target_class is None and rel_meta.target_class_name:
                continue

            if target_class is None:
                continue

            # Create async lazy proxy
            proxy = create_async_lazy_proxy(
                graph=self._graph,
                source_id=entity_id,
                relationship_meta=rel_meta,
                entity_class=target_class,
                mapper=self,
                query_builder=self._query_builder,
            )

            # Set the proxy on the entity
            setattr(entity, rel_meta.python_name, proxy)

    async def map_from_node(self, node: Any, entity_class: Type[T]) -> T:
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

            # Initialize async lazy relationships if we have an ID
            if internal_id is not None:
                await self._initialize_lazy_relationships(entity, internal_id)

            return entity
        except Exception as e:
            raise MappingException(
                f"Failed to create instance of {entity_class.__name__}: {e}"
            ) from e

    async def map_from_record(self, record: Any, entity_class: Type[T], var_name: str = "n", header: Any = None) -> T:
        """
        Convert FalkorDB query result record to entity instance.

        Args:
            record: FalkorDB result record
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
            # Dict-based record
            node = record[var_name]
        
        return await self.map_from_node(node, entity_class)

    def update_entity_id(self, entity: Any, node_id: int) -> None:
        """
        Update entity's ID after creation.

        Args:
            entity: Entity instance
            node_id: Generated node ID
        """
        self._sync_mapper.update_entity_id(entity, node_id)

    async def map_with_relationships(
        self, record: Any, entity_class: Type[T], fetch_hints: List[str], var_name: str = "n"
    ) -> T:
        """
        Convert FalkorDB query result record to entity with eagerly loaded relationships.

        Args:
            record: FalkorDB result record
            entity_class: Target entity class
            fetch_hints: List of relationship names that were eagerly loaded
            var_name: Variable name in query (default: 'n')

        Returns:
            Entity instance with relationships populated
        """
        # Map main entity
        node = record[var_name]
        entity = await self.map_from_node(node, entity_class)

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

            # Map nodes to entities (async)
            if rel_meta.target_class:
                related_entities = []
                for node in related_nodes:
                    entity_obj = await self.map_from_node(node, rel_meta.target_class)
                    related_entities.append(entity_obj)

                # Set on entity based on relationship type
                if rel_meta.is_collection:
                    setattr(entity, rel_meta.python_name, related_entities)
                else:
                    # For single relationships, take first or None
                    value = related_entities[0] if related_entities else None
                    setattr(entity, rel_meta.python_name, value)

        return entity
