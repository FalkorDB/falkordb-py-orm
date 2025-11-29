"""Relationship loading and management."""

from typing import Any, Generic, Iterator, List, Optional, Type, TypeVar

from .metadata import RelationshipMetadata

T = TypeVar("T")


class LazyList(Generic[T]):
    """
    Lazy proxy for List[T] relationships.

    Loads related entities on first access and caches them.
    """

    def __init__(
        self,
        graph: Any,
        source_id: int,
        relationship_meta: RelationshipMetadata,
        entity_class: Type[T],
        mapper: Any,
        query_builder: Any,
    ):
        """
        Initialize lazy list proxy.

        Args:
            graph: FalkorDB graph instance
            source_id: ID of source entity
            relationship_meta: Relationship metadata
            entity_class: Target entity class
            mapper: Entity mapper instance
            query_builder: Query builder instance
        """
        self._graph = graph
        self._source_id = source_id
        self._relationship_meta = relationship_meta
        self._entity_class = entity_class
        self._mapper = mapper
        self._query_builder = query_builder
        self._loaded = False
        self._items: List[T] = []

    def _load(self) -> None:
        """Load related entities from database."""
        if self._loaded:
            return

        # Build and execute query
        cypher, params = self._query_builder.build_relationship_load_query(
            self._relationship_meta, self._source_id, self._entity_class
        )

        result = self._graph.query(cypher, params)

        # Map results to entities
        self._items = []
        for record in result.result_set:
            entity = self._mapper.map_from_record(record, self._entity_class, "target")
            self._items.append(entity)

        self._loaded = True

    def __iter__(self) -> Iterator[T]:
        """Iterate over related entities."""
        self._load()
        return iter(self._items)

    def __len__(self) -> int:
        """Get count of related entities."""
        self._load()
        return len(self._items)

    def __getitem__(self, index: int) -> T:
        """Get entity by index."""
        self._load()
        return self._items[index]

    def __contains__(self, item: T) -> bool:
        """Check if entity is in collection."""
        self._load()
        return item in self._items

    def __repr__(self) -> str:
        """String representation."""
        if self._loaded:
            return f"LazyList({self._items})"
        return f"LazyList(<not loaded>, {self._relationship_meta.relationship_type})"


