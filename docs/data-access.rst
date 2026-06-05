Data Access, Queries, and Pagination
====================================

This guide combines repositories, derived queries, custom Cypher, aggregates,
and pagination. These APIs form the main application-facing data access surface.

Repository Lifecycle
--------------------

Create a repository from a FalkorDB graph and an entity class. The repository
holds the mapper, query builder, query parser, relationship manager, metadata,
and method-name query cache for that entity type.

.. code-block:: python

   from falkordb import FalkorDB
   from falkordb_orm import Repository

   graph = FalkorDB(host="localhost", port=6379).select_graph("myapp")
   people = Repository(graph, Person)

Use one repository per entity type, and share the same graph object across
repositories that participate in the same application workflow.

The constructor has two required arguments:

.. code-block:: python

  Repository(graph, EntityClass)

``graph`` is the selected FalkorDB graph. ``EntityClass`` is a class decorated
with ``@node``. Reuse repository instances where practical; constructing a new
repository for every operation recreates mappers, parsers, and relationship
managers without changing the query behavior.

.. code-block:: python

  # Good: one repository for a workflow or service.
  people = Repository(graph, Person)
  for payload in payloads:
     people.save(Person(**payload))

  # Avoid: repeated construction adds noise and overhead.
  for payload in payloads:
     Repository(graph, Person).save(Person(**payload))

Save Semantics
--------------

``save(entity)`` creates a new node when the configured id field is missing. It
updates an existing node when the id is already set. For generated ids, the saved
entity is returned with the FalkorDB node id populated.

.. code-block:: python

   alice = Person(name="Alice", email="alice@example.com", age=30)
   saved = people.save(alice)
   print(saved.id)

   saved.age = 31
   people.save(saved)

Relationship persistence runs after the node is saved. If a relationship is set
and declared with ``cascade=True``, unsaved related entities are saved before the
edge is created.

.. code-block:: python

  company = Company(name="Acme")
  alice = Person(name="Alice", company=company)

  people.save(alice)

  assert alice.id is not None
  assert company.id is not None

``save_all(entities)`` saves each entity in sequence. It is convenient for small
sets, but it is not a bulk ``UNWIND`` optimization.

Read Methods
------------

``find_by_id(id)`` returns one entity or ``None``. ``find_all()`` returns all
entities for the repository labels. ``find_all_by_id(ids)`` loops over ids and
returns the entities that are found.

.. code-block:: python

  person = people.find_by_id(1)
  selected = people.find_all_by_id([1, 2, 3])
  everyone = people.find_all()

Both ``find_by_id`` and ``find_all`` accept ``fetch=[...]`` for eager loading.

.. code-block:: python

  person = people.find_by_id(1, fetch=["friends", "company"])
  people_with_companies = people.find_all(fetch=["company"])

Use ``find_all()`` carefully on large graphs. Prefer pagination, derived queries,
or raw Cypher when a full-label scan would load too much data into memory.

Delete Methods
--------------

``delete(entity)`` requires an entity with an id. ``delete_by_id(id)`` deletes by
id directly. ``delete_all()`` deletes all nodes for the repository labels, while
``delete_all(entities)`` deletes a selected iterable of entities.

.. code-block:: python

  person = people.find_by_id(1)
  if person is not None:
     people.delete(person)

  people.delete_by_id(2)
  people.delete_all([stale_person, duplicate_person])

Delete operations remove matching nodes and their graph relationships, but they
do not cascade-delete related entity nodes. Model destructive workflows
explicitly when related nodes should also be removed.

CRUD Method Reference
---------------------

.. list-table:: Repository methods
   :header-rows: 1

   * - Method
     - Behavior
   * - ``save(entity)``
     - Create or update one entity based on id presence.
   * - ``save_all(entities)``
     - Save entities one by one and return the saved list.
   * - ``find_by_id(id, fetch=None)``
     - Load one entity and optionally eager-load relationships.
   * - ``find_all(fetch=None)``
     - Load every entity of the repository type.
   * - ``find_all_by_id(ids)``
     - Load a set of ids, skipping ids that are not found.
   * - ``exists_by_id(id)``
     - Return a boolean existence check.
   * - ``count()``
     - Count all nodes for the repository labels.
   * - ``delete(entity)`` / ``delete_by_id(id)``
     - Delete one entity by id.
   * - ``delete_all(entities=None)``
     - Delete selected entities or all entities of the repository type.

Common repository errors are wrapped in ``QueryException``. ``delete(entity)``
raises ``EntityNotFoundException`` if the entity has no mapped id property or no
id value.

Aggregates
----------

Aggregate helpers build simple Cypher aggregate expressions over one property.

.. code-block:: python

   total_age = people.sum("age")
   average_age = people.avg("age")
   youngest = people.min("age")
   oldest = people.max("age")

Use raw Cypher for grouped aggregates, projections across multiple labels, or
complex analytics.

