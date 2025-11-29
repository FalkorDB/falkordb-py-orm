# Phase 10: Role-Based Access Control (RBAC) Security

## Overview
Implement comprehensive Role-Based Access Control (RBAC) for FalkorDB Python ORM, inspired by Neo4j's enterprise security model. This phase adds enterprise-grade security features including fine-grained access control, query rewriting, graph-stored security metadata, and a complete admin API for RBAC management.

**Priority**: HIGH (Enterprise requirement)  
**Estimated Effort**: ~3,000 lines of code + 2,100 lines tests + 1,800 lines docs/examples = 6,870 total  
**Duration**: 10-15 weeks (6 sprints)  
**Complexity**: HIGH - Requires query rewriting, security enforcement, and management API

## Motivation

### Why RBAC is Needed
1. **Enterprise Requirements**: Organizations need fine-grained access control
2. **Regulatory Compliance**: GDPR, HIPAA, SOC2 require data access controls
3. **Multi-tenant Applications**: Different users need different data access levels
4. **Data Protection**: Sensitive properties (SSN, salary) need restricted access
5. **Audit Requirements**: Track who accessed what data and when

### Current Limitations
- No built-in access control
- Security must be implemented in application layer
- No property-level security
- No audit logging
- Cannot enforce row-level security

## Neo4j RBAC Analysis

### Key Features Learned from Neo4j
1. **Hierarchical Privilege Model**: Database → Graph → Node/Relationship → Property
2. **GRANT/DENY/REVOKE Commands**: Fine-grained permission management
3. **Built-in Roles**: PUBLIC, reader, editor, publisher, architect, admin
4. **Property-Level Security**: Control access to specific properties
5. **Immutable Privileges**: Prevent unauthorized privilege changes
6. **Impersonation**: Services can act on behalf of users

### Neo4j Privilege Types
- **Database Privileges**: ACCESS, START, STOP, INDEX MANAGEMENT
- **Graph Privileges**: TRAVERSE, READ, MATCH, WRITE, CREATE, DELETE
- **Element-Level**: Specific node labels, relationship types
- **Property-Level**: Specific property names or name-value pairs

## Design Principles

1. **ORM-Native**: Integrate security directly into Repository and Session
2. **Declarative**: Define security policies alongside entity models
3. **Storage Options**: Support both in-memory and graph-stored RBAC
4. **Performance**: Query rewriting with caching (~5-10ms overhead)
5. **Backward Compatible**: Optional feature, doesn't break existing code
6. **Developer-Friendly**: Use decorators and context managers

## Implementation Phases

### Phase 10a: Core RBAC Infrastructure (Sprint 1 - 2-3 weeks)

**Goal**: Build foundation with security metadata and storage

#### Tasks

##### 1. Create Security Metadata Models
**File**: `falkordb_orm/security/models.py` (~150 lines)

```python
from datetime import datetime
from typing import List, Optional
from falkordb_orm import node, generated_id, relationship, unique

@node("_Security_Role")
class Role:
    """Security role with privileges."""
    id: Optional[int] = generated_id()
    name: str = unique(required=True)
    description: str
    created_at: datetime
    is_immutable: bool = False
    
    # Hierarchical roles
    parent_roles: List['Role'] = relationship(
        'INHERITS_FROM', 
        target='Role',
        direction='OUTGOING'
    )

@node("_Security_User")
class User:
    """User with assigned roles."""
    id: Optional[int] = generated_id()
    username: str = unique(required=True)
    email: str
    created_at: datetime
    is_active: bool = True
    
    roles: List[Role] = relationship('HAS_ROLE', target=Role)

@node("_Security_Privilege")
class Privilege:
    """Permission granted to a role."""
    id: Optional[int] = generated_id()
    action: str  # READ, WRITE, CREATE, DELETE, TRAVERSE
    resource_type: str  # NODE, RELATIONSHIP, PROPERTY
    resource_label: Optional[str]  # Label/type or * for all
    resource_property: Optional[str]  # Property name or * for all
    grant_type: str  # GRANT or DENY
    scope: str  # GRAPH, DATABASE
    is_immutable: bool = False
    created_at: datetime
    
    role: Role = relationship('GRANTED_TO', target=Role)

@node("_Security_AuditLog")
class AuditLog:
    """Audit trail for security events."""
    id: Optional[int] = generated_id()
    timestamp: datetime
    user_id: int
    username: str
    action: str
    resource: str
    resource_id: Optional[int]
    granted: bool
    reason: Optional[str]
    ip_address: Optional[str]
```

##### 2. Create Security Policy DSL
**File**: `falkordb_orm/security/policy.py` (~200 lines)

```python
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

@dataclass
class PolicyRule:
    """Individual security policy rule."""
    action: str  # READ, WRITE, CREATE, DELETE
    resource_pattern: str  # "Person", "Person.email", "KNOWS"
    grant_type: str  # GRANT or DENY
    role: str
    conditions: Optional[Dict] = None

class SecurityPolicy:
    """Declarative security policy manager."""
    
    def __init__(self, graph):
        self.graph = graph
        self.rules: List[PolicyRule] = []
    
    def grant(self, action: str, resource: str, to: str, 
              conditions: Optional[Dict] = None):
        """Grant privilege to role.
        
        Examples:
            policy.grant('READ', 'Person', to='reader')
            policy.grant('READ', 'Person.name', to='analyst')
            policy.grant('WRITE', 'Document', to='editor', 
                        conditions={'owner_id': '{{user.id}}'})
        """
        rule = PolicyRule(
            action=action,
            resource_pattern=resource,
            grant_type='GRANT',
            role=to,
            conditions=conditions
        )
        self.rules.append(rule)
        self._persist_rule(rule)
    
    def deny(self, action: str, resource: str, to: str,
             conditions: Optional[Dict] = None):
        """Deny privilege to role."""
        rule = PolicyRule(
            action=action,
            resource_pattern=resource,
            grant_type='DENY',
            role=to,
            conditions=conditions
        )
        self.rules.append(rule)
        self._persist_rule(rule)
    
    def revoke(self, action: str, resource: str, from_role: str):
        """Revoke privilege from role."""
        # Remove rule and delete from graph
        pass
    
    def _persist_rule(self, rule: PolicyRule):
        """Store rule as Privilege node in graph."""
        pass
```

