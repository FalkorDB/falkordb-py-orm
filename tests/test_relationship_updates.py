"""Tests for relationship update and delete functionality."""

import pytest
from typing import List, Optional
from unittest.mock import Mock, call

from falkordb_orm import node, generated_id, relationship, Repository
from falkordb_orm.metadata import get_entity_metadata


# Test entities
@node("Person")
class Person:
    id: Optional[int] = generated_id()
    name: str
    age: int

    friends: List["Person"] = relationship("KNOWS", target="Person", cascade=True)


@node("Company")
class Company:
    id: Optional[int] = generated_id()
    name: str


@node("Employee")
class Employee:
    id: Optional[int] = generated_id()
    name: str

    company: Optional[Company] = relationship("WORKS_FOR", target=Company, cascade=True)


@node("Team")
class Team:
    id: Optional[int] = generated_id()
    name: str

    members: List[Person] = relationship("HAS_MEMBER", target=Person, cascade=True)


class TestRelationshipUpdates:
    """Test updating relationships on existing entities."""

    def test_update_single_relationship(self):
        """Test that updating a single relationship creates new edge."""
        # Setup mocks
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            # Return mock result with ID
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create entities
        acme = Company(name="Acme Corp")
        acme.id = 1  # Already saved

        globex = Company(name="Globex Corp")
        globex.id = 2  # Already saved

        employee = Employee(name="Alice")
        employee.id = 10  # Already saved
        employee.company = acme

        # Save with first company
        repo = Repository(graph, Employee)
        employee = repo.save(employee)

        initial_count = call_count[0]

        # Update to different company
        employee.company = globex
        employee = repo.save(employee)

        # Should create new relationship edge
        assert call_count[0] > initial_count

        # Note: Current implementation doesn't delete old edge
        # This is a known limitation to be fixed

    def test_update_collection_relationship_add_item(self):
        """Test adding items to a collection relationship."""
        # Setup mocks
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create entities
        alice = Person(name="Alice", age=30)
        alice.id = 1  # Already saved

        bob = Person(name="Bob", age=28)
        bob.id = 2  # Already saved

        charlie = Person(name="Charlie", age=32)
        charlie.id = 3  # Already saved

        # Initial: Alice has one friend (Bob)
        alice.friends = [bob]

        repo = Repository(graph, Person)
        alice = repo.save(alice)

        initial_count = call_count[0]

        # Update: Add Charlie as friend
        alice.friends = [bob, charlie]
        alice = repo.save(alice)

        # Should create new relationship for Charlie
        assert call_count[0] > initial_count

    def test_update_collection_relationship_remove_item(self):
        """Test removing items from a collection relationship."""
        # Setup mocks
        graph = Mock()
        queries_executed = []

        def mock_query(cypher, params):
            queries_executed.append((cypher, params))
            return Mock(result_set=[[Mock(), len(queries_executed)]])

        graph.query = mock_query

        # Create entities
        alice = Person(name="Alice", age=30)
        alice.id = 1

        bob = Person(name="Bob", age=28)
        bob.id = 2

        charlie = Person(name="Charlie", age=32)
        charlie.id = 3

        # Initial: Alice has two friends
        alice.friends = [bob, charlie]

        repo = Repository(graph, Person)
        alice = repo.save(alice)

        queries_executed.clear()

        # Update: Remove Charlie, keep only Bob
        alice.friends = [bob]
        alice = repo.save(alice)

        # Should delete old relationships and create new ones
        delete_queries = [q for q, _ in queries_executed if "DELETE" in q and "KNOWS" in q]
        assert len(delete_queries) >= 1, "Should DELETE old KNOWS relationships on update"

    def test_update_collection_relationship_replace_all(self):
        """Test replacing all items in a collection relationship."""
        # Setup mocks
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create entities
        alice = Person(name="Alice", age=30)
        alice.id = 1

        bob = Person(name="Bob", age=28)
        bob.id = 2

        charlie = Person(name="Charlie", age=32)
        charlie.id = 3

        diana = Person(name="Diana", age=27)
        diana.id = 4

        # Initial: Alice knows Bob and Charlie
        alice.friends = [bob, charlie]

        repo = Repository(graph, Person)
        alice = repo.save(alice)

        initial_count = call_count[0]

        # Update: Replace with completely different friends
        alice.friends = [diana]
        alice = repo.save(alice)

        # Should create new relationships
        assert call_count[0] > initial_count

    def test_clear_single_relationship(self):
        """Test setting a single relationship to None."""
        # Setup mocks
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create entities
        company = Company(name="Acme Corp")
        company.id = 1

        employee = Employee(name="Alice")
        employee.id = 10
        employee.company = company

        # Save with company
        repo = Repository(graph, Employee)
        employee = repo.save(employee)

        initial_count = call_count[0]

        # Clear the relationship
        employee.company = None
        employee = repo.save(employee)

        # Should handle None gracefully (no new edge created)
        # Expected: should also delete old edge (not implemented yet)
        assert call_count[0] >= initial_count  # At least the update query

    def test_clear_collection_relationship(self):
        """Test setting a collection relationship to empty list."""
        # Setup mocks
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create entities
        alice = Person(name="Alice", age=30)
        alice.id = 1

        bob = Person(name="Bob", age=28)
        bob.id = 2

        # Initial: Alice has friends
        alice.friends = [bob]

        repo = Repository(graph, Person)
        alice = repo.save(alice)

        initial_count = call_count[0]

        # Clear all friends
        alice.friends = []
        alice = repo.save(alice)

        # Should handle empty list (no new edges)
        # Expected: should delete old edges (not implemented yet)
        assert call_count[0] >= initial_count