Derived Query Actions
---------------------

Dynamic query methods are resolved through ``Repository.__getattr__``. If the
method name starts with one of the supported prefixes, the repository parses the
name, caches the resulting query specification, validates the number of
positional arguments, builds Cypher, and maps the result.

.. list-table:: Derived query actions
   :header-rows: 1

   * - Prefix
     - Return shape
     - Example
   * - ``find_by``
     - ``list[T]``
     - ``people.find_by_email("alice@example.com")``
   * - ``find_first_by``
     - ``list[T]`` limited to one row
     - ``people.find_first_by_email("alice@example.com")``
   * - ``find_top_N_by``
     - ``list[T]`` limited to ``N`` rows
     - ``people.find_top_10_by_status("active")``
   * - ``count_by``
     - ``int``
     - ``people.count_by_age_greater_than(18)``
   * - ``exists_by``
     - ``bool``
     - ``people.exists_by_email("alice@example.com")``
   * - ``delete_by``
     - ``None``
     - ``people.delete_by_status("inactive")``

There is no ``exists(id)`` shortcut. Use ``exists_by_id(id)`` for id checks or
``exists_by_<property>(...)`` for derived existence checks.

Derived Query Grammar
---------------------

Unknown repository attributes are parsed dynamically when they start with
``find_``, ``count_``, ``exists_``, or ``delete_``. Parsed query specs are cached
on the repository instance.

.. code-block:: python

   people.find_by_email("alice@example.com")
   people.find_by_age_greater_than(18)
   people.count_by_country("DE")
   people.exists_by_email("alice@example.com")
   people.delete_by_status("inactive")

Supported operator suffixes:

.. list-table:: Derived query operators
   :header-rows: 1

   * - Suffix
     - Meaning
     - Example
   * - no suffix
     - equals
     - ``find_by_email(value)``
   * - ``_not``
     - not equals
     - ``find_by_status_not(value)``
   * - ``_greater_than`` / ``_greater_than_equal``
     - greater-than comparisons
     - ``find_by_age_greater_than_equal(18)``
   * - ``_less_than`` / ``_less_than_equal``
     - less-than comparisons
     - ``find_by_price_less_than_equal(100)``
   * - ``_between``
     - two-argument range comparison
     - ``find_by_age_between(18, 65)``
   * - ``_in`` / ``_not_in``
     - collection membership
     - ``find_by_status_in(["active", "pending"])``
   * - ``_is_null`` / ``_is_not_null``
     - null checks with no argument
     - ``find_by_deleted_at_is_null()``
   * - ``_containing``
     - string contains
     - ``find_by_name_containing("ali")``
   * - ``_starting_with`` / ``_ending_with``
     - string prefix or suffix
     - ``find_by_email_ending_with("@example.com")``
   * - ``_like``
     - regular expression match
     - ``find_by_name_like("A.*")``

Combine conditions with ``_and_`` or ``_or_``.

.. code-block:: python

   people.find_by_country_and_age_greater_than("DE", 18)
   people.find_by_name_or_email("Alice", "alice@example.com")

Ordering and Limits
-------------------

Use ``_order_by_`` with ``_asc`` or ``_desc``. Use ``first`` or ``top_N`` to add
a Cypher limit to a ``find`` query. Limited ``find`` methods still return a
list; ``find_first_by_email(...)`` returns a list with zero or one entity.

.. code-block:: python

   people.find_by_status_order_by_name_asc("active")
   people.find_first_by_email("alice@example.com")
   people.find_top_10_by_status_order_by_created_at_desc("active")
  people.find_by_age_greater_than_order_by_name_asc_age_desc(18)

Complex Derived Query Examples
------------------------------

.. code-block:: python

   # All active users from a country, oldest first.
   users.find_by_status_and_country_order_by_age_desc("active", "DE")

   # Users with either missing phone numbers or unverified email.
   users.find_by_phone_is_null_or_email_verified(False)

   # Products in a category and price range.
   products.find_by_category_and_price_between("database", 50, 500)

   # Top five open tasks ordered by creation time.
   tasks.find_top_5_by_status_order_by_created_at_desc("open")

The parser validates positional parameter count based on the operators in the
method name. Keyword arguments are not used by derived methods; pass values in
method-name order.

If a method name cannot be parsed or the provided positional argument count does
not match the derived conditions, the repository raises ``QueryException``.

Custom Cypher Queries
---------------------

Use ``@query`` when a method name cannot express the graph pattern clearly.
Parameters are collected from the decorated method signature and passed to
FalkorDB as query parameters.

.. code-block:: python

   from typing import List

   from falkordb_orm import Repository, query


   class PersonRepository(Repository[Person]):
       @query(
           "MATCH (p:Person)-[:KNOWS]->(f:Person) WHERE p.name = $name RETURN f",
           returns=Person,
       )
       def find_friends(self, name: str) -> List[Person]:
           pass

