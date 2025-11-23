"""Decorators for entity mapping."""

import inspect
from typing import Any, Callable, List, Optional, Type, TypeVar, Union, get_type_hints, get_origin, get_args

from .exceptions import InvalidEntityException
from .metadata import EntityMetadata, PropertyMetadata, RelationshipMetadata

T = TypeVar('T')


class PropertyDescriptor:
    """Descriptor for property mapping."""
    
    def __init__(
        self,
        name: Optional[str] = None,
        converter: Optional[Callable] = None,
        required: bool = False,
        interned: bool = False
    ):
        self.name = name
        self.converter = converter
        self.required = required
        self.interned = interned
        self._python_name: Optional[str] = None
        self._attr_name = f"_property_{id(self)}"
    
    def __set_name__(self, owner: Type, name: str) -> None:
        """Called when the descriptor is assigned to a class attribute."""
        self._python_name = name
    
    def __get__(self, instance: Any, owner: Type) -> Any:
        if instance is None:
            return self
        return getattr(instance, self._attr_name, None)
    
    def __set__(self, instance: Any, value: Any) -> None:
        setattr(instance, self._attr_name, value)


class GeneratedIDDescriptor:
    """Descriptor for generated ID fields."""
    
    def __init__(self, generator: Optional[Callable] = None):
        self.generator = generator
        self._python_name: Optional[str] = None
        self._attr_name = f"_id_{id(self)}"
    
    def __set_name__(self, owner: Type, name: str) -> None:
        """Called when the descriptor is assigned to a class attribute."""
        self._python_name = name
    
    def __get__(self, instance: Any, owner: Type) -> Any:
        if instance is None:
            return self
        return getattr(instance, self._attr_name, None)
    
    def __set__(self, instance: Any, value: Any) -> None:
        setattr(instance, self._attr_name, value)


class RelationshipDescriptor:
    """Descriptor for relationship mapping."""
    
    def __init__(
        self,
        relationship_type: str,
        direction: str = "OUTGOING",
        target: Optional[Union[Type, str]] = None,
        lazy: bool = True,
        cascade: bool = False
    ):
        self.relationship_type = relationship_type
        self.direction = direction.upper()
        self.target = target
        self.lazy = lazy
        self.cascade = cascade
        self._python_name: Optional[str] = None
        self._attr_name = f"_relationship_{id(self)}"
        
        # Validate direction
        if self.direction not in ("OUTGOING", "INCOMING", "BOTH"):
            raise ValueError(f"Invalid direction: {direction}. Must be OUTGOING, INCOMING, or BOTH")
    
    def __set_name__(self, owner: Type, name: str) -> None:
        """Called when the descriptor is assigned to a class attribute."""
        self._python_name = name
    
    def __get__(self, instance: Any, owner: Type) -> Any:
        if instance is None:
            return self
        return getattr(instance, self._attr_name, None)
    
    def __set__(self, instance: Any, value: Any) -> None:
        setattr(instance, self._attr_name, value)


def property(
    name: Optional[str] = None,
    converter: Optional[Callable] = None,
    required: bool = False,
    interned: bool = False
) -> Any:
    """
    Map a Python attribute to a graph property.
    
    Args:
        name: Property name in graph (defaults to attribute name)
        converter: Custom type converter function
        required: Whether property is required (validation)
        interned: Whether to use FalkorDB's intern() function for string deduplication
        
    Returns:
        Property descriptor
        
    Example:
        >>> @node("Person")
        >>> class Person:
        ...     name: str = property("full_name")
        ...     email: str = property(required=True)
        ...     country: str = property(interned=True)  # Deduplicated string
    """
    return PropertyDescriptor(name=name, converter=converter, required=required, interned=interned)


def interned(name: Optional[str] = None, required: bool = False) -> Any:
    """
    Map a Python string attribute to an interned graph property.
    
    This is a convenience function that marks a string property to use FalkorDB's
    intern() function, which deduplicates the string by storing a single internal
    copy across the database. This is especially useful for repeated string values
    like country names, email domains, tags, or status values.
    
    Args:
        name: Property name in graph (defaults to attribute name)
        required: Whether property is required (validation)
        
    Returns:
        Property descriptor with interned=True
        
    Example:
        >>> @node("Person")
        >>> class Person:
        ...     id: Optional[int] = None
        ...     name: str
        ...     country: str = interned()  # Deduplicated
        ...     status: str = interned("user_status")  # Maps to 'user_status' in graph
        ...     email_domain: str = interned(required=True)
        
    Note:
        The intern() function should only be used with string properties.
        It significantly reduces memory usage for frequently repeated values.
    """
    return PropertyDescriptor(name=name, converter=None, required=required, interned=True)