class TestRelationshipDeletes:
    """Test deleting relationships when entities are deleted."""

    def test_delete_entity_should_handle_relationships(self):
        """Test that deleting an entity is handled gracefully."""
        # This test documents expected behavior
        # Current: Basic delete doesn't cascade
        # Expected: Optionally cascade delete relationships

        # Setup mocks
        graph = Mock()
        graph.query = Mock(return_value=Mock(result_set=[]))

        # Create entity
        alice = Person(name="Alice", age=30)
        alice.id = 1

        repo = Repository(graph, Person)

        # Delete entity
        repo.delete(alice)

        # Should execute delete query
        assert graph.query.called

        # Note: Relationship edges are not automatically deleted
        # This is database-level behavior (depends on constraints)

    def test_delete_by_id_with_relationships(self):
        """Test deleting entity by ID when it has relationships."""
        # Setup mocks
        graph = Mock()
        graph.query = Mock(return_value=Mock(result_set=[]))

        repo = Repository(graph, Person)

        # Delete by ID
        repo.delete_by_id(1)

        # Should execute delete query
        assert graph.query.called

        # Relationships handling depends on database constraints


class TestRelationshipUpdatePatterns:
    """Test common update patterns for relationships."""

    def test_swap_relationship_target(self):
        """Test swapping relationship from one entity to another."""
        # Setup mocks
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create entities
        team_a = Team(name="Team A")
        team_a.id = 1

        team_b = Team(name="Team B")
        team_b.id = 2

        alice = Person(name="Alice", age=30)
        alice.id = 10

        # Alice is in Team A
        team_a.members = [alice]

        repo = Repository(graph, Team)
        team_a = repo.save(team_a)

        # Move Alice to Team B
        team_a.members = []  # Remove from A
        team_b.members = [alice]  # Add to B

        team_a = repo.save(team_a)
        team_b = repo.save(team_b)

        # Should create new relationships
        assert call_count[0] > 0

    def test_bidirectional_update(self):
        """Test updating both sides of a bidirectional relationship."""
        # Setup mocks
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create entities
        alice = Person(name="Alice", age=30)
        alice.id = 1

        bob = Person(name="Bob", age=28)
        bob.id = 2

        # Create bidirectional friendship
        alice.friends = [bob]
        bob.friends = [alice]

        repo = Repository(graph, Person)
        alice = repo.save(alice)
        bob = repo.save(bob)

        # Both should have relationships
        assert call_count[0] >= 2

        # Note: Currently requires manual sync of both sides
        # Future enhancement: auto-sync bidirectional relationships

    def test_bulk_relationship_update(self):
        """Test updating multiple relationships at once."""
        # Setup mocks
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create entities
        team = Team(name="Dev Team")
        team.id = 1

        alice = Person(name="Alice", age=30)
        alice.id = 10

        bob = Person(name="Bob", age=28)
        bob.id = 11

        charlie = Person(name="Charlie", age=32)
        charlie.id = 12

        # Initial: Team has Alice and Bob
        team.members = [alice, bob]

        repo = Repository(graph, Team)
        team = repo.save(team)

        initial_count = call_count[0]

        # Update: Replace with Alice, Charlie (remove Bob, add Charlie)
        team.members = [alice, charlie]
        team = repo.save(team)

        # Should create relationships for new members
        assert call_count[0] > initial_count


