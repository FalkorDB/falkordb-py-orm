"""RBAC Manager API example for admin operations."""

from datetime import datetime

from falkordb import FalkorDB

from falkordb_orm import generated_id, node
from falkordb_orm.repository import Repository
from falkordb_orm.security import (
    RBACManager,
    Role,
    SecureSession,
    User,
)


@node("Document")
class Document:
    """Document entity for testing."""

    id: int | None = generated_id()
    title: str
    content: str
    owner_id: int


def main():
    """Demonstrate RBAC Manager API."""
    print("=== RBAC Manager API Example ===\n")

    # Initialize
    graph = FalkorDB(host="localhost", port=6379)

    # Create admin user and session
    admin_role = Role(
        name="admin",
        description="Administrator",
        created_at=datetime.now(),
        is_immutable=True,
    )
    role_repo = Repository(graph, Role)
    role_repo.save(admin_role)

    admin_user = User(
        username="admin",
        email="admin@example.com",
        created_at=datetime.now(),
        is_active=True,
    )
    admin_user.roles = [admin_role]
    user_repo = Repository(graph, User)
    user_repo.save(admin_user)

    # Create admin session and RBAC manager
    admin_session = SecureSession(graph, admin_user)
    rbac = RBACManager(graph, admin_session.security_context)

    print("✓ Admin session created\n")

    # === USER MANAGEMENT ===
    print("--- User Management ---")

    # Create users
    alice = rbac.create_user(
        username="alice", email="alice@example.com", roles=["reader"]
    )
    print(f"✓ Created user: {alice.username}")

    bob = rbac.create_user(username="bob", email="bob@example.com", roles=["editor"])
    print(f"✓ Created user: {bob.username}")

    # List users
    users = rbac.list_users()
    print(f"✓ Total users: {len(users)}")

    # Update user
    rbac.update_user("alice", email="alice.smith@example.com")
    print("✓ Updated Alice's email")

    print()

    # === ROLE MANAGEMENT ===
    print("--- Role Management ---")

    # Create roles
    analyst_role = rbac.create_role(
        name="analyst",
        description="Data analyst with read access",
        parent_roles=["reader"],
    )
    print(f"✓ Created role: {analyst_role.name} (inherits from reader)")

    reviewer_role = rbac.create_role(
        name="reviewer", description="Can review documents"
    )
    print(f"✓ Created role: {reviewer_role.name}")

    # List roles
    roles = rbac.list_roles()
    print(f"✓ Total roles: {len(roles)}")

    print()

    # === ROLE ASSIGNMENT ===
    print("--- Role Assignment ---")

    # Assign role to user
    rbac.assign_role("alice", "analyst")
    print("✓ Assigned 'analyst' role to Alice")

    # Get user's effective roles
    alice_roles = rbac.get_user_roles("alice")
    print(f"✓ Alice's effective roles: {', '.join(alice_roles)}")

    print()

    # === PRIVILEGE MANAGEMENT ===
    print("--- Privilege Management ---")

    # Grant privileges
    priv1 = rbac.grant_privilege(
        role_name="analyst",
        action="READ",
        resource_type="NODE",
        resource_label="Document",
    )
    print("✓ Granted READ access to Document for analyst")

    priv2 = rbac.grant_privilege(
        role_name="editor",
        action="WRITE",
        resource_type="NODE",
        resource_label="Document",
    )
    print("✓ Granted WRITE access to Document for editor")

    # Deny sensitive operations
    priv3 = rbac.deny_privilege(
        role_name="reader",
        action="DELETE",
        resource_type="NODE",
        resource_label="Document",
    )
    print("✓ Denied DELETE access to Document for reader")

    # List privileges for role
    analyst_privs = rbac.list_privileges(role_name="analyst")
    print(f"✓ Analyst has {len(analyst_privs)} privileges")

    print()

    # === AUDIT LOGS ===
    print("--- Audit Logs ---")

    # Query recent audit logs
    logs = rbac.query_audit_logs(limit=10)
    print(f"✓ Retrieved {len(logs)} audit log entries")

    # Show last 3 operations
    print("\nRecent operations:")
    for log in logs[:3]:
        print(
            f"  - {log['username']}: {log['action']} on {log['resource']} "
            f"[{'✓' if log['granted'] else '✗'}]"
        )

    print()

    # === ROLE REVOCATION ===
    print("--- Role Revocation ---")

    rbac.revoke_role("alice", "reader")
    print("✓ Revoked 'reader' role from Alice")

    alice_roles_after = rbac.get_user_roles("alice")
    print(f"✓ Alice's roles now: {', '.join(alice_roles_after)}")

    print()

    # === PRIVILEGE REVOCATION ===
    print("--- Privilege Revocation ---")

    # Note: In real usage, you'd get the privilege ID when granting
    analyst_privs_before = rbac.list_privileges(role_name="analyst")
    if analyst_privs_before:
        priv_to_revoke = analyst_privs_before[0]
        rbac.revoke_privilege(priv_to_revoke.id)
        print(f"✓ Revoked privilege {priv_to_revoke.id}")

    print()

    # === CLEANUP (Optional) ===
    print("--- Cleanup ---")

    # Delete user
    rbac.delete_user("bob")
    print("✓ Deleted user 'bob'")

    # Note: Cannot delete roles if assigned to users
    try:
        rbac.delete_role("analyst")
        print("✗ Should not have been able to delete role with users!")
    except Exception as e:
        print(f"✓ Cannot delete role with users: {e}")

    # Revoke role first, then delete
    rbac.revoke_role("alice", "analyst")
    rbac.delete_role("analyst")
    print("✓ Deleted role 'analyst' after revoking from all users")

    print("\n✓ RBAC Manager example completed!")


if __name__ == "__main__":
    main()
