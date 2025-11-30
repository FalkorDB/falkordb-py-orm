"""Security context for managing user permissions."""

from typing import Any, Dict, Optional, Set

from .models import Privilege, Role, User


class SecurityContext:
    """Manages current user and their effective permissions."""

    def __init__(self, user: User, graph):
        self.user = user
        self.graph = graph
        self.effective_roles = self._compute_effective_roles()
        self.privilege_cache = self._build_privilege_cache()

    def _compute_effective_roles(self) -> Set[str]:
        """Compute all roles including inherited ones."""
        roles = {"PUBLIC"}  # Everyone has PUBLIC

        # Add direct roles
        for role in self.user.roles:
            roles.add(role.name)
            # Add inherited roles (recursive)
            roles.update(self._get_inherited_roles(role))

        return roles

    def _get_inherited_roles(self, role: Role) -> Set[str]:
        """Recursively get inherited roles."""
        inherited = set()
        if hasattr(role, "parent_roles") and role.parent_roles:
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
                if priv.grant_type == "DENY":
                    cache[key]["granted"] = False
                elif priv.grant_type == "GRANT" and "granted" not in cache[key]:
                    cache[key]["granted"] = True

        return cache

    def _load_role_privileges(self, role_name: str) -> list:
        """Load privileges for a role."""
        try:
            # Query privileges from graph
            query = """
            MATCH (p:_Security_Privilege)-[:GRANTED_TO]->(r:_Security_Role {name: $role_name})
            RETURN p
            """
            result = self.graph.query(query, {"role_name": role_name})

            privileges = []
            if hasattr(result, "result_set"):
                for record in result.result_set:
                    priv_node = record[0]
                    # Convert node to Privilege object
                    priv = Privilege(
                        action=priv_node.properties.get("action"),
                        resource_type=priv_node.properties.get("resource_type"),
                        resource_label=priv_node.properties.get("resource_label"),
                        resource_property=priv_node.properties.get("resource_property"),
                        grant_type=priv_node.properties.get("grant_type"),
                        scope=priv_node.properties.get("scope", "GRAPH"),
                        is_immutable=priv_node.properties.get("is_immutable", False),
                        created_at=priv_node.properties.get("created_at"),
                    )
                    privileges.append(priv)

            return privileges
        except Exception:
            # If graph query fails, return empty list
            return []

    def can(self, action: str, resource: str, entity: Optional[Any] = None) -> bool:
        """Check if user can perform action on resource.

        Examples:
            if context.can('READ', 'Person'):
                # Load person

            if context.can('WRITE', 'Person.salary', entity=person):
                # Update salary
        """
        # Admin has all permissions
        if "admin" in self.effective_roles:
            return True

        # Parse resource
        if "." in resource:
            parts = resource.split(".", 1)
            resource_label = parts[0]
            resource_type = "PROPERTY"
        else:
            resource_label = resource
            resource_type = "NODE" if not resource.isupper() else "RELATIONSHIP"

        # Check cache
        key = f"{action}:{resource_type}:{resource_label}"
        if key in self.privilege_cache:
            return self.privilege_cache[key].get("granted", False)

        # Check wildcard permissions
        wildcard_key = f"{action}:{resource_type}:*"
        if wildcard_key in self.privilege_cache:
            return self.privilege_cache[wildcard_key].get("granted", False)

        # Default deny
        return False

    def get_denied_properties(self, entity_class: str, action: str) -> Set[str]:
        """Get list of properties user cannot access."""
        denied = set()

        # Check property-level privileges
        for role_name in self.effective_roles:
            privileges = self._load_role_privileges(role_name)

            for priv in privileges:
                if (
                    priv.action == action
                    and priv.resource_type == "PROPERTY"
                    and priv.resource_label == entity_class
                    and priv.grant_type == "DENY"
                    and priv.resource_property
                ):
                    denied.add(priv.resource_property)

        # Check entity security metadata
        # This would need to be implemented when we have access to entity classes

        return denied

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return role_name in self.effective_roles

    def get_effective_roles(self) -> Set[str]:
        """Get all effective roles for the user."""
        return self.effective_roles.copy()
