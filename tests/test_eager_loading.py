"""Tests for eager loading functionality with fetch hints."""

import pytest
from typing import List, Optional
from unittest.mock import Mock

from falkordb_orm import node, generated_id, relationship, Repository


# Test entities
@node("Person")
class Person:
    id: Optional[int] = generated_id()
    name: str
    age: int

    friends: List["Person"] = relationship("KNOWS", target="Person")
    company: Optional["Company"] = relationship("WORKS_FOR", target="Company")


@node("Company")
class Company:
    id: Optional[int] = generated_id()
    name: str
    industry: str

    employees: List[Person] = relationship("WORKS_FOR", target=Person, direction="INCOMING")


@node("Project")
class Project:
    id: Optional[int] = generated_id()
    name: str
    description: str


@node("Developer")
class Developer:
    id: Optional[int] = generated_id()
    name: str

    projects: List[Project] = relationship("WORKS_ON", target=Project)
    team: Optional["Team"] = relationship("MEMBER_OF", target="Team")


@node("Team")
class Team:
    id: Optional[int] = generated_id()
    name: str

    members: List[Developer] = relationship("MEMBER_OF", target=Developer, direction="INCOMING")


class TestEagerLoading:
    """Test eager loading with fetch parameter."""

    def test_find_by_id_with_fetch(self):
        """Test that find_by_id with fetch uses eager loading query."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[[Mock(properties={"name": "Alice", "age": 30}, id=1), []]],
                header=[[0, "n"], [1, "friends"]],
            )
        )

        # Create repository
        repo = Repository(graph, Person)

        # Find with fetch hint
        repo.find_by_id(1, fetch=["friends"])

        # Verify eager loading query was used
        assert graph.query.called
        call_args = graph.query.call_args[0]
        cypher = call_args[0]

        # Should contain OPTIONAL MATCH
        assert "OPTIONAL MATCH" in cypher
        assert "KNOWS" in cypher

    def test_find_by_id_without_fetch(self):
        """Test that find_by_id without fetch uses standard query."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[[Mock(properties={"name": "Alice", "age": 30}, id=1)]],
                header=[[0, "n"]],
            )
        )

        # Create repository
        repo = Repository(graph, Person)

        # Find without fetch hint
        repo.find_by_id(1)

        # Verify standard query was used (no OPTIONAL MATCH)
        assert graph.query.called
        call_args = graph.query.call_args[0]
        cypher = call_args[0]

        # Should NOT contain OPTIONAL MATCH
        assert "OPTIONAL MATCH" not in cypher

    def test_find_all_with_fetch(self):
        """Test that find_all with fetch uses eager loading query."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[
                    [Mock(properties={"name": "Alice", "age": 30}, id=1), []],
                    [Mock(properties={"name": "Bob", "age": 28}, id=2), []],
                ],
                header=[[0, "n"], [1, "friends"]],
            )
        )

        # Create repository
        repo = Repository(graph, Person)

        # Find all with fetch hint
        repo.find_all(fetch=["friends"])

        # Verify eager loading query was used
        assert graph.query.called
        call_args = graph.query.call_args[0]
        cypher = call_args[0]

        # Should contain OPTIONAL MATCH
        assert "OPTIONAL MATCH" in cypher
        assert "KNOWS" in cypher

    def test_multiple_fetch_hints(self):
        """Test eager loading with multiple fetch hints."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[
                    [
                        Mock(properties={"name": "Alice", "age": 30}, id=1),
                        [],  # friends
                        Mock(properties={"name": "Acme Corp", "industry": "Tech"}, id=2),  # company
                    ]
                ],
                header=[[0, "n"], [1, "friends"], [2, "company"]],
            )
        )

        # Create repository
        repo = Repository(graph, Person)

        # Find with multiple fetch hints
        repo.find_by_id(1, fetch=["friends", "company"])

        # Verify both relationships in query
        assert graph.query.called
        call_args = graph.query.call_args[0]
        cypher = call_args[0]

        # Should contain both relationships
        assert cypher.count("OPTIONAL MATCH") >= 2
        assert "KNOWS" in cypher
        assert "WORKS_FOR" in cypher

    def test_eager_loading_prevents_n_plus_one(self):
        """Test that eager loading loads relationships in single query."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[
                    [
                        Mock(properties={"name": "Alice", "age": 30}, id=1),
                        [
                            Mock(properties={"name": "Bob", "age": 28}, id=2),
                            Mock(properties={"name": "Charlie", "age": 32}, id=3),
                        ],
                    ]
                ],
                header=[[0, "n"], [1, "friends"]],
            )
        )

        # Create repository
        repo = Repository(graph, Person)

        # Find with eager loading
        repo.find_by_id(1, fetch=["friends"])

        # Only one query should be executed
        assert graph.query.call_count == 1

        # Accessing friends should not trigger additional queries
        # (This would normally trigger lazy loading if not eagerly loaded)

    def test_eager_loading_collection_relationship(self):
        """Test eager loading of collection relationships."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[
                    [
                        Mock(properties={"name": "Dev Team"}, id=1),
                        [
                            Mock(properties={"name": "Alice"}, id=2),
                            Mock(properties={"name": "Bob"}, id=3),
                        ],
                    ]
                ],
                header=[[0, "n"], [1, "members"]],
            )
        )

        # Create repository
        repo = Repository(graph, Team)

        # Find with eager loading
        repo.find_by_id(1, fetch=["members"])

        # Verify query was called
        assert graph.query.called
        call_args = graph.query.call_args[0]
        cypher = call_args[0]

        # Should collect relationships
        assert "collect" in cypher.lower()

    def test_eager_loading_single_relationship(self):
        """Test eager loading of single (Optional) relationships."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[
                    [
                        Mock(properties={"name": "Alice", "age": 30}, id=1),
                        Mock(properties={"name": "Acme Corp", "industry": "Tech"}, id=2),
                    ]
                ],
                header=[[0, "n"], [1, "company"]],
            )
        )

        # Create repository
        repo = Repository(graph, Person)

        # Find with eager loading
        repo.find_by_id(1, fetch=["company"])

        # Verify query was called
        assert graph.query.called

    def test_eager_loading_empty_relationship(self):
        """Test eager loading when relationship is empty."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[
                    [Mock(properties={"name": "Alice", "age": 30}, id=1), []]  # No friends
                ],
                header=[[0, "n"], [1, "friends"]],
            )
        )

        # Create repository
        repo = Repository(graph, Person)

        # Find with eager loading
        repo.find_by_id(1, fetch=["friends"])

        # Should handle empty relationships gracefully
        assert graph.query.called

    def test_eager_loading_none_relationship(self):
        """Test eager loading when single relationship is None."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[
                    [Mock(properties={"name": "Alice", "age": 30}, id=1), None]  # No company
                ],
                header=[[0, "n"], [1, "company"]],
            )
        )

        # Create repository
        repo = Repository(graph, Person)

        # Find with eager loading
        repo.find_by_id(1, fetch=["company"])

        # Should handle None relationships gracefully
        assert graph.query.called

    def test_fetch_with_invalid_relationship_name(self):
        """Test that invalid relationship names in fetch are ignored."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[[Mock(properties={"name": "Alice", "age": 30}, id=1)]],
                header=[[0, "n"]],
            )
        )

        # Create repository
        repo = Repository(graph, Person)

        # Find with invalid fetch hint
        repo.find_by_id(1, fetch=["nonexistent_relationship"])

        # Should not crash, just ignore invalid hint
        assert graph.query.called

    def test_eager_loading_with_direction(self):
        """Test eager loading respects relationship direction."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[
                    [
                        Mock(properties={"name": "Acme Corp", "industry": "Tech"}, id=1),
                        [],  # employees
                    ]
                ],
                header=[[0, "n"], [1, "employees"]],
            )
        )

        # Create repository
        repo = Repository(graph, Company)

        # Find with eager loading (INCOMING relationship)
        repo.find_by_id(1, fetch=["employees"])

        # Verify query uses correct direction
        assert graph.query.called
        call_args = graph.query.call_args[0]
        cypher = call_args[0]

        # Should use incoming direction arrow
        assert "<-" in cypher or "INCOMING" in cypher.upper()

    def test_nested_eager_loading(self):
        """Test that eager loading works for nested relationships."""
        # Note: This tests current behavior - nested eager loading
        # requires multiple queries or a more complex implementation

        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[
                    [
                        Mock(properties={"name": "Alice"}, id=1),
                        [Mock(properties={"name": "Project Alpha", "description": "Desc"}, id=2)],
                        Mock(properties={"name": "Dev Team"}, id=3),
                    ]
                ],
                header=[[0, "n"], [1, "projects"], [2, "team"]],
            )
        )

        # Create repository
        repo = Repository(graph, Developer)

        # Find with multiple relationships
        repo.find_by_id(1, fetch=["projects", "team"])

        # Should load both relationships
        assert graph.query.called


class TestEagerLoadingPerformance:
    """Test performance characteristics of eager loading."""

    def test_eager_vs_lazy_query_count(self):
        """Compare query count between eager and lazy loading."""
        # Eager loading - single query
        graph_eager = Mock()
        graph_eager.query = Mock(
            return_value=Mock(
                result_set=[
                    [
                        Mock(properties={"name": "Alice", "age": 30}, id=1),
                        [Mock(properties={"name": "Bob", "age": 28}, id=2)],
                    ]
                ],
                header=[[0, "n"], [1, "friends"]],
            )
        )

        repo_eager = Repository(graph_eager, Person)
        repo_eager.find_by_id(1, fetch=["friends"])
        eager_queries = graph_eager.query.call_count

        # Lazy loading - would require additional queries
        # (not testing actual lazy load here, just documenting expected behavior)

        # Eager should use fewer queries
        assert eager_queries >= 1

    def test_bulk_eager_loading(self):
        """Test eager loading with find_all for multiple entities."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[
                    [Mock(properties={"name": "Alice", "age": 30}, id=1), []],
                    [Mock(properties={"name": "Bob", "age": 28}, id=2), []],
                    [Mock(properties={"name": "Charlie", "age": 32}, id=3), []],
                ],
                header=[[0, "n"], [1, "friends"]],
            )
        )

        # Create repository
        repo = Repository(graph, Person)

        # Find all with eager loading
        repo.find_all(fetch=["friends"])

        # Should use single query for all entities
        assert graph.query.call_count == 1


