"""RBAC management API for admin operations."""

from datetime import datetime
from typing import Dict, List, Optional

from ..repository import Repository
from .audit import AuditLogger
from .context import SecurityContext
from .exceptions import SecurityException, UnauthorizedException
from .models import Privilege, Role, User


class RBACManager:
    """RBAC management API for admin operations.

    All methods require 'admin' role.
    """

    def __init__(self, graph, security_context: SecurityContext):
        self.graph = graph
        self.security_context = security_context
        self.audit_logger = AuditLogger(graph)
        self._check_admin()

    def _check_admin(self):
        """Verify user has admin role."""
        if "admin" not in self.security_context.effective_roles:
            raise UnauthorizedException("Admin role required for RBAC management")

    # ========== USER MANAGEMENT ==========

    def create_user(self, username: str, email: str, roles: Optional[List[str]] = None) -> User:
        """Create new user with optional roles."""
        user_repo = Repository(self.graph, User)

        # Check if user exists
        existing_query = "MATCH (u:_Security_User {username: $username}) RETURN u"
        result = self.graph.query(existing_query, {"username": username})
        if result.result_set:
            raise SecurityException(f"User '{username}' already exists")

        user = User(
            username=username,
            email=email,
            created_at=datetime.now(),
            is_active=True,
        )

        # Assign roles
        if roles:
            user.roles = []
            for role_name in roles:
                role = self._find_role_by_name(role_name)
                if role:
                    user.roles.append(role)

        user_repo.save(user)
        self._audit_log("CREATE_USER", f"User:{username}", granted=True)
        return user

    def update_user(
        self,
        username: str,
        email: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> User:
        """Update user details."""
        user = self.get_user(username)
        if not user:
            raise SecurityException(f"User '{username}' not found")

        if email is not None:
            user.email = email
        if is_active is not None:
            user.is_active = is_active

        user_repo = Repository(self.graph, User)
        user_repo.save(user)

        self._audit_log("UPDATE_USER", f"User:{username}", granted=True)
        return user

    def delete_user(self, username: str) -> None:
        """Delete user and revoke all roles."""
        user = self.get_user(username)
        if not user:
            raise SecurityException(f"User '{username}' not found")

        user_repo = Repository(self.graph, User)
        user_repo.delete(user)

        self._audit_log("DELETE_USER", f"User:{username}", granted=True)

    def list_users(self, active_only: bool = True) -> List[User]:
        """List all users."""
        query = "MATCH (u:_Security_User)"
        if active_only:
            query += " WHERE u.is_active = true"
        query += " RETURN u"

        result = self.graph.query(query)

        users = []
        if hasattr(result, "result_set"):
            user_repo = Repository(self.graph, User)
            for record in result.result_set:
                user_node = record[0]
                # Load user with relationships
                user = user_repo.find_by_id(user_node.id, fetch=["roles"])
                if user:
                    users.append(user)

        return users

    def get_user(self, username: str) -> Optional[User]:
        """Get user by username."""
        query = "MATCH (u:_Security_User {username: $username}) RETURN u"
        result = self.graph.query(query, {"username": username})

        if result.result_set:
            user_repo = Repository(self.graph, User)
            user_node = result.result_set[0][0]
            return user_repo.find_by_id(user_node.id, fetch=["roles"])

        return None

    # ========== ROLE MANAGEMENT ==========

    def create_role(
        self,
        name: str,
        description: str,
        parent_roles: Optional[List[str]] = None,
        is_immutable: bool = False,
    ) -> Role:
        """Create new role."""
        # Check if role exists
        existing = self._find_role_by_name(name)
        if existing:
            raise SecurityException(f"Role '{name}' already exists")

        role = Role(
            name=name,
            description=description,
            created_at=datetime.now(),
            is_immutable=is_immutable,
        )

        # Set parent roles for inheritance
        if parent_roles:
            role.parent_roles = []
            for parent_name in parent_roles:
                parent = self._find_role_by_name(parent_name)
                if parent:
                    role.parent_roles.append(parent)

        role_repo = Repository(self.graph, Role)
        role_repo.save(role)

        self._audit_log("CREATE_ROLE", f"Role:{name}", granted=True)
        return role

    def update_role(
        self,
        name: str,
        description: Optional[str] = None,
        parent_roles: Optional[List[str]] = None,
    ) -> Role:
        """Update role details."""
        role = self.get_role(name)

        if role.is_immutable:
            raise SecurityException(f"Role '{name}' is immutable")

        if description is not None:
            role.description = description

        if parent_roles is not None:
            role.parent_roles = []
            for parent_name in parent_roles:
                parent = self._find_role_by_name(parent_name)
                if parent:
                    role.parent_roles.append(parent)

        role_repo = Repository(self.graph, Role)
        role_repo.save(role)

        self._audit_log("UPDATE_ROLE", f"Role:{name}", granted=True)
        return role

    def delete_role(self, name: str) -> None:
        """Delete role."""
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

        self._audit_log("DELETE_ROLE", f"Role:{name}", granted=True)

    def list_roles(self) -> List[Role]:
        """List all roles."""
        query = "MATCH (r:_Security_Role) RETURN r"
        result = self.graph.query(query)

        roles = []
        if hasattr(result, "result_set"):
            role_repo = Repository(self.graph, Role)
            for record in result.result_set:
                role_node = record[0]
                role = role_repo.find_by_id(role_node.id, fetch=["parent_roles"])
                if role:
                    roles.append(role)

        return roles

    def get_role(self, name: str) -> Role:
        """Get role by name."""
        role = self._find_role_by_name(name)
        if not role:
            raise SecurityException(f"Role '{name}' not found")
        return role

    # ========== USER-ROLE ASSIGNMENT ==========

    def assign_role(self, username: str, role_name: str) -> None:
        """Assign role to user."""
        user = self.get_user(username)
        if not user:
            raise SecurityException(f"User '{username}' not found")

        role = self.get_role(role_name)

        # Check if already assigned
        if any(r.name == role_name for r in user.roles):
            return  # Already assigned

        user.roles.append(role)
        user_repo = Repository(self.graph, User)
        user_repo.save(user)

        self._audit_log("ASSIGN_ROLE", f"User:{username}->Role:{role_name}", granted=True)

    def revoke_role(self, username: str, role_name: str) -> None:
        """Revoke role from user."""
        user = self.get_user(username)
        if not user:
            raise SecurityException(f"User '{username}' not found")

        # Remove role
        user.roles = [r for r in user.roles if r.name != role_name]
        user_repo = Repository(self.graph, User)
        user_repo.save(user)

        self._audit_log("REVOKE_ROLE", f"User:{username}->Role:{role_name}", granted=True)

    def get_user_roles(self, username: str) -> List[str]:
        """Get all roles assigned to user (including inherited)."""
        user = self.get_user(username)
        if not user:
            raise SecurityException(f"User '{username}' not found")

        # Get all effective roles including inherited
        context = SecurityContext(user, self.graph)
        return list(context.effective_roles)

    # ========== PRIVILEGE MANAGEMENT ==========

    def grant_privilege(
        self,
        role_name: str,
        action: str,
        resource_type: str,
        resource_label: str = "*",
        resource_property: Optional[str] = None,
        scope: str = "GRAPH",
    ) -> Privilege:
        """Grant privilege to role."""
        role = self.get_role(role_name)

        if role.is_immutable:
            raise SecurityException(f"Cannot modify privileges for immutable role '{role_name}'")

        privilege = Privilege(
            action=action,
            resource_type=resource_type,
            resource_label=resource_label,
            resource_property=resource_property,
            grant_type="GRANT",
            scope=scope,
            is_immutable=False,
            created_at=datetime.now(),
        )
        privilege.role = role

        priv_repo = Repository(self.graph, Privilege)
        priv_repo.save(privilege)

        self._audit_log(
            "GRANT_PRIVILEGE",
            f"Role:{role_name}:{action}:{resource_type}:{resource_label}",
            granted=True,
        )
        return privilege

    def deny_privilege(
        self,
        role_name: str,
        action: str,
        resource_type: str,
        resource_label: str = "*",
        resource_property: Optional[str] = None,
        scope: str = "GRAPH",
    ) -> Privilege:
        """Deny privilege to role."""
        role = self.get_role(role_name)

        privilege = Privilege(
            action=action,
            resource_type=resource_type,
            resource_label=resource_label,
            resource_property=resource_property,
            grant_type="DENY",
            scope=scope,
            is_immutable=False,
            created_at=datetime.now(),
        )
        privilege.role = role

        priv_repo = Repository(self.graph, Privilege)
        priv_repo.save(privilege)

        self._audit_log(
            "DENY_PRIVILEGE",
            f"Role:{role_name}:{action}:{resource_type}:{resource_label}",
            granted=True,
        )
        return privilege

    def revoke_privilege(self, privilege_id: int) -> None:
        """Revoke privilege by ID."""
        priv_repo = Repository(self.graph, Privilege)
        privilege = priv_repo.find_by_id(privilege_id)

        if not privilege:
            raise SecurityException(f"Privilege {privilege_id} not found")

        if privilege.is_immutable:
            raise SecurityException(f"Privilege {privilege_id} is immutable")

        priv_repo.delete(privilege)

        self._audit_log("REVOKE_PRIVILEGE", f"Privilege:{privilege_id}", granted=True)

    def list_privileges(self, role_name: Optional[str] = None) -> List[Privilege]:
        """List privileges, optionally filtered by role."""
        if role_name:
            query = """
            MATCH (p:_Security_Privilege)-[:GRANTED_TO]->(r:_Security_Role {name: $role_name})
            RETURN p
            """
            params = {"role_name": role_name}
        else:
            query = "MATCH (p:_Security_Privilege) RETURN p"
            params = {}

        result = self.graph.query(query, params)

        privileges = []
        if hasattr(result, "result_set"):
            priv_repo = Repository(self.graph, Privilege)
            for record in result.result_set:
                priv_node = record[0]
                priv = priv_repo.find_by_id(priv_node.id, fetch=["role"])
                if priv:
                    privileges.append(priv)

        return privileges

    # ========== AUDIT QUERIES ==========

    def query_audit_logs(
        self,
        username: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Query audit logs with filters."""
        logs = self.audit_logger.query_logs(
            username=username,
            action=action,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        return [
            {
                "timestamp": log.timestamp,
                "username": log.username,
                "action": log.action,
                "resource": log.resource,
                "granted": log.granted,
                "reason": log.reason,
            }
            for log in logs
        ]

    # ========== HELPER METHODS ==========

    def _find_role_by_name(self, name: str) -> Optional[Role]:
        """Find role by name."""
        query = "MATCH (r:_Security_Role {name: $name}) RETURN r"
        result = self.graph.query(query, {"name": name})

        if result.result_set:
            role_repo = Repository(self.graph, Role)
            role_node = result.result_set[0][0]
            return role_repo.find_by_id(role_node.id, fetch=["parent_roles"])

        return None

    def _get_users_with_role(self, role_name: str) -> List[User]:
        """Get all users with specific role."""
        query = """
        MATCH (user:_Security_User)-[:HAS_ROLE]->(role:_Security_Role {name: $role_name})
        RETURN user
        """
        result = self.graph.query(query, {"role_name": role_name})

        users = []
        if hasattr(result, "result_set"):
            user_repo = Repository(self.graph, User)
            for record in result.result_set:
                user_node = record[0]
                user = user_repo.find_by_id(user_node.id)
                if user:
                    users.append(user)

        return users

    def _audit_log(self, action: str, resource: str, granted: bool):
        """Log security event to audit log."""
        self.audit_logger.log(
            user=self.security_context.user,
            action=action,
            resource=resource,
            granted=granted,
        )
