"""
Comprehensive relationships example demonstrating all features.

This example showcases:
- Relationship declaration
- Lazy loading
- Eager loading
- Cascade operations
- Bidirectional relationships
- N+1 query prevention
"""

from typing import List, Optional
from falkordb import FalkorDB
from falkordb_orm import node, generated_id, relationship, Repository


# Social Network Domain Model
@node("Person")
class Person:
    id: Optional[int] = generated_id()
    name: str
    age: int
    email: str
    # Lazy-loaded relationships
    friends: List['Person'] = relationship('KNOWS', target='Person', cascade=False)
    posts: List['Post'] = relationship('AUTHORED', target='Post', cascade=True)


@node("Post")
class Post:
    id: Optional[int] = generated_id()
    title: str
    content: str
    # Reverse relationship (lazy)
    author: Optional[Person] = relationship('AUTHORED', direction='INCOMING', target=Person, cascade=False)
    tags: List['Tag'] = relationship('TAGGED_WITH', target='Tag', cascade=True)


@node("Tag")
class Tag:
    id: Optional[int] = generated_id()
    name: str


def demonstrate_relationships():
    """Comprehensive relationship demonstration."""
    
    # Connect to FalkorDB
    db = FalkorDB(host='localhost', port=6379)
    graph = db.select_graph('social_network')
    
    # Create repositories
    person_repo = Repository(graph, Person)
    post_repo = Repository(graph, Post)
    tag_repo = Repository(graph, Tag)
    
    # Clean up
    person_repo.delete_all()
    post_repo.delete_all()
    tag_repo.delete_all()
    
    print("=" * 70)
    print("COMPREHENSIVE RELATIONSHIPS EXAMPLE")
    print("=" * 70)
    
    # ========== PART 1: CASCADE SAVE ==========
    print("\n" + "=" * 70)
    print("PART 1: CASCADE SAVE")
    print("=" * 70)
    
    print("\n1. Creating person with posts and tags (cascade)...")
    
    # Create tags (will be cascade-saved with posts)
    tech_tag = Tag(name="Technology")
    python_tag = Tag(name="Python")
    ai_tag = Tag(name="AI")
    
    # Create posts (will be cascade-saved with person)
    post1 = Post(
        title="Introduction to Python",
        content="Python is a great language..."
    )
    post1.tags = [tech_tag, python_tag]
    
    post2 = Post(
        title="AI in 2025",
        content="Artificial intelligence continues to evolve..."
    )
    post2.tags = [tech_tag, ai_tag]
    
    # Create person with posts
    alice = Person(name="Alice Johnson", age=30, email="alice@example.com")
    alice.posts = [post1, post2]
    
    print(f"   Before save:")
    print(f"     Alice ID: {alice.id}")
    print(f"     Post 1 ID: {post1.id}")
    print(f"     Post 2 ID: {post2.id}")
    print(f"     Tech Tag ID: {tech_tag.id}")
    print(f"     Python Tag ID: {python_tag.id}")
    print(f"     AI Tag ID: {ai_tag.id}")
    
    # Save - cascades to posts and tags
    alice = person_repo.save(alice)
    
    print(f"\n   After save:")
    print(f"     Alice ID: {alice.id}")
    print(f"     Post 1 ID: {post1.id}")
    print(f"     Post 2 ID: {post2.id}")
    print(f"     Tech Tag ID: {tech_tag.id}")
    print(f"     Python Tag ID: {python_tag.id}")
    print(f"     AI Tag ID: {ai_tag.id}")
    print("   ^ All entities saved due to cascade=True!")
    
    # ========== PART 2: LAZY LOADING ==========
    print("\n" + "=" * 70)
    print("PART 2: LAZY LOADING")
    print("=" * 70)
    
    print("\n2. Fetching person with lazy loading...")
    
    fetched_alice = person_repo.find_by_id(alice.id)
    print(f"   Fetched: {fetched_alice.name}")
    print(f"   Posts (lazy proxy): {fetched_alice.posts}")
    print("   ^ Posts not loaded yet - LazyList proxy created")
    
    print("\n3. Accessing lazy-loaded posts (triggers load)...")
    print(f"   Number of posts: {len(fetched_alice.posts)}")
    print("   ^ Query executed to load posts")
    
    print(f"\n   Posts:")
    for post in fetched_alice.posts:
        print(f"     - {post.title}")
        print(f"       Tags (lazy proxy): {post.tags}")
    print("   ^ Each post has lazy tags")
    
    print("\n4. Accessing nested lazy-loaded tags...")
    first_post = list(fetched_alice.posts)[0]
    print(f"   Tags for '{first_post.title}':")
    for tag in first_post.tags:
        print(f"     - {tag.name}")
    print("   ^ Query executed to load tags for first post")
    
    # ========== PART 3: N+1 QUERY PROBLEM ==========
    print("\n" + "=" * 70)
    print("PART 3: N+1 QUERY PROBLEM (LAZY LOADING)")
    print("=" * 70)
    
    # Create more people
    bob = Person(name="Bob Smith", age=28, email="bob@example.com")
    bob = person_repo.save(bob)
    
    charlie = Person(name="Charlie Brown", age=32, email="charlie@example.com")
    charlie = person_repo.save(charlie)
    
    print("\n5. Fetching all people and accessing their posts (lazy)...")
    print("   WARNING: This causes N+1 queries!")
    
    all_people = person_repo.find_all()
    print(f"   Query 1: Fetched {len(all_people)} people")
    
    for i, person in enumerate(all_people, 1):
        post_count = len(person.posts)  # Each triggers a query!
        print(f"   Query {i+1}: {person.name} has {post_count} post(s)")
    
    print("   ^ N+1 queries: 1 for all people + N for each person's posts")
    
    # ========== PART 4: EAGER LOADING SOLUTION ==========
    print("\n" + "=" * 70)
    print("PART 4: EAGER LOADING (SOLVES N+1)")
    print("=" * 70)
    
    print("\n6. Fetching all people with eager loading...")
    print("   Using fetch=['posts'] to load posts in single query")
    
    all_people_eager = person_repo.find_all(fetch=['posts'])
    print(f"   Single query fetched {len(all_people_eager)} people WITH their posts!")
    
    for person in all_people_eager:
        post_count = len(person.posts)  # No additional query!
        print(f"     {person.name} has {post_count} post(s)")
        for post in person.posts:
            print(f"       - {post.title}")
    
    print("   ^ Only 1 query for everything!")
    
    # ========== PART 5: NESTED EAGER LOADING ==========
    print("\n" + "=" * 70)
    print("PART 5: MULTIPLE EAGER LOADS")
    print("=" * 70)
    
    print("\n7. Fetching person with posts eagerly loaded...")
    
    alice_with_posts = person_repo.find_by_id(alice.id, fetch=['posts'])
    print(f"   Loaded: {alice_with_posts.name} with {len(alice_with_posts.posts)} posts")
    
    for post in alice_with_posts.posts:
        print(f"     - {post.title} (tags are still lazy)")
        # Note: post.tags is still lazy - would need nested eager loading
    
    # ========== PART 6: BIDIRECTIONAL RELATIONSHIPS ==========
    print("\n" + "=" * 70)
    print("PART 6: BIDIRECTIONAL RELATIONSHIPS")
    print("=" * 70)
    
    print("\n8. Creating bidirectional friendships...")
    
    # Already have alice, bob, charlie
    # Create friendships
    alice_existing = person_repo.find_by_id(alice.id)
    bob_existing = person_repo.find_by_id(bob.id)
    charlie_existing = person_repo.find_by_id(charlie.id)
    
    alice_existing.friends = [bob_existing, charlie_existing]
    alice_existing = person_repo.save(alice_existing)
    
    bob_existing.friends = [alice_existing]
    bob_existing = person_repo.save(bob_existing)
    
    print(f"   Alice is friends with: {len(alice_existing.friends)} people")
    print(f"   Bob is friends with: {len(bob_existing.friends)} person(s)")
    
    # Verify bidirectional
    alice_fresh = person_repo.find_by_id(alice.id)
    print(f"\n   Alice's friends:")
    for friend in alice_fresh.friends:
        print(f"     - {friend.name}")
    
    bob_fresh = person_repo.find_by_id(bob.id)
    print(f"\n   Bob's friends:")
    for friend in bob_fresh.friends:
        print(f"     - {friend.name}")
    
    # ========== PART 7: REVERSE RELATIONSHIPS ==========
    print("\n" + "=" * 70)
    print("PART 7: REVERSE/INCOMING RELATIONSHIPS")
    print("=" * 70)
    
    print("\n9. Fetching post and accessing its author (reverse)...")
    
    # Fetch a post
    some_post = post_repo.find_by_id(post1.id)
    print(f"   Post: '{some_post.title}'")
    print(f"   Author (lazy): {some_post.author}")
    
    # Access author (triggers reverse relationship load)
    author = some_post.author.get()
    if author:
        print(f"   Author loaded: {author.name}")
    print("   ^ INCOMING direction loaded correctly")
    
    # ========== SUMMARY ==========
    print("\n" + "=" * 70)
    print("SUMMARY: KEY FEATURES")
    print("=" * 70)
    print("""
✓ LAZY LOADING
  - Relationships loaded on first access
  - Cached for subsequent accesses
  - Avoids loading unused data

✓ EAGER LOADING
  - Use fetch=['rel1', 'rel2'] parameter
  - Loads relationships in single query
  - Solves N+1 query problem

✓ CASCADE OPERATIONS
  - cascade=True auto-saves related entities
  - cascade=False requires manual save
  - Handles circular references safely

✓ BIDIRECTIONAL RELATIONSHIPS
  - Define relationships in both directions
  - Independently managed
  - Can be asymmetric

✓ REVERSE RELATIONSHIPS
  - Use direction='INCOMING'
  - Traverse edges backward
  - Automatic inverse traversal

✓ FLEXIBLE LOADING
  - Mix lazy and eager as needed
  - Choose per-query
  - Optimize for use case
    """)
    
    print("=" * 70)
    
    # Cleanup
    print("\nCleaning up...")
    person_repo.delete_all()
    post_repo.delete_all()
    tag_repo.delete_all()
    print("Done!")


if __name__ == "__main__":
    demonstrate_relationships()
