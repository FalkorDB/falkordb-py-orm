"""Security metadata models for RBAC."""

from datetime import datetime
from typing import List, Optional

from ..decorators import generated_id, node, relationship, unique


@node("_Security_Role")
class Role:
    """Security role with privileges."""

    id: Optional[int] = generated_id()
    name: str = unique(required=True)
    description: str
    created_at: datetime
    is_immutable: bool = False

    # Hierarchical roles
    parent_roles: List["Role"] = relationship(
        "INHERITS_FROM", target="Role", direction="OUTGOING"
    )


@node("_Security_User")
class User:
    """User with assigned roles."""

    id: Optional[int] = generated_id()
    username: str = unique(required=True)
    email: str
    created_at: datetime
    is_active: bool = True

    roles: List[Role] = relationship("HAS_ROLE", target=Role, direction="OUTGOING")


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

    role: Role = relationship("GRANTED_TO", target=Role, direction="OUTGOING")


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