##### 3. Create Security Decorators
**File**: `falkordb_orm/security/decorators.py` (~150 lines)

```python
from typing import List, Dict, Optional, Callable

def secured(
    read: Optional[List[str]] = None,
    write: Optional[List[str]] = None,
    create: Optional[List[str]] = None,
    delete: Optional[List[str]] = None,
    deny_read_properties: Optional[Dict[str, List[str]]] = None,
    deny_write_properties: Optional[Dict[str, List[str]]] = None
):
    """Decorator to add security metadata to entity class.
    
    Examples:
        @node("Person")
        @secured(
            read=["reader", "admin"],
            write=["editor", "admin"],
            deny_read_properties={
                "ssn": ["*"],  # Nobody can read
                "salary": ["reader"]  # Reader cannot read
            }
        )
        class Person:
            id: Optional[int] = generated_id()
            name: str
            ssn: str
            salary: float
    """
    def decorator(cls):
        # Store security metadata on class
        if not hasattr(cls, '__security_metadata__'):
            cls.__security_metadata__ = {}
        
        cls.__security_metadata__['read_roles'] = read or []
        cls.__security_metadata__['write_roles'] = write or []
        cls.__security_metadata__['create_roles'] = create or []
        cls.__security_metadata__['delete_roles'] = delete or []
        cls.__security_metadata__['deny_read_properties'] = deny_read_properties or {}
        cls.__security_metadata__['deny_write_properties'] = deny_write_properties or {}
        
        return cls
    return decorator

def row_level_security(filter_func: Callable):
    """Decorator for row-level security filtering.
    
    Example:
        @node("Document")
        @row_level_security(
            filter_func=lambda user, doc: (
                doc.owner_id == user.id or 
                user.has_role('admin')
            )
        )
        class Document:
            id: Optional[int] = generated_id()
            title: str
            owner_id: int
    """
    def decorator(cls):
        if not hasattr(cls, '__security_metadata__'):
            cls.__security_metadata__ = {}
        cls.__security_metadata__['row_filter'] = filter_func
        return cls
    return decorator

def secured_property(
    deny_read: Optional[List[str]] = None,
    deny_write: Optional[List[str]] = None
):
    """Property-level security decorator.
    
    Example:
        class Person:
            ssn: str = secured_property(deny_read=['reader', 'analyst'])
            salary: float = secured_property(deny_write=['viewer'])
    """
    # Return a property descriptor with security metadata
    pass
```

##### 4. Create In-Memory RBAC Store
**File**: `falkordb_orm/security/store.py` (~200 lines)

```python
import yaml
import json
from typing import Dict, List
from .models import Role, User, Privilege

class InMemoryRBACStore:
    """Fast in-memory RBAC storage."""
    
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.users: Dict[str, User] = {}
        self.privileges: List[Privilege] = []
        self._init_built_in_roles()
    
    def _init_built_in_roles(self):
        """Initialize Neo4j-style built-in roles."""
        self.roles['PUBLIC'] = Role(
            name='PUBLIC',
            description='Default role for all users',
            is_immutable=True
        )
        self.roles['reader'] = Role(
            name='reader',
            description='Read-only access'
        )
        self.roles['editor'] = Role(
            name='editor',
            description='Read and write access'
        )
        self.roles['publisher'] = Role(
            name='publisher',
            description='Editor + schema modification'
        )
        self.roles['admin'] = Role(
            name='admin',
            description='Full access'
        )
    
    def load_from_yaml(self, config_path: str):
        """Load RBAC configuration from YAML."""
        with open(config_path) as f:
            config = yaml.safe_load(f)
        # Parse and load roles, users, privileges
        pass
    
    def load_from_json(self, config_path: str):
        """Load RBAC configuration from JSON."""
        with open(config_path) as f:
            config = json.load(f)
        pass
```

#### Deliverables
- `falkordb_orm/security/__init__.py` - Package exports
- `falkordb_orm/security/models.py` - RBAC entity models (~150 lines)
- `falkordb_orm/security/policy.py` - Policy DSL (~200 lines)
- `falkordb_orm/security/decorators.py` - Security decorators (~150 lines)
- `falkordb_orm/security/store.py` - In-memory storage (~200 lines)
- `falkordb_orm/security/exceptions.py` - Security exceptions (~50 lines)
- `tests/security/test_models.py` - Model tests (~100 lines)
- `tests/security/test_policy.py` - Policy tests (~100 lines)

**Total Sprint 1**: ~950 lines code + 200 lines tests = 1,150 lines

---

### Phase 10b: Query Rewriting Engine (Sprint 2 - 2-3 weeks)

**Goal**: Implement query rewriting to enforce security

#### Tasks

##### 1. Create Security Context
**File**: `falkordb_orm/security/context.py` (~250 lines)

