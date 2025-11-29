"""Tests for session management."""

import pytest
from typing import Optional
from unittest.mock import Mock, MagicMock

from falkordb_orm import node, property, generated_id
from falkordb_orm.session import Session
from falkordb_orm.async_session import AsyncSession
from falkordb_orm.exceptions import QueryException, EntityNotFoundException


@node("Person")
class Person:
    """Test Person entity."""

    id: Optional[int] = generated_id()
    name: str = property()
    age: int = property()
    email: Optional[str] = property()


class TestSessionBasics:
    """Test basic session functionality."""

    def test_session_initialization(self):
        """Test session initialization."""
        graph = Mock()
        session = Session(graph)

        assert session.graph == graph
        assert session.is_active
        assert not session.has_pending_changes

    def test_context_manager_commit(self):
        """Test context manager commits on success."""
        graph = Mock()
        graph.query.return_value.result_set = [[None, 1]]

        person = Person(name="Alice", age=25)

        with Session(graph) as session:
            session.add(person)

        # Session should be closed after context exit
        assert not session.is_active

        # Should have called query (for INSERT)
        assert graph.query.called

    def test_context_manager_rollback_on_exception(self):
        """Test context manager rolls back on exception."""
        graph = Mock()

        person = Person(name="Alice", age=25)

        with pytest.raises(ValueError):
            with Session(graph) as session:
                session.add(person)
                raise ValueError("Test error")

        # Session should be closed
        assert not session.is_active

        # Should not have called query (rollback occurred)
        assert not graph.query.called

    def test_close(self):
        """Test session close."""
        graph = Mock()
        session = Session(graph)

        person = Person(name="Alice", age=25)
        session.add(person)

        assert session.has_pending_changes

        session.close()

        assert not session.is_active
        assert not session.has_pending_changes

    def test_closed_session_raises_error(self):
        """Test operations on closed session raise error."""
        graph = Mock()
        session = Session(graph)
        session.close()

        with pytest.raises(RuntimeError, match="Session is closed"):
            session.add(Person(name="Alice", age=25))

        with pytest.raises(RuntimeError, match="Session is closed"):
            session.get(Person, 1)

        with pytest.raises(RuntimeError, match="Session is closed"):
            session.commit()


class TestSessionAdd:
    """Test session add operations."""

    def test_add_new_entity(self):
        """Test adding new entity."""
        graph = Mock()
        session = Session(graph)

        person = Person(name="Alice", age=25)
        session.add(person)

        assert session.has_pending_changes
        assert person in session._new

    def test_add_same_entity_twice(self):
        """Test adding same entity twice doesn't duplicate."""
        graph = Mock()
        session = Session(graph)

        person = Person(name="Alice", age=25)
        session.add(person)
        session.add(person)

        # Should only be added once
        assert len(session._new) == 1

    def test_add_deleted_entity_marks_as_dirty(self):
        """Test adding deleted entity marks it as dirty."""
        graph = Mock()
        session = Session(graph)

        person = Person(id=1, name="Alice", age=25)
        session.delete(person)
        assert person in session._deleted

        session.add(person)

        # Should be removed from deleted and added to dirty
        assert person not in session._deleted
        assert person in session._dirty


class TestSessionDelete:
    """Test session delete operations."""

    def test_delete_entity(self):
        """Test deleting entity."""
        graph = Mock()
        session = Session(graph)

        person = Person(id=1, name="Alice", age=25)
        session.delete(person)

        assert session.has_pending_changes
        assert person in session._deleted

    def test_delete_new_entity_removes_from_new(self):
        """Test deleting new entity removes it from new set."""
        graph = Mock()
        session = Session(graph)

        person = Person(name="Alice", age=25)
        session.add(person)
        assert person in session._new

        session.delete(person)

        # Should be removed from new, not added to deleted
        assert person not in session._new
        assert person not in session._deleted

    def test_delete_removes_from_identity_map(self):
        """Test delete removes entity from identity map."""
        graph = Mock()
        session = Session(graph)

        person = Person(id=1, name="Alice", age=25)
        key = (Person, 1)
        session._identity_map[key] = person

        session.delete(person)

        assert key not in session._identity_map


class TestSessionGet:
    """Test session get operations."""

    def test_get_from_identity_map(self):
        """Test get returns entity from identity map."""
        graph = Mock()
        session = Session(graph)

        person = Person(id=1, name="Alice", age=25)
        key = (Person, 1)
        session._identity_map[key] = person

        result = session.get(Person, 1)

        assert result is person
        # Should not query database
        assert not graph.query.called

    def test_get_from_database(self):
        """Test get loads entity from database."""
        graph = Mock()

        # Mock database result
        result_mock = Mock()
        result_mock.result_set = [[Mock(properties={"id": 1, "name": "Alice", "age": 25})]]
        result_mock.header = ["n"]
        graph.query.return_value = result_mock

        session = Session(graph)
        person = session.get(Person, 1)

        assert person is not None
        # Should be added to identity map
        key = (Person, 1)
        assert key in session._identity_map
        assert session._identity_map[key] is person

    def test_get_returns_none_when_not_found(self):
        """Test get returns None when entity not found."""
        graph = Mock()

        # Mock empty result
        result_mock = Mock()
        result_mock.result_set = []
        graph.query.return_value = result_mock

        session = Session(graph)
        person = session.get(Person, 999)

        assert person is None


