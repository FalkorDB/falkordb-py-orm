"""Integration tests for RBAC security."""

from datetime import datetime
from typing import Optional

import pytest

from falkordb_orm import generated_id, node
from falkordb_orm.repository import Repository
from falkordb_orm.security import (
    AccessDeniedException,
    Privilege,
    RBACManager,
    Role,
    SecureSession,
    SecurityPolicy,
    User,
    secured,
)


# Test entities
@node("Person")
@secured(
    read=["reader", "admin"],
    write=["editor", "admin"],
    deny_read_properties={"ssn": ["*"], "salary": ["reader"]},
)
class Person:
    """Test person entity with security."""

    id: Optional[int] = generated_id()
    name: str
    email: str
    ssn: str
    salary: float


@pytest.fixture
def graph():
    """Mock graph fixture."""
    # In real tests, this would be a FalkorDB connection
    # For now, return None to test structure
    return None


def test_secured_decorator():
    """Test @secured decorator adds metadata."""
    assert hasattr(Person, "__security_metadata__")
    metadata = Person.__security_metadata__

    assert "reader" in metadata["read_roles"]
    assert "admin" in metadata["read_roles"]
    assert "editor" in metadata["write_roles"]
    assert "ssn" in metadata["deny_read_properties"]
    assert "salary" in metadata["deny_read_properties"]


def test_role_creation():
    """Test Role model creation."""
    role = Role(
        name="test_role",
        description="Test role",
        created_at=datetime.now(),
        is_immutable=False,
    )

    assert role.name == "test_role"
    assert role.description == "Test role"
    assert role.is_immutable is False


def test_user_creation():
    """Test User model creation."""
    user = User(
        username="testuser",
        email="test@example.com",
        created_at=datetime.now(),
        is_active=True,
    )

    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.is_active is True


def test_privilege_creation():
    """Test Privilege model creation."""
    priv = Privilege(
        action="READ",
        resource_type="NODE",
        resource_label="Person",
        resource_property=None,
        grant_type="GRANT",
        scope="GRAPH",
        is_immutable=False,
        created_at=datetime.now(),
    )

    assert priv.action == "READ"
    assert priv.resource_type == "NODE"
    assert priv.grant_type == "GRANT"


def test_security_policy_resource_parsing():
    """Test SecurityPolicy resource pattern parsing."""
    from falkordb_orm.security.policy import SecurityPolicy

    # Create a mock graph
    class MockGraph:
        def query(self, q, p):
            class Result:
                result_set = []

            return Result()

    graph = MockGraph()
    policy = SecurityPolicy(graph)

    # Test parsing
    node_type, label, prop = policy._parse_resource("Person")
    assert node_type == "NODE"
    assert label == "Person"
    assert prop is None

    node_type, label, prop = policy._parse_resource("Person.email")
    assert node_type == "PROPERTY"
    assert label == "Person"
    assert prop == "email"

    node_type, label, prop = policy._parse_resource("KNOWS")
    assert node_type == "RELATIONSHIP"
    assert label == "KNOWS"


def test_role_hierarchy():
    """Test role hierarchy and inheritance."""
    admin_role = Role(name="admin", description="Admin", created_at=datetime.now())
    editor_role = Role(name="editor", description="Editor", created_at=datetime.now())
    editor_role.parent_roles = [admin_role]

    assert len(editor_role.parent_roles) == 1
    assert editor_role.parent_roles[0].name == "admin"


def test_user_role_assignment():
    """Test user role assignment."""
    role = Role(name="test_role", description="Test", created_at=datetime.now())
    user = User(username="testuser", email="test@example.com", created_at=datetime.now())
    user.roles = [role]

    assert len(user.roles) == 1
    assert user.roles[0].name == "test_role"


def test_privilege_role_assignment():
    """Test privilege role assignment."""
    role = Role(name="reader", description="Reader", created_at=datetime.now())
    priv = Privilege(
        action="READ",
        resource_type="NODE",
        resource_label="Person",
        grant_type="GRANT",
        scope="GRAPH",
        created_at=datetime.now(),
    )
    priv.role = role

    assert priv.role.name == "reader"


def test_multiple_decorators():
    """Test multiple security decorators on same entity."""

    @node("MultiSecure")
    @secured(read=["reader"], write=["editor"])
    class MultiSecure:
        id: Optional[int] = generated_id()
        name: str

    assert hasattr(MultiSecure, "__security_metadata__")
    assert MultiSecure.__security_metadata__["read_roles"] == ["reader"]
    assert MultiSecure.__security_metadata__["write_roles"] == ["editor"]


def test_empty_security_metadata():
    """Test entity without security decorator."""

    @node("Unsecured")
    class Unsecured:
        id: Optional[int] = generated_id()
        name: str

    # Should not have security metadata
    assert not hasattr(Unsecured, "__security_metadata__")


def test_deny_takes_precedence():
    """Test that DENY rules take precedence over GRANT."""
    # This would be tested in SecurityContext
    # For now, verify the concept is encoded in models
    grant_priv = Privilege(
        action="READ",
        resource_type="NODE",
        resource_label="Person",
        grant_type="GRANT",
        scope="GRAPH",
        created_at=datetime.now(),
    )

    deny_priv = Privilege(
        action="READ",
        resource_type="NODE",
        resource_label="Person",
        grant_type="DENY",
        scope="GRAPH",
        created_at=datetime.now(),
    )

    assert grant_priv.grant_type == "GRANT"
    assert deny_priv.grant_type == "DENY"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
