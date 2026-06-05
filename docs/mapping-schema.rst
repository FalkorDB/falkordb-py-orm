Mapping and Schema
==================

This guide combines entity mapping, relationship modeling, index declarations,
and schema validation. These concepts belong together because the decorators on
your Python classes define both how objects are persisted and which graph schema
helpers the ORM can manage.

The Mapping Model
-----------------

``@node`` marks a class as a graph node. The mapper reads type annotations and
descriptor metadata to decide which labels, properties, id fields, relationships,
and index hints belong to the entity.

.. code-block:: python

   from typing import Optional

   from falkordb_orm import generated_id, node, property


   @node("Person")
   class Person:
       id: Optional[int] = generated_id()
       name: str = property("full_name", required=True)
       email: str
       age: int

Plain annotated attributes become graph properties. Descriptors are needed only
when the attribute has mapping behavior beyond a default property.

Labels and IDs
--------------

Use a single label for most entity types, and multiple labels when one class
should participate in several graph categories.

.. code-block:: python

   @node(labels=["Person", "Employee", "Manager"])
   class Manager:
       id: Optional[int] = generated_id()
       name: str
       department: str

``generated_id()`` stores FalkorDB's node id on the Python object after a create.
Manual ids are also valid when your domain has an external stable identifier.

.. code-block:: python

   @node("ExternalAccount")
   class ExternalAccount:
       id: str
       provider: str
       display_name: str

Property Descriptors
--------------------

``property()`` can rename a graph property, mark it required, attach a converter,
or set index flags. Convenience helpers such as ``indexed()``, ``unique()``, and
``interned()`` create specialized property descriptors.

.. code-block:: python

   from falkordb_orm import indexed, interned, unique


   @node("User")
   class User:
       id: int | None = generated_id()
       email: str = unique(required=True)
       age: int = indexed()
       status: str = interned(required=True)
       bio: str = indexed(index_type="FULLTEXT")

Use ``interned()`` for repeated strings such as status values, country codes,
tags, or categories. It is not a general string indexing feature; it is a memory
optimization for repeated values.

Migrating Existing Property Names
---------------------------------

Existing FalkorDB graphs often use property names that do not match the Python
attribute names you want in application code. Keep the graph property name in the
descriptor and expose the cleaner Python attribute on the class.

.. code-block:: python

   @node("Person")
   class Person:
       id: int | None = generated_id()
       name: str = property("full_name")
       email: str = property("email_address")

This avoids raw-client migration bugs where data appears to be missing only
because the ORM is reading ``name`` while the graph stores ``full_name``.

Custom Type Conversion
----------------------

Register a ``TypeConverter`` when a domain object needs a graph-compatible
representation.

.. code-block:: python

   from dataclasses import dataclass

   from falkordb_orm import TypeConverter, register_converter


   @dataclass
   class GeoPoint:
       lat: float
       lon: float


   class GeoPointConverter(TypeConverter):
       def to_graph(self, value: GeoPoint) -> dict[str, float]:
           return {"lat": value.lat, "lon": value.lon}

       def from_graph(self, value: dict[str, float]) -> GeoPoint:
           return GeoPoint(lat=value["lat"], lon=value["lon"])


   register_converter(GeoPoint, GeoPointConverter())

Relationship Mapping
--------------------

``relationship()`` maps a Python attribute to a graph edge. It records edge type,
direction, target entity, lazy loading, and cascade behavior.

.. code-block:: python

   from typing import List, Optional

   from falkordb_orm import generated_id, node, relationship


   @node("Company")
   class Company:
       id: Optional[int] = generated_id()
       name: str
       employees: List["Person"] = relationship(
           "WORKS_FOR",
           direction="INCOMING",
           target="Person",
       )


   @node("Person")
   class Person:
       id: Optional[int] = generated_id()
       name: str
       friends: List["Person"] = relationship("KNOWS", target="Person")
       company: Optional[Company] = relationship(
           "WORKS_FOR",
           direction="OUTGOING",
           target=Company,
           cascade=True,
       )

Direction can be ``OUTGOING``, ``INCOMING``, or ``BOTH``. Use a string target for
forward references and circular type declarations.

Lazy and Eager Loading
----------------------

Lazy loading is the default. The entity loads first and relationship traversal
happens when the relationship is accessed. Use eager loading when the relationship
is known to be needed for a response or workflow.