```python
from typing import Dict, Set, Optional, Any
from .models import User, Role, Privilege

class SecurityContext:
    """Manages current user and their effective permissions."""
    
    def __init__(self, user: User, graph):
        self.user = user
        self.graph = graph
        self.effective_roles = self._compute_effective_roles()
        self.privilege_cache = self._build_privilege_cache()
    
    def _compute_effective_roles(self) -> Set[str]:
        """Compute all roles including inherited ones."""
        roles = {'PUBLIC'}  # Everyone has PUBLIC
        
        # Add direct roles
        for role in self.user.roles:
            roles.add(role.name)
            # Add inherited roles (recursive)
            roles.update(self._get_inherited_roles(role))
        
        return roles
    
    def _get_inherited_roles(self, role: Role) -> Set[str]:
        """Recursively get inherited roles."""
        inherited = set()
        for parent in role.parent_roles:
            inherited.add(parent.name)
            inherited.update(self._get_inherited_roles(parent))
        return inherited
    
    def _build_privilege_cache(self) -> Dict[str, Dict[str, bool]]:
        """Build fast lookup cache for privileges."""
        cache = {}
        
        for role_name in self.effective_roles:
            # Load privileges for role from graph
            privileges = self._load_role_privileges(role_name)
            
            for priv in privileges:
                key = f"{priv.action}:{priv.resource_type}:{priv.resource_label}"
                
                if key not in cache:
                    cache[key] = {}
                
                # DENY takes precedence over GRANT
                if priv.grant_type == 'DENY':
                    cache[key]['granted'] = False
                elif priv.grant_type == 'GRANT' and 'granted' not in cache[key]:
                    cache[key]['granted'] = True
        
        return cache
    
    def can(self, action: str, resource: str, 
            entity: Optional[Any] = None) -> bool:
        """Check if user can perform action on resource.
        
        Examples:
            if context.can('READ', 'Person'):
                # Load person
            
            if context.can('WRITE', 'Person.salary', entity=person):
                # Update salary
        """
        # Check cache
        key = f"{action}:{resource}"
        if key in self.privilege_cache:
            return self.privilege_cache[key].get('granted', False)
        
        # Check wildcard permissions
        wildcard_key = f"{action}:*"
        if wildcard_key in self.privilege_cache:
            return self.privilege_cache[wildcard_key].get('granted', False)
        
        return False
    
    def get_denied_properties(self, entity_class: str, 
                            action: str) -> Set[str]:
        """Get list of properties user cannot access."""
        denied = set()
        
        # Check each property
        for priv in self._get_property_privileges(entity_class, action):
            if priv.grant_type == 'DENY':
                denied.add(priv.resource_property)
        
        return denied
```

##### 2. Create Query Rewriter
**File**: `falkordb_orm/security/rewriter.py` (~300 lines)

```python
import re
from typing import Dict, Tuple, Set

class QueryRewriter:
    """Rewrites Cypher queries to enforce security."""
    
    def __init__(self, security_context):
        self.context = security_context
    
    def rewrite(self, cypher: str, params: Dict) -> Tuple[str, Dict]:
        """Rewrite query to enforce RBAC.
        
        Strategies:
        1. Add WHERE clauses for row-level filtering
        2. Remove unauthorized properties from RETURN
        3. Add OPTIONAL MATCH for conditional visibility
        4. Inject user context into query parameters
        """
        # Parse query to identify components
        query_parts = self._parse_query(cypher)
        
        # Apply security filters
        if query_parts['match_clause']:
            cypher = self._add_row_filters(cypher, query_parts)
        
        if query_parts['return_clause']:
            cypher = self._filter_properties(cypher, query_parts)
        
        # Inject user context
        params['__security_user_id'] = self.context.user.id
        params['__security_roles'] = list(self.context.effective_roles)
        
        return cypher, params
    
    def _parse_query(self, cypher: str) -> Dict:
        """Parse Cypher into components."""
        return {
            'match_clause': self._extract_match(cypher),
            'where_clause': self._extract_where(cypher),
            'return_clause': self._extract_return(cypher),
            'variables': self._extract_variables(cypher)
        }
    
    def _add_row_filters(self, cypher: str, parts: Dict) -> str:
        """Add row-level security filters."""
        # For each matched node, check if row-level filter exists
        # Inject additional WHERE conditions
        pass
    
    def _filter_properties(self, cypher: str, parts: Dict) -> str:
        """Remove unauthorized properties from RETURN."""
        # Parse RETURN clause
        # Remove denied properties
        # Reconstruct RETURN clause
        pass
```

##### 3. Create Secure Repository
**File**: `falkordb_orm/security/repository.py` (~250 lines)

```python
from typing import Type, TypeVar, Optional, Any
from ..repository import Repository
from .context import SecurityContext
from .rewriter import QueryRewriter
from .exceptions import SecurityException

T = TypeVar('T')

class SecureRepository(Repository[T]):
    """Security-aware repository wrapper."""
    
    def __init__(self, graph, entity_class: Type[T], 
                 security_context: SecurityContext):
        super().__init__(graph, entity_class)
        self.security_context = security_context
        self.rewriter = QueryRewriter(security_context)
    
    def find_by_id(self, entity_id: Any, 
                   fetch: Optional[List[str]] = None) -> Optional[T]:
        """Find with security enforcement."""
        # Check READ permission
        if not self.security_context.can('READ', self.entity_class.__name__):
            raise SecurityException(
                f"Access denied: Cannot read {self.entity_class.__name__}"
            )
        
        # Get denied properties
        denied_props = self.security_context.get_denied_properties(
            self.entity_class.__name__, 'READ'
        )
        
        # Load entity
        entity = super().find_by_id(entity_id, fetch)
        
        if entity:
            # Filter out denied properties
            return self._filter_properties(entity, denied_props)
        
        return None
    
    def save(self, entity: T) -> T:
        """Save with security enforcement."""
        # Check if new entity (CREATE) or existing (WRITE)
        is_new = self._is_new_entity(entity)
        action = 'CREATE' if is_new else 'WRITE'
        
        if not self.security_context.can(action, self.entity_class.__name__):
            raise SecurityException(
                f"Access denied: Cannot {action.lower()} {self.entity_class.__name__}"
            )
        
        # Check property-level write permissions
        self._validate_property_writes(entity)
        
        return super().save(entity)
    
    def delete(self, entity: T) -> None:
        """Delete with security enforcement."""
        if not self.security_context.can('DELETE', self.entity_class.__name__):
            raise SecurityException(
                f"Access denied: Cannot delete {self.entity_class.__name__}"
            )
        
        super().delete(entity)
    
    def _filter_properties(self, entity: T, denied: Set[str]) -> T:
        """Remove denied properties from entity."""
        for prop in denied:
            if hasattr(entity, prop):
                setattr(entity, prop, None)
        return entity
    
    def _validate_property_writes(self, entity: T):
        """Check property-level write permissions."""
        denied_props = self.security_context.get_denied_properties(
            self.entity_class.__name__, 'WRITE'
        )
        
        metadata = self.mapper.get_entity_metadata(type(entity))
        for prop in metadata.properties:
            if prop.python_name in denied_props:
                # Check if property was modified
                if self._was_property_modified(entity, prop.python_name):
                    raise SecurityException(
                        f"Access denied: Cannot write property '{prop.python_name}'"
                    )
```

