"""Pagination support for query results."""

from dataclasses import dataclass
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


@dataclass
class Pageable:
    """
    Pagination parameters for query results.

    Attributes:
        page: Zero-indexed page number (0 = first page)
        size: Number of items per page
        sort_by: Optional property name to sort by
        direction: Sort direction ('ASC' or 'DESC')

    Example:
        >>> pageable = Pageable(page=0, size=10, sort_by="name", direction="ASC")
        >>> page = repo.find_all_paginated(pageable)
    """

    page: int
    size: int
    sort_by: Optional[str] = None
    direction: str = "ASC"

    def __post_init__(self):
        """Validate pagination parameters."""
        if self.page < 0:
            raise ValueError("Page number must be >= 0")
        if self.size <= 0:
            raise ValueError("Page size must be > 0")
        if self.direction not in ("ASC", "DESC"):
            raise ValueError("Direction must be 'ASC' or 'DESC'")

    def skip(self) -> int:
        """
        Calculate the number of items to skip (SKIP clause value).

        Returns:
            Number of items to skip for this page
        """
        return self.page * self.size

    def next(self) -> "Pageable":
        """
        Get Pageable for the next page.

        Returns:
            New Pageable instance for next page
        """
        return Pageable(
            page=self.page + 1, size=self.size, sort_by=self.sort_by, direction=self.direction
        )

    def previous(self) -> "Pageable":
        """
        Get Pageable for the previous page.

        Returns:
            New Pageable instance for previous page

        Raises:
            ValueError: If already on first page
        """
        if self.page == 0:
            raise ValueError("Already on first page")
        return Pageable(
            page=self.page - 1, size=self.size, sort_by=self.sort_by, direction=self.direction
        )

    def first(self) -> "Pageable":
        """
        Get Pageable for the first page.

        Returns:
            New Pageable instance for first page
        """
        return Pageable(page=0, size=self.size, sort_by=self.sort_by, direction=self.direction)


@dataclass
class Page(Generic[T]):
    """
    A page of query results with pagination metadata.

    Type Parameters:
        T: Entity type

    Attributes:
        content: List of entities on this page
        page_number: Current page number (0-indexed)
        page_size: Number of items per page
        total_elements: Total number of items across all pages
        total_pages: Total number of pages (calculated)

    Example:
        >>> page = repo.find_all_paginated(Pageable(page=0, size=10))
        >>> print(f"Page {page.page_number + 1} of {page.total_pages}")
        >>> print(f"Showing {len(page.content)} of {page.total_elements} items")
        >>> for item in page.content:
        ...     print(item.name)
    """

    content: List[T]
    page_number: int
    page_size: int
    total_elements: int

    @property
    def total_pages(self) -> int:
        """
        Calculate total number of pages.

        Returns:
            Total number of pages needed for all elements
        """
        if self.total_elements == 0:
            return 0
        return (self.total_elements + self.page_size - 1) // self.page_size

    def has_next(self) -> bool:
        """
        Check if there is a next page.

        Returns:
            True if there are more pages after this one
        """
        return self.page_number + 1 < self.total_pages

    def has_previous(self) -> bool:
        """
        Check if there is a previous page.

        Returns:
            True if there are pages before this one
        """
        return self.page_number > 0

    def is_first(self) -> bool:
        """
        Check if this is the first page.

        Returns:
            True if this is page 0
        """
        return self.page_number == 0

    def is_last(self) -> bool:
        """
        Check if this is the last page.

        Returns:
            True if this is the last page
        """
        return self.page_number + 1 >= self.total_pages

    def __len__(self) -> int:
        """
        Get number of items on this page.

        Returns:
            Number of items in content
        """
        return len(self.content)

    def __iter__(self):
        """
        Iterate over items on this page.

        Yields:
            Each item in content
        """
        return iter(self.content)

    def __repr__(self) -> str:
        """
        String representation of page.

        Returns:
            Human-readable page description
        """
        return (
            f"Page(page={self.page_number + 1}/{self.total_pages}, "
            f"items={len(self.content)}/{self.total_elements})"
        )