def generated_id(generator: Optional[Callable] = None) -> Any:
    """
    Mark field as auto-generated ID.
    
    Args:
        generator: Custom ID generator function (defaults to FalkorDB internal ID)
        
    Returns:
        Generated ID descriptor
        
    Example:
        >>> @node("Person")
        >>> class Person:
        ...     id: Optional[int] = generated_id()
        ...     name: str
    """
    return GeneratedIDDescriptor(generator=generator)


def relationship(
    relationship_type: str,
    direction: str = "OUTGOING",
    target: Optional[Union[Type, str]] = None,
    lazy: bool = True,
    cascade: bool = False
) -> Any:
    """
    Define a relationship to another entity.
    
    Args:
        relationship_type: Type of the relationship edge (e.g., 'KNOWS', 'WORKS_FOR')
        direction: Direction of relationship: 'OUTGOING', 'INCOMING', or 'BOTH'
        target: Target entity class or class name string for forward references
        lazy: Whether to use lazy loading (default: True)
        cascade: Whether to cascade save/delete operations (default: False)
        
    Returns:
        Relationship descriptor
        
    Example:
        >>> @node("Person")
        >>> class Person:
        ...     id: Optional[int] = generated_id()
        ...     name: str
        ...     friends: List['Person'] = relationship('KNOWS', target='Person')
        ...     company: Optional['Company'] = relationship('WORKS_FOR', target='Company')
    """
    return RelationshipDescriptor(
        relationship_type=relationship_type,
        direction=direction,
        target=target,
        lazy=lazy,
        cascade=cascade
    )


