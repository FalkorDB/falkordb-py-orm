"""Global entity class registry for resolving forward references."""

from typing import Dict, Type, Optional

# Global registry mapping class names to entity classes
_entity_registry: Dict[str, Type] = {}


def register_entity(class_name: str, entity_class: Type) -> None:
    """
    Register an entity class in the global registry.
    
    Args:
        class_name: Name of the class
        entity_class: The entity class type
    """
    _entity_registry[class_name] = entity_class


def get_entity_class(class_name: str) -> Optional[Type]:
    """
    Get an entity class from the registry by name.
    
    Args:
        class_name: Name of the class
        
    Returns:
        Entity class if registered, None otherwise
    """
    return _entity_registry.get(class_name)


def clear_registry() -> None:
    """Clear the entity registry (mainly for testing)."""
    _entity_registry.clear()