#### Deliverables
- `falkordb_orm/security/context.py` - SecurityContext (~250 lines)
- `falkordb_orm/security/rewriter.py` - QueryRewriter (~300 lines)
- `falkordb_orm/security/repository.py` - SecureRepository (~250 lines)
- `tests/security/test_context.py` - Context tests (~150 lines)
- `tests/security/test_rewriter.py` - Rewriter tests (~200 lines)
- `tests/security/test_secure_repository.py` - Repository tests (~200 lines)

**Total Sprint 2**: ~800 lines code + 550 lines tests = 1,350 lines

---

### Phase 10c: Session Integration (Sprint 3 - 1-2 weeks)

**Goal**: Integrate security with Session and add impersonation

#### Tasks

##### 1. Create Secure Session
**File**: `falkordb_orm/security/session.py` (~200 lines)

```python
from ..session import Session
from .context import SecurityContext
from .repository import SecureRepository

class SecureSession(Session):
    """Session with integrated security."""
    
    def __init__(self, graph, user):
        super().__init__(graph)
        self.security_context = SecurityContext(user, graph)
    
    def get_repository(self, entity_class):
        """Get security-aware repository."""
        return SecureRepository(
            self.graph, 
            entity_class, 
            self.security_context
        )
    
    def get(self, entity_class, entity_id):
        """Get with security checks."""
        repo = self.get_repository(entity_class)
        return repo.find_by_id(entity_id)
    
    def impersonate(self, user):
        """Create impersonation context."""
        return ImpersonationContext(self, user)

class ImpersonationContext:
    """Context manager for impersonation."""
    
    def __init__(self, session: SecureSession, impersonate_user):
        self.session = session
        self.original_user = session.security_context.user
        self.impersonate_user = impersonate_user
    
    def __enter__(self):
        self.session.security_context = SecurityContext(
            self.impersonate_user, 
            self.session.graph
        )
        return self.session
    
    def __exit__(self, *args):
        self.session.security_context = SecurityContext(
            self.original_user, 
            self.session.graph
        )
```

#### Deliverables
- `falkordb_orm/security/session.py` (~200 lines)
- `tests/security/test_secure_session.py` (~150 lines)
- `examples/security/basic_security_example.py` (~150 lines)

**Total Sprint 3**: ~200 lines code + 300 lines tests/examples = 500 lines

---

### Phase 10d: Graph Storage Backend (Sprint 4 - 2 weeks)

**Goal**: Implement graph-stored RBAC with caching

#### Tasks

##### 1. Implement Graph RBAC Store
**File**: `falkordb_orm/security/graph_store.py` (~300 lines)

- Store/load roles, users, privileges from FalkorDB
- Implement caching layer
- Handle role hierarchy traversal
- Provide migration from in-memory to graph storage

##### 2. Create RBAC Management API
**File**: `falkordb_orm/security/manager.py` (~350 lines)

Comprehensive API for client applications to manage RBAC (admin role required):

