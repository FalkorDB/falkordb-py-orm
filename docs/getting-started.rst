Getting Started
===============

This guide takes you from a running FalkorDB instance to your first mapped
entity, saved node, derived query, and relationship.

Install
-------

Install the package from PyPI:

.. code-block:: bash

   pip install falkordb-orm

For local development in this repository, install the package in editable mode:

.. code-block:: bash

   pip install -e .

You also need a FalkorDB server. The examples assume the default Redis protocol
endpoint on ``localhost:6379``.

Define entities
---------------

Entities are normal Python classes decorated with ``@node``. Properties are
inferred from type annotations unless you need custom graph names or metadata.

.. code-block:: python

   from typing import Optional

   from falkordb_orm import Repository, generated_id, node, property


   @node("Person")
   class Person:
       id: Optional[int] = generated_id()
       name: str = property("full_name")
       email: str
       age: int


   @node("Company")
   class Company:
       id: Optional[int] = generated_id()
       name: str

Connect and create a repository
-------------------------------

``Repository[T]`` owns the mapper, query builder, derived query parser, and
relationship manager for one entity type.

.. code-block:: python

   from falkordb import FalkorDB

   db = FalkorDB(host="localhost", port=6379)
   graph = db.select_graph("myapp")

   people = Repository(graph, Person)

Create, read, update, delete
----------------------------

``save()`` creates a new node when the entity has no ID and updates an existing
node when the ID is already set.

.. code-block:: python

   alice = Person(name="Alice", email="alice@example.com", age=30)
   people.save(alice)

   same_alice = people.find_by_id(alice.id)
   same_alice.age = 31
   people.save(same_alice)

   assert people.exists_by_id(alice.id)
   assert people.count() >= 1

   people.delete_by_id(alice.id)

Query by method name
--------------------

Repository methods that start with ``find_``, ``count_``, ``exists_``, or
``delete_`` can be derived at runtime.

.. code-block:: python

   adults = people.find_by_age_greater_than(18)
   alice = people.find_by_email("alice@example.com")
   names = people.find_top_10_by_age_greater_than_order_by_name_asc(18)
   exists = people.exists_by_email("alice@example.com")

Add relationships
-----------------

Use ``relationship()`` for outgoing, incoming, or bidirectional graph edges.
Cascade save is useful when the related entity should be persisted with the
source entity.

.. code-block:: python

   from typing import List, Optional

   from falkordb_orm import generated_id, node, relationship


   @node("Person")
   class Person:
       id: Optional[int] = generated_id()
       name: str
       friends: List["Person"] = relationship("KNOWS", target="Person")
       company: Optional["Company"] = relationship(
           "WORKS_FOR",
           target="Company",
           cascade=True,
       )


   @node("Company")
   class Company:
       id: Optional[int] = generated_id()
       name: str
       employees: List[Person] = relationship(
           "WORKS_FOR",
           direction="INCOMING",
           target=Person,
       )

Load relationships eagerly when you know you will traverse them:

.. code-block:: python

   alice = people.find_by_id(1, fetch=["friends", "company"])
   everyone = people.find_all(fetch=["friends"])

Next steps
----------

Read :doc:`core-concepts` for the architecture, :doc:`mapping-schema` for
entities, relationships, indexes, and schema validation, :doc:`data-access` for
repositories, queries, and pagination, and :doc:`performance-boundaries` before
depending on advanced behavior in production.
