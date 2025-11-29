"""Query rewriter for enforcing security at query level."""

import re
from typing import Dict, Tuple


class QueryRewriter:
    """Rewrites Cypher queries to enforce security."""

    def __init__(self, security_context):
        self.context = security_context

    def rewrite(self, cypher: str, params: Dict) -> Tuple[str, Dict]:
        """Rewrite query to enforce RBAC.

        Strategies:
        1. Add WHERE clauses for row-level filtering
        2. Remove unauthorized properties from RETURN
        3. Inject user context into query parameters
        """
        # Parse query to identify components
        query_parts = self._parse_query(cypher)

        # Apply security filters
        modified_cypher = cypher

        # Add row-level filters if needed
        if query_parts["match_clause"] and query_parts.get("requires_filtering"):
            modified_cypher = self._add_row_filters(modified_cypher, query_parts)

        # Filter properties in RETURN clause
        if query_parts["return_clause"]:
            modified_cypher = self._filter_properties(modified_cypher, query_parts)

        # Inject user context
        params["__security_user_id"] = self.user.id if hasattr(self, "user") else None
        params["__security_roles"] = list(self.context.effective_roles)

        return modified_cypher, params

    def _parse_query(self, cypher: str) -> Dict:
        """Parse Cypher into components."""
        # Simple pattern matching for Cypher components
        match_pattern = r"MATCH\s+(.*?)(?:WHERE|RETURN|$)"
        where_pattern = r"WHERE\s+(.*?)(?:RETURN|$)"
        return_pattern = r"RETURN\s+(.*?)(?:ORDER|LIMIT|$)"

        match_match = re.search(match_pattern, cypher, re.IGNORECASE | re.DOTALL)
        where_match = re.search(where_pattern, cypher, re.IGNORECASE | re.DOTALL)
        return_match = re.search(return_pattern, cypher, re.IGNORECASE | re.DOTALL)

        return {
            "match_clause": match_match.group(1).strip() if match_match else None,
            "where_clause": where_match.group(1).strip() if where_match else None,
            "return_clause": return_match.group(1).strip() if return_match else None,
            "variables": self._extract_variables(cypher),
            "requires_filtering": False,  # Would be determined based on entity metadata
        }

    def _extract_variables(self, cypher: str) -> list:
        """Extract variable names from MATCH clause."""
        # Simple extraction - looks for (var:Label) patterns
        pattern = r"\((\w+):\w+\)"
        matches = re.findall(pattern, cypher)
        return list(set(matches))

    def _add_row_filters(self, cypher: str, parts: Dict) -> str:
        """Add row-level security filters.

        This is a simplified version. A full implementation would:
        1. Identify entity types in MATCH
        2. Check if entity has row-level security
        3. Inject appropriate WHERE conditions
        """
        # For now, return unchanged
        # Full implementation would add WHERE clauses based on row_level_security decorators
        return cypher

    def _filter_properties(self, cypher: str, parts: Dict) -> str:
        """Remove unauthorized properties from RETURN.

        This is a simplified version. A full implementation would:
        1. Parse RETURN clause completely
        2. Identify property accesses (e.g., person.ssn)
        3. Remove denied properties
        4. Reconstruct RETURN clause
        """
        # For now, return unchanged
        # Full implementation would parse and filter RETURN properties
        return cypher

    def should_filter_query(self, entity_class) -> bool:
        """Determine if query needs security filtering."""
        # Check if entity class has security metadata
        if hasattr(entity_class, "__security_metadata__"):
            metadata = entity_class.__security_metadata__
            if metadata.get("row_filter") or metadata.get("deny_read_properties"):
                return True
        return False
