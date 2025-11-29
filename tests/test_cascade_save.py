"""Tests for cascade save functionality in relationship persistence."""

import pytest
from typing import List, Optional
from unittest.mock import Mock, MagicMock, call

from falkordb_orm import node, generated_id, relationship, Repository
from falkordb_orm.relationships import RelationshipManager
from falkordb_orm.metadata import get_entity_metadata


# Test entities
@node("Person")
class Person:
    id: Optional[int] = generated_id()
    name: str
    age: int

    # Cascade enabled - auto-saves friends
    friends: List["Person"] = relationship("KNOWS", target="Person", cascade=True)


@node("Company")
class Company:
    id: Optional[int] = generated_id()
    name: str
    industry: str


@node("Employee")
class Employee:
    id: Optional[int] = generated_id()
    name: str
    position: str

    # Cascade enabled - auto-saves company
    company: Optional[Company] = relationship("WORKS_FOR", target=Company, cascade=True)


@node("Project")
class Project:
    id: Optional[int] = generated_id()
    name: str
    description: str


@node("Team")
class Team:
    id: Optional[int] = generated_id()
    name: str

    # Cascade enabled for multiple relationships
    members: List[Person] = relationship("HAS_MEMBER", target=Person, cascade=True)
    projects: List[Project] = relationship("WORKS_ON", target=Project, cascade=True)


@node("NonCascadePerson")
class NonCascadePerson:
    id: Optional[int] = generated_id()
    name: str

    # Cascade disabled - must save manually
    friends: List["NonCascadePerson"] = relationship(
        "KNOWS", target="NonCascadePerson", cascade=False
    )


class TestCascadeSave:
    """Test cascade save functionality."""

    def test_cascade_save_single_relationship(self):
        """Test that cascade save works for single relationships."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(
            return_value=Mock(
                result_set=[
                    [Mock(), 1],  # First call: save employee
                    [Mock(), 2],  # Second call: save company (cascade)
                ]
            )
        )

        # Create entities
        company = Company(name="Acme Corp", industry="Tech")
        employee = Employee(name="Alice", position="Engineer", company=company)

        # Save employee
        repo = Repository(graph, Employee)
        saved = repo.save(employee)

        # Verify company was saved (cascade)
        assert company.id is not None
        assert employee.id is not None

        # Verify relationship edge was created
        assert graph.query.call_count >= 3  # employee save + company save + relationship

        # Check that relationship create query was called
        calls = [str(call) for call in graph.query.call_args_list]
        assert any("CREATE" in str(call) and "WORKS_FOR" in str(call) for call in calls)

    def test_cascade_save_collection_relationship(self):
        """Test that cascade save works for collection relationships."""
        # Setup mocks
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            # Return incrementing IDs
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create entities
        alice = Person(name="Alice", age=30)
        bob = Person(name="Bob", age=28)
        charlie = Person(name="Charlie", age=32)

        alice.friends = [bob, charlie]

        # Save alice
        repo = Repository(graph, Person)
        saved = repo.save(alice)

        # Verify all entities got IDs
        assert alice.id is not None
        assert bob.id is not None
        assert charlie.id is not None

        # Should have saved: alice + 2 friends + 2 relationships = 5 queries
        assert call_count[0] >= 5

    def test_cascade_save_already_saved_entity(self):
        """Test that cascade save skips already-saved entities."""
        # Setup mocks
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create and "pre-save" company
        company = Company(name="Acme Corp", industry="Tech")
        company.id = 999  # Simulate already saved

        employee = Employee(name="Alice", position="Engineer", company=company)

        # Save employee
        repo = Repository(graph, Employee)
        saved = repo.save(employee)

        # Should only save employee + relationship, not company again
        # employee save (1) + relationship create (1) = 2 queries
        assert call_count[0] == 2

    def test_non_cascade_relationship(self):
        """Test that non-cascade relationships don't auto-save."""
        # Setup mocks
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create entities (friends not saved)
        alice = NonCascadePerson(name="Alice")
        bob = NonCascadePerson(name="Bob")  # No ID!

        alice.friends = [bob]

        # Save alice
        repo = Repository(graph, NonCascadePerson)
        saved = repo.save(alice)

        # Bob should NOT be saved (no ID assigned)
        assert bob.id is None

        # Only alice should be saved, no relationship created (bob has no ID)
        assert call_count[0] == 1

    def test_cascade_save_multiple_relationships(self):
        """Test cascade save with multiple relationship types."""
        # Setup mocks
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create team with members and projects
        alice = Person(name="Alice", age=30)
        bob = Person(name="Bob", age=28)

        proj1 = Project(name="Alpha", description="First project")
        proj2 = Project(name="Beta", description="Second project")

        team = Team(name="Dev Team")
        team.members = [alice, bob]
        team.projects = [proj1, proj2]

        # Save team
        repo = Repository(graph, Team)
        saved = repo.save(team)

        # Verify all entities got IDs
        assert team.id is not None
        assert alice.id is not None
        assert bob.id is not None
        assert proj1.id is not None
        assert proj2.id is not None

        # Should save: team + 2 members + 2 projects + 4 relationships = 9 queries
        assert call_count[0] >= 9

    def test_circular_reference_handling(self):
        """Test that circular references don't cause infinite loops."""
        # Setup mocks
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create circular reference
        alice = Person(name="Alice", age=30)
        bob = Person(name="Bob", age=28)

        # Circular friendship
        alice.friends = [bob]
        bob.friends = [alice]

        # Save alice (which cascades to bob, which would cascade back to alice)
        repo = Repository(graph, Person)
        saved = repo.save(alice)

        # Should not cause infinite loop
        # alice save + bob save (cascade) + 2 relationships = 4 queries
        # bob.friends = [alice] won't cascade again because alice is tracked
        assert call_count[0] < 10  # Reasonable upper bound

    def test_relationship_edge_creation(self):
        """Test that relationship edges are actually created."""
        # Setup mocks
        graph = Mock()
        queries_executed = []

        def mock_query(cypher, params):
            queries_executed.append((cypher, params))
            if "CREATE" in cypher and "node" in cypher.lower():
                # Node creation - return ID
                return Mock(result_set=[[Mock(), len(queries_executed)]])
            else:
                # Relationship creation
                return Mock(result_set=[])

        graph.query = mock_query

        # Create entities
        company = Company(name="Acme Corp", industry="Tech")
        employee = Employee(name="Alice", position="Engineer", company=company)

        # Save employee
        repo = Repository(graph, Employee)
        saved = repo.save(employee)

        # Find relationship creation query
        rel_queries = [q for q in queries_executed if "WORKS_FOR" in q[0]]

        assert len(rel_queries) >= 1, "Relationship edge should be created"

        # Verify relationship query structure
        rel_query = rel_queries[0]
        assert "MATCH" in rel_query[0]
        assert "CREATE" in rel_query[0]
        assert "source_id" in rel_query[1]
        assert "target_id" in rel_query[1]

    def test_empty_relationship_list(self):
        """Test that empty relationship lists are handled."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(return_value=Mock(result_set=[[Mock(), 1]]))

        # Create person with no friends
        alice = Person(name="Alice", age=30)
        alice.friends = []

        # Save alice
        repo = Repository(graph, Person)
        saved = repo.save(alice)

        # Should only save alice, no relationship queries
        assert graph.query.call_count == 1

    def test_none_relationship_value(self):
        """Test that None relationship values are handled."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(return_value=Mock(result_set=[[Mock(), 1]]))

        # Create employee with no company
        employee = Employee(name="Alice", position="Engineer")
        employee.company = None

        # Save employee
        repo = Repository(graph, Employee)
        saved = repo.save(employee)

        # Should only save employee, no relationship queries
        assert graph.query.call_count == 1


