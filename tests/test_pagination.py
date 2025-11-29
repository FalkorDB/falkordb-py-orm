"""Tests for pagination functionality."""

import pytest
from typing import Optional
from unittest.mock import Mock

from falkordb_orm import node, generated_id, Repository, Pageable, Page


@node("Person")
class Person:
    id: Optional[int] = generated_id()
    name: str
    age: int


class TestPageable:
    """Test Pageable class."""

    def test_pageable_creation(self):
        """Test creating a Pageable instance."""
        pageable = Pageable(page=0, size=10)
        assert pageable.page == 0
        assert pageable.size == 10
        assert pageable.sort_by is None
        assert pageable.direction == "ASC"

    def test_pageable_with_sorting(self):
        """Test creating Pageable with sorting."""
        pageable = Pageable(page=2, size=20, sort_by="name", direction="DESC")
        assert pageable.page == 2
        assert pageable.size == 20
        assert pageable.sort_by == "name"
        assert pageable.direction == "DESC"

    def test_pageable_skip_calculation(self):
        """Test skip value calculation."""
        assert Pageable(page=0, size=10).skip() == 0
        assert Pageable(page=1, size=10).skip() == 10
        assert Pageable(page=2, size=10).skip() == 20
        assert Pageable(page=5, size=25).skip() == 125

    def test_pageable_next(self):
        """Test getting next page."""
        pageable = Pageable(page=0, size=10, sort_by="name")
        next_page = pageable.next()

        assert next_page.page == 1
        assert next_page.size == 10
        assert next_page.sort_by == "name"
        assert next_page.direction == "ASC"

    def test_pageable_previous(self):
        """Test getting previous page."""
        pageable = Pageable(page=2, size=10)
        prev_page = pageable.previous()

        assert prev_page.page == 1
        assert prev_page.size == 10

    def test_pageable_previous_on_first_page(self):
        """Test that previous() raises error on first page."""
        pageable = Pageable(page=0, size=10)

        with pytest.raises(ValueError, match="Already on first page"):
            pageable.previous()

    def test_pageable_first(self):
        """Test getting first page."""
        pageable = Pageable(page=5, size=10, sort_by="age")
        first_page = pageable.first()

        assert first_page.page == 0
        assert first_page.size == 10
        assert first_page.sort_by == "age"

    def test_pageable_validation_negative_page(self):
        """Test that negative page number raises error."""
        with pytest.raises(ValueError, match="Page number must be >= 0"):
            Pageable(page=-1, size=10)

    def test_pageable_validation_zero_size(self):
        """Test that zero page size raises error."""
        with pytest.raises(ValueError, match="Page size must be > 0"):
            Pageable(page=0, size=0)

    def test_pageable_validation_invalid_direction(self):
        """Test that invalid direction raises error."""
        with pytest.raises(ValueError, match="Direction must be 'ASC' or 'DESC'"):
            Pageable(page=0, size=10, direction="INVALID")


class TestPage:
    """Test Page class."""

    def test_page_creation(self):
        """Test creating a Page instance."""
        content = [Person(name="Alice", age=30), Person(name="Bob", age=28)]
        page = Page(content=content, page_number=0, page_size=10, total_elements=25)

        assert len(page.content) == 2
        assert page.page_number == 0
        assert page.page_size == 10
        assert page.total_elements == 25

    def test_page_total_pages_calculation(self):
        """Test total pages calculation."""
        # Exactly divisible
        page1 = Page(content=[], page_number=0, page_size=10, total_elements=100)
        assert page1.total_pages == 10

        # With remainder
        page2 = Page(content=[], page_number=0, page_size=10, total_elements=105)
        assert page2.total_pages == 11

        # Single page
        page3 = Page(content=[], page_number=0, page_size=10, total_elements=5)
        assert page3.total_pages == 1

        # Empty
        page4 = Page(content=[], page_number=0, page_size=10, total_elements=0)
        assert page4.total_pages == 0

    def test_page_has_next(self):
        """Test has_next method."""
        # First page with more pages
        page1 = Page(content=[], page_number=0, page_size=10, total_elements=100)
        assert page1.has_next() is True

        # Last page
        page2 = Page(content=[], page_number=9, page_size=10, total_elements=100)
        assert page2.has_next() is False

        # Only page
        page3 = Page(content=[], page_number=0, page_size=10, total_elements=5)
        assert page3.has_next() is False

    def test_page_has_previous(self):
        """Test has_previous method."""
        # First page
        page1 = Page(content=[], page_number=0, page_size=10, total_elements=100)
        assert page1.has_previous() is False

        # Middle page
        page2 = Page(content=[], page_number=5, page_size=10, total_elements=100)
        assert page2.has_previous() is True

        # Last page
        page3 = Page(content=[], page_number=9, page_size=10, total_elements=100)
        assert page3.has_previous() is True

    def test_page_is_first(self):
        """Test is_first method."""
        page1 = Page(content=[], page_number=0, page_size=10, total_elements=100)
        assert page1.is_first() is True

        page2 = Page(content=[], page_number=1, page_size=10, total_elements=100)
        assert page2.is_first() is False

    def test_page_is_last(self):
        """Test is_last method."""
        # Last page
        page1 = Page(content=[], page_number=9, page_size=10, total_elements=100)
        assert page1.is_last() is True

        # Not last page
        page2 = Page(content=[], page_number=8, page_size=10, total_elements=100)
        assert page2.is_last() is False

        # Only page
        page3 = Page(content=[], page_number=0, page_size=10, total_elements=5)
        assert page3.is_last() is True

    def test_page_len(self):
        """Test __len__ method."""
        content = [Person(name=f"Person{i}", age=20 + i) for i in range(5)]
        page = Page(content=content, page_number=0, page_size=10, total_elements=50)

        assert len(page) == 5

    def test_page_iter(self):
        """Test __iter__ method."""
        content = [Person(name=f"Person{i}", age=20 + i) for i in range(3)]
        page = Page(content=content, page_number=0, page_size=10, total_elements=30)

        items = list(page)
        assert len(items) == 3
        assert items[0].name == "Person0"
        assert items[2].name == "Person2"

    def test_page_repr(self):
        """Test __repr__ method."""
        page = Page(content=[], page_number=2, page_size=10, total_elements=100)
        repr_str = repr(page)

        assert "Page(page=3/10" in repr_str
        assert "items=0/100)" in repr_str


