"""In-memory RBAC storage for fast permission checking."""

import json
from datetime import datetime
from typing import Dict, List

from .models import Privilege, Role, User

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class InMemoryRBACStore:
    """Fast in-memory RBAC storage."""

    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.users: Dict[str, User] = {}
        self.privileges: List[Privilege] = []
        self._init_built_in_roles()

    def _init_built_in_roles(self):
        """Initialize Neo4j-style built-in roles."""
        now = datetime.now()

        self.roles["PUBLIC"] = Role(
            name="PUBLIC",
            description="Default role for all users",
            created_at=now,
            is_immutable=True,
        )
        self.roles["reader"] = Role(name="reader", description="Read-only access", created_at=now)
        self.roles["editor"] = Role(
            name="editor", description="Read and write access", created_at=now
        )
        self.roles["publisher"] = Role(
            name="publisher",
            description="Editor + schema modification",
            created_at=now,
        )
        self.roles["admin"] = Role(name="admin", description="Full access", created_at=now)

    def load_from_yaml(self, config_path: str):
        """Load RBAC configuration from YAML."""
        if not HAS_YAML:
            raise ImportError(
                "PyYAML is required to load YAML configs. Install with: pip install pyyaml"
            )

        with open(config_path) as f:
            config = yaml.safe_load(f)

        self._load_config(config)

    def load_from_json(self, config_path: str):
        """Load RBAC configuration from JSON."""
        with open(config_path) as f:
            config = json.load(f)

        self._load_config(config)

    def _load_config(self, config: dict):
        """Load configuration from dict."""
        now = datetime.now()

        # Load roles
        if "roles" in config:
            for role_config in config["roles"]:
                role = Role(
                    name=role_config["name"],
                    description=role_config.get("description", ""),
                    created_at=now,
                    is_immutable=role_config.get("is_immutable", False),
                )
                self.roles[role.name] = role

        # Load users
        if "users" in config:
            for user_config in config["users"]:
                user = User(
                    username=user_config["username"],
                    email=user_config.get("email", ""),
                    created_at=now,
                    is_active=user_config.get("is_active", True),
                )

                # Assign roles
                role_names = user_config.get("roles", [])
                user.roles = [self.roles[r] for r in role_names if r in self.roles]

                self.users[user.username] = user

        # Load privileges
        if "privileges" in config:
            for priv_config in config["privileges"]:
                role = self.roles.get(priv_config["role"])
                if not role:
                    continue

                privilege = Privilege(
                    action=priv_config["action"],
                    resource_type=priv_config.get("resource_type", "NODE"),
                    resource_label=priv_config.get("resource_label", "*"),
                    resource_property=priv_config.get("resource_property"),
                    grant_type=priv_config.get("grant_type", "GRANT"),
                    scope=priv_config.get("scope", "GRAPH"),
                    is_immutable=priv_config.get("is_immutable", False),
                    created_at=now,
                )
                privilege.role = role
                self.privileges.append(privilege)

    def add_role(self, role: Role):
        """Add role to store."""
        self.roles[role.name] = role

    def add_user(self, user: User):
        """Add user to store."""
        self.users[user.username] = user

    def add_privilege(self, privilege: Privilege):
        """Add privilege to store."""
        self.privileges.append(privilege)

    def get_role(self, name: str) -> Role:
        """Get role by name."""
        return self.roles.get(name)

    def get_user(self, username: str) -> User:
        """Get user by username."""
        return self.users.get(username)

    def get_privileges_for_role(self, role_name: str) -> List[Privilege]:
        """Get all privileges for a role."""
        return [p for p in self.privileges if p.role.name == role_name]