Return mapping is intentionally simple. Primitive return types use the first
column, entity return types map returned nodes, and unspecified return types
return ``None`` after executing the query.

Custom Query Examples
---------------------

Return a scalar count:

.. code-block:: python

   class PersonRepository(Repository[Person]):
       @query("MATCH (p:Person)-[:KNOWS]->(:Person) RETURN count(p)", returns=int)
       def count_people_with_friends(self) -> int:
           pass

Return related entities through a multi-hop traversal:

.. code-block:: python

   class ProjectRepository(Repository[Project]):
       @query(
           """
           MATCH (p:Project {key: $key})-[:HAS_TASK]->(t:Task)
           WHERE t.status IN $statuses
           RETURN t
           """,
           returns=Task,
       )
       def find_tasks_by_statuses(self, key: str, statuses: list[str]) -> list[Task]:
           pass

Use a write query for graph maintenance:

.. code-block:: python

   class TaskRepository(Repository[Task]):
       @query(
           "MATCH (t:Task {status: $status}) SET t.status = $new_status RETURN count(t)",
           returns=int,
           write=True,
       )
       def bulk_update_status(self, status: str, new_status: str) -> int:
           pass

For complex projections with multiple returned values, prefer raw
``repo.graph.query()`` or manual result mapping.

Async Repository Counterpart
----------------------------

``AsyncRepository`` exposes the same core repository concepts for the FalkorDB
async client. Methods are awaited, and derived methods are resolved dynamically
in the same style as the synchronous repository.

.. code-block:: python

   from falkordb.asyncio import FalkorDB
   from redis.asyncio import BlockingConnectionPool
   from falkordb_orm import AsyncRepository

   pool = BlockingConnectionPool(max_connections=16, decode_responses=True)
   db = FalkorDB(connection_pool=pool)
   graph = db.select_graph("myapp")

   people = AsyncRepository(graph, Person)
   alice = await people.save(Person(name="Alice", email="alice@example.com", age=30))
   adults = await people.find_by_age_greater_than_equal(18)
   total = await people.count()

For a full async walkthrough, see :doc:`async`.

Pagination
----------

Pagination uses ``Pageable`` input and returns ``Page[T]`` metadata.

.. code-block:: python

   from falkordb_orm import Pageable

   pageable = Pageable(page=0, size=25, sort_by="name", direction="ASC")
   page = people.find_all_paginated(pageable)

   print(f"Page {page.page_number + 1} of {page.total_pages}")
   for person in page:
     print(person.name)

``Pageable`` is zero-indexed. ``size`` must be positive. ``direction`` must be
``ASC`` or ``DESC``.

Pagination Navigation
---------------------

``Pageable`` creates new paging requests, while ``Page`` describes the returned
result.

.. code-block:: python

   if page.has_next():
     next_page = people.find_all_paginated(pageable.next())

   if page.has_previous():
     previous_page = people.find_all_paginated(pageable.previous())

   first_page = people.find_all_paginated(pageable.first())

``Page`` also supports ``len(page)``, iteration, ``is_first()``, ``is_last()``,
``total_elements``, and ``total_pages``.

Repository Composition Example
------------------------------

This repository combines built-in CRUD, derived methods, custom Cypher, and
pagination into one application-facing interface.

.. code-block:: python

   class UserRepository(Repository[User]):
     def active_page(self, page: int = 0, size: int = 50):
       pageable = Pageable(page=page, size=size, sort_by="email", direction="ASC")
       return self.find_all_paginated(pageable)

     def find_verified_adults(self):
       return self.find_by_email_verified_and_age_greater_than(True, 18)

     @query(
       """
       MATCH (u:User)-[:MEMBER_OF]->(o:Organization {slug: $slug})
       WHERE u.status = 'active'
       RETURN u
       """,
       returns=User,
     )
     def find_active_members(self, slug: str):
       pass


   users = UserRepository(graph, User)
   first_page = users.active_page()
   adults = users.find_verified_adults()
   members = users.find_active_members("falkordb")

Repository Best Practices
-------------------------

Reuse repository instances within services or request workflows, use eager
loading for known relationship data, and keep derived methods readable.

.. code-block:: python

   # Good: a simple derived query communicates intent.
   adults = people.find_by_age_greater_than_equal(18)

   # Less useful: custom Cypher adds boilerplate for a basic filter.
   class PersonRepository(Repository[Person]):
     @query("MATCH (p:Person) WHERE p.age >= $age RETURN p", returns=Person)
     def find_adults(self, age: int) -> list[Person]:
       pass

Use raw Cypher or a custom ``@query`` method when a derived method name stops
being readable, when the query returns a custom projection, or when the workload
needs batching or planner-specific tuning.

When to Use Raw Cypher
----------------------

Stay with direct ``graph.query()`` when you need grouped projections, several
returned entity types, graph algorithms, large imports, bulk ``UNWIND`` writes,
or planner-specific query tuning.
