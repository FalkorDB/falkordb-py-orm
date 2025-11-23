"""Repository pattern for entity data access."""

from typing import Any, Callable, Dict, Generic, Iterable, List, Optional, Type, TypeVar

from .exceptions import EntityNotFoundException, QueryException
from .mapper import EntityMapper
from .metadata import EntityMetadata
from .query_builder import QueryBuilder
from .query_parser import QueryParser, QuerySpec, Operation

T = TypeVar("T")


class Repository(Generic[T]):
    """
    Base repository for entity data access.

    Provides CRUD operations and query methods for entities.

    Type Parameters:
        T: Entity type
    """

    def __init__(self, graph: Any, entity_class: Type[T]):
        """
        Initialize repository.

        Args:
            graph: FalkorDB graph instance
            entity_class: Entity class type
        """
        self.graph = graph
        self.entity_class = entity_class
        self.query_builder = QueryBuilder()
        self.mapper = EntityMapper(graph=graph, query_builder=self.query_builder)
        self.query_parser = QueryParser()
        self.metadata: EntityMetadata = self.mapper.get_entity_metadata(entity_class)
        self._query_spec_cache: Dict[str, QuerySpec] = {}

        # Initialize relationship manager
        from .relationships import RelationshipManager

        self.relationship_manager = RelationshipManager(
            graph=graph, mapper=self.mapper, query_builder=self.query_builder
        )

    def save(self, entity: T) -> T:
        """
        Save or update entity.

        If entity has an ID, performs MERGE (update), otherwise CREATE (insert).

        Args:
            entity: Entity instance to save

        Returns:
            Saved entity with ID populated

        Raises:
            QueryException: If save operation fails
        """
        # Check if entity has ID
        has_id = False
        if self.metadata.id_property:
            entity_id = getattr(entity, self.metadata.id_property.python_name, None)
            has_id = entity_id is not None

        try:
            if has_id:
                # Update existing entity
                cypher, params = self.mapper.map_to_cypher_merge(entity)
            else:
                # Create new entity
                cypher, params = self.mapper.map_to_cypher_create(entity)

            result = self.graph.query(cypher, params)

            # Extract the returned node ID
            if result.result_set:
                record = result.result_set[0]
                # node = record[0]  # 'n' - not used
                node_id = record[1]  # 'node_id'

                # Update entity's ID if it was auto-generated
                if not has_id and self.metadata.id_property:
                    self.mapper.update_entity_id(entity, node_id)

                # Save relationships if any are set
                if self.metadata.relationships:
                    self.relationship_manager.save_relationships(
                        source_entity=entity, source_id=node_id, metadata=self.metadata
                    )

            return entity

        except Exception as e:
            raise QueryException(f"Failed to save entity: {e}") from e

    def save_all(self, entities: Iterable[T]) -> List[T]:
        """
        Save multiple entities.

        Args:
            entities: Iterable of entities to save

        Returns:
            List of saved entities
        """
        return [self.save(entity) for entity in entities]

    def find_by_id(self, entity_id: Any, fetch: Optional[List[str]] = None) -> Optional[T]:
        """
        Find entity by ID.

        Args:
            entity_id: ID value to search for
            fetch: Optional list of relationship names to eagerly load

        Returns:
            Entity instance if found, None otherwise

        Raises:
            QueryException: If query execution fails
        """
        try:
            # Use eager loading if fetch hints provided
            if fetch:
                cypher, params = self.query_builder.build_eager_loading_query(
                    self.metadata, entity_id, fetch
                )

                result = self.graph.query(cypher, params)

                if not result.result_set:
                    return None

                record = result.result_set[0]
                return self.mapper.map_with_relationships(record, self.entity_class, fetch)
            else:
                # Standard lazy loading
                cypher, params = self.query_builder.build_match_by_id_query(
                    self.metadata, entity_id
                )

                result = self.graph.query(cypher, params)

                if not result.result_set:
                    return None

                record = result.result_set[0]
                return self.mapper.map_from_record(record, self.entity_class)

        except Exception as e:
            raise QueryException(f"Failed to find entity by ID: {e}") from e

    def find_all(self, fetch: Optional[List[str]] = None) -> List[T]:
        """
        Find all entities.

        Args:
            fetch: Optional list of relationship names to eagerly load

        Returns:
            List of all entities

        Raises:
            QueryException: If query execution fails
        """
        try:
            # Use eager loading if fetch hints provided
            if fetch:
                cypher, params = self.query_builder.build_eager_loading_query_all(
                    self.metadata, fetch
                )

                result = self.graph.query(cypher, params)

                entities: List[T] = []
                for record in result.result_set:
                    entity = self.mapper.map_with_relationships(record, self.entity_class, fetch)
                    entities.append(entity)

                return entities
            else:
                # Standard lazy loading
                cypher, params = self.query_builder.build_match_all_query(self.metadata)

                result = self.graph.query(cypher, params)

                entities: List[T] = []
                for record in result.result_set:
                    entity = self.mapper.map_from_record(record, self.entity_class)
                    entities.append(entity)

                return entities

        except Exception as e:
            raise QueryException(f"Failed to find all entities: {e}") from e

    def find_all_by_id(self, ids: Iterable[Any]) -> List[T]:
        """
        Find multiple entities by their IDs.

        Args:
            ids: Iterable of ID values

        Returns:
            List of found entities
        """
        entities: List[T] = []
        for entity_id in ids:
            entity = self.find_by_id(entity_id)
            if entity:
                entities.append(entity)
        return entities

    def exists_by_id(self, entity_id: Any) -> bool:
        """
        Check if entity exists by ID.

        Args:
            entity_id: ID value to check

        Returns:
            True if entity exists, False otherwise

        Raises:
            QueryException: If query execution fails
        """
        try:
            cypher, params = self.query_builder.build_exists_by_id_query(self.metadata, entity_id)

            result = self.graph.query(cypher, params)

            if result.result_set:
                return result.result_set[0][0]  # 'exists' column

            return False

        except Exception as e:
            raise QueryException(f"Failed to check if entity exists: {e}") from e

    def count(self) -> int:
        """
        Count all entities.

        Returns:
            Number of entities

        Raises:
            QueryException: If query execution fails
        """
        try:
            cypher, params = self.query_builder.build_count_query(self.metadata)

            result = self.graph.query(cypher, params)

            if result.result_set:
                return result.result_set[0][0]  # 'count' column

            return 0

        except Exception as e:
            raise QueryException(f"Failed to count entities: {e}") from e

    def sum(self, property_name: str) -> float:
        """
        Sum values of a numeric property across all entities.

        Args:
            property_name: Name of the property to sum

        Returns:
            Sum of property values

        Raises:
            QueryException: If query execution fails
        """
        try:
            labels_str = ":".join(self.metadata.labels)
            cypher = f"MATCH (n:{labels_str}) RETURN sum(n.{property_name}) as total"

            result = self.graph.query(cypher, {})

            if result.result_set and result.result_set[0][0] is not None:
                return float(result.result_set[0][0])

            return 0.0

        except Exception as e:
            raise QueryException(f"Failed to sum property '{property_name}': {e}") from e

    def avg(self, property_name: str) -> float:
        """
        Calculate average of a numeric property across all entities.

        Args:
            property_name: Name of the property to average

        Returns:
            Average of property values

        Raises:
            QueryException: If query execution fails
        """
        try:
            labels_str = ":".join(self.metadata.labels)
            cypher = f"MATCH (n:{labels_str}) RETURN avg(n.{property_name}) as average"

            result = self.graph.query(cypher, {})

            if result.result_set and result.result_set[0][0] is not None:
                return float(result.result_set[0][0])

            return 0.0

        except Exception as e:
            raise QueryException(f"Failed to average property '{property_name}': {e}") from e

    def min(self, property_name: str) -> Any:
        """
        Find minimum value of a property across all entities.

        Args:
            property_name: Name of the property

        Returns:
            Minimum property value

        Raises:
            QueryException: If query execution fails
        """
        try:
            labels_str = ":".join(self.metadata.labels)
            cypher = f"MATCH (n:{labels_str}) RETURN min(n.{property_name}) as minimum"

            result = self.graph.query(cypher, {})

            if result.result_set:
                return result.result_set[0][0]

            return None

        except Exception as e:
            raise QueryException(f"Failed to find min of property '{property_name}': {e}") from e

    def max(self, property_name: str) -> Any:
        """
        Find maximum value of a property across all entities.

        Args:
            property_name: Name of the property

        Returns:
            Maximum property value

        Raises:
            QueryException: If query execution fails
        """
        try:
            labels_str = ":".join(self.metadata.labels)
            cypher = f"MATCH (n:{labels_str}) RETURN max(n.{property_name}) as maximum"

            result = self.graph.query(cypher, {})

            if result.result_set:
                return result.result_set[0][0]

            return None

        except Exception as e:
            raise QueryException(f"Failed to find max of property '{property_name}': {e}") from e

    def delete(self, entity: T) -> None:
        """
        Delete entity.

        Args:
            entity: Entity instance to delete

        Raises:
            EntityNotFoundException: If entity has no ID
            QueryException: If delete operation fails
        """
        if self.metadata.id_property is None:
            raise EntityNotFoundException("Entity has no ID property")

        entity_id = getattr(entity, self.metadata.id_property.python_name, None)
        if entity_id is None:
            raise EntityNotFoundException("Entity has no ID value")

        self.delete_by_id(entity_id)

    def delete_by_id(self, entity_id: Any) -> None:
        """
        Delete entity by ID.

        Args:
            entity_id: ID value of entity to delete

        Raises:
            QueryException: If delete operation fails
        """
        try:
            cypher, params = self.query_builder.build_delete_by_id_query(self.metadata, entity_id)

            self.graph.query(cypher, params)

        except Exception as e:
            raise QueryException(f"Failed to delete entity: {e}") from e

    def delete_all(self, entities: Optional[Iterable[T]] = None) -> None:
        """
        Delete multiple entities or all entities.

        Args:
            entities: Optional iterable of entities to delete.
                     If None, deletes all entities of this type.

        Raises:
            QueryException: If delete operation fails
        """
        if entities is None:
            # Delete all entities
            try:
                cypher, params = self.query_builder.build_delete_all_query(self.metadata)
                self.graph.query(cypher, params)
            except Exception as e:
                raise QueryException(f"Failed to delete all entities: {e}") from e
        else:
            # Delete specific entities
            for entity in entities:
                self.delete(entity)

    def __getattr__(self, name: str) -> Callable:
        """
        Dynamic method resolution for derived queries.

        Intercepts calls to methods like find_by_name(), count_by_age_greater_than(), etc.
        and automatically generates and executes the appropriate Cypher query.

        Args:
            name: Method name being called

        Returns:
            Callable that executes the derived query

        Raises:
            AttributeError: If method name doesn't match derived query pattern
        """
        # Check if this looks like a derived query method
        if name.startswith(("find_", "count_", "exists_", "delete_")):
            return self._create_derived_query_method(name)

        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def _create_derived_query_method(self, method_name: str) -> Callable:
        """
        Create a callable for a derived query method.

        Args:
            method_name: The method name to create a callable for

        Returns:
            Callable that executes the derived query
        """

        def derived_query_method(*args: Any, **kwargs: Any) -> Any:
            # Parse method name (with caching)
            if method_name not in self._query_spec_cache:
                try:
                    spec = self.query_parser.parse_method_name(method_name)
                    self._query_spec_cache[method_name] = spec
                except Exception as e:
                    raise QueryException(f"Failed to parse method name '{method_name}': {e}") from e
            else:
                spec = self._query_spec_cache[method_name]

            # Validate parameter count
            expected_params = sum(cond.param_count for cond in spec.conditions)
            provided_params = len(args)

            if provided_params != expected_params:
                raise QueryException(
                    f"Method '{method_name}' expects {expected_params} parameter(s), "
                    f"but {provided_params} were provided"
                )

            # Build and execute query
            try:
                cypher, params = self.query_builder.build_derived_query(
                    self.metadata, spec, list(args)
                )

                result = self.graph.query(cypher, params)

                # Return results based on operation type
                if spec.operation == Operation.FIND:
                    entities: List[T] = []
                    for record in result.result_set:
                        entity = self.mapper.map_from_record(record, self.entity_class)
                        entities.append(entity)
                    return entities

                elif spec.operation == Operation.COUNT:
                    if result.result_set:
                        return result.result_set[0][0]  # count column
                    return 0

                elif spec.operation == Operation.EXISTS:
                    if result.result_set:
                        return result.result_set[0][0]  # exists column
                    return False

                elif spec.operation == Operation.DELETE:
                    return None  # DELETE doesn't return anything

            except Exception as e:
                raise QueryException(f"Failed to execute derived query '{method_name}': {e}") from e

        return derived_query_method
