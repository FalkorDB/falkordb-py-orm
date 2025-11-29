"""
Integration tests for FalkorDB ORM end-to-end workflows.

These tests require a running FalkorDB instance.
Run with: docker run -p 6379:6379 falkordb/falkordb:latest
"""

import pytest
from typing import List, Optional
from falkordb import FalkorDB

from falkordb_orm import (
    node,
    relationship,
    property,
    indexed,
    unique,
    generated_id,
    Repository,
    Session,
    Pageable,
    IndexManager,
    SchemaManager,
)


# Test entities
@node("IntegrationPerson")
class Person:
    """Person entity for integration testing."""
    
    id: Optional[int] = generated_id()
    email: str = unique(required=True)
    name: str = property(required=True)
    age: int = indexed()
    
    friends: List["Person"] = relationship(
        relationship_type="KNOWS",
        target="Person",
        direction="OUTGOING",
        cascade=True,
    )


@node("IntegrationCompany")
class Company:
    """Company entity for integration testing."""
    
    id: Optional[int] = generated_id()
    name: str = unique(required=True)
    industry: str = indexed()
    
    employees: List["Employee"] = relationship(
        relationship_type="EMPLOYS",
        target="Employee",
        direction="OUTGOING",
        cascade=False,
    )


@node("IntegrationEmployee")
class Employee:
    """Employee entity for integration testing."""
    
    id: Optional[int] = generated_id()
    name: str = property(required=True)
    position: str = indexed()
    
    company: Optional[Company] = relationship(
        relationship_type="WORKS_FOR",
        target=Company,
        direction="OUTGOING",
        cascade=False,
    )


@pytest.fixture(scope="module")
def db():
    """Create FalkorDB connection."""
    return FalkorDB(host="localhost", port=6379)


@pytest.fixture(scope="function")
def graph(db):
    """Create test graph and clean up after."""
    graph_name = "integration_test"
    graph = db.select_graph(graph_name)
    
    # Clean up before test
    try:
        graph.query("MATCH (n) DETACH DELETE n")
    except:
        pass
    
    yield graph
    
    # Clean up after test
    try:
        graph.query("MATCH (n) DETACH DELETE n")
    except:
        pass


@pytest.fixture
def person_repo(graph):
    """Create Person repository."""
    return Repository(graph, Person)


@pytest.fixture
def company_repo(graph):
    """Create Company repository."""
    return Repository(graph, Company)


@pytest.fixture
def employee_repo(graph):
    """Create Employee repository."""
    return Repository(graph, Employee)


class TestBasicCRUD:
    """Test basic CRUD operations with real database."""
    
    def test_create_and_find(self, person_repo):
        """Test creating and finding an entity."""
        # Create
        person = Person(name="Alice", email="alice@example.com", age=30)
        saved = person_repo.save(person)
        
        assert saved.id is not None
        assert saved.name == "Alice"
        
        # Find by ID
        found = person_repo.find_by_id(saved.id)
        assert found is not None
        assert found.name == "Alice"
        assert found.email == "alice@example.com"
    
    def test_update_entity(self, person_repo):
        """Test updating an entity."""
        # Create
        person = Person(name="Bob", email="bob@example.com", age=25)
        saved = person_repo.save(person)
        
        # Update
        saved.age = 26
        updated = person_repo.save(saved)
        
        # Verify
        found = person_repo.find_by_id(saved.id)
        assert found.age == 26
    
    def test_delete_entity(self, person_repo):
        """Test deleting an entity."""
        # Create
        person = Person(name="Charlie", email="charlie@example.com", age=35)
        saved = person_repo.save(person)
        
        # Delete
        person_repo.delete(saved)
        
        # Verify
        found = person_repo.find_by_id(saved.id)
        assert found is None