```python
from typing import List, Optional, Dict
from .models import Role, User, Privilege
from .exceptions import SecurityException, UnauthorizedException

class RBACManager:
    """RBAC management API for admin operations.
    
    All methods require 'admin' role.
    """
    
    def __init__(self, graph, security_context):
        self.graph = graph
        self.security_context = security_context
        self._check_admin()
    
    def _check_admin(self):
        """Verify user has admin role."""
        if 'admin' not in self.security_context.effective_roles:
            raise UnauthorizedException(
                "Admin role required for RBAC management"
            )
    
    # ========== USER MANAGEMENT ==========
    
    def create_user(self, username: str, email: str, 
                   roles: Optional[List[str]] = None) -> User:
        """Create new user with optional roles.
        
        Args:
            username: Unique username
            email: User email address
            roles: List of role names to assign (optional)
        
        Returns:
            Created User object
        
        Raises:
            SecurityException: If username already exists
        """
        # Check if user exists
        existing = User.find_by_username(username)
        if existing:
            raise SecurityException(f"User '{username}' already exists")
        
        user = User(
            username=username,
            email=email,
            created_at=datetime.now(),
            is_active=True
        )
        
        # Assign roles
        if roles:
            user.roles = [self.get_role(role_name) for role_name in roles]
        
        # Save to graph
        user_repo = Repository(self.graph, User)
        user_repo.save(user)
        
        self._audit_log('CREATE_USER', f'User:{username}', granted=True)
        return user
    
    def update_user(self, username: str, 
                   email: Optional[str] = None,
                   is_active: Optional[bool] = None) -> User:
        """Update user details.
        
        Args:
            username: Username to update
            email: New email (optional)
            is_active: New active status (optional)
        
        Returns:
            Updated User object
        """
        user = User.find_by_username(username)
        if not user:
            raise SecurityException(f"User '{username}' not found")
        
        if email is not None:
            user.email = email
        if is_active is not None:
            user.is_active = is_active
        
        user_repo = Repository(self.graph, User)
        user_repo.save(user)
        
        self._audit_log('UPDATE_USER', f'User:{username}', granted=True)
        return user
    
    def delete_user(self, username: str) -> None:
        """Delete user and revoke all roles.
        
        Args:
            username: Username to delete
        """
        user = User.find_by_username(username)
        if not user:
            raise SecurityException(f"User '{username}' not found")
        
        user_repo = Repository(self.graph, User)
        user_repo.delete(user)
        
        self._audit_log('DELETE_USER', f'User:{username}', granted=True)
    
    def list_users(self, active_only: bool = True) -> List[User]:
        """List all users.
        
        Args:
            active_only: Only return active users
        
        Returns:
            List of User objects
        """
        user_repo = Repository(self.graph, User)
        users = user_repo.find_all()
        
        if active_only:
            users = [u for u in users if u.is_active]
        
        return users
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username.
        
        Args:
            username: Username to find
        
        Returns:
            User object or None
        """
        return User.find_by_username(username)
    
    # ========== ROLE MANAGEMENT ==========
    
    def create_role(self, name: str, description: str,
                   parent_roles: Optional[List[str]] = None,
                   is_immutable: bool = False) -> Role:
        """Create new role.
        
        Args:
            name: Unique role name
            description: Role description
            parent_roles: List of parent role names for inheritance
            is_immutable: Whether role can be modified/deleted
        
        Returns:
            Created Role object
        """
        existing = Role.find_by_name(name)
        if existing:
            raise SecurityException(f"Role '{name}' already exists")
        
        role = Role(
            name=name,
            description=description,
            created_at=datetime.now(),
            is_immutable=is_immutable
        )
        
        # Set parent roles for inheritance
        if parent_roles:
            role.parent_roles = [
                self.get_role(parent_name) 
                for parent_name in parent_roles
            ]
        
        role_repo = Repository(self.graph, Role)
        role_repo.save(role)
        
        self._audit_log('CREATE_ROLE', f'Role:{name}', granted=True)
        return role
    
    def update_role(self, name: str, 
                   description: Optional[str] = None,
                   parent_roles: Optional[List[str]] = None) -> Role:
        """Update role details.
        
        Args:
            name: Role name to update
            description: New description (optional)
            parent_roles: New parent roles (optional)
        
        Returns:
            Updated Role object
        """
        role = self.get_role(name)
        
        if role.is_immutable:
            raise SecurityException(f"Role '{name}' is immutable")
        
        if description is not None:
            role.description = description
        
        if parent_roles is not None:
            role.parent_roles = [
                self.get_role(parent_name) 
                for parent_name in parent_roles
            ]
        
        role_repo = Repository(self.graph, Role)
        role_repo.save(role)
        
        self._audit_log('UPDATE_ROLE', f'Role:{name}', granted=True)
        return role
    
    def delete_role(self, name: str) -> None:
        """Delete role.
        
        Args:
            name: Role name to delete
        """
        role = self.get_role(name)
        
        if role.is_immutable:
            raise SecurityException(f"Role '{name}' is immutable")
        
        # Check if role is assigned to users
        users_with_role = self._get_users_with_role(name)
        if users_with_role:
            raise SecurityException(
                f"Cannot delete role '{name}': assigned to {len(users_with_role)} users"
            )
        
        role_repo = Repository(self.graph, Role)
        role_repo.delete(role)
        
        self._audit_log('DELETE_ROLE', f'Role:{name}', granted=True)
    
    def list_roles(self) -> List[Role]:
        """List all roles.
        
        Returns:
            List of Role objects
        """
        role_repo = Repository(self.graph, Role)
        return role_repo.find_all()
    
    def get_role(self, name: str) -> Role:
        """Get role by name.
        
        Args:
            name: Role name to find
        
        Returns:
            Role object
        
        Raises:
            SecurityException: If role not found
        """
        role = Role.find_by_name(name)
        if not role:
            raise SecurityException(f"Role '{name}' not found")
        return role
    
    # ========== USER-ROLE ASSIGNMENT ==========
    
    def assign_role(self, username: str, role_name: str) -> None:
        """Assign role to user.
        
        Args:
            username: Username
            role_name: Role name to assign
        """
        user = self.get_user(username)
        if not user:
            raise SecurityException(f"User '{username}' not found")
        
        role = self.get_role(role_name)
        
        # Check if already assigned
        if role in user.roles:
            return  # Already assigned
        
        user.roles.append(role)
        user_repo = Repository(self.graph, User)
        user_repo.save(user)
        
        self._audit_log(
            'ASSIGN_ROLE', 
            f'User:{username}->Role:{role_name}',
            granted=True
        )
    
    def revoke_role(self, username: str, role_name: str) -> None:
        """Revoke role from user.
        
        Args:
            username: Username
            role_name: Role name to revoke
        """
        user = self.get_user(username)
        if not user:
            raise SecurityException(f"User '{username}' not found")
        
        role = self.get_role(role_name)
        
        # Remove role
        user.roles = [r for r in user.roles if r.name != role_name]
        user_repo = Repository(self.graph, User)
        user_repo.save(user)
        
        self._audit_log(
            'REVOKE_ROLE',
            f'User:{username}->Role:{role_name}',
            granted=True
        )
    
    def get_user_roles(self, username: str) -> List[Role]:
        """Get all roles assigned to user.
        
        Args:
            username: Username
        
        Returns:
            List of Role objects (including inherited)
        """
        user = self.get_user(username)
        if not user:
            raise SecurityException(f"User '{username}' not found")
        
        # Get all effective roles including inherited
        context = SecurityContext(user, self.graph)
        return list(context.effective_roles)
    
    # ========== PRIVILEGE MANAGEMENT ==========
    
    def grant_privilege(self, role_name: str, action: str,
                       resource_type: str, resource_label: str = '*',
                       resource_property: Optional[str] = None,
                       scope: str = 'GRAPH') -> Privilege:
        """Grant privilege to role.
        
        Args:
            role_name: Role name
            action: Action (READ, WRITE, CREATE, DELETE, TRAVERSE)
            resource_type: Resource type (NODE, RELATIONSHIP, PROPERTY)
            resource_label: Specific label/type or * for all
            resource_property: Specific property or None
            scope: GRAPH or DATABASE
        
        Returns:
            Created Privilege object
        """
        role = self.get_role(role_name)
        
        if role.is_immutable:
            raise SecurityException(
                f"Cannot modify privileges for immutable role '{role_name}'"
            )
        
        privilege = Privilege(
            action=action,
            resource_type=resource_type,
            resource_label=resource_label,
            resource_property=resource_property,
            grant_type='GRANT',
            scope=scope,
            is_immutable=False,
            created_at=datetime.now()
        )
        privilege.role = role
        
        priv_repo = Repository(self.graph, Privilege)
        priv_repo.save(privilege)
        
        self._audit_log(
            'GRANT_PRIVILEGE',
            f'Role:{role_name}:{action}:{resource_type}:{resource_label}',
            granted=True
        )
        return privilege
    
    def deny_privilege(self, role_name: str, action: str,
                      resource_type: str, resource_label: str = '*',
                      resource_property: Optional[str] = None,
                      scope: str = 'GRAPH') -> Privilege:
        """Deny privilege to role.
        
        Args:
            role_name: Role name
            action: Action to deny
            resource_type: Resource type
            resource_label: Specific label/type or * for all
            resource_property: Specific property or None
            scope: GRAPH or DATABASE
        
        Returns:
            Created Privilege object
        """
        role = self.get_role(role_name)
        
        privilege = Privilege(
            action=action,
            resource_type=resource_type,
            resource_label=resource_label,
            resource_property=resource_property,
            grant_type='DENY',
            scope=scope,
            is_immutable=False,
            created_at=datetime.now()
        )
        privilege.role = role
        
        priv_repo = Repository(self.graph, Privilege)
        priv_repo.save(privilege)
        
        self._audit_log(
            'DENY_PRIVILEGE',
            f'Role:{role_name}:{action}:{resource_type}:{resource_label}',
            granted=True
        )
        return privilege
    
    def revoke_privilege(self, privilege_id: int) -> None:
        """Revoke privilege by ID.
        
        Args:
            privilege_id: Privilege ID to revoke
        """
        priv_repo = Repository(self.graph, Privilege)
        privilege = priv_repo.find_by_id(privilege_id)
        
        if not privilege:
            raise SecurityException(f"Privilege {privilege_id} not found")
        
        if privilege.is_immutable:
            raise SecurityException(
                f"Privilege {privilege_id} is immutable"
            )
        
        priv_repo.delete(privilege)
        
        self._audit_log(
            'REVOKE_PRIVILEGE',
            f'Privilege:{privilege_id}',
            granted=True
        )
    
    def list_privileges(self, role_name: Optional[str] = None) -> List[Privilege]:
        """List privileges, optionally filtered by role.
        
        Args:
            role_name: Optional role name to filter
        
        Returns:
            List of Privilege objects
        """
        priv_repo = Repository(self.graph, Privilege)
        privileges = priv_repo.find_all()
        
        if role_name:
            privileges = [
                p for p in privileges 
                if p.role.name == role_name
            ]
        
        return privileges
    
    # ========== AUDIT QUERIES ==========
    
    def query_audit_logs(self, 
                        username: Optional[str] = None,
                        action: Optional[str] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        limit: int = 100) -> List[Dict]:
        """Query audit logs with filters.
        
        Args:
            username: Filter by username
            action: Filter by action type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum results to return
        
        Returns:
            List of audit log entries
        """
        # Build Cypher query with filters
        query = "MATCH (log:_Security_AuditLog) WHERE 1=1"
        params = {}
        
        if username:
            query += " AND log.username = $username"
            params['username'] = username
        
        if action:
            query += " AND log.action = $action"
            params['action'] = action
        
        if start_date:
            query += " AND log.timestamp >= $start_date"
            params['start_date'] = start_date
        
        if end_date:
            query += " AND log.timestamp <= $end_date"
            params['end_date'] = end_date
        
        query += " RETURN log ORDER BY log.timestamp DESC LIMIT $limit"
        params['limit'] = limit
        
        result = self.graph.query(query, params)
        return [record['log'] for record in result.result_set]
    
    # ========== HELPER METHODS ==========
    
    def _get_users_with_role(self, role_name: str) -> List[User]:
        """Get all users with specific role."""
        query = """
        MATCH (user:_Security_User)-[:HAS_ROLE]->(role:_Security_Role)
        WHERE role.name = $role_name
        RETURN user
        """
        result = self.graph.query(query, {'role_name': role_name})
        return [record['user'] for record in result.result_set]
    
    def _audit_log(self, action: str, resource: str, granted: bool):
        """Log security event to audit log."""
        from .audit import AuditLogger
        logger = AuditLogger(self.graph)
        logger.log(
            user=self.security_context.user,
            action=action,
            resource=resource,
            granted=granted
        )
```

