Welcome to FalkorDB ORM
==============================

|PyPI| |Python| |License|


.. |PyPI| image:: https://img.shields.io/pypi/v/falkordb-orm.svg
   :target: https://pypi.org/project/falkordb-orm/
   :alt: PyPI

.. |Python| image:: https://img.shields.io/badge/python-3.11%2B-orange.svg
   :target: https://www.python.org
   :alt: Python Support

.. |License| image:: https://img.shields.io/badge/license-MIT-green.svg
   :target: https://github.com/FalkorDB/falkordb-py-orm/blob/main/LICENSE
   :alt: License


Documentation for version: ``1.2.2``.

Object-graph mapping for FalkorDB with Python type hints, repository
patterns, derived queries, relationships, async support, transactions,
indexes, pagination, and optional RBAC primitives.

Define your graph model in canonical Python, persist it through a typed
repository, and keep direct Cypher available for the parts of your graph that
need full database control.

.. code-block:: bash

   pip install falkordb-orm

Why use FalkorDB Python ORM?
----------------------------

.. raw:: html

   <div class="orm-why-list">
     <p><strong>Entity mapping</strong> Decorate Python classes with <code>@node</code> and let the mapper handle graph properties, labels, and ids.</p>
     <p><strong>Repository workflow</strong> Use CRUD methods, aggregates, pagination, and typed repositories instead of repeating boilerplate Cypher.</p>
     <p><strong>Derived queries</strong> Call methods like <code>find_by_age_greater_than</code> and let the query parser build the Cypher shape.</p>
     <p><strong>Relationships</strong> Declare edges with direction, lazy loading, eager fetch hints, cascade save, and update handling.</p>
     <p><strong>Async support</strong> Use <code>AsyncRepository</code> and <code>AsyncSession</code> in FastAPI, aiohttp, and other async stacks.</p>
     <p><strong>Still Cypher-native</strong> Drop to <code>@query</code> or <code>graph.query()</code> for complex graph algorithms and tuned queries.</p>
   </div>

FalkorDB ORM examples
---------------------

Start with a mapped entity and a repository:

.. raw:: html

   <div class="orm-example-label success">Entity saved</div>

.. code-block:: python

   from typing import Optional

   from falkordb import FalkorDB
   from falkordb_orm import Repository, generated_id, node


   @node("Person")
   class Person:
       id: Optional[int] = generated_id()
       name: str
       email: str
       age: int


   graph = FalkorDB(host="localhost", port=6379).select_graph("myapp")
   people = Repository(graph, Person)

   alice = people.save(Person(name="Alice", email="alice@example.com", age=30))
   print(alice.id)

Then query by method name:

.. raw:: html

   <div class="orm-example-label">Derived query</div>

.. code-block:: python

   adults = people.find_by_age_greater_than(18)
   alice = people.find_by_email("alice@example.com")
   count = people.count_by_age_greater_than(18)

Or use explicit Cypher where it reads better:

.. raw:: html

   <div class="orm-example-label">Custom Cypher</div>

.. code-block:: python

   from falkordb_orm import query


   class PersonRepository(Repository[Person]):
       @query(
           "MATCH (p:Person)-[:KNOWS]->(f:Person) WHERE p.name = $name RETURN f",
           returns=Person,
       )
       def find_friends(self, name: str):
           pass

Where to go next
----------------

.. raw:: html

    <div class="orm-card-grid">
       <a class="orm-card" href="getting-started.html">
          <strong>Get started</strong>
          <span>Install, connect to FalkorDB, define a node, and save your first entity.</span>
       </a>
       <a class="orm-card" href="mapping-schema.html">
          <strong>Mapping and schema</strong>
          <span>Model nodes, properties, relationships, indexes, and schema validation.</span>
       </a>
       <a class="orm-card" href="data-access.html">
          <strong>Data access</strong>
          <span>Use repositories, derived queries, custom Cypher, pagination, and aggregates.</span>
       </a>
       <a class="orm-card" href="performance-boundaries.html">
          <strong>Performance and boundaries</strong>
          <span>Understand tuning patterns, raw-client escape hatches, and current limits.</span>
       </a>
    </div>

Additional links
----------------

* :doc:`getting-started`
* :doc:`migration-guide`
* :doc:`api/index`
* :doc:`changelog`

.. toctree::
   :maxdepth: 1
   :caption: User Guide

   getting-started
   core-concepts
   mapping-schema
   data-access
   transactions
   security
   async
   performance-boundaries
   migration-guide

.. toctree::
   :maxdepth: 1
   :caption: Reference

   api/index
   changelog
