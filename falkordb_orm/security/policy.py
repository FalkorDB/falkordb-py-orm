"""Security policy DSL for declarative RBAC management."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from ..repository import Repository
from .models import Privilege, Role


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

    def grant(self, action: str, resource: str, to: str, conditions: Optional[Dict] = None):
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
            grant_type="GRANT",
            role=to,
            conditions=conditions,
        )
        self.rules.append(rule)
        self._persist_rule(rule)

    def deny(self, action: str, resource: str, to: str, conditions: Optional[Dict] = None):
        """Deny privilege to role."""
        rule = PolicyRule(
            action=action,
            resource_pattern=resource,
            grant_type="DENY",
            role=to,
            conditions=conditions,
        )
        self.rules.append(rule)
        self._persist_rule(rule)

    def revoke(self, action: str, resource: str, from_role: str):
        """Revoke privilege from role."""
        # Parse resource pattern
        resource_type, resource_label, resource_property = self._parse_resource(resource)

        # Find and delete matching privileges
        priv_repo = Repository(self.graph, Privilege)
        role_repo = Repository(self.graph, Role)

        role = role_repo.find_by(name=from_role)
        if not role:
            return

        # Query for matching privileges
        query = """
        MATCH (p:_Security_Privilege)-[:GRANTED_TO]->(r:_Security_Role {name: $role_name})
        WHERE p.action = $action
          AND p.resource_type = $resource_type
          AND p.resource_label = $resource_label
        """

        params = {
            "role_name": from_role,
            "action": action,
            "resource_type": resource_type,
            "resource_label": resource_label,
        }

        if resource_property:
            query += " AND p.resource_property = $resource_property"
            params["resource_property"] = resource_property

        query += " DELETE p"

        self.graph.query(query, params)

        # Remove from in-memory rules
        self.rules = [
            r
            for r in self.rules
            if not (r.action == action and r.resource_pattern == resource and r.role == from_role)
        ]

    def _persist_rule(self, rule: PolicyRule):
        """Store rule as Privilege node in graph."""
        role_repo = Repository(self.graph, Role)
        priv_repo = Repository(self.graph, Privilege)

        # Find or create role
        role = role_repo.find_by(name=rule.role)
        if not role:
            raise ValueError(f"Role '{rule.role}' does not exist")

        # Parse resource pattern
        resource_type, resource_label, resource_property = self._parse_resource(
            rule.resource_pattern
        )

        # Create privilege
        privilege = Privilege(
            action=rule.action,
            resource_type=resource_type,
            resource_label=resource_label,
            resource_property=resource_property,
            grant_type=rule.grant_type,
            scope="GRAPH",
            is_immutable=False,
            created_at=datetime.now(),
        )
        privilege.role = role

        priv_repo.save(privilege)

    def _parse_resource(self, resource: str) -> tuple:
        """Parse resource pattern into components.

        Examples:
            "Person" -> ("NODE", "Person", None)
            "Person.email" -> ("PROPERTY", "Person", "email")
            "KNOWS" -> ("RELATIONSHIP", "KNOWS", None)
        """
        if "." in resource:
            # Property-level
            parts = resource.split(".", 1)
            return ("PROPERTY", parts[0], parts[1])
        elif resource.isupper():
            # Relationship type
            return ("RELATIONSHIP", resource, None)
        else:
            # Node label
            return ("NODE", resource, None)