class TestRelationshipManager:
    """Test RelationshipManager directly."""

    def test_relationship_manager_creation(self):
        """Test that RelationshipManager can be created."""
        graph = Mock()
        mapper = Mock()
        query_builder = Mock()

        manager = RelationshipManager(graph, mapper, query_builder)

        assert manager._graph == graph
        assert manager._mapper == mapper
        assert manager._query_builder == query_builder

    def test_save_relationships_with_cascade(self):
        """Test save_relationships method with cascade enabled."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(return_value=Mock(result_set=[]))

        mapper = Mock()
        mapper.get_entity_metadata = lambda cls: get_entity_metadata(cls)

        query_builder = Mock()
        query_builder.build_relationship_create_query = Mock(
            return_value=("CREATE query", {"source_id": 1, "target_id": 2})
        )

        manager = RelationshipManager(graph, mapper, query_builder)

        # Create entities with IDs
        alice = Person(name="Alice", age=30)
        alice.id = 1

        bob = Person(name="Bob", age=28)
        bob.id = 2

        alice.friends = [bob]

        # Get metadata
        metadata = get_entity_metadata(Person)

        # Save relationships
        manager.save_relationships(alice, 1, metadata)

        # Verify relationship edge was created
        assert query_builder.build_relationship_create_query.called
        assert graph.query.called

    def test_entity_tracker_prevents_loops(self):
        """Test that entity tracker prevents infinite loops."""
        # Setup mocks
        graph = Mock()
        mapper = Mock()
        query_builder = Mock()

        manager = RelationshipManager(graph, mapper, query_builder)

        # Add entity to tracker
        alice = Person(name="Alice", age=30)
        entity_key = (id(alice), 1)
        manager._entity_tracker.add(entity_key)

        # Try to save relationships again - should return early
        metadata = Mock(relationships=[])
        manager.save_relationships(alice, 1, metadata)

        # Should not process relationships (early return)
        assert not mapper.called


class TestBidirectionalRelationships:
    """Test bidirectional relationship handling."""

    def test_bidirectional_relationships(self):
        """Test that both sides of relationship can be set."""
        # This is a future feature - document expected behavior
        # For now, just verify both entities can have relationships

        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create bidirectional friendship
        alice = Person(name="Alice", age=30)
        bob = Person(name="Bob", age=28)

        alice.friends = [bob]
        bob.friends = [alice]

        # Save both
        repo = Repository(graph, Person)
        alice = repo.save(alice)
        bob = repo.save(bob)

        # Both should have IDs
        assert alice.id is not None
        assert bob.id is not None

        # Note: Currently requires saving both sides separately
        # Future enhancement: auto-sync bidirectional relationships


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
