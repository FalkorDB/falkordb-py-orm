"""Type converters for mapping between Python and graph types."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Type


class TypeConverter(ABC):
    """Abstract base class for type converters."""

    @abstractmethod
    def to_graph(self, value: Any) -> Any:
        """
        Convert Python value to graph-compatible type.

        Args:
            value: Python value to convert

        Returns:
            Graph-compatible value
        """
        pass

    @abstractmethod
    def from_graph(self, value: Any) -> Any:
        """
        Convert graph value to Python type.

        Args:
            value: Graph value to convert

        Returns:
            Python value
        """
        pass


class IdentityConverter(TypeConverter):
    """Converter that passes values through unchanged (for primitives)."""

    def to_graph(self, value: Any) -> Any:
        return value

    def from_graph(self, value: Any) -> Any:
        return value


class IntConverter(TypeConverter):
    """Converter for integer types."""

    def to_graph(self, value: Any) -> int:
        if value is None:
            return None
        return int(value)

    def from_graph(self, value: Any) -> int:
        if value is None:
            return None
        return int(value)


class FloatConverter(TypeConverter):
    """Converter for float types."""

    def to_graph(self, value: Any) -> float:
        if value is None:
            return None
        return float(value)

    def from_graph(self, value: Any) -> float:
        if value is None:
            return None
        return float(value)


class StrConverter(TypeConverter):
    """Converter for string types."""

    def to_graph(self, value: Any) -> str:
        if value is None:
            return None
        return str(value)

    def from_graph(self, value: Any) -> str:
        if value is None:
            return None
        return str(value)


class BoolConverter(TypeConverter):
    """Converter for boolean types."""

    def to_graph(self, value: Any) -> bool:
        if value is None:
            return None
        return bool(value)

    def from_graph(self, value: Any) -> bool:
        if value is None:
            return None
        return bool(value)


class TypeRegistry:
    """Registry for type converters."""

    def __init__(self) -> None:
        self._converters: Dict[Type, TypeConverter] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default type converters."""
        self._converters[str] = StrConverter()
        self._converters[int] = IntConverter()
        self._converters[float] = FloatConverter()
        self._converters[bool] = BoolConverter()

    def register(self, python_type: Type, converter: TypeConverter) -> None:
        """
        Register a type converter.

        Args:
            python_type: Python type to register converter for
            converter: TypeConverter instance
        """
        self._converters[python_type] = converter

    def get_converter(self, python_type: Type) -> TypeConverter:
        """
        Get converter for a Python type.

        Args:
            python_type: Python type to get converter for

        Returns:
            TypeConverter instance, or IdentityConverter if not found
        """
        # Handle Optional types
        if hasattr(python_type, "__origin__"):
            # For Optional[T], get the actual type T
            if (
                python_type.__origin__ is type(None)
                or str(python_type.__origin__) == "typing.Union"
            ):
                args = getattr(python_type, "__args__", ())
                for arg in args:
                    if arg is not type(None):
                        return self.get_converter(arg)

        return self._converters.get(python_type, IdentityConverter())

    def convert_to_graph(self, value: Any, python_type: Type) -> Any:
        """
        Convert value to graph-compatible type.

        Args:
            value: Python value
            python_type: Expected Python type

        Returns:
            Graph-compatible value
        """
        if value is None:
            return None
        converter = self.get_converter(python_type)
        return converter.to_graph(value)

    def convert_from_graph(self, value: Any, python_type: Type) -> Any:
        """
        Convert value from graph to Python type.

        Args:
            value: Graph value
            python_type: Target Python type

        Returns:
            Python value
        """
        if value is None:
            return None
        converter = self.get_converter(python_type)
        return converter.from_graph(value)


# Global type registry instance
_type_registry = TypeRegistry()


def register_converter(python_type: Type, converter: TypeConverter) -> None:
    """
    Register a custom type converter globally.

    Args:
        python_type: Python type to register converter for
        converter: TypeConverter instance
    """
    _type_registry.register(python_type, converter)


def get_type_registry() -> TypeRegistry:
    """Get the global type registry instance."""
    return _type_registry
