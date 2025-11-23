"""Example: Using Interned Strings for Memory Optimization

This example demonstrates how to use the `interned()` decorator to optimize memory
usage for frequently repeated string values in FalkorDB.

The intern() function deduplicates strings by storing a single internal copy across
the database, which is especially useful for properties like:
- Country names
- City names  
- Status values
- Tags
- Email domains
- Categories
"""

from typing import Optional
from falkordb import FalkorDB
from falkordb_orm import node, interned, property, Repository


# Define User entity with interned string properties
@node("User")
class User:
    id: Optional[int] = None
    name: str
    email: str
    
    # These properties will use intern() function for deduplication
    country: str = interned()  # Many users share same countries
    city: str = interned()     # Many users in same cities
    status: str = interned("user_status")  # Maps to 'user_status' in graph
    email_domain: str = interned()  # Many users from same domains
    
    # Regular properties (not interned)
    bio: str = property()


# Define Product entity
@node("Product")
class Product:
    id: Optional[int] = None
    name: str
    price: float
    
    # Interned properties for common repeated values
    category: str = interned()  # Electronics, Books, Clothing, etc.
    brand: str = interned()     # Apple, Samsung, Nike, etc.
    status: str = interned()    # Active, Discontinued, Out of Stock


def main():
    """Demonstrate interned strings usage."""
    
    # Connect to FalkorDB
    db = FalkorDB(host='localhost', port=6379)
    graph = db.select_graph('interned_example')
    
    # Create repositories
    user_repo = Repository(graph, User)
    product_repo = Repository(graph, Product)
    
    print("Creating users with interned string properties...")
    
    # Create multiple users from the same country and city
    # The country and city strings will be deduplicated in memory
    users = [
        User(
            name="Alice Smith",
            email="alice@gmail.com",
            country="United States",
            city="New York",
            status="Active",
            email_domain="gmail.com",
            bio="Software developer"
        ),
        User(
            name="Bob Johnson",
            email="bob@gmail.com",
            country="United States",
            city="New York",
            status="Active",
            email_domain="gmail.com",
            bio="Product manager"
        ),
        User(
            name="Charlie Brown",
            email="charlie@outlook.com",
            country="United States",
            city="San Francisco",
            status="Active",
            email_domain="outlook.com",
            bio="Designer"
        ),
        User(
            name="Diana Prince",
            email="diana@gmail.com",
            country="United Kingdom",
            city="London",
            status="Inactive",
            email_domain="gmail.com",
            bio="Marketing specialist"
        ),
    ]
    
    # Save users
    for user in users:
        saved = user_repo.save(user)
        print(f"✓ Saved {saved.name} (ID: {saved.id})")
    
    print(f"\nCreated {len(users)} users")
    print("Notice: 'United States', 'New York', 'Active', and 'gmail.com' are stored only once!")
    
    print("\n" + "="*60)
    print("Creating products with interned categories and brands...")
    print("="*60 + "\n")
    
    # Create multiple products with same categories and brands
    products = [
        Product(name="iPhone 15", price=999.99, category="Electronics", brand="Apple", status="Active"),
        Product(name="MacBook Pro", price=2499.99, category="Electronics", brand="Apple", status="Active"),
        Product(name="iPad Air", price=599.99, category="Electronics", brand="Apple", status="Active"),
        Product(name="Galaxy S24", price=899.99, category="Electronics", brand="Samsung", status="Active"),
        Product(name="Nike Air Max", price=129.99, category="Footwear", brand="Nike", status="Active"),
        Product(name="Nike Jordans", price=179.99, category="Footwear", brand="Nike", status="Active"),
    ]
    
    # Save products
    for product in products:
        saved = product_repo.save(product)
        print(f"✓ Saved {saved.name} (ID: {saved.id})")
    
    print(f"\nCreated {len(products)} products")
    print("Notice: 'Electronics', 'Apple', 'Active', etc. are stored only once!")
    
    print("\n" + "="*60)
    print("Query Examples")
    print("="*60 + "\n")
    
    # Query by interned properties - works just like regular strings
    active_users = user_repo.find_by_status("Active")
    print(f"Active users: {len(active_users)}")
    for user in active_users:
        print(f"  - {user.name} ({user.city}, {user.country})")
    
    print()
    
    # Query products by interned category
    electronics = product_repo.find_by_category("Electronics")
    print(f"Electronics: {len(electronics)} products")
    for product in electronics:
        print(f"  - {product.name} by {product.brand} (${product.price})")
    
    print()
    
    # Query by brand
    apple_products = product_repo.find_by_brand("Apple")
    print(f"Apple products: {len(apple_products)}")
    
    print("\n" + "="*60)
    print("Memory Benefits")
    print("="*60 + "\n")
    
    print("Without intern():")
    print("  - 'United States' stored 3 times = 3x memory")
    print("  - 'New York' stored 2 times = 2x memory")
    print("  - 'Active' stored 10 times = 10x memory")
    print("  - 'Electronics' stored 4 times = 4x memory")
    print("  - 'Apple' stored 3 times = 3x memory")
    print()
    print("With intern():")
    print("  - Each unique string stored only ONCE")
    print("  - Significant memory savings with large datasets")
    print("  - Faster string comparison (reference equality)")
    print()
    print("Best use cases:")
    print("  ✓ Country/City names (limited unique values)")
    print("  ✓ Status fields (Active, Inactive, Pending, etc.)")
    print("  ✓ Categories and tags")
    print("  ✓ Email domains")
    print("  ✓ Any repeated string values")
    
    # Cleanup
    graph.delete()
    print("\n✓ Example completed and cleaned up")


if __name__ == "__main__":
    main()
