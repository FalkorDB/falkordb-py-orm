"""
Phase 4 Advanced Features Example

Demonstrates:
- Custom Cypher queries with @query decorator
- Aggregation methods (sum, avg, min, max)
- Parameter binding
- Complex query patterns
"""

from typing import List, Optional
from falkordb import FalkorDB
from falkordb_orm import node, generated_id, relationship, Repository, query


# Define entities
@node("Person")
class Person:
    id: Optional[int] = generated_id()
    name: str
    age: int
    salary: float
    email: str
    friends: List['Person'] = relationship('KNOWS', target='Person')


@node("Company")
class Company:
    id: Optional[int] = generated_id()
    name: str
    industry: str
    revenue: float


@node("Employee")
class Employee:
    id: Optional[int] = generated_id()
    name: str
    position: str
    salary: float
    company: Optional[Company] = relationship('WORKS_FOR', target=Company, cascade=True)


# Custom Repository with @query methods
class PersonRepository(Repository[Person]):
    """Extended repository with custom queries."""
    
    @query(
        "MATCH (p:Person)-[:KNOWS]->(f:Person) WHERE p.name = $name RETURN f",
        returns=Person
    )
    def find_friends_of(self, name: str) -> List[Person]:
        """Find all friends of a person by name."""
        pass
    
    @query(
        "MATCH (p:Person) WHERE p.age > $min_age AND p.age < $max_age RETURN p",
        returns=Person
    )
    def find_by_age_range(self, min_age: int, max_age: int) -> List[Person]:
        """Find people within an age range."""
        pass
    
    @query(
        "MATCH (p:Person) WHERE p.salary >= $threshold RETURN p ORDER BY p.salary DESC",
        returns=Person
    )
    def find_high_earners(self, threshold: float) -> List[Person]:
        """Find people earning above a threshold."""
        pass
    
    @query(
        "MATCH (p:Person) WHERE p.email CONTAINS $domain RETURN p",
        returns=Person
    )
    def find_by_email_domain(self, domain: str) -> List[Person]:
        """Find people with email from specific domain."""
        pass
    
    @query(
        "MATCH (p:Person) RETURN count(DISTINCT p.age) as unique_ages",
        returns=int
    )
    def count_unique_ages(self) -> int:
        """Count number of unique ages."""
        pass
    
    @query(
        """
        MATCH (p:Person)-[:KNOWS]->(f:Person)
        WITH p, count(f) as friend_count
        WHERE friend_count >= $min_friends
        RETURN p
        ORDER BY friend_count DESC
        """,
        returns=Person
    )
    def find_popular_people(self, min_friends: int) -> List[Person]:
        """Find people with at least N friends."""
        pass


class EmployeeRepository(Repository[Employee]):
    """Employee repository with custom queries."""
    
    @query(
        """
        MATCH (e:Employee)-[:WORKS_FOR]->(c:Company)
        WHERE c.name = $company_name
        RETURN e
        ORDER BY e.salary DESC
        """,
        returns=Employee
    )
    def find_by_company(self, company_name: str) -> List[Employee]:
        """Find all employees of a company."""
        pass
    
    @query(
        """
        MATCH (e:Employee)-[:WORKS_FOR]->(c:Company)
        WHERE c.industry = $industry
        RETURN avg(e.salary) as avg_salary
        """,
        returns=float
    )
    def average_salary_in_industry(self, industry: str) -> float:
        """Calculate average salary in an industry."""
        pass


