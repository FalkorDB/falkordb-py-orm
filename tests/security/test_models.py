"""Tests for security models."""

from datetime import datetime

import pytest

from falkordb_orm.security import Privilege, Role, User
from falkordb_orm.security.store import InMemoryRBACStore


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
    assert priv.resource_label == "Person"
    assert priv.grant_type == "GRANT"


def test_in_memory_store_built_in_roles():
    """Test built-in roles initialization."""
    store = InMemoryRBACStore()

    assert "PUBLIC" in store.roles
    assert "reader" in store.roles
    assert "editor" in store.roles
    assert "publisher" in store.roles
    assert "admin" in store.roles

    # PUBLIC should be immutable
    assert store.roles["PUBLIC"].is_immutable is True


def test_in_memory_store_add_role():
    """Test adding role to store."""
    store = InMemoryRBACStore()

    role = Role(
        name="analyst", description="Data analyst", created_at=datetime.now()
    )
    store.add_role(role)

    assert "analyst" in store.roles
    assert store.get_role("analyst") == role


def test_in_memory_store_add_user():
    """Test adding user to store."""
    store = InMemoryRBACStore()

    user = User(
        username="alice",
        email="alice@example.com",
        created_at=datetime.now(),
    )
    store.add_user(user)

    assert "alice" in store.users
    assert store.get_user("alice") == user


def test_in_memory_store_load_from_json(tmp_path):
    """Test loading config from JSON."""
    config_file = tmp_path / "rbac.json"
    config_file.write_text(
        """
    {
        "roles": [
            {"name": "analyst", "description": "Data analyst"}
        ],
        "users": [
            {"username": "alice", "email": "alice@example.com", "roles": ["analyst", "reader"]}
        ],
        "privileges": [
            {
                "role": "analyst",
                "action": "READ",
                "resource_type": "NODE",
                "resource_label": "Person"
            }
        ]
    }
    """
    )

    store = InMemoryRBACStore()
    store.load_from_json(str(config_file))

    assert "analyst" in store.roles
    assert "alice" in store.users
    assert len(store.privileges) > 0

    alice = store.get_user("alice")
    assert len(alice.roles) == 2
    assert any(r.name == "analyst" for r in alice.roles)