**Key Features:**
- **Admin-Only Access**: All methods require admin role
- **User Management**: Create, update, delete, list users
- **Role Management**: Create, update, delete roles with inheritance
- **User-Role Assignment**: Assign/revoke roles to/from users
- **Privilege Management**: Grant, deny, revoke privileges at all levels
- **Audit Queries**: Query audit logs with flexible filters
- **Safety Checks**: Prevents deletion of roles in use, modification of immutable roles
- **Comprehensive Logging**: All operations logged to audit trail

#### Deliverables
- `falkordb_orm/security/graph_store.py` (~300 lines)
- `falkordb_orm/security/manager.py` (~350 lines)
- `falkordb_orm/security/exceptions.py` - Add UnauthorizedException (~20 lines)
- `tests/security/test_graph_store.py` (~200 lines)
- `tests/security/test_manager.py` (~250 lines)
- `examples/security/graph_stored_rbac.py` (~150 lines)
- `examples/security/rbac_management_api.py` (~200 lines)

**Total Sprint 4**: ~670 lines code + 800 lines tests/examples = 1,470 lines

---

### Phase 10e: Advanced Features (Sprint 5 - 2-3 weeks)

**Goal**: Implement row-level security, dynamic policies, and audit logging

#### Tasks

1. **Row-Level Security** (~200 lines)
   - Filter entities based on custom functions
   - Integrate with query rewriter