class TestRelationships:
    """Test relationship functionality."""
    
    def test_cascade_save_single_relationship(self, employee_repo, company_repo):
        """Test cascade save with single relationship."""
        # Create company and employee
        company = Company(name="Acme Corp", industry="Technology")
        company = company_repo.save(company)
        
        employee = Employee(name="Alice", position="Engineer")
        employee.company = company
        employee = employee_repo.save(employee)
        
        # Verify relationship edge exists
        result = employee_repo.graph.query(
            """
            MATCH (e:IntegrationEmployee)-[r:WORKS_FOR]->(c:IntegrationCompany)
            WHERE id(e) = $emp_id AND id(c) = $comp_id
            RETURN count(r) as count
            """,
            {"emp_id": employee.id, "comp_id": company.id}
        )
        
        assert result.result_set[0][0] == 1
    
    def test_cascade_save_collection_relationship(self, person_repo):
        """Test cascade save with collection relationship."""
        # Create people
        alice = Person(name="Alice", email="alice@test.com", age=30)
        bob = Person(name="Bob", email="bob@test.com", age=28)
        charlie = Person(name="Charlie", email="charlie@test.com", age=32)
        
        # Set relationships with cascade
        alice.friends = [bob, charlie]
        alice = person_repo.save(alice)
        
        # All should have IDs
        assert alice.id is not None
        assert bob.id is not None
        assert charlie.id is not None
        
        # Verify edges exist
        result = person_repo.graph.query(
            """
            MATCH (a:IntegrationPerson)-[r:KNOWS]->(f:IntegrationPerson)
            WHERE id(a) = $alice_id
            RETURN count(r) as count
            """,
            {"alice_id": alice.id}
        )
        
        assert result.result_set[0][0] == 2
    
    def test_relationship_update_deletes_old_edges(self, person_repo):
        """Test that updating relationships deletes old edges."""
        # Create people
        alice = Person(name="Alice", email="alice@update.com", age=30)
        bob = Person(name="Bob", email="bob@update.com", age=28)
        charlie = Person(name="Charlie", email="charlie@update.com", age=32)
        diana = Person(name="Diana", email="diana@update.com", age=27)
        
        # Save all
        bob = person_repo.save(bob)
        charlie = person_repo.save(charlie)
        diana = person_repo.save(diana)
        
        # Alice knows Bob and Charlie
        alice.friends = [bob, charlie]
        alice = person_repo.save(alice)
        
        # Update: Alice now only knows Diana
        alice.friends = [diana]
        alice = person_repo.save(alice)
        
        # Verify only 1 edge exists (to Diana)
        result = person_repo.graph.query(
            """
            MATCH (a:IntegrationPerson)-[r:KNOWS]->(f:IntegrationPerson)
            WHERE id(a) = $alice_id
            RETURN count(r) as count
            """,
            {"alice_id": alice.id}
        )
        
        assert result.result_set[0][0] == 1


class TestQueryDerivation:
    """Test derived query methods."""
    
    def test_find_by_property(self, person_repo):
        """Test find by property methods."""
        # Create test data
        person_repo.save(Person(name="Alice", email="alice@query.com", age=30))
        person_repo.save(Person(name="Bob", email="bob@query.com", age=25))
        person_repo.save(Person(name="Charlie", email="charlie@query.com", age=35))
        
        # Find by age
        results = person_repo.find_by_age(30)
        assert len(results) == 1
        assert results[0].name == "Alice"
    
    def test_find_by_age_greater_than(self, person_repo):
        """Test comparison operators."""
        # Create test data
        person_repo.save(Person(name="Alice", email="alice@compare.com", age=30))
        person_repo.save(Person(name="Bob", email="bob@compare.com", age=25))
        person_repo.save(Person(name="Charlie", email="charlie@compare.com", age=35))
        
        # Find age > 28
        results = person_repo.find_by_age_greater_than(28)
        assert len(results) == 2
        names = {r.name for r in results}
        assert names == {"Alice", "Charlie"}


class TestPagination:
    """Test pagination functionality."""
    
    def test_basic_pagination(self, person_repo):
        """Test paginating results."""
        # Create test data (15 people)
        for i in range(15):
            person_repo.save(
                Person(name=f"Person{i}", email=f"person{i}@page.com", age=20 + i)
            )
        
        # Get first page
        pageable = Pageable(page=0, size=5, sort_by="age", direction="ASC")
        page = person_repo.find_all_paginated(pageable)
        
        assert len(page.content) == 5
        assert page.page_number == 0
        assert page.total_elements == 15
        assert page.total_pages == 3
        assert page.has_next()
        assert not page.has_previous()
        
        # Verify sorted by age
        ages = [p.age for p in page.content]
        assert ages == sorted(ages)
    
    def test_page_navigation(self, person_repo):
        """Test navigating between pages."""
        # Create test data
        for i in range(10):
            person_repo.save(
                Person(name=f"Nav{i}", email=f"nav{i}@page.com", age=20 + i)
            )
        
        # First page
        page1 = person_repo.find_all_paginated(Pageable(page=0, size=3))
        assert len(page1.content) == 3
        assert page1.is_first()
        
        # Second page
        page2 = person_repo.find_all_paginated(Pageable(page=1, size=3))
        assert len(page2.content) == 3
        assert not page2.is_first()
        assert not page2.is_last()
        
        # Last page
        page4 = person_repo.find_all_paginated(Pageable(page=3, size=3))
        assert len(page4.content) == 1
        assert page4.is_last()


