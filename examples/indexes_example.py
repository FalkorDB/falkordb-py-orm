"""
Index Management Examples

Demonstrates:
- Declaring indexed properties
- Unique constraints
- Different index types (RANGE, FULLTEXT, VECTOR)
- Index creation and management
- Schema validation and synchronization
"""

from falkordb import FalkorDB
from typing import Optional, List

from falkordb_orm import (
    node,
    property,
    indexed,
    unique,
    generated_id,
    IndexManager,
    SchemaManager,
)


# Define entities with indexed properties
@node("User")
class User:
    """User entity with various index types."""
    id: Optional[int] = generated_id()
    
    # Unique constraint (automatically creates an index)
    email: str = unique(required=True)
    username: str = unique()
    
    # Regular indexed properties for fast lookups
    age: int = indexed()
    country: str = indexed()
    
    # Full-text indexed for text search
    bio: str = indexed(index_type="FULLTEXT")
    
    # Other non-indexed properties
    name: str = property()
    created_at: str = property()


@node("Product")
class Product:
    """Product entity with indexes."""
    id: Optional[int] = generated_id()
    
    # Unique SKU
    sku: str = unique(required=True)
    
    # Indexed for filtering
    category: str = indexed()
    price: float = indexed()
    
    # Full-text search on description
    description: str = indexed(index_type="FULLTEXT")
    
    # Regular properties
    name: str = property()
    in_stock: bool = property()


@node("Document")
class Document:
    """Document with vector embeddings."""
    id: Optional[int] = generated_id()
    
    title: str = property()
    content: str = indexed(index_type="FULLTEXT")
    
    # Vector embedding for similarity search
    # Note: In practice, this would be a List[float]
    embedding_vector: str = indexed(index_type="VECTOR")


def basic_index_management():
    """Basic index management operations."""
    print("=" * 60)
    print("Basic Index Management")
    print("=" * 60)
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("index_demo")
    
    # Create index manager
    manager = IndexManager(graph)
    
    # Create all indexes for User entity
    print("\n✓ Creating indexes for User entity...")
    queries = manager.create_indexes(User, if_not_exists=True)
    
    for query in queries:
        print(f"  Executed: {query}")
    
    print(f"\n✓ Created {len(queries)} index(es)")
    print()


def list_indexes_example():
    """List existing indexes."""
    print("=" * 60)
    print("List Indexes Example")
    print("=" * 60)
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("index_demo")
    
    manager = IndexManager(graph)
    
    # List all indexes for User entity
    print("\n✓ Indexes for User entity:")
    indexes = manager.list_indexes(User)
    
    for idx in indexes:
        unique_marker = " (UNIQUE)" if idx.is_unique else ""
        print(f"  - {idx.label}.{idx.property_name}: {idx.index_type}{unique_marker}")
    
    # List all indexes in database
    print("\n✓ All indexes in database:")
    all_indexes = manager.list_indexes()
    
    for idx in all_indexes:
        unique_marker = " (UNIQUE)" if idx.is_unique else ""
        print(f"  - {idx.label}.{idx.property_name}: {idx.index_type}{unique_marker}")
    
    print()


def schema_validation_example():
    """Schema validation and synchronization."""
    print("=" * 60)
    print("Schema Validation Example")
    print("=" * 60)
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("index_demo")
    
    schema_manager = SchemaManager(graph)
    
    # Validate schema
    print("\n✓ Validating schema...")
    result = schema_manager.validate_schema([User, Product, Document])
    
    print(result)
    
    if not result.is_valid:
        print("\n✓ Synchronizing schema...")
        stats = schema_manager.sync_schema([User, Product, Document])
        print(f"  Created: {stats['created']} index(es)")
        print(f"  Dropped: {stats['dropped']} index(es)")
    
    print()


def schema_info_example():
    """Get schema information."""
    print("=" * 60)
    print("Schema Information Example")
    print("=" * 60)
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("index_demo")
    
    schema_manager = SchemaManager(graph)
    
    # Get schema info
    info = schema_manager.get_schema_info([User, Product, Document])
    
    print(f"\n✓ Schema Information:")
    print(f"  Total entities: {info['entity_count']}")
    print(f"  Total properties: {info['total_properties']}")
    print(f"  Indexed properties: {info['indexed_properties']}")
    print(f"  Unique properties: {info['unique_properties']}")
    print(f"  Total indexes in DB: {info['total_indexes']}")
    
    print()


def ensure_schema_example():
    """Ensure schema is synchronized (safe operation)."""
    print("=" * 60)
    print("Ensure Schema Example")
    print("=" * 60)
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("index_demo")
    
    schema_manager = SchemaManager(graph)
    
    # Ensure schema (safe - won't fail if indexes exist)
    print("\n✓ Ensuring schema is synchronized...")
    schema_manager.ensure_schema([User, Product, Document])
    
    print("✓ Schema synchronized successfully")
    print()


def manual_index_creation():
    """Create indexes manually without entity metadata."""
    print("=" * 60)
    print("Manual Index Creation Example")
    print("=" * 60)
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("index_demo")
    
    manager = IndexManager(graph)
    
    # Create index manually
    print("\n✓ Creating manual index...")
    query = manager.create_index_for_property("Person", "last_name")
    print(f"  Executed: {query}")
    
    # Create unique constraint manually
    print("\n✓ Creating unique constraint...")
    query = manager.create_index_for_property("Person", "ssn", unique=True)
    print(f"  Executed: {query}")
    
    # Create full-text index manually
    print("\n✓ Creating full-text index...")
    query = manager.create_index_for_property("Person", "bio", index_type="FULLTEXT")
    print(f"  Executed: {query}")
    
    print()


def drop_indexes_example():
    """Drop indexes for an entity."""
    print("=" * 60)
    print("Drop Indexes Example")
    print("=" * 60)
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("index_demo")
    
    manager = IndexManager(graph)
    
    # Drop all indexes for Product entity
    print("\n✓ Dropping indexes for Product entity...")
    queries = manager.drop_indexes(Product)
    
    for query in queries:
        print(f"  Executed: {query}")
    
    print(f"\n✓ Dropped {len(queries)} index(es)")
    print()


def performance_comparison():
    """Compare query performance with and without indexes."""
    print("=" * 60)
    print("Performance Comparison (Conceptual)")
    print("=" * 60)
    
    print("\n✓ Without index:")
    print("  MATCH (u:User) WHERE u.email = 'alice@example.com'")
    print("  → Scans all User nodes (O(n))")
    
    print("\n✓ With index:")
    print("  MATCH (u:User) WHERE u.email = 'alice@example.com'")
    print("  → Uses index lookup (O(log n))")
    
    print("\n✓ With unique constraint:")
    print("  MATCH (u:User) WHERE u.email = 'alice@example.com'")
    print("  → Direct lookup (O(1)) + enforces uniqueness")
    
    print("\n✓ Full-text search:")
    print("  CALL db.idx.fulltext.queryNodes('User', 'bio', 'python developer')")
    print("  → Text search with relevance scoring")
    
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("FALKORDB ORM - INDEX MANAGEMENT EXAMPLES")
    print("=" * 60 + "\n")
    
    try:
        # Basic operations
        basic_index_management()
        list_indexes_example()
        
        # Schema management
        schema_validation_example()
        schema_info_example()
        ensure_schema_example()
        
        # Advanced operations
        manual_index_creation()
        drop_indexes_example()
        
        # Performance
        performance_comparison()
        
        print("=" * 60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