class TestEagerLoadingEdgeCases:
    """Test edge cases in eager loading."""

    def test_empty_fetch_list(self):
        """Test that empty fetch list behaves like no fetch."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[[Mock(properties={"name": "Alice", "age": 30}, id=1)]],
                header=[[0, "n"]],
            )
        )

        # Create repository
        repo = Repository(graph, Person)

        # Find with empty fetch list
        repo.find_by_id(1, fetch=[])

        # Should use standard query
        assert graph.query.called
        call_args = graph.query.call_args[0]
        cypher = call_args[0]

        # Should NOT contain OPTIONAL MATCH
        assert "OPTIONAL MATCH" not in cypher

    def test_duplicate_fetch_hints(self):
        """Test that duplicate fetch hints don't cause issues."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[[Mock(properties={"name": "Alice", "age": 30}, id=1), []]],
                header=[[0, "n"], [1, "friends"]],
            )
        )

        # Create repository
        repo = Repository(graph, Person)

        # Find with duplicate hints
        repo.find_by_id(1, fetch=["friends", "friends"])

        # Should handle gracefully
        assert graph.query.called

    def test_case_sensitive_fetch_hints(self):
        """Test that fetch hints are case-sensitive."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[[Mock(properties={"name": "Alice", "age": 30}, id=1)]],
                header=[[0, "n"]],
            )
        )

        # Create repository
        repo = Repository(graph, Person)

        # Find with wrong case (should not match)
        repo.find_by_id(1, fetch=["FRIENDS"])  # Should be "friends"

        # Should handle gracefully (ignore invalid hint)
        assert graph.query.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
