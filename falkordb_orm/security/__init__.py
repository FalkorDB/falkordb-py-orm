"""Security module for Role-Based Access Control (RBAC)."""

from .audit import AuditLogger
from .context import SecurityContext
from .decorators import row_level_security, secured, secured_property
from .exceptions import (
    AccessDeniedException,
    PrivilegeException,
    RoleException,
    SecurityException,
    UnauthorizedException,
)
from .manager import RBACManager
from .models import AuditLog, Privilege, Role, User
from .policy import PolicyRule, SecurityPolicy
from .repository import SecureRepository
from .rewriter import QueryRewriter
from .session import ImpersonationContext, SecureSession
from .store import InMemoryRBACStore

__all__ = [
    # Exceptions
    "SecurityException",
    "UnauthorizedException",
    "AccessDeniedException",
    "PrivilegeException",
    "RoleException",
    # Models
    "Role",
    "User",
    "Privilege",
    "AuditLog",
    # Policy
    "SecurityPolicy",
    "PolicyRule",
    # Store
    "InMemoryRBACStore",
    # Context
    "SecurityContext",
    # Repository
    "SecureRepository",
    # Session
    "SecureSession",
    "ImpersonationContext",
    # Rewriter
    "QueryRewriter",
    # Manager
    "RBACManager",
    # Audit
    "AuditLogger",
    # Decorators
    "secured",
    "row_level_security",
    "secured_property",
]
