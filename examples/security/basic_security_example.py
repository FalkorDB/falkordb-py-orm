"""Basic security example demonstrating RBAC features."""

from datetime import datetime

from falkordb import FalkorDB

from falkordb_orm import generated_id, node
from falkordb_orm.repository import Repository
from falkordb_orm.security import (
    Role,
    SecurityPolicy,
    SecureSession,
    User,
    secured,
)


# Define entity with security
@node("Person")
@secured(
    read=["reader", "admin"],
    write=["editor", "admin"],
    deny_read_properties={"ssn": ["*"], "salary": ["reader"]},
)
class Person:
    """Person entity with security metadata."""

    id: int | None = generated_id()
    name: str
    email: str
    ssn: str
    salary: float


def main():
    """Demonstrate basic RBAC features."""
    # Initialize graph
    graph = FalkorDB(host="localhost", port=6379)

    # Create security policy
    policy = SecurityPolicy(graph)

    # Create roles in graph
    role_repo = Repository(graph, Role)

    admin_role = Role(
        name="admin",
        description="Administrator role",
        created_at=datetime.now(),
        is_immutable=True,
    )
    role_repo.save(admin_role)

    reader_role = Role(
        name="reader", description="Read-only role", created_at=datetime.now()
    )
    role_repo.save(reader_role)

    editor_role = Role(
        name="editor", description="Edit role", created_at=datetime.now()
    )
    role_repo.save(editor_role)

    # Grant privileges
    policy.grant("READ", "Person", to="reader")
    policy.grant("WRITE", "Person", to="editor")
    policy.deny("READ", "Person.ssn", to="reader")
    policy.deny("READ", "Person.salary", to="reader")

    # Create users
    user_repo = Repository(graph, User)

    alice = User(
        username="alice",
        email="alice@example.com",
        created_at=datetime.now(),
        is_active=True,
    )
    alice.roles = [reader_role]
    user_repo.save(alice)

    bob = User(
        username="bob",
        email="bob@example.com",
        created_at=datetime.now(),
        is_active=True,
    )
    bob.roles = [editor_role]
    user_repo.save(bob)

    admin_user = User(
        username="admin",
        email="admin@example.com",
        created_at=datetime.now(),
        is_active=True,
    )
    admin_user.roles = [admin_role]
    user_repo.save(admin_user)

    # Create test person (as admin)
    admin_session = SecureSession(graph, admin_user)
    person_repo = admin_session.get_repository(Person)

    person = Person(
        name="John Doe",
        email="john@example.com",
        ssn="123-45-6789",
        salary=75000.0,
    )
    person_repo.save(person)
    print(f"✓ Created person: {person.name}")

    # Test read access as reader (Alice)
    alice_session = SecureSession(graph, alice)
    alice_person_repo = alice_session.get_repository(Person)

    try:
        person_for_alice = alice_person_repo.find_by_id(person.id)
        print(f"\n✓ Alice can read: {person_for_alice.name}")
        print(f"  Email: {person_for_alice.email}")
        print(f"  SSN: {person_for_alice.ssn} (should be None)")
        print(f"  Salary: {person_for_alice.salary} (should be None)")
    except Exception as e:
        print(f"✗ Alice cannot read: {e}")

    # Test write access as reader (should fail)
    try:
        person.name = "Jane Doe"
        alice_person_repo.save(person)
        print("\n✗ Alice should not be able to write!")
    except Exception as e:
        print(f"\n✓ Alice cannot write: {e}")

    # Test write access as editor (Bob)
    bob_session = SecureSession(graph, bob)
    bob_person_repo = bob_session.get_repository(Person)

    try:
        person.name = "Jane Doe"
        bob_person_repo.save(person)
        print(f"\n✓ Bob can write: updated name to {person.name}")
    except Exception as e:
        print(f"\n✗ Bob cannot write: {e}")

    # Test impersonation
    print("\n--- Testing Impersonation ---")
    with admin_session.impersonate(alice):
        # Operations now use Alice's permissions
        try:
            test_person = person_repo.find_by_id(person.id)
            print(f"✓ Impersonating Alice: {test_person.name}")
            print(f"  SSN (should be None): {test_person.ssn}")
        except Exception as e:
            print(f"✗ Impersonation failed: {e}")

    print("\n✓ Security example completed!")


if __name__ == "__main__":
    main()