2. **Dynamic Policies** (~150 lines)
   - Evaluate policies based on graph relationships
   - Support conditional access rules

3. **Audit Logging** (~200 lines)
   - Log all security events
   - Provide audit query API
   - Performance optimization

#### Deliverables
- Extended `falkordb_orm/security/rewriter.py` (~200 lines)
- Extended `falkordb_orm/security/policy.py` (~150 lines)
- `falkordb_orm/security/audit.py` (~200 lines)
- `tests/security/test_advanced.py` (~250 lines)
- `examples/security/advanced_security.py` (~200 lines)

**Total Sprint 5**: ~550 lines code + 450 lines tests/examples = 1,000 lines

---

### Phase 10f: Testing, Documentation & Integration (Sprint 6 - 1-2 weeks)

**Goal**: Comprehensive testing and documentation

#### Tasks

1. **Security Testing** (~300 lines tests)
   - Penetration testing scenarios
   - Privilege escalation attempts
   - Property-level filtering validation
   - Impersonation boundary tests

2. **Performance Testing** (~200 lines tests)
   - Query rewriting overhead measurement
   - Cache effectiveness metrics
   - Large permission set benchmarks

3. **Documentation** (~800 lines)
   - `docs/SECURITY.md` - Complete security guide
   - `docs/api/security.md` - API reference
   - Migration guide from no-security to RBAC
   - Best practices and patterns

4. **Integration Testing** (~200 lines tests)
   - Test with all ORM features
   - Test with existing phases (pagination, transactions, indexes)

#### Deliverables
- `tests/security/test_penetration.py` (~150 lines)
- `tests/security/test_performance.py` (~200 lines)
- `tests/security/test_integration.py` (~200 lines)
- `docs/SECURITY.md` (~500 lines)
- `docs/api/security.md` (~300 lines)
- `examples/security/complete_example.py` (~300 lines)

**Total Sprint 6**: ~500 lines tests + 1,100 lines docs/examples = 1,600 lines

---

## Implementation Summary

### Total Effort Breakdown

| Sprint | Component | Code | Tests | Docs/Examples | Total |
|--------|-----------|------|-------|---------------|-------|
| 1 | Core Infrastructure | 750 | 200 | 0 | 950 |
| 2 | Query Rewriting | 800 | 550 | 0 | 1,350 |
| 3 | Session Integration | 200 | 150 | 150 | 500 |
| 4 | Graph Storage + Admin API | 670 | 450 | 350 | 1,470 |
| 5 | Advanced Features | 550 | 250 | 200 | 1,000 |
| 6 | Testing & Docs | 0 | 500 | 1,100 | 1,600 |
| **TOTAL** | | **2,970** | **2,100** | **1,800** | **6,870** |

### Timeline

- **Sprint 1**: 2-3 weeks - Core Infrastructure
- **Sprint 2**: 2-3 weeks - Query Rewriting Engine  
- **Sprint 3**: 1-2 weeks - Session Integration
- **Sprint 4**: 2 weeks - Graph Storage Backend
- **Sprint 5**: 2-3 weeks - Advanced Features
- **Sprint 6**: 1-2 weeks - Testing & Documentation

**Total Duration**: 10-15 weeks

## Success Criteria

### Functional Requirements
- ✅ Can define roles and assign to users
- ✅ Can grant/deny privileges at multiple levels
- ✅ Property-level access control works
- ✅ Row-level security filters correctly
- ✅ Query rewriting enforces security
- ✅ Impersonation works for testing
- ✅ Audit logging captures events
- ✅ Graph-stored RBAC functional

### Performance Requirements
- ✅ Permission checks < 5ms (with cache)
- ✅ Query rewriting overhead < 10ms
- ✅ Cache hit rate > 90% for repeated checks
- ✅ No N+1 queries for permission loading

### Security Requirements
- ✅ No privilege escalation possible
- ✅ DENY always overrides GRANT
- ✅ Immutable privileges cannot be changed
- ✅ All security events audited
- ✅ No data leakage through error messages

## Usage Examples

### Basic Setup

```python
from falkordb import FalkorDB
from falkordb_orm.security import (
    SecureSession, SecurityPolicy, User
)

# Initialize
graph = FalkorDB()

# Create security policy
policy = SecurityPolicy(graph)
policy.grant('READ', 'Person', to='reader')
policy.grant('WRITE', 'Person', to='editor')
policy.deny('READ', 'Person.ssn', to='reader')

# Create user
user = User(username="alice", email="alice@example.com")
user.roles = [Role.find_by_name("reader")]

# Create secure session
session = SecureSession(graph, user)
person_repo = session.get_repository(Person)

# Operations respect permissions
person = person_repo.find_by_id(1)  # SSN property will be None
# person.ssn is None due to denied access
```

### Advanced Usage

```python
# Define entity with security
@node("Person")
@secured(
    read=["reader", "admin"],
    write=["editor", "admin"],
    deny_read_properties={
        "ssn": ["*"],
        "salary": ["reader"]
    }
)
class Person:
    id: Optional[int] = generated_id()
    name: str
    ssn: str
    salary: float

# Row-level security
@node("Document")
@row_level_security(
    filter_func=lambda user, doc: (
        doc.owner_id == user.id or 
        user.has_role('admin')
    )
)
class Document:
    id: Optional[int] = generated_id()
    title: str
    owner_id: int
    content: str

# Impersonation for testing
with session.impersonate(test_user):
    # All operations use test_user's permissions
    person = person_repo.find_by_id(1)
```

### RBAC Management API (Admin Only)

