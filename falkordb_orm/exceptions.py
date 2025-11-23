"""Custom exceptions for falkordb-orm."""
from typing import Optional, Any


class FalkorDBORMException(Exception):
    """Base exception for all falkordb-orm exceptions.
    
    Attributes:
        message: The error message
        details: Additional context about the error
    """
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format the error message with details."""
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message


class EntityNotFoundException(FalkorDBORMException):
    """Raised when an entity is not found in the database.
    
    Example:
        >>> raise EntityNotFoundException(
        ...     "Person with id 123 not found",
        ...     {"entity_type": "Person", "id": 123}
        ... )
    """
    
    def __init__(
        self,
        message: str = "Entity not found",
        entity_type: Optional[str] = None,
        entity_id: Optional[Any] = None,
        **kwargs: Any
    ):
        details = {"entity_type": entity_type, "entity_id": entity_id, **kwargs}
        details = {k: v for k, v in details.items() if v is not None}
        super().__init__(message, details)


class InvalidEntityException(FalkorDBORMException):
    """Raised when an entity is invalid or improperly configured.
    
    Example:
        >>> raise InvalidEntityException(
        ...     "Entity missing required field 'name'",
        ...     {"entity_type": "Person", "field": "name"}
        ... )
    """
    pass


class MappingException(FalkorDBORMException):
    """Raised when there's an error mapping between entities and graph structures.
    
    Example:
        >>> raise MappingException(
        ...     "Cannot convert value to target type",
        ...     {"field": "age", "value": "invalid", "target_type": "int"}
        ... )
    """
    pass


class QueryException(FalkorDBORMException):
    """Raised when there's an error building or executing a query.
    
    Example:
        >>> raise QueryException(
        ...     "Invalid query method name",
        ...     {"method_name": "find_by_invalid_field", "cypher": "..."}
        ... )
    """
    
    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        params: Optional[dict[str, Any]] = None,
        **kwargs: Any
    ):
        details = {"query": query, "params": params, **kwargs}
        details = {k: v for k, v in details.items() if v is not None}
        super().__init__(message, details)


class MetadataException(FalkorDBORMException):
    """Raised when there's an error with entity metadata.
    
    Example:
        >>> raise MetadataException(
        ...     "Entity class not decorated with @node",
        ...     {"class_name": "Person"}
        ... )
    """
    pass


class ValidationException(FalkorDBORMException):
    """Raised when entity validation fails.
    
    Example:
        >>> raise ValidationException(
        ...     "Field validation failed",
        ...     {"field": "email", "value": "invalid", "constraint": "email format"}
        ... )
    """
    pass


class RelationshipException(FalkorDBORMException):
    """Raised when there's an error with relationship operations.
    
    Example:
        >>> raise RelationshipException(
        ...     "Cannot load relationship",
        ...     {"relationship": "friends", "source_id": 123}
        ... )
    """
    pass


class ConfigurationException(FalkorDBORMException):
    """Raised when there's an error with ORM configuration.
    
    Example:
        >>> raise ConfigurationException(
        ...     "Invalid relationship direction",
        ...     {"direction": "INVALID", "valid_values": ["INCOMING", "OUTGOING", "BOTH"]}
        ... )
    """
    pass


class TransactionException(FalkorDBORMException):
    """Raised when there's an error with transaction operations.
    
    Example:
        >>> raise TransactionException(
        ...     "Transaction already committed",
        ...     {"transaction_id": "abc123"}
        ... )
    """
    pass
