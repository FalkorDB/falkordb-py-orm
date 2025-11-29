# FalkorDB ORM Security Module (RBAC)

## Overview

The security module provides enterprise-grade Role-Based Access Control (RBAC) for FalkorDB Python ORM. It includes fine-grained access control, property-level security, query rewriting, and comprehensive audit capabilities.

## Features

✅ **Implemented (Sprints 1-3)**:
- ✅ Security metadata models (Role, User, Privilege, AuditLog)
- ✅ Policy DSL for declarative security management
- ✅ Security decorators (`@secured`, `@row_level_security`)
- ✅ In-memory RBAC store with JSON/YAML config loading
- ✅ SecurityContext for permission checking
- ✅ SecureRepository with access control enforcement
- ✅ SecureSession with impersonation support
- ✅ Built-in roles (PUBLIC, reader, editor, publisher, admin)

🚧 **Planned (Sprints 4-6)**:
- ⏳ Graph-stored RBAC with caching
- ⏳ RBACManager API for client applications
- ⏳ Advanced row-level security with query rewriting
- ⏳ Dynamic policies based on graph relationships
- ⏳ Comprehensive audit logging
- ⏳ Performance optimization and benchmarking

## Quick Start

### 1. Define Entities with Security

```python
from falkordb_orm import node, generated_id
from falkordb_orm.security import secured

@node("Person")
@secured(
    read=["reader", "admin"],
    write=["editor", "admin"],
    deny_read_properties={
        "ssn": ["*"],  # Nobody can read SSN
        "salary": ["reader"]  # Readers cannot see salary
    }
)
class Person:
    id: int | None = generated_id()
    name: str
    email: str
    ssn: str
    salary: float
```

### 2. Create Roles and Users

```python
from datetime import datetime
from falkordb_orm.repository import Repository
from falkordb_orm.security import Role, User

# Create roles
role_repo = Repository(graph, Role)

reader_role = Role(
    name="reader",
    description="Read-only access",
    created_at=datetime.now()
)
role_repo.save(reader_role)

# Create user with role
user_repo = Repository(graph, User)

alice = User(
    username="alice",
    email="alice@example.com",
    created_at=datetime.now(),
    is_active=True
)
alice.roles = [reader_role]
user_repo.save(alice)
```

### 3. Grant Privileges

```python
from falkordb_orm.security import SecurityPolicy

policy = SecurityPolicy(graph)

# Grant READ access to Person
policy.grant("READ", "Person", to="reader")

# Deny access to sensitive properties
policy.deny("READ", "Person.ssn", to="reader")
policy.deny("READ", "Person.salary", to="reader")

# Grant WRITE access to editors
policy.grant("WRITE", "Person", to="editor")
```

### 4. Use Secure Session

```python
from falkordb_orm.security import SecureSession

# Create secure session for user
session = SecureSession(graph, alice)

# Get security-aware repository
person_repo = session.get_repository(Person)

# Operations respect permissions
person = person_repo.find_by_id(1)
print(person.name)  # ✓ Allowed
print(person.ssn)   # None - Denied property
```

### 5. Impersonation (for testing)

```python
# Admin impersonating another user
admin_session = SecureSession(graph, admin_user)

with admin_session.impersonate(alice):
    # All operations use Alice's permissions
    person = person_repo.find_by_id(1)
    # person.ssn will be None due to Alice's restrictions
```

## Security Model

### Hierarchy

```
Database
  └── Graph
      ├── Node (by label)
      │   └── Property
      └── Relationship (by type)
          └── Property
```

### Permission Actions

- **READ**: View entities and properties
- **WRITE**: Modify existing entities
- **CREATE**: Create new entities
- **DELETE**: Remove entities
- **TRAVERSE**: Navigate relationships

### Grant Types

- **GRANT**: Allow access
- **DENY**: Explicitly deny access (takes precedence)

### Built-in Roles

- **PUBLIC**: Default role for all users
- **reader**: Read-only access
- **editor**: Read and write access
- **publisher**: Editor + schema modification
- **admin**: Full access (bypasses all checks)

## API Reference

### SecurityContext

```python
class SecurityContext:
    def can(self, action: str, resource: str) -> bool
    def get_denied_properties(self, entity_class: str, action: str) -> Set[str]
    def has_role(self, role_name: str) -> bool
    def get_effective_roles(self) -> Set[str]
```

### SecurityPolicy

```python
class SecurityPolicy:
    def grant(self, action: str, resource: str, to: str)
    def deny(self, action: str, resource: str, to: str)
    def revoke(self, action: str, resource: str, from_role: str)
```

### SecureRepository

```python
class SecureRepository(Repository[T]):
    # All Repository methods with security enforcement
    def find_by_id(self, entity_id: Any) -> Optional[T]
    def find_all(self) -> List[T]
    def save(self, entity: T) -> T
    def delete(self, entity: T) -> None
```

### SecureSession

```python
class SecureSession(Session):
    def get_repository(self, entity_class: Type[T]) -> SecureRepository[T]
    def get(self, entity_class: Type[T], entity_id) -> Optional[T]
    def impersonate(self, user: User) -> ImpersonationContext
```

## Configuration

### JSON Configuration

```json
{
  "roles": [
    {"name": "analyst", "description": "Data analyst"}
  ],
  "users": [
    {
      "username": "alice",
      "email": "alice@example.com",
      "roles": ["analyst", "reader"]
    }
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
```

Load with:
```python
from falkordb_orm.security import InMemoryRBACStore

store = InMemoryRBACStore()
store.load_from_json("rbac_config.json")
```

## Examples

See `examples/security/` directory for complete examples:

- `basic_security_example.py` - Basic RBAC usage
- More examples coming in future sprints

## Implementation Status

| Sprint | Component | Status |
|--------|-----------|--------|
| 1 | Core Infrastructure | ✅ Complete |
| 2 | Query Rewriting Engine | ✅ Complete |
| 3 | Session Integration | ✅ Complete |
| 4 | Graph Storage + Admin API | ⏳ Planned |
| 5 | Advanced Features | ⏳ Planned |
| 6 | Testing & Documentation | ⏳ Planned |

## Performance Considerations

- **SecurityContext caching**: Privileges are cached per context (~1-5ms overhead)
- **Admin bypass**: Admin role skips all permission checks
- **Property filtering**: Done in-memory after query execution
- **Query rewriting**: Planned for Sprint 5 (row-level security)

## Limitations

Current implementation:
- Property filtering is post-query (Sprint 5 will add query-level filtering)
- Row-level security decorators not yet enforced in queries
- Graph-stored RBAC not yet implemented (Sprint 4)
- Admin API not yet available (Sprint 4)

## Security Best Practices

1. **Use least privilege**: Grant minimum required permissions
2. **DENY over GRANT**: Explicit denies take precedence
3. **Test with impersonation**: Verify permissions before deploying
4. **Regular audits**: Review roles and privileges regularly
5. **Immutable roles**: Mark critical roles as immutable

## Next Steps

Sprint 4 will add:
- Graph-stored RBAC with caching
- RBACManager API for runtime management
- Admin-only operations
- User/role/privilege management endpoints

Sprint 5 will add:
- True row-level security with query rewriting
- Dynamic policies based on graph paths
- Comprehensive audit logging

Sprint 6 will add:
- Security penetration testing
- Performance benchmarks
- Complete documentation
- Migration guides

## Contributing

The security module is actively being developed. Contributions welcome for:
- Query rewriter improvements
- Additional security decorators
- Performance optimizations
- Documentation and examples

## License

Same as FalkorDB Python ORM.
