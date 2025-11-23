"""Custom query decorator for user-defined Cypher queries."""

import inspect
from typing import Any, Callable, Optional, Type, TypeVar, get_type_hints

T = TypeVar("T")


class QueryMethod:
    """Descriptor for custom query methods."""

    def __init__(
        self,
        cypher: str,
        returns: Optional[Type] = None,
        write: bool = False,
        method: Optional[Callable] = None,
    ):
        """
        Initialize custom query method.

        Args:
            cypher: Cypher query with $param placeholders
            returns: Expected return type (entity class, primitive, or None)
            write: Whether query performs write operations
            method: Original method (for extracting signature)
        """
        self.cypher = cypher
        self.returns = returns
        self.write = write
        self.method = method
        self._param_names: Optional[list] = None

    def __set_name__(self, owner: Type, name: str) -> None:
        """Called when descriptor is assigned to class attribute."""
        self.name = name

    def __get__(self, instance: Any, owner: Type) -> Callable:
        """Return bound method when accessed."""
        if instance is None:
            return self

        # Return a bound method
        def bound_method(*args: Any, **kwargs: Any) -> Any:
            return self._execute_query(instance, args, kwargs)

        return bound_method

    def _execute_query(self, repository: Any, args: tuple, kwargs: dict) -> Any:
        """
        Execute the custom query.

        Args:
            repository: Repository instance
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Query results based on returns type
        """
        # Build parameters from args and kwargs
        params = self._build_parameters(args, kwargs)

        # Execute query
        result = repository.graph.query(self.cypher, params)

        # Map results based on returns type
        return self._map_results(result, repository)

    def _build_parameters(self, args: tuple, kwargs: dict) -> dict:
        """
        Build parameter dictionary from method arguments.

        Args:
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Parameter dictionary for Cypher query
        """
        params = {}

        # Get parameter names from method signature
        if self.method:
            sig = inspect.signature(self.method)
            param_names = [name for name in sig.parameters.keys() if name != "self"]

            # Map positional args to parameter names
            for i, arg in enumerate(args):
                if i < len(param_names):
                    params[param_names[i]] = arg

        # Add keyword arguments
        params.update(kwargs)

        return params

    def _map_results(self, result: Any, repository: Any) -> Any:
        """
        Map query results to appropriate Python types.

        Args:
            result: Query result from FalkorDB
            repository: Repository instance

        Returns:
            Mapped results
        """
        if not result.result_set:
            # No results
            if self.returns is None:
                return None
            elif self.returns in (int, float, str, bool):
                return 0 if self.returns in (int, float) else None
            else:
                return []

        # No return type specified - return raw results
        if self.returns is None:
            return None

        # Primitive return types
        if self.returns in (int, float, str, bool):
            return result.result_set[0][0]

        # Entity return type - map to objects
        if hasattr(self.returns, "__node_metadata__"):
            entities = []
            for record in result.result_set:
                # Assume first column is the entity node
                entity = repository.mapper.map_from_record(
                    record, self.returns, var_name=self._get_var_name()
                )
                entities.append(entity)
            return entities

        # List return type
        if hasattr(self.returns, "__origin__"):
            # Handle List[Entity] and similar generic types
            origin = getattr(self.returns, "__origin__", None)
            if origin is list:
                args = getattr(self.returns, "__args__", ())
                if args and hasattr(args[0], "__node_metadata__"):
                    entity_type = args[0]
                    entities = []
                    for record in result.result_set:
                        entity = repository.mapper.map_from_record(
                            record, entity_type, var_name=self._get_var_name()
                        )
                        entities.append(entity)
                    return entities

        # Default: return first column of all rows
        return [record[0] for record in result.result_set]

    def _get_var_name(self) -> str:
        """Extract variable name from Cypher RETURN clause."""
        # Simple heuristic: look for RETURN statement and extract first variable
        cypher_upper = self.cypher.upper()
        if "RETURN" in cypher_upper:
            return_idx = cypher_upper.rfind("RETURN")
            after_return = self.cypher[return_idx + 6 :].strip()
            # Extract first word/identifier
            var_name = after_return.split()[0].split(",")[0].strip()
            # Remove any AS alias
            if " AS " in var_name.upper():
                var_name = var_name.split()[0]
            return var_name
        return "n"  # Default fallback


def query(
    cypher: str, returns: Optional[Type] = None, write: bool = False
) -> Callable[[Callable], QueryMethod]:
    """
    Decorator for custom Cypher query methods.

    Args:
        cypher: Cypher query with $param placeholders
        returns: Expected return type (entity class, primitive, or None)
        write: Whether query performs write operations (default: False)

    Returns:
        Decorated method that executes custom query

    Example:
        >>> class PersonRepository(Repository[Person]):
        ...     @query(
        ...         "MATCH (p:Person)-[:KNOWS]->(f:Person) WHERE p.name = $name RETURN f",
        ...         returns=Person
        ...     )
        ...     def find_friends(self, name: str) -> List[Person]:
        ...         pass
        ...
        ...     @query(
        ...         "MATCH (p:Person) WHERE p.age > $min AND p.age < $max RETURN p",
        ...         returns=Person
        ...     )
        ...     def find_by_age_range(self, min: int, max: int) -> List[Person]:
        ...         pass
        ...
        ...     @query(
        ...         "MATCH (p:Person) RETURN count(p)",
        ...         returns=int
        ...     )
        ...     def count_all(self) -> int:
        ...         pass
    """

    def decorator(method: Callable) -> QueryMethod:
        return QueryMethod(cypher=cypher, returns=returns, write=write, method=method)

    return decorator
