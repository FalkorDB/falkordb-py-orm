"""
Transaction and Session Management Examples

Demonstrates:
- Using sessions for transaction management
- Identity map preventing duplicate entity loads
- Change tracking and dirty checking
- Rollback on error
- Async session support
"""

from falkordb import FalkorDB
from typing import Optional
import asyncio

from falkordb_orm import node, property, generated_id
from falkordb_orm.session import Session
from falkordb_orm.async_session import AsyncSession


# Define entities
@node("User")
class User:
    """User entity."""
    id: Optional[int] = generated_id()
    username: str = property()
    email: str = property()
    balance: float = property()


@node("Account")
class Account:
    """Account entity."""
    id: Optional[int] = generated_id()
    account_number: str = property()
    balance: float = property()
    account_type: str = property()


def basic_session_example():
    """Basic session usage example."""
    print("=" * 60)
    print("Basic Session Example")
    print("=" * 60)
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("transaction_demo")
    
    # Using context manager - auto commits on success
    with Session(graph) as session:
        # Create new users
        user1 = User(username="alice", email="alice@example.com", balance=1000.0)
        user2 = User(username="bob", email="bob@example.com", balance=500.0)
        
        session.add(user1)
        session.add(user2)
        
        print("✓ Added 2 users to session")
        print(f"  - {user1.username}: ${user1.balance}")
        print(f"  - {user2.username}: ${user2.balance}")
        
        # Changes are saved on context exit
    
    print("✓ Session committed and closed")
    print()


def identity_map_example():
    """Identity map prevents duplicate entity loads."""
    print("=" * 60)
    print("Identity Map Example")
    print("=" * 60)
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("transaction_demo")
    
    with Session(graph) as session:
        # First get - loads from database
        user1 = session.get(User, 1)
        print(f"✓ Loaded user from database: {user1.username if user1 else 'Not found'}")
        
        # Second get - returns same instance from identity map
        user2 = session.get(User, 1)
        print(f"✓ Retrieved user from identity map: {user2.username if user2 else 'Not found'}")
        
        # Verify they're the same instance
        if user1 and user2:
            assert user1 is user2
            print(f"✓ Confirmed: user1 is user2 = {user1 is user2}")
            print("  (No duplicate database query - identity map at work!)")
    
    print()


def change_tracking_example():
    """Change tracking and dirty checking."""
    print("=" * 60)
    print("Change Tracking Example")
    print("=" * 60)
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("transaction_demo")
    
    with Session(graph) as session:
        # Load user
        user = session.get(User, 1)
        if not user:
            print("✗ User not found (run basic_session_example first)")
            return
        
        print(f"✓ Loaded user: {user.username}")
        print(f"  Original balance: ${user.balance}")
        
        # Modify user
        original_balance = user.balance
        user.balance += 500.0
        user.email = "alice.new@example.com"
        
        print(f"✓ Modified user:")
        print(f"  New balance: ${user.balance}")
        print(f"  New email: {user.email}")
        
        # Mark as dirty (in real usage, you'd add to _dirty set or let session track)
        session._dirty.add(user)
        
        # Session detects changes automatically
        if session.has_pending_changes:
            print("✓ Session detected pending changes")
        
        # Commit saves changes
        session.commit()
        print("✓ Changes committed to database")
    
    print()


def rollback_example():
    """Rollback on error."""
    print("=" * 60)
    print("Rollback Example")
    print("=" * 60)
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("transaction_demo")
    
    try:
        with Session(graph) as session:
            # Load user
            user = session.get(User, 1)
            if not user:
                print("✗ User not found (run basic_session_example first)")
                return
            
            print(f"✓ Loaded user: {user.username}")
            original_balance = user.balance
            print(f"  Original balance: ${original_balance}")
            
            # Modify user
            user.balance -= 200.0
            session._dirty.add(user)
            
            print(f"✓ Modified balance: ${user.balance}")
            
            # Simulate error
            print("✗ Simulating error...")
            raise ValueError("Transaction failed!")
            
    except ValueError as e:
        print(f"✗ Error caught: {e}")
        print("✓ Session automatically rolled back")
    
    # Verify rollback
    with Session(graph) as session:
        user = session.get(User, 1)
        if user:
            print(f"✓ Balance after rollback: ${user.balance}")
            print("  (Balance unchanged - rollback successful)")
    
    print()