class LazySingle(Generic[T]):
    """
    Lazy proxy for Optional[T] relationships.

    Loads related entity on first access and caches it.
    """

    def __init__(
        self,
        graph: Any,
        source_id: int,
        relationship_meta: RelationshipMetadata,
        entity_class: Type[T],
        mapper: Any,
        query_builder: Any,
    ):
        """
        Initialize lazy single proxy.

        Args:
            graph: FalkorDB graph instance
            source_id: ID of source entity
            relationship_meta: Relationship metadata
            entity_class: Target entity class
            mapper: Entity mapper instance
            query_builder: Query builder instance
        """
        self._graph = graph
        self._source_id = source_id
        self._relationship_meta = relationship_meta
        self._entity_class = entity_class
        self._mapper = mapper
        self._query_builder = query_builder
        self._loaded = False
        self._item: Optional[T] = None

    def _load(self) -> None:
        """Load related entity from database."""
        if self._loaded:
            return

        # Build and execute query
        cypher, params = self._query_builder.build_relationship_load_query(
            self._relationship_meta, self._source_id, self._entity_class
        )

        result = self._graph.query(cypher, params)

        # Map result to entity (take first result only)
        if result.result_set:
            self._item = self._mapper.map_from_record(
                result.result_set[0], self._entity_class, "target"
            )
        else:
            self._item = None

        self._loaded = True

    def get(self) -> Optional[T]:
        """Get the related entity."""
        self._load()
        return self._item

    def __bool__(self) -> bool:
        """Check if relationship exists."""
        self._load()
        return self._item is not None

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        self._load()
        if isinstance(other, LazySingle):
            other._load()
            return self._item == other._item
        return self._item == other

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to underlying entity."""
        self._load()
        if self._item is None:
            raise AttributeError(f"Cannot access attribute '{name}' on None")
        return getattr(self._item, name)

    def __repr__(self) -> str:
        """String representation."""
        if self._loaded:
            return f"LazySingle({self._item})"
        return f"LazySingle(<not loaded>, {self._relationship_meta.relationship_type})"


def create_lazy_proxy(
    graph: Any,
    source_id: int,
    relationship_meta: RelationshipMetadata,
    entity_class: Type[T],
    mapper: Any,
    query_builder: Any,
) -> Any:
    """
    Create appropriate lazy proxy based on relationship metadata.

    Args:
        graph: FalkorDB graph instance
        source_id: ID of source entity
        relationship_meta: Relationship metadata
        entity_class: Target entity class
        mapper: Entity mapper instance
        query_builder: Query builder instance

    Returns:
        LazyList for collections, LazySingle for single relationships
    """
    if relationship_meta.is_collection:
        return LazyList(
            graph=graph,
            source_id=source_id,
            relationship_meta=relationship_meta,
            entity_class=entity_class,
            mapper=mapper,
            query_builder=query_builder,
        )
    else:
        return LazySingle(
            graph=graph,
            source_id=source_id,
            relationship_meta=relationship_meta,
            entity_class=entity_class,
            mapper=mapper,
            query_builder=query_builder,
        )


class RelationshipManager:
    """
    Manages relationship persistence operations including cascade save/delete.
    """

    def __init__(self, graph: Any, mapper: Any, query_builder: Any):
        """
        Initialize relationship manager.

        Args:
            graph: FalkorDB graph instance
            mapper: Entity mapper instance
            query_builder: Query builder instance
        """
        self._graph = graph
        self._mapper = mapper
        self._query_builder = query_builder
        self._entity_tracker: set = set()

    def save_relationships(
        self, source_entity: Any, source_id: int, metadata: Any, is_update: bool = False
    ) -> None:
        """
        Save relationships for an entity.

        Args:
            source_entity: Source entity instance
            source_id: Source entity's database ID
            metadata: Entity metadata
            is_update: Whether this is an update (True) or initial save (False)
        """
        # Track this entity to avoid infinite loops
        entity_key = (id(source_entity), source_id)
        if entity_key in self._entity_tracker:
            return

        self._entity_tracker.add(entity_key)

        try:
            for rel_meta in metadata.relationships:
                # Get relationship value from entity
                rel_value = getattr(source_entity, rel_meta.python_name, None)

                # Skip if not set or is a lazy proxy (not yet loaded)
                if rel_value is None:
                    continue

                # Skip lazy proxies that haven't been modified
                if isinstance(rel_value, (LazyList, LazySingle)):
                    continue

                # If this is an update, delete existing relationship edges first
                if is_update:
                    self._delete_relationship_edges(source_id, rel_meta)

                # Handle collection relationships
                if rel_meta.is_collection:
                    if not isinstance(rel_value, (list, tuple)):
                        continue

                    for related_entity in rel_value:
                        target_id = self._get_or_save_related_entity(related_entity, rel_meta)
                        if target_id is not None:
                            self._create_relationship_edge(source_id, target_id, rel_meta)

                # Handle single relationships
                else:
                    target_id = self._get_or_save_related_entity(rel_value, rel_meta)
                    if target_id is not None:
                        self._create_relationship_edge(source_id, target_id, rel_meta)

        finally:
            # Clean up tracker for this entity
            self._entity_tracker.discard(entity_key)

    def _get_or_save_related_entity(
        self, entity: Any, rel_meta: RelationshipMetadata
    ) -> Optional[int]:
        """
        Get entity ID or save entity if cascade is enabled.

        Args:
            entity: Related entity instance
            rel_meta: Relationship metadata

        Returns:
            Entity ID if available, None otherwise
        """
        if entity is None:
            return None

        # Get entity metadata
        entity_metadata = self._mapper.get_entity_metadata(type(entity))

        # Check if entity has an ID
        if entity_metadata.id_property:
            entity_id = getattr(entity, entity_metadata.id_property.python_name, None)

            # If has ID, return it
            if entity_id is not None:
                return entity_id

            # If no ID and cascade enabled, save the entity
            if rel_meta.cascade:
                # Import here to avoid circular dependency
                from .repository import Repository

                # Create temporary repository for the target entity
                target_repo = Repository(self._graph, type(entity))
                saved_entity = target_repo.save(entity)

                # Return the saved entity's ID
                return getattr(saved_entity, entity_metadata.id_property.python_name, None)

        return None

    def _create_relationship_edge(
        self, source_id: int, target_id: int, rel_meta: RelationshipMetadata
    ) -> None:
        """
        Create relationship edge in the graph.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            rel_meta: Relationship metadata
        """
        cypher, params = self._query_builder.build_relationship_create_query(
            rel_meta, source_id, target_id
        )

        self._graph.query(cypher, params)

    def _delete_relationship_edges(self, source_id: int, rel_meta: RelationshipMetadata) -> None:
        """
        Delete all existing relationship edges for a given relationship.

        Args:
            source_id: Source node ID
            rel_meta: Relationship metadata
        """
        cypher, params = self._query_builder.build_relationship_delete_query(rel_meta, source_id)

        self._graph.query(cypher, params)

    def clear_tracker(self) -> None:
        """Clear the entity tracker."""
        self._entity_tracker.clear()
