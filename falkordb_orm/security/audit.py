"""Audit logging for security events."""

from datetime import datetime
from typing import Optional

from ..repository import Repository
from .models import AuditLog, User


class AuditLogger:
    """Logger for security events."""

    def __init__(self, graph):
        self.graph = graph
        self.repo = Repository(graph, AuditLog)

    def log(
        self,
        user: User,
        action: str,
        resource: str,
        granted: bool,
        resource_id: Optional[int] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
    ):
        """Log a security event.

        Args:
            user: User performing the action
            action: Action type (READ, WRITE, CREATE, DELETE, etc.)
            resource: Resource being accessed
            granted: Whether access was granted
            resource_id: Optional resource ID
            reason: Optional reason for denial
            ip_address: Optional IP address
        """
        log_entry = AuditLog(
            timestamp=datetime.now(),
            user_id=user.id,
            username=user.username,
            action=action,
            resource=resource,
            resource_id=resource_id,
            granted=granted,
            reason=reason,
            ip_address=ip_address,
        )

        self.repo.save(log_entry)

    def query_logs(
        self,
        username: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        granted: Optional[bool] = None,
        limit: int = 100,
    ) -> list:
        """Query audit logs with filters.

        Args:
            username: Filter by username
            action: Filter by action type
            start_date: Filter by start date
            end_date: Filter by end date
            granted: Filter by granted status
            limit: Maximum results

        Returns:
            List of AuditLog entries
        """
        query = "MATCH (log:_Security_AuditLog) WHERE 1=1"
        params = {}

        if username:
            query += " AND log.username = $username"
            params["username"] = username

        if action:
            query += " AND log.action = $action"
            params["action"] = action

        if start_date:
            query += " AND log.timestamp >= $start_date"
            params["start_date"] = start_date

        if end_date:
            query += " AND log.timestamp <= $end_date"
            params["end_date"] = end_date

        if granted is not None:
            query += " AND log.granted = $granted"
            params["granted"] = granted

        query += " RETURN log ORDER BY log.timestamp DESC LIMIT $limit"
        params["limit"] = limit

        result = self.graph.query(query, params)

        logs = []
        if hasattr(result, "result_set"):
            for record in result.result_set:
                log_node = record[0]
                log = AuditLog(
                    timestamp=log_node.properties.get("timestamp"),
                    user_id=log_node.properties.get("user_id"),
                    username=log_node.properties.get("username"),
                    action=log_node.properties.get("action"),
                    resource=log_node.properties.get("resource"),
                    resource_id=log_node.properties.get("resource_id"),
                    granted=log_node.properties.get("granted"),
                    reason=log_node.properties.get("reason"),
                    ip_address=log_node.properties.get("ip_address"),
                )
                log.id = log_node.id
                logs.append(log)

        return logs