def node(
    labels: Optional[Union[str, List[str]]] = None,
    primary_label: Optional[str] = None
) -> Callable[[Type[T]], Type[T]]:
    """
    Decorator to mark a class as a FalkorDB node entity.
    
    Args:
        labels: Single label or list of labels for the node
        primary_label: Explicit primary label (defaults to first label or class name)
        
    Returns:
        Decorated class with entity metadata
        
    Example:
        >>> @node("Person")
        >>> class Person:
        ...     id: Optional[int] = None
        ...     name: str
        ...     age: int
        
        >>> @node(labels=["Person", "Individual"])
        >>> class Person:
        ...     pass
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Determine labels
        if labels is None:
            node_labels = [cls.__name__]
        elif isinstance(labels, str):
            node_labels = [labels]
        else:
            node_labels = list(labels)
        
        if not node_labels:
            raise InvalidEntityException(f"Entity {cls.__name__} must have at least one label")
        
        # Determine primary label
        primary = primary_label if primary_label else node_labels[0]
        
        # Extract property and relationship metadata from class
        properties: List[PropertyMetadata] = []
        relationships: List[RelationshipMetadata] = []
        id_property: Optional[PropertyMetadata] = None
        
        # Get type hints for the class
        try:
            type_hints = get_type_hints(cls)
        except Exception:
            # If get_type_hints fails (e.g., forward references), use __annotations__
            type_hints = getattr(cls, '__annotations__', {})
        
        # Scan class attributes
        for attr_name, attr_value in inspect.getmembers(cls):
            if attr_name.startswith('_'):
                continue
            
            # Check if it's a RelationshipDescriptor
            if isinstance(attr_value, RelationshipDescriptor):
                # Get type hint to determine target class and if it's a collection
                python_type = type_hints.get(attr_name, Any)
                
                # Determine if it's a collection (List) or single (Optional)
                is_collection = False
                target_class = None
                target_class_name = None
                
                # Check if type is List[T] or Optional[T]
                origin = get_origin(python_type)
                if origin is list or (hasattr(origin, '__name__') and origin.__name__ == 'list'):
                    is_collection = True
                    args = get_args(python_type)
                    if args:
                        target_type = args[0]
                        if isinstance(target_type, str):
                            target_class_name = target_type
                        else:
                            # Handle ForwardRef objects
                            if hasattr(target_type, '__forward_arg__'):
                                target_class_name = target_type.__forward_arg__
                            elif hasattr(target_type, '__name__'):
                                target_class = target_type
                                target_class_name = target_type.__name__
                            else:
                                target_class_name = str(target_type)
                elif origin is Union:
                    # Optional[T] is Union[T, None]
                    args = get_args(python_type)
                    if args:
                        # Get the non-None type
                        target_type = next((arg for arg in args if arg is not type(None)), None)
                        if target_type:
                            if isinstance(target_type, str):
                                target_class_name = target_type
                            else:
                                # Handle ForwardRef objects
                                if hasattr(target_type, '__forward_arg__'):
                                    target_class_name = target_type.__forward_arg__
                                elif hasattr(target_type, '__name__'):
                                    target_class = target_type
                                    target_class_name = target_type.__name__
                                else:
                                    target_class_name = str(target_type)
                
                # If target not determined from type hint, use descriptor's target
                if target_class is None and target_class_name is None:
                    if attr_value.target:
                        if isinstance(attr_value.target, str):
                            target_class_name = attr_value.target
                        else:
                            target_class = attr_value.target
                            target_class_name = attr_value.target.__name__ if hasattr(attr_value.target, '__name__') else str(attr_value.target)
                
                rel_meta = RelationshipMetadata(
                    python_name=attr_name,
                    relationship_type=attr_value.relationship_type,
                    direction=attr_value.direction,
                    target_class=target_class,
                    target_class_name=target_class_name,
                    is_collection=is_collection,
                    lazy=attr_value.lazy,
                    cascade=attr_value.cascade
                )
                relationships.append(rel_meta)
            
            # Check if it's a PropertyDescriptor
            elif isinstance(attr_value, PropertyDescriptor):
                graph_name = attr_value.name if attr_value.name else attr_name
                python_type = type_hints.get(attr_name, Any)
                
                prop_meta = PropertyMetadata(
                    python_name=attr_name,
                    graph_name=graph_name,
                    python_type=python_type,
                    converter=attr_value.converter,
                    required=attr_value.required,
                    is_id=False,
                    interned=attr_value.interned
                )
                properties.append(prop_meta)
            
            # Check if it's a GeneratedIDDescriptor
            elif isinstance(attr_value, GeneratedIDDescriptor):
                graph_name = "id"
                python_type = type_hints.get(attr_name, Any)
                
                prop_meta = PropertyMetadata(
                    python_name=attr_name,
                    graph_name=graph_name,
                    python_type=python_type,
                    is_id=True,
                    id_generator=attr_value.generator
                )
                properties.append(prop_meta)
                id_property = prop_meta
        
        # If no explicit ID descriptor, look for 'id' field in type hints
        if id_property is None and 'id' in type_hints:
            prop_meta = PropertyMetadata(
                python_name='id',
                graph_name='id',
                python_type=type_hints['id'],
                is_id=True
            )
            properties.append(prop_meta)
            id_property = prop_meta
        
        # Add remaining type-hinted attributes as properties (skip relationships)
        for attr_name, attr_type in type_hints.items():
            if attr_name.startswith('_'):
                continue
            
            # Skip if already processed as property or relationship
            if any(p.python_name == attr_name for p in properties):
                continue
            if any(r.python_name == attr_name for r in relationships):
                continue
            
            # Skip if it's a method or special attribute
            if hasattr(cls, attr_name) and callable(getattr(cls, attr_name)):
                continue
            
            prop_meta = PropertyMetadata(
                python_name=attr_name,
                graph_name=attr_name,
                python_type=attr_type,
                is_id=(attr_name == 'id')
            )
            properties.append(prop_meta)
            
            if attr_name == 'id' and id_property is None:
                id_property = prop_meta
        
        # Create and attach metadata
        metadata = EntityMetadata(
            entity_class=cls,
            labels=node_labels,
            primary_label=primary,
            properties=properties,
            id_property=id_property,
            relationships=relationships
        )
        
        setattr(cls, '__node_metadata__', metadata)
        
        return cls
    
    return decorator