.. code-block:: python

   person = people.find_by_id(1, fetch=["friends", "company"])
   team = people.find_all(fetch=["company"])

Eager loading is the main way to avoid N+1 query patterns when rendering lists
of entities and their related objects.

Cascade Save
------------

Set ``cascade=True`` when a source entity should save unsaved related entities
before creating the edge.

.. code-block:: python

   company = Company(name="Acme")
   alice = Person(name="Alice")
   alice.company = company

   people.save(alice)

   assert alice.id is not None
   assert company.id is not None

Complex Relationship Example
----------------------------

This example models a project graph with ownership, team membership, and tasks.
It demonstrates mixed single and collection relationships plus cascade on the
project owner.

.. code-block:: python

   @node("Task")
   class Task:
       id: int | None = generated_id()
       title: str
       status: str = interned()


   @node("Project")
   class Project:
       id: int | None = generated_id()
       key: str = unique(required=True)
       name: str
       owner: Person | None = relationship(
           "OWNED_BY",
           target=Person,
           cascade=True,
       )
       members: list[Person] = relationship("HAS_MEMBER", target=Person)
       tasks: list[Task] = relationship("HAS_TASK", target=Task, cascade=True)


   owner = Person(name="Ada")
   reviewer = Person(name="Grace")
   project = Project(key="ORM-DOCS", name="Documentation")
   project.owner = owner
   project.members = [owner, reviewer]
   project.tasks = [
       Task(title="Merge mapping docs", status="done"),
       Task(title="Add advanced examples", status="review"),
   ]

   project_repo.save(project)

Relationship Updates and Boundaries
-----------------------------------

When a saved entity is updated with new relationship values, current repository
saves delete old edges before creating edges for the current values.

.. code-block:: python

   project.members = [owner, reviewer]
   project_repo.save(project)

   project.members = [reviewer]
   project_repo.save(project)

Bidirectional synchronization is manual. If both Python objects should expose the
relationship in memory, set both sides explicitly.

.. code-block:: python

   alice.friends = [bob]
   bob.friends = [alice]
   people.save_all([alice, bob])

Index Management
----------------

Property descriptors record index intent. ``IndexManager`` applies those
declarations to FalkorDB.

.. code-block:: python

   from falkordb_orm import IndexManager

   manager = IndexManager(graph)
   manager.create_indexes(User, if_not_exists=True)
   manager.ensure_indexes(Project)

The metadata supports range indexes, full-text indexes, vector index hints, and
unique constraints. Composite index helpers are not provided; use raw schema
commands for advanced index definitions.

Schema Validation and Synchronization
-------------------------------------

``SchemaManager`` compares declared entity indexes with the database and can
create missing indexes.

.. code-block:: python

   from falkordb_orm import SchemaManager

   schema = SchemaManager(graph)
   result = schema.validate_schema([User, Project, Task])

   if not result.is_valid:
       print(result)
       schema.sync_schema([User, Project, Task])

Useful schema APIs include:

.. list-table:: Schema APIs
   :header-rows: 1

   * - API
     - Use
   * - ``validate_schema([Entity, ...])``
     - Return missing indexes, extra indexes, and validation errors.
   * - ``sync_schema([Entity, ...], drop_extra=False)``
     - Create missing indexes and optionally drop extra managed indexes.
   * - ``get_schema_diff([Entity, ...])``
     - Return a human-readable diff string.
   * - ``ensure_schema([Entity, ...])``
     - Convenience method for creating missing indexes.
   * - ``get_schema_info([Entity, ...])``
     - Return counts and metadata useful for diagnostics.

Production Startup Pattern
--------------------------

A common startup flow is to validate schema, create missing indexes, and fail or
warn when unexpected indexes are present.

.. code-block:: python

   MANAGED_ENTITIES = [User, Person, Company, Project, Task]


   def prepare_schema(graph) -> None:
       schema = SchemaManager(graph)
       result = schema.validate_schema(MANAGED_ENTITIES)

       if result.missing_indexes:
           stats = schema.sync_schema(MANAGED_ENTITIES)
           print(f"Created {stats['created']} missing indexes")

       if result.extra_indexes:
           print("Extra indexes found; review before dropping:")
           for index in result.extra_indexes:
               print(f"- {index.label}.{index.property_name} ({index.index_type})")

This keeps schema management explicit. The ORM does not currently provide a full
versioned migration system.