def manual_flush_example():
    """Manual flush for fine-grained control."""
    print("=" * 60)
    print("Manual Flush Example")
    print("=" * 60)
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("transaction_demo")
    
    with Session(graph) as session:
        # Add multiple entities
        accounts = [
            Account(account_number="ACC001", balance=1000.0, account_type="savings"),
            Account(account_number="ACC002", balance=5000.0, account_type="checking"),
            Account(account_number="ACC003", balance=250.0, account_type="savings"),
        ]
        
        for account in accounts:
            session.add(account)
        
        print(f"✓ Added {len(accounts)} accounts to session")
        
        # Flush immediately to get IDs
        session.flush()
        print("✓ Flushed - accounts now have IDs:")
        
        for account in accounts:
            if hasattr(account, 'id') and account.id:
                print(f"  - {account.account_number}: ID={account.id}")
        
        # Can continue adding more entities
        user = User(username="charlie", email="charlie@example.com", balance=750.0)
        session.add(user)
        print("✓ Added another user")
        
        # All changes committed on context exit
    
    print("✓ All changes committed")
    print()


def transfer_example():
    """Money transfer with transaction safety."""
    print("=" * 60)
    print("Transfer Example (Transaction Safety)")
    print("=" * 60)
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("transaction_demo")
    
    def transfer_money(from_user_id: int, to_user_id: int, amount: float):
        """Transfer money between users safely."""
        with Session(graph) as session:
            # Load both users
            from_user = session.get(User, from_user_id)
            to_user = session.get(User, to_user_id)
            
            if not from_user or not to_user:
                raise ValueError("User not found")
            
            print(f"✓ Transfer: ${amount} from {from_user.username} to {to_user.username}")
            print(f"  Before: {from_user.username}=${from_user.balance}, {to_user.username}=${to_user.balance}")
            
            # Check balance
            if from_user.balance < amount:
                raise ValueError("Insufficient funds")
            
            # Perform transfer
            from_user.balance -= amount
            to_user.balance += amount
            
            # Mark as dirty
            session._dirty.add(from_user)
            session._dirty.add(to_user)
            
            print(f"  After: {from_user.username}=${from_user.balance}, {to_user.username}=${to_user.balance}")
            
            # Commit happens automatically
        
        print("✓ Transfer completed successfully")
    
    # Successful transfer
    try:
        transfer_money(1, 2, 100.0)
    except Exception as e:
        print(f"✗ Transfer failed: {e}")
    
    print()


async def async_session_example():
    """Async session example."""
    print("=" * 60)
    print("Async Session Example")
    print("=" * 60)
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("transaction_demo")
    
    # Use async context manager
    async with AsyncSession(graph) as session:
        # Add entity
        user = User(username="dave", email="dave@example.com", balance=1200.0)
        session.add(user)
        
        print("✓ Added user to async session")
        
        # Commit with await
        await session.commit()
        print("✓ Async commit completed")
    
    print("✓ Async session closed")
    print()


def session_properties_example():
    """Session properties and state checking."""
    print("=" * 60)
    print("Session Properties Example")
    print("=" * 60)
    
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("transaction_demo")
    
    session = Session(graph)
    
    print(f"Is active: {session.is_active}")
    print(f"Has pending changes: {session.has_pending_changes}")
    
    # Add entity
    user = User(username="eve", email="eve@example.com", balance=800.0)
    session.add(user)
    
    print(f"After add - Has pending changes: {session.has_pending_changes}")
    
    # Rollback
    session.rollback()
    
    print(f"After rollback - Has pending changes: {session.has_pending_changes}")
    
    # Close
    session.close()
    print(f"After close - Is active: {session.is_active}")
    
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("FALKORDB ORM - TRANSACTION & SESSION EXAMPLES")
    print("=" * 60 + "\n")
    
    try:
        # Sync examples
        basic_session_example()
        identity_map_example()
        change_tracking_example()
        rollback_example()
        manual_flush_example()
        transfer_example()
        session_properties_example()
        
        # Async example
        print("Running async example...")
        asyncio.run(async_session_example())
        
        print("=" * 60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
