"""Tests for query parser module."""

import pytest

from falkordb_orm.query_parser import (
    QueryParser, QuerySpec, Operation, Operator, LogicalOperator
)
from falkordb_orm.exceptions import QueryException


def test_query_parser_initialization():
    """Test QueryParser initialization."""
    parser = QueryParser()
    assert parser is not None


def test_parse_simple_find_by():
    """Test parsing simple find_by_property query."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_name")
    
    assert spec.operation == Operation.FIND
    assert len(spec.conditions) == 1
    assert spec.conditions[0].property_name == "name"
    assert spec.conditions[0].operator == Operator.EQUALS
    assert spec.conditions[0].param_count == 1


def test_parse_count_by():
    """Test parsing count_by_property query."""
    parser = QueryParser()
    spec = parser.parse_method_name("count_by_age")
    
    assert spec.operation == Operation.COUNT
    assert len(spec.conditions) == 1
    assert spec.conditions[0].property_name == "age"


def test_parse_exists_by():
    """Test parsing exists_by_property query."""
    parser = QueryParser()
    spec = parser.parse_method_name("exists_by_email")
    
    assert spec.operation == Operation.EXISTS
    assert len(spec.conditions) == 1
    assert spec.conditions[0].property_name == "email"


def test_parse_delete_by():
    """Test parsing delete_by_property query."""
    parser = QueryParser()
    spec = parser.parse_method_name("delete_by_id")
    
    assert spec.operation == Operation.DELETE
    assert len(spec.conditions) == 1
    assert spec.conditions[0].property_name == "id"


def test_parse_greater_than():
    """Test parsing greater_than operator."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_age_greater_than")
    
    assert len(spec.conditions) == 1
    assert spec.conditions[0].property_name == "age"
    assert spec.conditions[0].operator == Operator.GREATER_THAN
    assert spec.conditions[0].param_count == 1


def test_parse_less_than():
    """Test parsing less_than operator."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_age_less_than")
    
    assert spec.conditions[0].operator == Operator.LESS_THAN


def test_parse_greater_than_equal():
    """Test parsing greater_than_equal operator."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_age_greater_than_equal")
    
    assert spec.conditions[0].operator == Operator.GREATER_THAN_EQUAL


def test_parse_less_than_equal():
    """Test parsing less_than_equal operator."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_age_less_than_equal")
    
    assert spec.conditions[0].operator == Operator.LESS_THAN_EQUAL


def test_parse_between():
    """Test parsing between operator."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_age_between")
    
    assert spec.conditions[0].operator == Operator.BETWEEN
    assert spec.conditions[0].param_count == 2


def test_parse_in():
    """Test parsing in operator."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_age_in")
    
    assert spec.conditions[0].operator == Operator.IN


def test_parse_not_in():
    """Test parsing not_in operator."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_age_not_in")
    
    assert spec.conditions[0].operator == Operator.NOT_IN


def test_parse_is_null():
    """Test parsing is_null operator."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_email_is_null")
    
    assert spec.conditions[0].operator == Operator.IS_NULL
    assert spec.conditions[0].param_count == 0


def test_parse_is_not_null():
    """Test parsing is_not_null operator."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_email_is_not_null")
    
    assert spec.conditions[0].operator == Operator.IS_NOT_NULL
    assert spec.conditions[0].param_count == 0


def test_parse_containing():
    """Test parsing containing operator."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_name_containing")
    
    assert spec.conditions[0].operator == Operator.CONTAINING


def test_parse_starting_with():
    """Test parsing starting_with operator."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_name_starting_with")
    
    assert spec.conditions[0].operator == Operator.STARTING_WITH


def test_parse_ending_with():
    """Test parsing ending_with operator."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_name_ending_with")
    
    assert spec.conditions[0].operator == Operator.ENDING_WITH


def test_parse_like():
    """Test parsing like operator."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_name_like")
    
    assert spec.conditions[0].operator == Operator.LIKE


