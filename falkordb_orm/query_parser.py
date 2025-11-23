"""Query parser for deriving Cypher queries from method names."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from .exceptions import QueryException


class Operation(Enum):
    """Query operation types."""

    FIND = "find"
    COUNT = "count"
    EXISTS = "exists"
    DELETE = "delete"


class Operator(Enum):
    """Comparison operators for query conditions."""

    EQUALS = "="
    NOT_EQUALS = "<>"
    GREATER_THAN = ">"
    GREATER_THAN_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_EQUAL = "<="
    BETWEEN = "BETWEEN"
    IN = "IN"
    NOT_IN = "NOT IN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"
    CONTAINING = "CONTAINS"
    STARTING_WITH = "STARTS WITH"
    ENDING_WITH = "ENDS WITH"
    LIKE = "=~"


class LogicalOperator(Enum):
    """Logical operators for combining conditions."""

    AND = "AND"
    OR = "OR"


@dataclass
class Condition:
    """Represents a single WHERE clause condition."""

    property_name: str
    """The property to filter on."""

    operator: Operator
    """The comparison operator."""

    param_count: int = 1
    """Number of parameters required (e.g., 2 for BETWEEN)."""


@dataclass
class OrderClause:
    """Represents an ORDER BY clause."""

    property_name: str
    """The property to sort by."""

    direction: str = "ASC"
    """Sort direction: ASC or DESC."""


@dataclass
class QuerySpec:
    """Structured representation of a derived query."""

    operation: Operation
    """The query operation (find, count, exists, delete)."""

    conditions: List[Condition] = field(default_factory=list)
    """List of WHERE conditions."""

    logical_operator: LogicalOperator = LogicalOperator.AND
    """Logical operator for combining conditions (AND/OR)."""

    ordering: List[OrderClause] = field(default_factory=list)
    """ORDER BY clauses."""

    limit: Optional[int] = None
    """Result limit (for first/top_N queries)."""


class QueryParser:
    """Parses repository method names into QuerySpec objects."""

    # Operator suffix patterns (order matters - longer matches first)
    OPERATOR_PATTERNS = [
        ("_greater_than_equal", Operator.GREATER_THAN_EQUAL),
        ("_greater_than", Operator.GREATER_THAN),
        ("_less_than_equal", Operator.LESS_THAN_EQUAL),
        ("_less_than", Operator.LESS_THAN),
        ("_is_not_null", Operator.IS_NOT_NULL),
        ("_is_null", Operator.IS_NULL),
        ("_not_in", Operator.NOT_IN),
        ("_starting_with", Operator.STARTING_WITH),
        ("_ending_with", Operator.ENDING_WITH),
        ("_containing", Operator.CONTAINING),
        ("_between", Operator.BETWEEN),
        ("_like", Operator.LIKE),
        ("_not", Operator.NOT_EQUALS),
        ("_in", Operator.IN),
    ]

    def parse_method_name(self, method_name: str) -> QuerySpec:
        """
        Parse a repository method name into a QuerySpec.

        Args:
            method_name: The method name to parse (e.g., "find_by_name_and_age")

        Returns:
            QuerySpec representing the parsed query

        Raises:
            QueryException: If the method name cannot be parsed

        Examples:
            >>> parser = QueryParser()
            >>> spec = parser.parse_method_name("find_by_name")
            >>> spec.operation
            <Operation.FIND: 'find'>

            >>> spec = parser.parse_method_name("count_by_age_greater_than")
            >>> spec.conditions[0].operator
            <Operator.GREATER_THAN: '>'>
        """
        original_name = method_name

        # Extract operation
        operation = self._extract_operation(method_name)
        if not operation:
            raise QueryException(f"Invalid query method: {original_name}")

        # Remove operation prefix
        remaining = method_name[len(operation.value) + 1 :]  # +1 for underscore

        # Extract limit (first/top_N)
        limit = self._extract_limit(remaining)
        if limit is not None:
            remaining = self._remove_limit_prefix(remaining)

        # Split by order_by if present
        parts = remaining.split("_order_by_")
        conditions_part = parts[0]
        ordering_part = parts[1] if len(parts) > 1 else None

        # Parse conditions
        if not conditions_part or conditions_part == "":
            conditions = []
            logical_op = LogicalOperator.AND
        else:
            conditions, logical_op = self._parse_conditions(conditions_part)

        # Parse ordering
        ordering = self._parse_ordering(ordering_part) if ordering_part else []

        return QuerySpec(
            operation=operation,
            conditions=conditions,
            logical_operator=logical_op,
            ordering=ordering,
            limit=limit,
        )

    def _extract_operation(self, method_name: str) -> Optional[Operation]:
        """Extract the operation from method name."""
        for op in Operation:
            if method_name.startswith(op.value + "_"):
                return op
        return None

    def _extract_limit(self, text: str) -> Optional[int]:
        """Extract limit from first/top_N prefix."""
        if text.startswith("first_"):
            return 1

        # Match top_N pattern
        match = re.match(r"top_(\d+)_", text)
        if match:
            return int(match.group(1))

        return None

    def _remove_limit_prefix(self, text: str) -> str:
        """Remove first/top_N prefix from text."""
        if text.startswith("first_"):
            return text[6:]  # Remove "first_"

        match = re.match(r"top_(\d+)_", text)
        if match:
            return text[len(match.group(0)) :]

        return text

    def _parse_conditions(self, text: str) -> tuple[List[Condition], LogicalOperator]:
        """
        Parse conditions from text like 'by_name_and_age_greater_than'.

        Returns:
            Tuple of (conditions list, logical operator)
        """
        # Remove 'by_' prefix if present
        if text.startswith("by_"):
            text = text[3:]

        # Determine logical operator
        logical_op = LogicalOperator.AND
        if "_or_" in text:
            logical_op = LogicalOperator.OR
            condition_parts = text.split("_or_")
        else:
            condition_parts = text.split("_and_")

        conditions = []
        for part in condition_parts:
            if part:
                condition = self._parse_single_condition(part)
                conditions.append(condition)

        return conditions, logical_op

    def _parse_single_condition(self, text: str) -> Condition:
        """Parse a single condition like 'age_greater_than'."""
        # Try to match operator patterns
        for suffix, operator in self.OPERATOR_PATTERNS:
            if text.endswith(suffix):
                property_name = text[: -len(suffix)]
                param_count = 2 if operator == Operator.BETWEEN else 1
                if operator in (Operator.IS_NULL, Operator.IS_NOT_NULL):
                    param_count = 0
                return Condition(
                    property_name=property_name, operator=operator, param_count=param_count
                )

        # No operator suffix - default to equals
        return Condition(property_name=text, operator=Operator.EQUALS, param_count=1)

    def _parse_ordering(self, text: str) -> List[OrderClause]:
        """
        Parse ordering from text like 'name_asc_age_desc'.

        Returns:
            List of OrderClause objects
        """
        if not text:
            return []

        ordering = []
        parts = re.split(r"_(asc|desc)_?", text)

        # Process in pairs: property_name, direction
        i = 0
        while i < len(parts) - 1:
            property_name = parts[i]
            direction = parts[i + 1].upper()

            if property_name:  # Skip empty parts
                ordering.append(OrderClause(property_name=property_name, direction=direction))

            i += 2

        return ordering
