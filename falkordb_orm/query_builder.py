"""Query builder for generating Cypher queries."""

from typing import Any, Dict, List, Optional, Type

from .metadata import EntityMetadata, RelationshipMetadata, get_entity_metadata
from .query_parser import (
    QuerySpec, Condition, OrderClause, Operation, Operator, LogicalOperator
)


class QueryBuilder:
    """Generates Cypher queries for common operations."""
    
    def build_match_by_id_query(self, metadata: EntityMetadata, entity_id: Any) -> tuple[str, Dict[str, Any]]:
        """
        Build MATCH query to find entity by ID.
        
        Args:
            metadata: Entity metadata
            entity_id: ID value to match
            
        Returns:
            Tuple of (cypher_query, parameters)
        """
        labels_str = ':'.join(metadata.labels)
        
        if metadata.id_property and metadata.id_property.id_generator is not None:
            # Use internal FalkorDB ID
            cypher = f"MATCH (n:{labels_str}) WHERE id(n) = $id RETURN n"
        else:
            # Use property-based ID
            cypher = f"MATCH (n:{labels_str} {{id: $id}}) RETURN n"
        
        params = {'id': entity_id}
        return cypher, params
    
    def build_match_all_query(self, metadata: EntityMetadata) -> tuple[str, Dict[str, Any]]:
        """
        Build MATCH query to find all entities.
        
        Args:
            metadata: Entity metadata
            
        Returns:
            Tuple of (cypher_query, parameters)
        """
        labels_str = ':'.join(metadata.labels)
        cypher = f"MATCH (n:{labels_str}) RETURN n"
        params: Dict[str, Any] = {}
        return cypher, params
    
    def build_count_query(self, metadata: EntityMetadata) -> tuple[str, Dict[str, Any]]:
        """
        Build query to count entities.
        
        Args:
            metadata: Entity metadata
            
        Returns:
            Tuple of (cypher_query, parameters)
        """
        labels_str = ':'.join(metadata.labels)
        cypher = f"MATCH (n:{labels_str}) RETURN count(n) as count"
        params: Dict[str, Any] = {}
        return cypher, params
    
    def build_delete_by_id_query(self, metadata: EntityMetadata, entity_id: Any) -> tuple[str, Dict[str, Any]]:
        """
        Build DELETE query to remove entity by ID.
        
        Args:
            metadata: Entity metadata
            entity_id: ID value to match
            
        Returns:
            Tuple of (cypher_query, parameters)
        """
        labels_str = ':'.join(metadata.labels)
        
        if metadata.id_property and metadata.id_property.id_generator is not None:
            # Use internal FalkorDB ID
            cypher = f"MATCH (n:{labels_str}) WHERE id(n) = $id DELETE n"
        else:
            # Use property-based ID
            cypher = f"MATCH (n:{labels_str} {{id: $id}}) DELETE n"
        
        params = {'id': entity_id}
        return cypher, params
    
    def build_delete_all_query(self, metadata: EntityMetadata) -> tuple[str, Dict[str, Any]]:
        """
        Build DELETE query to remove all entities.
        
        Args:
            metadata: Entity metadata
            
        Returns:
            Tuple of (cypher_query, parameters)
        """
        labels_str = ':'.join(metadata.labels)
        cypher = f"MATCH (n:{labels_str}) DELETE n"
        params: Dict[str, Any] = {}
        return cypher, params
    
    def build_exists_by_id_query(self, metadata: EntityMetadata, entity_id: Any) -> tuple[str, Dict[str, Any]]:
        """
        Build query to check if entity exists by ID.
        
        Args:
            metadata: Entity metadata
            entity_id: ID value to check
            
        Returns:
            Tuple of (cypher_query, parameters)
        """
        labels_str = ':'.join(metadata.labels)
        
        if metadata.id_property and metadata.id_property.id_generator is not None:
            # Use internal FalkorDB ID
            cypher = f"MATCH (n:{labels_str}) WHERE id(n) = $id RETURN count(n) > 0 as exists"
        else:
            # Use property-based ID
            cypher = f"MATCH (n:{labels_str} {{id: $id}}) RETURN count(n) > 0 as exists"
        
        params = {'id': entity_id}
        return cypher, params
    
    def build_derived_query(
        self, 
        metadata: EntityMetadata, 
        spec: QuerySpec, 
        param_values: List[Any]
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build a derived query from a QuerySpec.
        
        Args:
            metadata: Entity metadata
            spec: Parsed query specification
            param_values: Values for query parameters
            
        Returns:
            Tuple of (cypher_query, parameters)
        """
        labels_str = ':'.join(metadata.labels)
        
        # Build WHERE clause
        where_clause, params = self.build_where_clause(spec.conditions, spec.logical_operator, param_values)
        
        # Build ORDER BY clause
        order_by_clause = self.build_order_by_clause(spec.ordering)
        
        # Build LIMIT clause
        limit_clause = f" LIMIT {spec.limit}" if spec.limit else ""
        
        # Build query based on operation
        if spec.operation == Operation.FIND:
            cypher = f"MATCH (n:{labels_str})"
            if where_clause:
                cypher += f" WHERE {where_clause}"
            cypher += " RETURN n"
            if order_by_clause:
                cypher += f" {order_by_clause}"
            cypher += limit_clause
        
        elif spec.operation == Operation.COUNT:
            cypher = f"MATCH (n:{labels_str})"
            if where_clause:
                cypher += f" WHERE {where_clause}"
            cypher += " RETURN count(n) as count"
        
        elif spec.operation == Operation.EXISTS:
            cypher = f"MATCH (n:{labels_str})"
            if where_clause:
                cypher += f" WHERE {where_clause}"
            cypher += " RETURN count(n) > 0 as exists"
        
        elif spec.operation == Operation.DELETE:
            cypher = f"MATCH (n:{labels_str})"
            if where_clause:
                cypher += f" WHERE {where_clause}"
            cypher += " DELETE n"
        
        return cypher, params
    
    def build_where_clause(
        self, 
        conditions: List[Condition], 
        logical_op: LogicalOperator,
        param_values: List[Any]
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build WHERE clause from conditions.
        
        Args:
            conditions: List of conditions
            logical_op: Logical operator (AND/OR)
            param_values: Parameter values
            
        Returns:
            Tuple of (where_clause_string, parameters_dict)
        """
        if not conditions:
            return "", {}
        
        clauses = []
        params = {}
        param_idx = 0
        
        for condition in conditions:
            clause, condition_params, param_idx = self._build_condition_clause(
                condition, param_values, param_idx
            )
            clauses.append(clause)
            params.update(condition_params)
        
        where_clause = f" {logical_op.value} ".join(clauses)
        return where_clause, params
    
    def _build_condition_clause(
        self, 
        condition: Condition, 
        param_values: List[Any],
        param_idx: int
    ) -> tuple[str, Dict[str, Any], int]:
        """
        Build a single condition clause.
        
        Returns:
            Tuple of (clause_string, params_dict, next_param_idx)
        """
        prop = f"n.{condition.property_name}"
        params = {}
        
        if condition.operator == Operator.EQUALS:
            param_name = f"p{param_idx}"
            clause = f"{prop} = ${param_name}"
            params[param_name] = param_values[param_idx]
            param_idx += 1
        
        elif condition.operator == Operator.NOT_EQUALS:
            param_name = f"p{param_idx}"
            clause = f"{prop} <> ${param_name}"
            params[param_name] = param_values[param_idx]
            param_idx += 1
        
        elif condition.operator == Operator.GREATER_THAN:
            param_name = f"p{param_idx}"
            clause = f"{prop} > ${param_name}"
            params[param_name] = param_values[param_idx]
            param_idx += 1
        
        elif condition.operator == Operator.GREATER_THAN_EQUAL:
            param_name = f"p{param_idx}"
            clause = f"{prop} >= ${param_name}"
            params[param_name] = param_values[param_idx]
            param_idx += 1
        
        elif condition.operator == Operator.LESS_THAN:
            param_name = f"p{param_idx}"
            clause = f"{prop} < ${param_name}"
            params[param_name] = param_values[param_idx]
            param_idx += 1
        
        elif condition.operator == Operator.LESS_THAN_EQUAL:
            param_name = f"p{param_idx}"
            clause = f"{prop} <= ${param_name}"
            params[param_name] = param_values[param_idx]
            param_idx += 1
        
        elif condition.operator == Operator.BETWEEN:
            param_name1 = f"p{param_idx}"
            param_name2 = f"p{param_idx + 1}"
            clause = f"{prop} >= ${param_name1} AND {prop} <= ${param_name2}"
            params[param_name1] = param_values[param_idx]
            params[param_name2] = param_values[param_idx + 1]
            param_idx += 2
        
        elif condition.operator == Operator.IN:
            param_name = f"p{param_idx}"
            clause = f"{prop} IN ${param_name}"
            params[param_name] = param_values[param_idx]
            param_idx += 1
        
        elif condition.operator == Operator.NOT_IN:
            param_name = f"p{param_idx}"
            clause = f"NOT {prop} IN ${param_name}"
            params[param_name] = param_values[param_idx]
            param_idx += 1
        
        elif condition.operator == Operator.IS_NULL:
            clause = f"{prop} IS NULL"
        
        elif condition.operator == Operator.IS_NOT_NULL:
            clause = f"{prop} IS NOT NULL"
        
        elif condition.operator == Operator.CONTAINING:
            param_name = f"p{param_idx}"
            clause = f"{prop} CONTAINS ${param_name}"
            params[param_name] = param_values[param_idx]
            param_idx += 1
        
        elif condition.operator == Operator.STARTING_WITH:
            param_name = f"p{param_idx}"
            clause = f"{prop} STARTS WITH ${param_name}"
            params[param_name] = param_values[param_idx]
            param_idx += 1
        
        elif condition.operator == Operator.ENDING_WITH:
            param_name = f"p{param_idx}"
            clause = f"{prop} ENDS WITH ${param_name}"
            params[param_name] = param_values[param_idx]
            param_idx += 1
        
        elif condition.operator == Operator.LIKE:
            param_name = f"p{param_idx}"
            clause = f"{prop} =~ ${param_name}"
            params[param_name] = param_values[param_idx]
            param_idx += 1
        
        else:
            clause = f"{prop} = ${param_idx}"
            params[f"p{param_idx}"] = param_values[param_idx]
            param_idx += 1
        
        return clause, params, param_idx
    
    def build_order_by_clause(self, ordering: List[OrderClause]) -> str:
        """
        Build ORDER BY clause from ordering specifications.
        
        Args:
            ordering: List of OrderClause objects
            
        Returns:
            ORDER BY clause string (empty if no ordering)
        """
        if not ordering:
            return ""
        
        clauses = [f"n.{order.property_name} {order.direction}" for order in ordering]
        return "ORDER BY " + ", ".join(clauses)
    
    def build_relationship_load_query(
        self, 
        relationship_meta: RelationshipMetadata,
        source_id: int,
        target_class: Type
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build query to load related entities through a relationship.
        
        Args:
            relationship_meta: Relationship metadata
            source_id: ID of source entity
            target_class: Target entity class
            
        Returns:
            Tuple of (cypher_query, parameters)
        """
        # Get target entity metadata
        target_metadata = get_entity_metadata(target_class)
        if target_metadata is None:
            raise ValueError(f"Target class {target_class.__name__} is not a valid entity")
        
        target_labels = ':'.join(target_metadata.labels)
        
        # Build relationship pattern based on direction
        if relationship_meta.direction == "OUTGOING":
            rel_pattern = f"-[:{relationship_meta.relationship_type}]->"
        elif relationship_meta.direction == "INCOMING":
            rel_pattern = f"<-[:{relationship_meta.relationship_type}]-"
        elif relationship_meta.direction == "BOTH":
            rel_pattern = f"-[:{relationship_meta.relationship_type}]-"
        else:
            raise ValueError(f"Invalid direction: {relationship_meta.direction}")
        
        # Build query
        cypher = f"""
        MATCH (source){rel_pattern}(target:{target_labels})
        WHERE id(source) = $source_id
        RETURN target
        """
        
        params = {'source_id': source_id}
        
        return cypher, params
    
    def build_relationship_create_query(
        self,
        relationship_meta: RelationshipMetadata,
        source_id: int,
        target_id: int
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build query to create a relationship edge between two nodes.
        
        Args:
            relationship_meta: Relationship metadata
            source_id: Source node ID
            target_id: Target node ID
            
        Returns:
            Tuple of (cypher_query, parameters)
        """
        # Build relationship pattern based on direction
        if relationship_meta.direction == "OUTGOING":
            rel_pattern = f"CREATE (source)-[:{relationship_meta.relationship_type}]->(target)"
        elif relationship_meta.direction == "INCOMING":
            rel_pattern = f"CREATE (source)<-[:{relationship_meta.relationship_type}]-(target)"
        elif relationship_meta.direction == "BOTH":
            rel_pattern = f"CREATE (source)-[:{relationship_meta.relationship_type}]-(target)"
        else:
            raise ValueError(f"Invalid direction: {relationship_meta.direction}")
        
        # Build query - match both nodes by ID, then create edge
        cypher = f"""
        MATCH (source), (target)
        WHERE id(source) = $source_id AND id(target) = $target_id
        {rel_pattern}
        """
        
        params = {
            'source_id': source_id,
            'target_id': target_id
        }
        
        return cypher, params
    
    def build_eager_loading_query(
        self,
        metadata: EntityMetadata,
        entity_id: Any,
        fetch_hints: List[str]
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build query with eager loading for specified relationships.
        
        Args:
            metadata: Entity metadata
            entity_id: ID of entity to fetch
            fetch_hints: List of relationship names to eagerly load
            
        Returns:
            Tuple of (cypher_query, parameters)
        """
        labels_str = ':'.join(metadata.labels)
        
        # Start with main entity match
        if metadata.id_property and metadata.id_property.id_generator is not None:
            where_clause = "WHERE id(n) = $id"
        else:
            where_clause = "WHERE n.id = $id"
        
        cypher_parts = [f"MATCH (n:{labels_str})", where_clause]
        
        # Add OPTIONAL MATCH for each relationship to fetch
        return_parts = ["n"]
        
        for hint in fetch_hints:
            # Find relationship metadata
            rel_meta = metadata.get_relationship_by_python_name(hint)
            if rel_meta is None:
                continue
            
            # Get target metadata
            target_metadata = get_entity_metadata(rel_meta.target_class)
            if target_metadata is None:
                continue
            
            target_labels = ':'.join(target_metadata.labels)
            var_name = f"{hint}_target"
            
            # Build relationship pattern
            if rel_meta.direction == "OUTGOING":
                rel_pattern = f"-[:{rel_meta.relationship_type}]->"
            elif rel_meta.direction == "INCOMING":
                rel_pattern = f"<-[:{rel_meta.relationship_type}]-"
            elif rel_meta.direction == "BOTH":
                rel_pattern = f"-[:{rel_meta.relationship_type}]-"
            else:
                continue
            
            # Add OPTIONAL MATCH
            cypher_parts.append(
                f"OPTIONAL MATCH (n){rel_pattern}({var_name}:{target_labels})"
            )
            
            # Add to RETURN with collection
            return_parts.append(f"collect(DISTINCT {var_name}) as {hint}")
        
        # Build final query
        cypher_parts.append("RETURN " + ", ".join(return_parts))
        cypher = "\n".join(cypher_parts)
        
        params = {'id': entity_id}
        
        return cypher, params
    
    def build_eager_loading_query_all(
        self,
        metadata: EntityMetadata,
        fetch_hints: List[str]
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build query with eager loading for all entities.
        
        Args:
            metadata: Entity metadata
            fetch_hints: List of relationship names to eagerly load
            
        Returns:
            Tuple of (cypher_query, parameters)
        """
        labels_str = ':'.join(metadata.labels)
        
        # Start with main entity match
        cypher_parts = [f"MATCH (n:{labels_str})"]
        
        # Add OPTIONAL MATCH for each relationship to fetch
        return_parts = ["n"]
        
        for hint in fetch_hints:
            # Find relationship metadata
            rel_meta = metadata.get_relationship_by_python_name(hint)
            if rel_meta is None:
                continue
            
            # Get target metadata
            target_metadata = get_entity_metadata(rel_meta.target_class)
            if target_metadata is None:
                continue
            
            target_labels = ':'.join(target_metadata.labels)
            var_name = f"{hint}_target"
            
            # Build relationship pattern
            if rel_meta.direction == "OUTGOING":
                rel_pattern = f"-[:{rel_meta.relationship_type}]->"
            elif rel_meta.direction == "INCOMING":
                rel_pattern = f"<-[:{rel_meta.relationship_type}]-"
            elif rel_meta.direction == "BOTH":
                rel_pattern = f"-[:{rel_meta.relationship_type}]-"
            else:
                continue
            
            # Add OPTIONAL MATCH
            cypher_parts.append(
                f"OPTIONAL MATCH (n){rel_pattern}({var_name}:{target_labels})"
            )
            
            # Add to RETURN with collection
            return_parts.append(f"collect(DISTINCT {var_name}) as {hint}")
        
        # Build final query
        cypher_parts.append("RETURN " + ", ".join(return_parts))
        cypher = "\n".join(cypher_parts)
        
        params: Dict[str, Any] = {}
        
        return cypher, params