def test_parse_not():
    """Test parsing not operator."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_age_not")
    
    assert spec.conditions[0].operator == Operator.NOT_EQUALS


def test_parse_and_conditions():
    """Test parsing AND conditions."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_name_and_age")
    
    assert len(spec.conditions) == 2
    assert spec.logical_operator == LogicalOperator.AND
    assert spec.conditions[0].property_name == "name"
    assert spec.conditions[1].property_name == "age"


def test_parse_or_conditions():
    """Test parsing OR conditions."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_name_or_email")
    
    assert len(spec.conditions) == 2
    assert spec.logical_operator == LogicalOperator.OR
    assert spec.conditions[0].property_name == "name"
    assert spec.conditions[1].property_name == "email"


def test_parse_complex_and_conditions():
    """Test parsing complex AND conditions with operators."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_name_and_age_greater_than")
    
    assert len(spec.conditions) == 2
    assert spec.logical_operator == LogicalOperator.AND
    assert spec.conditions[0].property_name == "name"
    assert spec.conditions[0].operator == Operator.EQUALS
    assert spec.conditions[1].property_name == "age"
    assert spec.conditions[1].operator == Operator.GREATER_THAN


def test_parse_order_by_asc():
    """Test parsing order_by with ASC."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_age_greater_than_order_by_name_asc")
    
    assert len(spec.ordering) == 1
    assert spec.ordering[0].property_name == "name"
    assert spec.ordering[0].direction == "ASC"


def test_parse_order_by_desc():
    """Test parsing order_by with DESC."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_age_less_than_order_by_name_desc")
    
    assert len(spec.ordering) == 1
    assert spec.ordering[0].property_name == "name"
    assert spec.ordering[0].direction == "DESC"


def test_parse_multiple_order_by():
    """Test parsing multiple order_by clauses."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_by_age_greater_than_order_by_name_asc_age_desc")
    
    assert len(spec.ordering) == 2
    assert spec.ordering[0].property_name == "name"
    assert spec.ordering[0].direction == "ASC"
    assert spec.ordering[1].property_name == "age"
    assert spec.ordering[1].direction == "DESC"


def test_parse_find_first():
    """Test parsing find_first_ query."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_first_by_age")
    
    assert spec.operation == Operation.FIND
    assert spec.limit == 1
    assert spec.conditions[0].property_name == "age"


def test_parse_find_top_n():
    """Test parsing find_top_N_ query."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_top_10_by_age_greater_than")
    
    assert spec.operation == Operation.FIND
    assert spec.limit == 10
    assert spec.conditions[0].property_name == "age"
    assert spec.conditions[0].operator == Operator.GREATER_THAN


def test_parse_complex_query():
    """Test parsing a complex query with all features."""
    parser = QueryParser()
    spec = parser.parse_method_name(
        "find_top_5_by_name_containing_and_age_greater_than_order_by_age_desc_name_asc"
    )
    
    assert spec.operation == Operation.FIND
    assert spec.limit == 5
    assert len(spec.conditions) == 2
    assert spec.logical_operator == LogicalOperator.AND
    assert spec.conditions[0].property_name == "name"
    assert spec.conditions[0].operator == Operator.CONTAINING
    assert spec.conditions[1].property_name == "age"
    assert spec.conditions[1].operator == Operator.GREATER_THAN
    assert len(spec.ordering) == 2
    assert spec.ordering[0].property_name == "age"
    assert spec.ordering[0].direction == "DESC"
    assert spec.ordering[1].property_name == "name"
    assert spec.ordering[1].direction == "ASC"


def test_parse_invalid_method_name():
    """Test parsing invalid method name."""
    parser = QueryParser()
    
    with pytest.raises(QueryException):
        parser.parse_method_name("invalid_method_name")


def test_parse_find_all_order_by():
    """Test parsing find_all with order_by."""
    parser = QueryParser()
    spec = parser.parse_method_name("find_order_by_name_asc")
    
    assert spec.operation == Operation.FIND
    assert len(spec.conditions) == 0
    assert len(spec.ordering) == 1
    assert spec.ordering[0].property_name == "name"