```python
from falkordb_orm.security import RBACManager, SecureSession

# Admin user session
admin_user = User.find_by_username("admin")
admin_session = SecureSession(graph, admin_user)

# Create RBAC manager (requires admin role)
rbac = RBACManager(graph, admin_session.security_context)

# === USER MANAGEMENT ===

# Create new user with roles
user = rbac.create_user(
    username="alice",
    email="alice@example.com",
    roles=["reader", "analyst"]
)

# Update user
rbac.update_user("alice", email="alice.smith@example.com")

# Deactivate user
rbac.update_user("alice", is_active=False)

# List all users
users = rbac.list_users(active_only=True)

# Delete user
rbac.delete_user("alice")

# === ROLE MANAGEMENT ===

# Create custom role
rbac.create_role(
    name="analyst",
    description="Data analyst with read access to analytics data",
    parent_roles=["reader"]  # Inherit from reader
)

# Update role
rbac.update_role(
    name="analyst",
    description="Senior data analyst",
    parent_roles=["reader", "editor"]
)

# List all roles
roles = rbac.list_roles()

# Delete role (only if not assigned to users)
rbac.delete_role("analyst")

# === USER-ROLE ASSIGNMENT ===

# Assign role to user
rbac.assign_role("alice", "editor")

# Revoke role from user
rbac.revoke_role("alice", "reader")

# Get user's effective roles (including inherited)
user_roles = rbac.get_user_roles("alice")

# === PRIVILEGE MANAGEMENT ===

# Grant READ access to Person nodes
rbac.grant_privilege(
    role_name="analyst",
    action="READ",
    resource_type="NODE",
    resource_label="Person"
)

# Grant READ access to specific property
rbac.grant_privilege(
    role_name="analyst",
    action="READ",
    resource_type="PROPERTY",
    resource_label="Person",
    resource_property="email"
)

# Deny access to sensitive property
rbac.deny_privilege(
    role_name="analyst",
    action="READ",
    resource_type="PROPERTY",
    resource_label="Person",
    resource_property="ssn"
)

# Grant WRITE access to Document nodes
rbac.grant_privilege(
    role_name="editor",
    action="WRITE",
    resource_type="NODE",
    resource_label="Document"
)

# List all privileges for a role
privileges = rbac.list_privileges(role_name="analyst")

# Revoke specific privilege
rbac.revoke_privilege(privilege_id=123)

# === AUDIT LOGGING ===

# Query audit logs
logs = rbac.query_audit_logs(
    username="alice",
    action="READ",
    start_date=datetime(2024, 1, 1),
    end_date=datetime.now(),
    limit=50
)

# Query all security events
all_logs = rbac.query_audit_logs(limit=1000)

# === CLIENT APPLICATION EXAMPLE ===

# REST API endpoint for user creation
@app.post("/api/rbac/users")
def create_user_endpoint(request):
    # Authenticate admin user
    admin_user = authenticate_admin(request.token)
    admin_session = SecureSession(graph, admin_user)
    
    try:
        rbac = RBACManager(graph, admin_session.security_context)
        user = rbac.create_user(
            username=request.username,
            email=request.email,
            roles=request.roles
        )
        return {"success": True, "user_id": user.id}
    except UnauthorizedException:
        return {"error": "Admin role required"}, 403
    except SecurityException as e:
        return {"error": str(e)}, 400

# REST API endpoint for granting privileges
@app.post("/api/rbac/privileges/grant")
def grant_privilege_endpoint(request):
    admin_user = authenticate_admin(request.token)
    admin_session = SecureSession(graph, admin_user)
    
    try:
        rbac = RBACManager(graph, admin_session.security_context)
        privilege = rbac.grant_privilege(
            role_name=request.role_name,
            action=request.action,
            resource_type=request.resource_type,
            resource_label=request.resource_label,
            resource_property=request.resource_property
        )
        return {"success": True, "privilege_id": privilege.id}
    except UnauthorizedException:
        return {"error": "Admin role required"}, 403
    except SecurityException as e:
        return {"error": str(e)}, 400
```

## Benefits

1. **Fine-Grained Control**: Property and entity-level access control
2. **Graph-Native**: Leverage FalkorDB for role hierarchies and policies
3. **Performance**: Query rewriting + caching minimizes overhead
4. **Flexible Storage**: Choose in-memory or graph-stored RBAC
5. **Developer-Friendly**: Declarative security with decorators
6. **Enterprise-Ready**: Audit logging, impersonation, immutable privileges
7. **ORM-Integrated**: Seamless integration with existing ORM features

## Considerations

### Performance Impact
- Query rewriting adds ~5-10ms overhead per query
- Permission checks cached in SecurityContext
- Graph-stored RBAC requires additional queries (mitigated by caching)
- Consider connection pooling for RBAC queries

### Migration Path
- RBAC is optional and opt-in
- Existing code continues to work without security
- Gradual adoption: add security to critical entities first
- Migration tools to convert existing auth to RBAC

### Limitations
- Cannot enforce security on direct Cypher queries (recommend using ORM)
- Graph-stored RBAC requires separate backup/restore
- Complex policies may impact query performance
- Need to handle security for custom @query methods

## Dependencies

- **Phase 7 (Transactions)**: Optional - SecureSession can extend Session
- **Phase 8 (Indexes)**: None
- **Phase 9 (Pagination)**: None - SecureRepository supports pagination

## Risk Mitigation

1. **Query Rewriting Bugs**: Comprehensive test suite with edge cases
2. **Performance Degradation**: Extensive caching and benchmarking
3. **Security Bypasses**: Penetration testing and code review
4. **Backward Compatibility**: Optional feature, thorough testing
5. **Complexity**: Clear documentation and examples

## Post-Implementation

After Phase 10 completion:

1. **Version Bump**: Release as v2.0.0 (major feature)
2. **Security Audit**: External security review
3. **Performance Benchmarks**: Publish performance characteristics
4. **Case Studies**: Document real-world usage
5. **Training Materials**: Create security best practices guide

## Next Steps

1. **Review and approve this plan**
2. **Begin with Sprint 1** (Core Infrastructure)
3. **Implement sprints sequentially** with reviews after each
4. **Continuous testing** throughout implementation
5. **Security review** before final release
