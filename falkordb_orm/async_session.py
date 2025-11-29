"""Async session management for transactional operations."""

from typing import Any, Dict, Optional, Set, Tuple, Type, TypeVar
import copy

from .exceptions import EntityNotFoundException, QueryException
from .async_mapper import AsyncEntityMapper
from .query_builder import QueryBuilder
from .metadata import get_entity_metadata

T = TypeVar("T")


class AsyncSession:
    """
    Async session for managing entities with identity map and change tracking.

    Provides:
    - Identity map to prevent duplicate entity instances
    - Change tracking for dirty checking
    - Transaction management with commit/rollback
    - Unit of work pattern
    - Async/await support

    Example:
        >>> async with AsyncSession(graph) as session:
        ...     # Add new entities
        ...     person = Person(name="Alice", age=25)
        ...     session.add(person)
        ...
        ...     # Modify existing entities
        ...     existing = await session.get(Person, 1)
        ...     existing.age = 26
        ...
        ...     # All changes saved on commit
        ...     await session.commit()
    """

    def __init__(self, graph: Any):
        """
        Initialize async session.

        Args:
            graph: FalkorDB async graph instance
        """
        self.graph = graph
        self.query_builder = QueryBuilder()
        self.mapper = AsyncEntityMapper(graph=graph, query_builder=self.query_builder)

        # Identity map: (Type, id) -> entity instance
        self._identity_map: Dict[Tuple[Type, Any], Any] = {}

        # Track entity states
        self._new: Set[Any] = set()  # Entities to INSERT
        self._dirty: Set[Any] = set()  # Entities to UPDATE
        self._deleted: Set[Any] = set()  # Entities to DELETE

        # Track original state for dirty checking
        self._original_state: Dict[int, Dict[str, Any]] = {}

        # Transaction state
        self._in_transaction = False
        self._closed = False

    async def __aenter__(self) -> "AsyncSession":
        """Enter async context manager."""
        self._in_transaction = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        if exc_type is None:
            # No exception - commit changes
            try:
                await self.commit()
            except Exception:
                await self.rollback()
                raise
        else:
            # Exception occurred - rollback
            await self.rollback()

        await self.close()
        return False  # Propagate exceptions

    def add(self, entity: Any) -> None:
        """
        Mark entity for insertion.

        Args:
            entity: Entity instance to add

        Example:
            >>> person = Person(name="Alice", age=25)
            >>> session.add(person)
            >>> await session.commit()  # INSERT executed here
        """
        if self._closed:
            raise RuntimeError("Session is closed")

        # Check if already tracked
        id(entity)
        if entity in self._deleted:
            self._deleted.remove(entity)
            self._dirty.add(entity)
        elif entity not in self._dirty and entity not in self._new:
            self._new.add(entity)
            # Capture original state
            self._capture_state(entity)

    def delete(self, entity: Any) -> None:
        """
        Mark entity for deletion.

        Args:
            entity: Entity instance to delete

        Example:
            >>> person = await session.get(Person, 1)
            >>> session.delete(person)
            >>> await session.commit()  # DELETE executed here
        """
        if self._closed:
            raise RuntimeError("Session is closed")

        # Remove from new/dirty if present
        if entity in self._new:
            self._new.discard(entity)
        else:
            self._dirty.discard(entity)
            self._deleted.add(entity)

        # Remove from identity map
        metadata = get_entity_metadata(type(entity))
        if metadata and metadata.id_property:
            entity_id = getattr(entity, metadata.id_property.python_name, None)
            if entity_id is not None:
                key = (type(entity), entity_id)
                self._identity_map.pop(key, None)

    async def get(self, entity_class: Type[T], entity_id: Any) -> Optional[T]:
        """
        Get entity by ID, using identity map if available.

        Args:
            entity_class: Entity class type
            entity_id: ID value

        Returns:
            Entity instance if found, None otherwise

        Example:
            >>> person = await session.get(Person, 1)
            >>> # Subsequent calls return same instance
            >>> same_person = await session.get(Person, 1)
            >>> assert person is same_person
        """
        if self._closed:
            raise RuntimeError("Session is closed")

        # Check identity map first
        key = (entity_class, entity_id)
        if key in self._identity_map:
            return self._identity_map[key]

        # Load from database
        metadata = self.mapper.get_entity_metadata(entity_class)
        cypher, params = self.query_builder.build_match_by_id_query(metadata, entity_id)

        try:
            result = await self.graph.query(cypher, params)

            if not result.result_set:
                return None

            # Map entity
            record = result.result_set[0]
            entity = self.mapper.map_from_record(record, entity_class, header=result.header)

            # Add to identity map
            self._identity_map[key] = entity

            # Capture original state for change tracking
            self._capture_state(entity)

            return entity

        except Exception as e:
            raise QueryException(f"Failed to get entity: {e}") from e

    async def flush(self) -> None:
        """
        Execute all pending operations without committing transaction.

        Processes:
        1. INSERTs for new entities
        2. UPDATEs for dirty entities
        3. DELETEs for deleted entities

        Example:
            >>> session.add(person1)
            >>> await session.flush()  # Execute INSERT
            >>> session.add(person2)
            >>> await session.commit()  # Execute second INSERT and commit
        """
        if self._closed:
            raise RuntimeError("Session is closed")

        try:
            # Process new entities (INSERTs)
            for entity in list(self._new):
                await self._insert_entity(entity)
            self._new.clear()

            # Process dirty entities (UPDATEs)
            for entity in list(self._dirty):
                if self._is_entity_modified(entity):
                    await self._update_entity(entity)
                    # Update original state
                    self._capture_state(entity)
            self._dirty.clear()

            # Process deleted entities (DELETEs)
            for entity in list(self._deleted):
                await self._delete_entity(entity)
            self._deleted.clear()

        except Exception as e:
            raise QueryException(f"Failed to flush session: {e}") from e

    async def commit(self) -> None:
        """
        Flush changes and commit transaction.

        Example:
            >>> async with AsyncSession(graph) as session:
            ...     session.add(person)
            ...     await session.commit()  # Changes persisted
        """
        if self._closed:
            raise RuntimeError("Session is closed")

        await self.flush()
        # Note: FalkorDB doesn't have explicit transaction commit
        # All queries are auto-committed

    async def rollback(self) -> None:
        """
        Discard all pending changes.

        Example:
            >>> session.add(person)
            >>> await session.rollback()  # Changes discarded
            >>> # person not saved to database
        """
        if self._closed:
            raise RuntimeError("Session is closed")

        # Clear all pending operations
        self._new.clear()
        self._dirty.clear()
        self._deleted.clear()

        # Restore original states for entities in identity map
        for entity in self._identity_map.values():
            entity_id = id(entity)
            if entity_id in self._original_state:
                self._restore_state(entity)

    async def close(self) -> None:
        """
        Close session and release resources.

        Example:
            >>> session = AsyncSession(graph)
            >>> try:
            ...     session.add(person)
            ...     await session.commit()
            ... finally:
            ...     await session.close()
        """
        if not self._closed:
            self._identity_map.clear()
            self._new.clear()
            self._dirty.clear()
            self._deleted.clear()
            self._original_state.clear()
            self._closed = True
            self._in_transaction = False

    def _capture_state(self, entity: Any) -> None:
        """
        Capture current state of entity for change tracking.

        Args:
            entity: Entity to capture state for
        """
        entity_id = id(entity)
        metadata = get_entity_metadata(type(entity))

        if metadata:
            state = {}
            for prop in metadata.properties:
                value = getattr(entity, prop.python_name, None)
                # Deep copy to detect changes
                if value is not None:
                    try:
                        state[prop.python_name] = copy.deepcopy(value)
                    except Exception:
                        # If can't deep copy, store reference
                        state[prop.python_name] = value

            self._original_state[entity_id] = state

    def _restore_state(self, entity: Any) -> None:
        """
        Restore entity to original state.

        Args:
            entity: Entity to restore
        """
        entity_id = id(entity)
        if entity_id in self._original_state:
            state = self._original_state[entity_id]
            for prop_name, value in state.items():
                setattr(entity, prop_name, value)

    def _is_entity_modified(self, entity: Any) -> bool:
        """
        Check if entity has been modified since loading.

        Args:
            entity: Entity to check

        Returns:
            True if entity has been modified
        """
        entity_id = id(entity)
        if entity_id not in self._original_state:
            return True  # Assume modified if no original state

        original = self._original_state[entity_id]
        metadata = get_entity_metadata(type(entity))

        if metadata:
            for prop in metadata.properties:
                current_value = getattr(entity, prop.python_name, None)
                original_value = original.get(prop.python_name)

                if current_value != original_value:
                    return True

        return False

    async def _insert_entity(self, entity: Any) -> None:
        """
        Insert new entity into database.

        Args:
            entity: Entity to insert
        """
        cypher, params = self.mapper.map_to_cypher_create(entity)
        result = await self.graph.query(cypher, params)

        # Update entity ID
        if result.result_set:
            node_id = result.result_set[0][1]  # node_id column
            metadata = get_entity_metadata(type(entity))
            if metadata and metadata.id_property:
                self.mapper.update_entity_id(entity, node_id)

                # Add to identity map
                key = (type(entity), node_id)
                self._identity_map[key] = entity

    async def _update_entity(self, entity: Any) -> None:
        """
        Update existing entity in database.

        Args:
            entity: Entity to update
        """
        cypher, params = self.mapper.map_to_cypher_merge(entity)
        await self.graph.query(cypher, params)

    async def _delete_entity(self, entity: Any) -> None:
        """
        Delete entity from database.

        Args:
            entity: Entity to delete
        """
        metadata = get_entity_metadata(type(entity))
        if not metadata or not metadata.id_property:
            raise EntityNotFoundException("Entity has no ID property")

        entity_id = getattr(entity, metadata.id_property.python_name, None)
        if entity_id is None:
            raise EntityNotFoundException("Entity has no ID value")

        cypher, params = self.query_builder.build_delete_by_id_query(metadata, entity_id)
        await self.graph.query(cypher, params)

    @property
    def is_active(self) -> bool:
        """
        Check if session is active.

        Returns:
            True if session is not closed
        """
        return not self._closed

    @property
    def has_pending_changes(self) -> bool:
        """
        Check if session has pending changes.

        Returns:
            True if there are unsaved changes
        """
        return bool(self._new or self._dirty or self._deleted)
