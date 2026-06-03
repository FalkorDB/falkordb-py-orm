Migration Guide
===============

This page explains how to move application code from direct FalkorDB client
queries to FalkorDB Python ORM. The goal is not to remove Cypher from your
project. The goal is to move stable CRUD and object mapping into typed
repositories while keeping explicit Cypher for graph-shaped work.

Why migrate
-----------

Migrate code when the same labels, properties, and relationships are used across
application workflows:

* Type-hinted entities and repository methods.
* Automatic object mapping for nodes and relationships.
* Repository methods for create, read, update, delete, aggregate, and pagination
  workflows.
* Derived query methods for common ``MATCH ... WHERE`` filters.
* Lazy loading, eager loading, cascade saves, and relationship updates.
* Easier unit testing around repositories.

Keep raw Cypher for graph algorithms, one-off administration, custom
projections, bulk imports, and performance-critical paths that need complete
control over query text.

Migration strategy
------------------

Migrate gradually. Raw client code and ORM repositories can share the same graph,
so you can start with stable CRUD paths and leave complex Cypher in place.

.. code-block:: python

   from falkordb import FalkorDB
   from falkordb_orm import Repository

   db = FalkorDB(host="localhost", port=6379)
   graph = db.select_graph("social")

   people = Repository(graph, Person)
   alice = people.find_by_email("alice@example.com")[0]

   result = graph.query(
       """
       MATCH path = (p:Person)-[:KNOWS*3..5]->(friend:Person)
       WHERE id(p) = $id
       RETURN friend
       """,
       {"id": alice.id},
   )

A practical migration order is:

* Define entity classes for the labels your application already uses.
* Map property names that differ from Python attribute names.
* Replace simple create, read, update, and delete functions with repositories.
* Add relationships and eager loading for high-traffic read paths.
* Move readable filters to derived query methods.
* Wrap repeated custom Cypher in repository methods with ``@query``.
* Keep advanced projections, graph algorithms, and bulk operations as direct
  ``graph.query()`` calls.

Step 1: map existing labels
---------------------------

Start by expressing an existing graph label as a Python class.

.. code-block:: python

   from typing import Optional

   from falkordb_orm import generated_id, node, property


   @node("Person")
   class Person:
       id: Optional[int] = generated_id()
       name: str = property("full_name")
       email: str
       age: int

This is the only mapping detail the migration page needs. :doc:`mapping-schema`
owns labels, generated ids, property aliases, converters, relationships,
cascade behavior, indexes, and schema validation.

Step 2: replace simple writes
-----------------------------

Raw client code builds Cypher and manually reads the returned id:

.. code-block:: python

   graph.query(
       "CREATE (p:Person {full_name: $name, email: $email, age: $age}) RETURN id(p)",
       {"name": "Alice", "email": "alice@example.com", "age": 25},
   )

With the ORM, construct the entity and save it:

.. code-block:: python

   person = Person(name="Alice", email="alice@example.com", age=25)
   saved = people.save(person)
   person_id = saved.id

Use the same repository for updates and deletes:

.. code-block:: python

   person = people.find_by_id(123)
   if person is not None:
       person.email = "new@example.com"
       person.age = 26
       people.save(person)

   people.delete_by_id(123)

Step 3: replace simple reads
----------------------------

Raw client code manually reads records and properties. ORM repositories return
typed entity objects:

.. code-block:: python

   person = people.find_by_id(123)
   adults = people.find_by_age_greater_than(18)

Use derived methods when the filter remains readable as a method name:

.. code-block:: python

   active_adults = people.find_by_status_and_age_greater_than("active", 18)
   matching = people.find_by_email_ending_with("@example.com")
   total = people.count_by_age_greater_than(18)

See :doc:`data-access` for the supported derived query grammar.

Step 4: migrate relationship workflows
--------------------------------------

Relationship creation often shrinks from several ``MATCH`` clauses to assigning
related objects and saving the source entity. Declare the relationship on the
model in :doc:`mapping-schema`, then update object attributes in application
code.