class TestTransactions:
    """Test transaction support."""
    
    def test_session_identity_map(self, graph, person_repo):
        """Test session identity map prevents duplicate loads."""
        # Create person
        person = Person(name="MapTest", email="map@test.com", age=30)
        person = person_repo.save(person)
        
        # Use session
        with Session(graph) as session:
            # Get same entity twice
            p1 = session.get(Person, person.id)
            p2 = session.get(Person, person.id)
            
            # Should be same instance
            assert p1 is p2
    
    def test_session_commit(self, graph, person_repo):
        """Test session commit saves changes."""
        # Create person
        person = Person(name="CommitTest", email="commit@test.com", age=30)
        person = person_repo.save(person)
        
        # Modify in session
        with Session(graph) as session:
            p = session.get(Person, person.id)
            p.age = 31
            session._dirty.add(p)
            session.commit()
        
        # Verify change persisted
        found = person_repo.find_by_id(person.id)
        assert found.age == 31
    
    def test_session_rollback(self, graph, person_repo):
        """Test session rollback discards changes."""
        # Create person
        person = Person(name="RollbackTest", email="rollback@test.com", age=30)
        person = person_repo.save(person)
        
        # Modify and rollback
        with Session(graph) as session:
            p = session.get(Person, person.id)
            p.age = 31
            session._dirty.add(p)
            session.rollback()
        
        # Verify change not persisted
        found = person_repo.find_by_id(person.id)
        assert found.age == 30


class TestIndexManagement:
    """Test index management functionality."""
    
    def test_create_indexes(self, graph):
        """Test creating indexes for entity."""
        manager = IndexManager(graph)
        
        # Create indexes
        queries = manager.create_indexes(Person, if_not_exists=True)
        
        # Should create email (unique) and age (indexed)
        assert len(queries) >= 2
    
    def test_list_indexes(self, graph):
        """Test listing indexes."""
        manager = IndexManager(graph)
        
        # Create indexes first
        manager.create_indexes(Person, if_not_exists=True)
        
        # List indexes
        indexes = manager.list_indexes(Person)
        
        # Should have at least email index
        property_names = {idx.property_name for idx in indexes}
        assert "email" in property_names


class TestSchemaManagement:
    """Test schema management functionality."""
    
    def test_validate_schema(self, graph):
        """Test schema validation."""
        manager = SchemaManager(graph)
        
        # Validate schema
        result = manager.validate_schema([Person, Company, Employee])
        
        # May or may not be valid depending on previous tests
        assert result is not None
        assert hasattr(result, 'is_valid')
    
    def test_sync_schema(self, graph):
        """Test schema synchronization."""
        manager = SchemaManager(graph)
        
        # Sync schema
        queries = manager.sync_schema([Person])
        
        # Should create any missing indexes
        assert queries is not None
        assert isinstance(queries, list)


class TestComplexWorkflow:
    """Test complex end-to-end workflows."""
    
    def test_social_network_scenario(self, person_repo):
        """Test a complete social network scenario."""
        # Create users
        alice = Person(name="Alice", email="alice@social.com", age=30)
        bob = Person(name="Bob", email="bob@social.com", age=28)
        charlie = Person(name="Charlie", email="charlie@social.com", age=32)
        diana = Person(name="Diana", email="diana@social.com", age=27)
        
        # Build network
        alice.friends = [bob, charlie]
        bob.friends = [alice, diana]
        charlie.friends = [alice]
        diana.friends = [bob]
        
        # Save all
        person_repo.save(alice)
        person_repo.save(bob)
        person_repo.save(charlie)
        person_repo.save(diana)
        
        # Query: Find Alice's friends
        result = person_repo.graph.query(
            """
            MATCH (a:IntegrationPerson)-[:KNOWS]->(f:IntegrationPerson)
            WHERE id(a) = $alice_id
            RETURN f.name as name
            ORDER BY f.name
            """,
            {"alice_id": alice.id}
        )
        
        friend_names = [row[0] for row in result.result_set]
        assert friend_names == ["Bob", "Charlie"]
    
    def test_company_employees_workflow(self, company_repo, employee_repo):
        """Test company-employees workflow."""
        # Create company
        company = Company(name="TechCorp", industry="Software")
        company = company_repo.save(company)
        
        # Create employees
        employees = []
        for i, position in enumerate(["Engineer", "Designer", "Manager"]):
            emp = Employee(name=f"Employee{i}", position=position)
            emp.company = company
            emp = employee_repo.save(emp)
            employees.append(emp)
        
        # Query: Find all engineers
        result = employee_repo.graph.query(
            """
            MATCH (e:IntegrationEmployee)
            WHERE e.position = $position
            RETURN count(e) as count
            """,
            {"position": "Engineer"}
        )
        
        assert result.result_set[0][0] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