class TestSessionFlushAndCommit:
    """Test session flush and commit operations."""

    def test_flush_inserts_new_entities(self):
        """Test flush inserts new entities."""
        graph = Mock()
        graph.query.return_value.result_set = [[None, 1]]

        session = Session(graph)
        person = Person(name="Alice", age=25)
        session.add(person)

        session.flush()

        # Should have called query for INSERT
        assert graph.query.called
        # New set should be cleared
        assert len(session._new) == 0

    def test_flush_updates_dirty_entities(self):
        """Test flush updates dirty entities."""
        graph = Mock()
        graph.query.return_value.result_set = [[None, 1]]

        session = Session(graph)

        # Simulate entity loaded from database
        person = Person(id=1, name="Alice", age=25)
        session._identity_map[(Person, 1)] = person
        session._capture_state(person)

        # Modify entity
        person.age = 26
        session._dirty.add(person)

        session.flush()

        # Should have called query for UPDATE
        assert graph.query.called
        # Dirty set should be cleared
        assert len(session._dirty) == 0

    def test_flush_skips_unmodified_entities(self):
        """Test flush skips unmodified entities in dirty set."""
        graph = Mock()

        session = Session(graph)

        # Add entity but don't modify it
        person = Person(id=1, name="Alice", age=25)
        session._identity_map[(Person, 1)] = person
        session._capture_state(person)
        session._dirty.add(person)

        session.flush()

        # Should not call query since entity wasn't modified
        assert not graph.query.called

    def test_flush_deletes_entities(self):
        """Test flush deletes entities."""
        graph = Mock()
        graph.query.return_value.result_set = []

        session = Session(graph)
        person = Person(id=1, name="Alice", age=25)
        session.delete(person)

        session.flush()

        # Should have called query for DELETE
        assert graph.query.called
        # Deleted set should be cleared
        assert len(session._deleted) == 0

    def test_commit_flushes_and_commits(self):
        """Test commit flushes changes."""
        graph = Mock()
        graph.query.return_value.result_set = [[None, 1]]

        session = Session(graph)
        person = Person(name="Alice", age=25)
        session.add(person)

        session.commit()

        # Should have flushed (called query)
        assert graph.query.called
        assert not session.has_pending_changes


class TestSessionRollback:
    """Test session rollback operations."""

    def test_rollback_clears_pending_changes(self):
        """Test rollback clears all pending changes."""
        graph = Mock()
        session = Session(graph)

        person1 = Person(name="Alice", age=25)
        person2 = Person(id=1, name="Bob", age=30)
        person3 = Person(id=2, name="Charlie", age=35)

        session.add(person1)
        session._dirty.add(person2)
        session.delete(person3)

        assert session.has_pending_changes

        session.rollback()

        assert not session.has_pending_changes
        assert len(session._new) == 0
        assert len(session._dirty) == 0
        assert len(session._deleted) == 0

    def test_rollback_restores_entity_state(self):
        """Test rollback restores original entity state."""
        graph = Mock()
        session = Session(graph)

        # Simulate entity loaded from database
        person = Person(id=1, name="Alice", age=25)
        session._identity_map[(Person, 1)] = person
        session._capture_state(person)

        # Modify entity
        person.age = 30
        person.name = "Alicia"

        # Rollback
        session.rollback()

        # Entity should be restored
        assert person.age == 25
        assert person.name == "Alice"


class TestIdentityMap:
    """Test identity map functionality."""

    def test_identity_map_prevents_duplicate_instances(self):
        """Test identity map returns same instance for same ID."""
        graph = Mock()

        # Mock database result
        result_mock = Mock()
        result_mock.result_set = [[Mock(properties={"id": 1, "name": "Alice", "age": 25})]]
        result_mock.header = ["n"]
        graph.query.return_value = result_mock

        session = Session(graph)

        person1 = session.get(Person, 1)
        person2 = session.get(Person, 1)

        # Should be same instance
        assert person1 is person2

        # Database should only be queried once
        assert graph.query.call_count == 1

    def test_identity_map_different_entities(self):
        """Test identity map distinguishes different entities."""
        graph = Mock()

        # Mock query to return empty result for ID=2
        result_mock = Mock()
        result_mock.result_set = []
        graph.query.return_value = result_mock

        session = Session(graph)

        person = Person(id=1, name="Alice", age=25)
        session._identity_map[(Person, 1)] = person

        # Different ID should not be in identity map
        result = session.get(Person, 2)
        assert result is None  # Not found in database

    def test_insert_adds_to_identity_map(self):
        """Test inserting entity adds it to identity map."""
        graph = Mock()
        graph.query.return_value.result_set = [[None, 1]]

        session = Session(graph)
        person = Person(name="Alice", age=25)
        session.add(person)
        session.flush()

        # Should be in identity map with ID 1
        key = (Person, 1)
        assert key in session._identity_map
        assert session._identity_map[key] is person