.. code-block:: python

   alice = people.find_by_id(1)
   bob = people.find_by_id(2)
   if alice is not None and bob is not None:
       alice.friends = [bob]
       people.save(alice)

For create flows where a root object owns related data, map the edge with
``cascade=True`` and save the root:

.. code-block:: python

   person = Person(name="Alice", company=Company(name="Acme"))
   people.save(person)

The company is saved first, then the ``WORKS_FOR`` edge is created.

Step 5: wrap repeated Cypher
----------------------------

When a query is too graph-shaped for a derived method but still belongs to an
entity workflow, put it on a repository with ``@query``. Keep the full query
language visible, but give application code a typed method to call.

.. code-block:: python

   from typing import List

   from falkordb_orm import Repository, query


   class PersonRepository(Repository[Person]):
       @query(
           """
           MATCH (p:Person)-[:KNOWS]->(:Person)-[:KNOWS]->(candidate:Person)
           WHERE id(p) = $person_id AND id(candidate) <> $person_id
           RETURN DISTINCT candidate
           """,
           returns=Person,
       )
       def suggest_friends(self, person_id: int) -> List[Person]:
           pass

Detailed return mapping rules and more examples live in :doc:`data-access`.

Step 6: choose what stays raw
-----------------------------

Not every query should become ORM code. Keep direct ``graph.query()`` for:

* Bulk ``UNWIND`` imports and exports.
* Graph algorithms and variable-length traversals where raw Cypher is clearer.
* Multi-column projections that need custom result mapping.
* Administrative maintenance scripts.
* Query plans that need hand tuning.

See :doc:`performance-boundaries` for the current boundaries.

Testing after migration
-----------------------

Repositories are easier to mock than scattered query strings. Service tests can
depend on repository behavior instead of FalkorDB result records.

.. code-block:: python

   from unittest.mock import Mock


   def test_user_lookup():
       repo = Mock(spec=Repository)
       repo.find_by_email.return_value = [User(email="alice@example.com")]

       user = repo.find_by_email("alice@example.com")[0]
       assert user.email == "alice@example.com"

Troubleshooting
---------------

Migrated code is slower than the raw version
   Check :doc:`performance-boundaries` first. The usual causes are relationship
   loading, bulk-write expectations, or queries that should stay raw.

Derived query names are becoming unreadable
   Stop migrating that query into a method name. Use ``@query`` from
   :doc:`data-access` or raw Cypher so the graph pattern remains explicit.

Mapped fields do not match existing graph properties
   See the property alias guidance in :doc:`mapping-schema`.

Relationship declarations are awkward during migration
   See forward references, direction, lazy/eager loading, and cascade behavior in
   :doc:`mapping-schema`.

Mixing raw client and ORM safely
--------------------------------

The repository stores the graph object as ``repo.graph``. You can use direct
Cypher in the same application, but keep responsibility boundaries clear so raw
queries do not surprise session or relationship assumptions.

Good boundaries are:

* Repositories own entity CRUD and common application lookups.
* ``@query`` methods own repeated graph traversals that return entities or
  simple scalar values.
* Raw ``graph.query()`` owns bulk writes, graph algorithms, custom projections,
  and administrative scripts.

Summary
-------

.. list-table:: Migration choices
   :header-rows: 1

   * - Existing raw-client pattern
     - ORM migration target
   * - ``CREATE`` or simple ``MATCH`` by id
     - Entity class plus ``Repository.save()`` and ``find_by_id()``.
   * - ``MATCH`` with property filters
     - Derived repository methods, when the name stays readable.
   * - Relationship creation and traversal
     - ``relationship()``, cascade where ownership is clear, and eager loading
       with ``fetch``.
   * - Counts, minimums, maximums, averages, sums
     - Repository aggregate helpers.
   * - Repeated custom traversal
     - Repository subclass method with ``@query``.
   * - Bulk imports, graph algorithms, custom projections
     - Keep direct ``graph.query()``.

Use the ORM for the stable, typed core of your application and keep raw Cypher
for the parts where explicit graph control matters.