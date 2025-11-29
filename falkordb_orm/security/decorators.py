"""Security decorators for entity classes."""

from typing import Callable, Dict, List, Optional


def secured(
    read: Optional[List[str]] = None,
    write: Optional[List[str]] = None,
    create: Optional[List[str]] = None,
    delete: Optional[List[str]] = None,
    deny_read_properties: Optional[Dict[str, List[str]]] = None,
    deny_write_properties: Optional[Dict[str, List[str]]] = None,
):
    """Decorator to add security metadata to entity class.

    Examples:
        @node("Person")
        @secured(
            read=["reader", "admin"],
            write=["editor", "admin"],
            deny_read_properties={
                "ssn": ["*"],  # Nobody can read
                "salary": ["reader"]  # Reader cannot read
            }
        )
        class Person:
            id: Optional[int] = generated_id()
            name: str
            ssn: str
            salary: float
    """

    def decorator(cls):
        # Store security metadata on class
        if not hasattr(cls, "__security_metadata__"):
            cls.__security_metadata__ = {}

        cls.__security_metadata__["read_roles"] = read or []
        cls.__security_metadata__["write_roles"] = write or []
        cls.__security_metadata__["create_roles"] = create or []
        cls.__security_metadata__["delete_roles"] = delete or []
        cls.__security_metadata__["deny_read_properties"] = deny_read_properties or {}
        cls.__security_metadata__["deny_write_properties"] = (
            deny_write_properties or {}
        )

        return cls

    return decorator


def row_level_security(filter_func: Callable):
    """Decorator for row-level security filtering.

    Example:
        @node("Document")
        @row_level_security(
            filter_func=lambda user, doc: (
                doc.owner_id == user.id or
                user.has_role('admin')
            )
        )
        class Document:
            id: Optional[int] = generated_id()
            title: str
            owner_id: int
    """

    def decorator(cls):
        if not hasattr(cls, "__security_metadata__"):
            cls.__security_metadata__ = {}
        cls.__security_metadata__["row_filter"] = filter_func
        return cls

    return decorator


def secured_property(
    deny_read: Optional[List[str]] = None, deny_write: Optional[List[str]] = None
):
    """Property-level security decorator.

    Example:
        class Person:
            ssn: str = secured_property(deny_read=['reader', 'analyst'])
            salary: float = secured_property(deny_write=['viewer'])
    """

    class SecuredPropertyDescriptor:
        def __init__(self, deny_read, deny_write):
            self.deny_read = deny_read or []
            self.deny_write = deny_write or []
            self._name = None

        def __set_name__(self, owner, name):
            self._name = f"_{name}"
            # Store property-level security metadata
            if not hasattr(owner, "__security_metadata__"):
                owner.__security_metadata__ = {}
            if "property_security" not in owner.__security_metadata__:
                owner.__security_metadata__["property_security"] = {}
            owner.__security_metadata__["property_security"][name] = {
                "deny_read": self.deny_read,
                "deny_write": self.deny_write,
            }

        def __get__(self, obj, objtype=None):
            if obj is None:
                return self
            return getattr(obj, self._name, None)

        def __set__(self, obj, value):
            setattr(obj, self._name, value)

    return SecuredPropertyDescriptor(deny_read, deny_write)
