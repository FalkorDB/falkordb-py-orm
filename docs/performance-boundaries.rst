Performance and Boundaries
==========================

FalkorDB Python ORM covers common object-graph mapping workflows. It is designed
for typed persistence, repository ergonomics, relationship management, and
schema/index helpers. It does not try to hide every Cypher decision or replace
the raw FalkorDB client for every workload.

Use this page when deciding whether to keep code in the ORM, use ``@query``, or
drop to direct ``graph.query()``.

Decision Guide
--------------

.. list-table:: Choosing the right surface
   :header-rows: 1

   * - Workload
     - Prefer
     - Why
   * - CRUD by id, simple property filters, counts, paging
     - Repository methods and derived queries
     - Lowest boilerplate, typed return values, mapper support.
   * - Repeated graph traversal returning one entity type or a scalar
     - ``@query`` on a repository subclass
     - Keeps Cypher explicit while preserving method-level API ergonomics.
   * - Multi-column projections, graph algorithms, variable-length traversals
     - Direct ``graph.query()`` or manual mapping
     - The result shape is not a simple entity or first-column scalar.
   * - High-volume imports and exports
     - Direct ``graph.query()`` with batching and ``UNWIND``
     - ``save_all()`` currently saves entities one at a time.
   * - Schema evolution across releases
     - Explicit deployment scripts or raw Cypher
     - The ORM manages declared indexes, not versioned migrations.

Avoid N+1 Relationship Loading
------------------------------

Lazy relationships are convenient for occasional traversal, but they can create
an N+1 pattern on list screens: one query loads entities, then each entity access
loads the same relationship separately.

.. code-block:: python

   # Risky on a list view: each company access may trigger another traversal.
   people = repo.find_all()
   for person in people:
       print(person.company.name)

Use eager loading when the response is known to need related data.

.. code-block:: python

   people = repo.find_all(fetch=["company", "friends"])
   for person in people:
       company_name = person.company.name if person.company else "Independent"
       friend_count = len(person.friends)
       print(person.name, company_name, friend_count)

For complex pages, treat eager loading as part of the query design. Fetch only
the relationships the screen or API response actually renders.

Bulk Writes and Imports
-----------------------

``save_all()`` is convenient for small batches, but it loops through entities and
saves them one at a time. For large imports, use raw Cypher with batching.

.. code-block:: python

   def import_people(graph, rows: list[dict[str, object]], batch_size: int = 1_000) -> None:
       for offset in range(0, len(rows), batch_size):
           batch = rows[offset : offset + batch_size]
           graph.query(
               """
               UNWIND $rows AS row
               CREATE (p:Person)
               SET p = row
               """,
               {"rows": batch},
           )

Use the ORM around the import when it adds value, for example to validate input
or to read back typed entities after the bulk load. Do not force high-volume
ingestion through repository saves just to keep one style everywhere.

Intern Repeated Strings
-----------------------

Use ``interned()`` for low-cardinality strings repeated across many nodes, such
as status values, country codes, tags, or email domains.

.. code-block:: python

   from falkordb_orm import generated_id, interned, node


   @node("Event")
   class Event:
       id: int | None = generated_id()
       source: str = interned()
       severity: str = interned()
       message: str

Avoid interning free-form text such as descriptions, messages, names, or user
comments. Those values are usually high-cardinality and are better represented as
normal properties or full-text indexed fields.

Custom Projections
------------------

``@query`` maps entity returns and simple scalar returns. It is intentionally not
a complete projection mapper. Use direct query results when you return several
values per row or mixed entity/value shapes.

.. code-block:: python

   @query(
       "MATCH (p:Person)-[:KNOWS]->(:Person) RETURN p",
       returns=Person,
   )
   def people_with_friends(self) -> list[Person]:
       pass

For a richer projection, map records yourself.

.. code-block:: python

   from dataclasses import dataclass


   @dataclass
   class PersonNetworkSummary:
       person_id: int
       name: str
       friend_count: int
       company_count: int


   def network_summary(graph) -> list[PersonNetworkSummary]:
       result = graph.query(
           """
           MATCH (p:Person)
           OPTIONAL MATCH (p)-[:KNOWS]->(friend:Person)
           OPTIONAL MATCH (p)-[:WORKS_FOR]->(company:Company)
           RETURN id(p), p.name, count(DISTINCT friend), count(DISTINCT company)
           ORDER BY p.name ASC
           """
       )
       return [
           PersonNetworkSummary(
               person_id=record[0],
               name=record[1],
               friend_count=record[2],
               company_count=record[3],
           )
           for record in result.result_set
       ]

Schema and Index Boundaries
---------------------------

The ORM can declare and apply single-property range, full-text, vector, and
unique index metadata. It does not provide a full versioned migration system and
does not model composite index helpers.

Use ``SchemaManager`` for startup or deployment checks:

.. code-block:: python

   from falkordb_orm import SchemaManager

   schema = SchemaManager(graph)
   result = schema.validate_schema([Person, Company, Event])
   if result.missing_indexes:
       schema.sync_schema([Person, Company, Event], drop_extra=False)

Use explicit scripts for schema evolution that needs review, ordering, rollback,
or raw FalkorDB syntax.

.. code-block:: python

   def apply_schema_v2(graph) -> None:
       graph.query("CREATE INDEX ON :Person(email)")
       graph.query("CREATE INDEX ON :Company(domain)")

       # Keep destructive schema changes in reviewed deployment scripts.
       # Example only; verify syntax and impact against your FalkorDB version.
       graph.query("DROP INDEX ON :Person(legacy_email)")

Session Dirty Tracking
----------------------

Sessions keep an identity map and track new, dirty, and deleted entities, but
there is no public ``mark_dirty`` helper. For modified loaded entities, prefer a
repository save when you need the update to be explicit.

.. code-block:: python

   person = repo.find_by_id(1)
   if person is not None:
       person.age = 31
       repo.save(person)

Use ``Session`` when the workflow benefits from identity-map behavior and unit
of work grouping. Be careful with loaded objects that are mutated after loading;
verify the session behavior you rely on with integration tests.

.. code-block:: python

   with Session(graph) as session:
       person = session.get(Person, 1)
       if person is not None:
           person.age = 31
           # No public mark_dirty API exists yet; prefer repo.save(person)
           # for explicit updates outside session-managed creation/deletion.

Bidirectional Relationship Sync
-------------------------------

Saving one side of a relationship creates or updates graph edges, but it does not
automatically mutate the related Python object in memory. Set both sides when the
current process needs both directions to be consistent before reloading.

.. code-block:: python

   alice.friends = [bob]
   people.save(alice)

   # The graph edge exists, but bob.friends is not magically changed in memory.
   bob.friends = [alice]

   people.save_all([alice, bob])

For response models, consider reloading with ``fetch=[...]`` after relationship
updates instead of relying on old in-memory objects.

Raw Client Remains First Class
------------------------------

Use direct ``graph.query()`` for advanced graph algorithms, hand-tuned Cypher,
large imports, administrative maintenance, and features not represented by the
ORM API.

.. code-block:: python

   result = graph.query(
       """
       MATCH path = shortestPath((start:Person)-[:KNOWS*]-(target:Person))
       WHERE start.email = $start_email AND target.email = $target_email
       RETURN path
       """,
       {
           "start_email": "alice@example.com",
           "target_email": "grace@example.com",
       },
   )

Security Boundaries
-------------------

Security exports are available, but advanced policy storage and performance
semantics should be verified against the concrete classes you use. In particular,
do not assume every older planning note is implemented as graph-backed RBAC.
Write integration tests for permission checks that protect production data.