class TestChangeTracking:
    """Test change tracking functionality."""

    def test_detect_property_change(self):
        """Test detecting property changes."""
        graph = Mock()
        session = Session(graph)

        person = Person(id=1, name="Alice", age=25)
        session._capture_state(person)

        # Modify property
        person.age = 26

        assert session._is_entity_modified(person)

    def test_no_change_detected_when_unmodified(self):
        """Test no change detected for unmodified entity."""
        graph = Mock()
        session = Session(graph)

        person = Person(id=1, name="Alice", age=25)
        session._capture_state(person)

        assert not session._is_entity_modified(person)

    def test_detect_multiple_property_changes(self):
        """Test detecting multiple property changes."""
        graph = Mock()
        session = Session(graph)

        person = Person(id=1, name="Alice", age=25, email="alice@example.com")
        session._capture_state(person)

        # Modify multiple properties
        person.age = 26
        person.email = "alice.new@example.com"

        assert session._is_entity_modified(person)

    def test_state_capture_on_get(self):
        """Test state is captured when entity is loaded."""
        graph = Mock()

        # Mock database result
        result_mock = Mock()
        result_mock.result_set = [[Mock(properties={"id": 1, "name": "Alice", "age": 25})]]
        result_mock.header = ["n"]
        graph.query.return_value = result_mock

        session = Session(graph)
        person = session.get(Person, 1)

        # Original state should be captured
        entity_id = id(person)
        assert entity_id in session._original_state


class TestAsyncSession:
    """Test async session functionality."""

    @pytest.mark.asyncio
    async def test_async_session_context_manager(self):
        """Test async session context manager."""
        graph = Mock()

        # Mock async query
        async def mock_query(*args, **kwargs):
            result = Mock()
            result.result_set = [[None, 1]]
            return result

        graph.query = mock_query

        person = Person(name="Alice", age=25)

        async with AsyncSession(graph) as session:
            session.add(person)

        # Session should be closed
        assert not session.is_active

    @pytest.mark.asyncio
    async def test_async_session_get(self):
        """Test async session get."""
        graph = Mock()

        # Mock async query
        async def mock_query(*args, **kwargs):
            result = Mock()
            result.result_set = [[Mock(properties={"id": 1, "name": "Alice", "age": 25})]]
            result.header = ["n"]
            return result

        graph.query = mock_query

        session = AsyncSession(graph)
        person = await session.get(Person, 1)

        assert person is not None
        key = (Person, 1)
        assert key in session._identity_map

    @pytest.mark.asyncio
    async def test_async_session_commit(self):
        """Test async session commit."""
        graph = Mock()

        # Mock async query
        async def mock_query(*args, **kwargs):
            result = Mock()
            result.result_set = [[None, 1]]
            return result

        graph.query = mock_query

        session = AsyncSession(graph)
        person = Person(name="Alice", age=25)
        session.add(person)

        await session.commit()

        assert not session.has_pending_changes

    @pytest.mark.asyncio
    async def test_async_session_rollback(self):
        """Test async session rollback."""
        graph = Mock()
        session = AsyncSession(graph)

        person = Person(name="Alice", age=25)
        session.add(person)

        await session.rollback()

        assert not session.has_pending_changes


class TestSessionEdgeCases:
    """Test session edge cases."""

    def test_delete_entity_without_id(self):
        """Test deleting entity without ID doesn't raise during delete call."""
        graph = Mock()
        session = Session(graph)

        person = Person(name="Alice", age=25)

        # Should not raise
        session.delete(person)

        # But flush should raise QueryException (wrapping EntityNotFoundException)
        with pytest.raises(QueryException):
            session.flush()

    def test_multiple_flush_calls(self):
        """Test multiple flush calls work correctly."""
        graph = Mock()
        graph.query.return_value.result_set = [[None, 1]]

        session = Session(graph)

        person1 = Person(name="Alice", age=25)
        session.add(person1)
        session.flush()

        person2 = Person(name="Bob", age=30)
        session.add(person2)
        session.flush()

        # Both flushes should succeed
        assert graph.query.call_count == 2

    def test_properties_after_close(self):
        """Test session properties after close."""
        graph = Mock()
        session = Session(graph)

        session.close()

        assert not session.is_active
        assert not session.has_pending_changes