def demonstrate_custom_queries():
    """Demonstrate custom query decorator."""
    
    # Connect to FalkorDB
    db = FalkorDB(host='localhost', port=6379)
    graph = db.select_graph('advanced_features')
    
    # Create repositories
    person_repo = PersonRepository(graph, Person)
    employee_repo = EmployeeRepository(graph, Employee)
    company_repo = Repository(graph, Company)
    
    # Clean up
    person_repo.delete_all()
    employee_repo.delete_all()
    company_repo.delete_all()
    
    print("=" * 70)
    print("PHASE 4: ADVANCED FEATURES DEMONSTRATION")
    print("=" * 70)
    
    # ========== PART 1: CUSTOM QUERIES ==========
    print("\n" + "=" * 70)
    print("PART 1: CUSTOM CYPHER QUERIES (@query decorator)")
    print("=" * 70)
    
    print("\n1. Creating test data...")
    
    # Create people
    alice = Person(name="Alice", age=30, salary=75000, email="alice@tech.com")
    alice = person_repo.save(alice)
    
    bob = Person(name="Bob", age=25, salary=60000, email="bob@tech.com")
    bob = person_repo.save(bob)
    
    charlie = Person(name="Charlie", age=35, salary=95000, email="charlie@finance.com")
    charlie = person_repo.save(charlie)
    
    diana = Person(name="Diana", age=28, salary=70000, email="diana@tech.com")
    diana = person_repo.save(diana)
    
    # Create friendships
    alice.friends = [bob, charlie]
    person_repo.save(alice)
    
    bob.friends = [alice, diana]
    person_repo.save(bob)
    
    print(f"   Created {person_repo.count()} people with friendships")
    
    # Use custom queries
    print("\n2. Using custom query: find_friends_of('Alice')...")
    friends = person_repo.find_friends_of("Alice")
    print(f"   Alice's friends: {[f.name for f in friends]}")
    
    print("\n3. Using custom query: find_by_age_range(25, 32)...")
    young_adults = person_repo.find_by_age_range(25, 32)
    print(f"   People aged 25-32: {[p.name for p in young_adults]}")
    
    print("\n4. Using custom query: find_high_earners(70000)...")
    high_earners = person_repo.find_high_earners(70000)
    print(f"   High earners (>=$70k): {[(p.name, p.salary) for p in high_earners]}")
    
    print("\n5. Using custom query: find_by_email_domain('tech.com')...")
    tech_people = person_repo.find_by_email_domain("tech.com")
    print(f"   Tech domain users: {[p.name for p in tech_people]}")
    
    print("\n6. Using custom query: count_unique_ages()...")
    unique_ages = person_repo.count_unique_ages()
    print(f"   Unique ages: {unique_ages}")
    
    print("\n7. Using custom query: find_popular_people(min_friends=2)...")
    popular = person_repo.find_popular_people(min_friends=2)
    print(f"   Popular people (2+ friends): {[p.name for p in popular]}")
    
    # ========== PART 2: AGGREGATION METHODS ==========
    print("\n" + "=" * 70)
    print("PART 2: AGGREGATION METHODS")
    print("=" * 70)
    
    print("\n8. Using built-in aggregation methods...")
    
    total_salary = person_repo.sum('salary')
    print(f"   Total salaries: ${total_salary:,.2f}")
    
    avg_salary = person_repo.avg('salary')
    print(f"   Average salary: ${avg_salary:,.2f}")
    
    min_age = person_repo.min('age')
    print(f"   Youngest person: {min_age} years old")
    
    max_age = person_repo.max('age')
    print(f"   Oldest person: {max_age} years old")
    
    min_salary = person_repo.min('salary')
    print(f"   Minimum salary: ${min_salary:,.2f}")
    
    max_salary = person_repo.max('salary')
    print(f"   Maximum salary: ${max_salary:,.2f}")
    
    # ========== PART 3: COMPLEX QUERIES WITH RELATIONSHIPS ==========
    print("\n" + "=" * 70)
    print("PART 3: COMPLEX QUERIES WITH RELATIONSHIPS")
    print("=" * 70)
    
    print("\n9. Creating companies and employees...")
    
    tech_corp = Company(name="TechCorp", industry="Technology", revenue=10000000)
    tech_corp = company_repo.save(tech_corp)
    
    finance_co = Company(name="FinanceCo", industry="Finance", revenue=8000000)
    finance_co = company_repo.save(finance_co)
    
    emp1 = Employee(name="Alice", position="Engineer", salary=75000)
    emp1.company = tech_corp
    emp1 = employee_repo.save(emp1)
    
    emp2 = Employee(name="Bob", position="Developer", salary=65000)
    emp2.company = tech_corp
    emp2 = employee_repo.save(emp2)
    
    emp3 = Employee(name="Charlie", position="Analyst", salary=80000)
    emp3.company = finance_co
    emp3 = employee_repo.save(emp3)
    
    print(f"   Created {employee_repo.count()} employees")
    
    print("\n10. Using custom query: find_by_company('TechCorp')...")
    tech_employees = employee_repo.find_by_company("TechCorp")
    print(f"   TechCorp employees: {[e.name for e in tech_employees]}")
    
    print("\n11. Using custom query: average_salary_in_industry('Technology')...")
    tech_avg = employee_repo.average_salary_in_industry("Technology")
    print(f"   Average tech salary: ${tech_avg:,.2f}")
    
    print("\n11. Using custom query: average_salary_in_industry('Finance')...")
    finance_avg = employee_repo.average_salary_in_industry("Finance")
    print(f"   Average finance salary: ${finance_avg:,.2f}")
    
    # ========== SUMMARY ==========
    print("\n" + "=" * 70)
    print("SUMMARY: PHASE 4 FEATURES")
    print("=" * 70)
    print("""
✓ CUSTOM QUERIES (@query decorator)
  - Define custom Cypher queries as repository methods
  - Automatic parameter binding from method arguments
  - Type-safe result mapping to entities
  - Support for primitive return types (int, float, str)
  - Complex query patterns with relationships

✓ AGGREGATION METHODS
  - sum(property) - Sum numeric property values
  - avg(property) - Average numeric property values
  - min(property) - Find minimum property value
  - max(property) - Find maximum property value
  - Built-in count() method

✓ ADVANCED PATTERNS
  - Complex WHERE clauses
  - JOIN-like patterns with relationships
  - Aggregations with GROUP BY (via WITH clause)
  - Sorting and filtering
  - Subqueries and CTEs
    """)
    
    print("=" * 70)
    
    # Cleanup
    print("\nCleaning up...")
    person_repo.delete_all()
    employee_repo.delete_all()
    company_repo.delete_all()
    print("Done!")


if __name__ == "__main__":
    demonstrate_custom_queries()
