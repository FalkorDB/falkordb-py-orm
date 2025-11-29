"""Security-related exceptions for RBAC."""


class SecurityException(Exception):
    """Base exception for security-related errors."""

    pass


class UnauthorizedException(SecurityException):
    """Raised when user lacks required authorization."""

    pass


class AccessDeniedException(SecurityException):
    """Raised when access to a resource is denied."""

    pass


class PrivilegeException(SecurityException):
    """Raised when privilege operations fail."""

    pass


class RoleException(SecurityException):
    """Raised when role operations fail."""

    pass
