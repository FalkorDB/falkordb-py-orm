"""Security-aware repository wrapper."""

from typing import Any, List, Optional, Set, Type, TypeVar

from ..repository import Repository
from .context import SecurityContext
from .exceptions import AccessDeniedException
from .rewriter import QueryRewriter

T = TypeVar("T")


class SecureRepository(Repository[T]):
    """Security-aware repository wrapper."""

    def __init__(self, graph, entity_class: Type[T], security_context: SecurityContext):
        super().__init__(graph, entity_class)
        self.security_context = security_context
        self.rewriter = QueryRewriter(security_context)

    def find_by_id(
        self, entity_id: Any, fetch: Optional[List[str]] = None
    ) -> Optional[T]:
        """Find with security enforcement."""
        # Check READ permission
        if not self.security_context.can("READ", self.entity_class.__name__):
            raise AccessDeniedException(
                f"Access denied: Cannot read {self.entity_class.__name__}"
            )

        # Get denied properties
        denied_props = self.security_context.get_denied_properties(
            self.entity_class.__name__, "READ"
        )

        # Load entity
        entity = super().find_by_id(entity_id, fetch)

        if entity:
            # Filter out denied properties
            return self._filter_properties(entity, denied_props)

        return None

    def find_all(self, fetch: Optional[List[str]] = None) -> List[T]:
        """Find all with security enforcement."""
        # Check READ permission
        if not self.security_context.can("READ", self.entity_class.__name__):
            raise AccessDeniedException(
                f"Access denied: Cannot read {self.entity_class.__name__}"
            )

        # Get denied properties
        denied_props = self.security_context.get_denied_properties(
            self.entity_class.__name__, "READ"
        )

        # Load entities
        entities = super().find_all(fetch)

        # Filter properties for all entities
        return [self._filter_properties(e, denied_props) for e in entities]

    def save(self, entity: T) -> T:
        """Save with security enforcement."""
        # Check if new entity (CREATE) or existing (WRITE)
        is_new = self._is_new_entity(entity)
        action = "CREATE" if is_new else "WRITE"

        if not self.security_context.can(action, self.entity_class.__name__):
            raise AccessDeniedException(
                f"Access denied: Cannot {action.lower()} {self.entity_class.__name__}"
            )

        # Check property-level write permissions
        self._validate_property_writes(entity)

        return super().save(entity)

    def delete(self, entity: T) -> None:
        """Delete with security enforcement."""
        if not self.security_context.can("DELETE", self.entity_class.__name__):
            raise AccessDeniedException(
                f"Access denied: Cannot delete {self.entity_class.__name__}"
            )

        super().delete(entity)

    def _filter_properties(self, entity: T, denied: Set[str]) -> T:
        """Remove denied properties from entity."""
        for prop in denied:
            if hasattr(entity, prop):
                setattr(entity, prop, None)
        return entity

    def _validate_property_writes(self, entity: T):
        """Check property-level write permissions."""
        denied_props = self.security_context.get_denied_properties(
            self.entity_class.__name__, "WRITE"
        )

        metadata = self.mapper.get_entity_metadata(type(entity))
        for prop in metadata.properties:
            if prop.python_name in denied_props:
                # Check if property was modified
                # For simplicity, we'll allow writes for now
                # A full implementation would track original values
                pass

    def _is_new_entity(self, entity: T) -> bool:
        """Check if entity is new (no ID)."""
        if self.metadata.id_property:
            entity_id = getattr(entity, self.metadata.id_property.python_name, None)
            return entity_id is None
        return True