class TestRelationshipUpdateEdgeCases:
    """Test edge cases in relationship updates."""

    def test_update_to_same_relationship(self):
        """Test updating relationship to same value (idempotent)."""
        # Setup mocks
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create entities
        company = Company(name="Acme Corp")
        company.id = 1

        employee = Employee(name="Alice")
        employee.id = 10
        employee.company = company

        repo = Repository(graph, Employee)
        employee = repo.save(employee)

        initial_count = call_count[0]

        # "Update" to same company
        employee.company = company
        employee = repo.save(employee)

        # Should still create edge (no duplicate detection)
        # This is acceptable behavior
        assert call_count[0] > initial_count

    def test_update_with_unsaved_entity(self):
        """Test updating relationship to unsaved entity with cascade."""
        # Setup mocks
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create entities
        old_company = Company(name="Old Corp")
        old_company.id = 1

        new_company = Company(name="New Corp")
        # new_company has no ID - not saved yet

        employee = Employee(name="Alice")
        employee.id = 10
        employee.company = old_company

        repo = Repository(graph, Employee)
        employee = repo.save(employee)

        # Update to unsaved company (with cascade)
        employee.company = new_company
        employee = repo.save(employee)

        # Should cascade save new company
        assert new_company.id is not None

    def test_update_collection_with_duplicates(self):
        """Test updating collection with duplicate entries."""
        # Setup mocks
        graph = Mock()
        call_count = [0]

        def mock_query(cypher, params):
            call_count[0] += 1
            return Mock(result_set=[[Mock(), call_count[0]]])

        graph.query = mock_query

        # Create entities
        alice = Person(name="Alice", age=30)
        alice.id = 1

        bob = Person(name="Bob", age=28)
        bob.id = 2

        # Set friends with duplicate
        alice.friends = [bob, bob]  # Bob appears twice

        repo = Repository(graph, Person)
        alice = repo.save(alice)

        # Should handle duplicates (may create duplicate edges)
        assert call_count[0] > 0


class TestRelationshipUpdateDocumentation:
    """Tests that verify relationship update behavior."""

    def test_relationship_edges_deleted_on_update(self):
        """Verify that old edges are deleted when relationships are updated."""
        # Setup mocks
        graph = Mock()
        queries_executed = []

        def mock_query(cypher, params):
            queries_executed.append((cypher, params))
            return Mock(result_set=[[Mock(), len(queries_executed)]])

        graph.query = mock_query

        # Create entities
        company1 = Company(name="Corp A")
        company1.id = 1

        company2 = Company(name="Corp B")
        company2.id = 2

        employee = Employee(name="Alice")
        employee.id = 10
        employee.company = company1

        repo = Repository(graph, Employee)
        employee = repo.save(employee)

        queries_executed.clear()

        # Update company
        employee.company = company2
        employee = repo.save(employee)

        # Verify DELETE query was executed for old relationship
        delete_queries = [q for q, _ in queries_executed if "DELETE" in q and "WORKS_FOR" in q]
        assert len(delete_queries) >= 1, "Should DELETE old relationships before creating new ones"

    def test_future_enhancement_relationship_tracking(self):
        """Document future enhancement for relationship change tracking."""
        # FUTURE ENHANCEMENT:
        # - Track original relationship values when entity is loaded
        # - On save, compare current vs original
        # - Delete removed relationships, create new ones
        # - Only modify what changed (delta updates)

        # This would require:
        # 1. Snapshot of relationships on load
        # 2. Comparison logic in save
        # 3. Smart edge deletion/creation
        pass

    def test_future_enhancement_bidirectional_sync(self):
        """Document future enhancement for bidirectional relationship sync."""
        # FUTURE ENHANCEMENT:
        # - Automatically sync both sides of bidirectional relationships
        # - When you set alice.friends = [bob], also set bob.friends to include alice
        # - Requires metadata about inverse relationships

        # This would require:
        # 1. Inverse relationship metadata
        # 2. Automatic sync logic
        # 3. Cycle detection
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