class TestRepositoryPagination:
    """Test Repository pagination."""

    def test_find_all_paginated_basic(self):
        """Test basic pagination."""
        # Setup mock
        graph = Mock()

        # Mock count query
        count_result = Mock(result_set=[[25]])

        # Mock paginated query
        page_result = Mock(
            result_set=[
                [Mock(properties={"name": "Alice", "age": 30}, id=1)],
                [Mock(properties={"name": "Bob", "age": 28}, id=2)],
            ],
            header=[[0, "n"]],
        )

        graph.query = Mock(side_effect=[count_result, page_result])

        # Create repository and paginate
        repo = Repository(graph, Person)
        pageable = Pageable(page=0, size=10)
        page = repo.find_all_paginated(pageable)

        # Verify
        assert len(page.content) == 2
        assert page.page_number == 0
        assert page.page_size == 10
        assert page.total_elements == 25
        assert page.total_pages == 3
        assert page.content[0].name == "Alice"
        assert page.content[1].name == "Bob"

    def test_find_all_paginated_with_sorting(self):
        """Test pagination with sorting."""
        graph = Mock()

        count_result = Mock(result_set=[[10]])
        page_result = Mock(result_set=[], header=[[0, "n"]])

        graph.query = Mock(side_effect=[count_result, page_result])

        repo = Repository(graph, Person)
        pageable = Pageable(page=0, size=5, sort_by="name", direction="DESC")
        page = repo.find_all_paginated(pageable)

        # Verify sorting was applied
        assert graph.query.call_count == 2
        paginated_call = graph.query.call_args_list[1]
        cypher = paginated_call[0][0]
        assert "ORDER BY n.name DESC" in cypher
        assert "SKIP 0 LIMIT 5" in cypher

    def test_find_all_paginated_second_page(self):
        """Test getting second page."""
        graph = Mock()

        count_result = Mock(result_set=[[100]])
        page_result = Mock(result_set=[], header=[[0, "n"]])

        graph.query = Mock(side_effect=[count_result, page_result])

        repo = Repository(graph, Person)
        pageable = Pageable(page=2, size=20)
        page = repo.find_all_paginated(pageable)

        # Verify SKIP/LIMIT
        paginated_call = graph.query.call_args_list[1]
        cypher = paginated_call[0][0]
        assert "SKIP 40 LIMIT 20" in cypher

        assert page.page_number == 2
        assert page.total_pages == 5
        assert page.has_previous() is True
        assert page.has_next() is True

    def test_find_all_paginated_empty_results(self):
        """Test pagination with no results."""
        graph = Mock()

        count_result = Mock(result_set=[[0]])
        page_result = Mock(result_set=[], header=[[0, "n"]])

        graph.query = Mock(side_effect=[count_result, page_result])

        repo = Repository(graph, Person)
        pageable = Pageable(page=0, size=10)
        page = repo.find_all_paginated(pageable)

        assert len(page.content) == 0
        assert page.total_elements == 0
        assert page.total_pages == 0
        assert page.has_next() is False
        assert page.is_first() is True
        assert page.is_last() is True

    def test_find_all_paginated_last_page_partial(self):
        """Test last page with partial results."""
        graph = Mock()

        count_result = Mock(result_set=[[45]])
        page_result = Mock(
            result_set=[
                [Mock(properties={"name": f"Person{i}", "age": 20 + i}, id=i)] for i in range(5)
            ],
            header=[[0, "n"]],
        )

        graph.query = Mock(side_effect=[count_result, page_result])

        repo = Repository(graph, Person)
        pageable = Pageable(page=4, size=10)
        page = repo.find_all_paginated(pageable)

        assert len(page.content) == 5  # Last page has only 5 items
        assert page.total_elements == 45
        assert page.total_pages == 5
        assert page.is_last() is True
        assert page.has_next() is False


class TestPaginationNavigation:
    """Test page navigation patterns."""

    def test_navigate_through_pages(self):
        """Test navigating through multiple pages."""
        pageable = Pageable(page=0, size=10, sort_by="name")

        # Navigate forward
        page0 = pageable
        page1 = page0.next()
        page2 = page1.next()

        assert page0.page == 0
        assert page1.page == 1
        assert page2.page == 2

        # Navigate backward
        back_to_1 = page2.previous()
        back_to_0 = back_to_1.previous()

        assert back_to_1.page == 1
        assert back_to_0.page == 0

        # All maintain sort settings
        assert all(p.sort_by == "name" for p in [page0, page1, page2, back_to_0])

    def test_jump_to_first_page(self):
        """Test jumping to first page from any page."""
        pageable = Pageable(page=10, size=20, sort_by="age")
        first = pageable.first()

        assert first.page == 0
        assert first.size == 20
        assert first.sort_by == "age"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
