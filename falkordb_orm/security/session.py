"""Secure session with integrated RBAC."""

from typing import Type, TypeVar

from ..session import Session
from .context import SecurityContext
from .models import User
from .repository import SecureRepository

T = TypeVar("T")


class SecureSession(Session):
    """Session with integrated security."""

    def __init__(self, graph, user: User):
        super().__init__(graph)
        self.security_context = SecurityContext(user, graph)

    def get_repository(self, entity_class: Type[T]) -> SecureRepository[T]:
        """Get security-aware repository."""
        return SecureRepository(self.graph, entity_class, self.security_context)

    def get(self, entity_class: Type[T], entity_id):
        """Get with security checks."""
        repo = self.get_repository(entity_class)
        return repo.find_by_id(entity_id)

    def impersonate(self, user: User):
        """Create impersonation context."""
        return ImpersonationContext(self, user)


class ImpersonationContext:
    """Context manager for impersonation."""

    def __init__(self, session: SecureSession, impersonate_user: User):
        self.session = session
        self.original_user = session.security_context.user
        self.impersonate_user = impersonate_user

    def __enter__(self):
        self.session.security_context = SecurityContext(
            self.impersonate_user, self.session.graph
        )
        return self.session

    def __exit__(self, *args):
        self.session.security_context = SecurityContext(
            self.original_user, self.session.graph
        )
