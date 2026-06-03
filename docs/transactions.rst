Transactions and Sessions
=========================

``Session`` and ``AsyncSession`` implement a **unit-of-work** pattern on top of
FalkorDB. They maintain an identity map, track insertions, updates, and
deletions, and expose explicit ``commit`` / ``rollback`` / ``flush`` control.

.. note::

   FalkorDB does not support multi-statement ACID transactions at the server
   level. ``commit()`` flushes all pending operations as individual auto-
   committed queries in the order: INSERTs → UPDATEs → DELETEs.
   ``rollback()`` discards in-memory pending state only — it cannot undo
   queries that were already sent to the database (e.g. after ``flush()``).

Session lifecycle
-----------------

A ``Session`` is typically used as a context manager. On normal exit it calls
``commit()``; on exception it calls ``rollback()`` and then ``close()``.

.. code-block:: python

   import falkordb
   from falkordb_orm import Session
   from myapp.models import Person, Department

   db    = falkordb.FalkorDB(host="localhost", port=6379)
   graph = db.select_graph("myapp")

   with Session(graph) as session:
       alice = Person(name="Alice", age=30)
       session.add(alice)
   # commit() called automatically on clean exit
   # alice.id is now populated

You can also manage the session manually when you need finer control:

.. code-block:: python

   session = Session(graph)
   try:
       session.add(Person(name="Bob", age=25))
       session.commit()
   except Exception:
       session.rollback()
       raise
   finally:
       session.close()

Identity map
------------

The first ``session.get(EntityClass, id)`` loads the entity from the graph and
registers it in an in-process cache keyed by ``(type, id)``. Every subsequent
call with the same key returns the **same Python object** without hitting the
database again.

.. code-block:: python

   with Session(graph) as session:
       alice  = session.get(Person, 1)
       alice2 = session.get(Person, 1)   # served from cache

       assert alice is alice2            # True — identical object

This prevents accidental dual-writes and makes it safe to pass the same entity
instance through multiple service layers within a single request.

Change tracking
---------------

The session tracks three sets of pending work:

.. list-table::
   :header-rows: 1
   :widths: 15 30 55

   * - Set
     - Populated by
     - Action on flush
   * - ``_new``
     - ``session.add(entity)``
     - Generates ``CREATE`` Cypher
   * - ``_dirty``
     - ``session.add(entity)`` after load, or explicit marking
     - Generates ``SET`` Cypher only for modified properties
   * - ``_deleted``
     - ``session.delete(entity)``
     - Generates ``DETACH DELETE`` Cypher

``flush()`` processes all three sets without ending the logical unit-of-work,
so you can flush mid-session to, for example, obtain a generated ID before
using it as a foreign reference:

.. code-block:: python

   with Session(graph) as session:
       dept = Department(name="Engineering")
       session.add(dept)
       session.flush()          # INSERT dept → dept.id is now set

       alice = Person(name="Alice", age=30, department_id=dept.id)
       session.add(alice)
       # commit() flushes alice and ends the unit-of-work

Adding and deleting entities
----------------------------

.. code-block:: python

   with Session(graph) as session:
       # Insert two new nodes
       alice = Person(name="Alice", age=30)
       bob   = Person(name="Bob",   age=25)
       session.add(alice)
       session.add(bob)

       # Load and delete an existing node
       legacy = session.get(Person, 99)
       if legacy:
           session.delete(legacy)

       # All three operations (2 INSERTs + 1 DELETE) execute on commit

Re-adding a deleted entity promotes it back to the dirty set, so it will be
updated rather than re-inserted:

.. code-block:: python

   session.delete(alice)
   session.add(alice)    # cancels deletion; alice goes to _dirty

Updating entities
-----------------

After loading an entity with ``session.get()``, modify its attributes and mark
it dirty before committing. The session compares the current state against the
snapshot it captured on load and sends only the changed properties.

.. code-block:: python

   with Session(graph) as session:
       alice = session.get(Person, 1)
       alice.age   = 31
       alice.email = "alice@newdomain.com"
       session._dirty.add(alice)        # explicit dirty marking required
       # commit() sends SET for age and email only

Rollback
--------

``rollback()`` discards all entries in ``_new``, ``_dirty``, and ``_deleted``
and restores the in-memory state of already-loaded entities to the snapshot
captured when they were first fetched. It does **not** reverse queries that
were already sent (e.g. via an earlier ``flush()``).

.. code-block:: python

   session = Session(graph)
   alice = session.get(Person, 1)
   alice.age = 99
   session._dirty.add(alice)

   session.rollback()          # alice.age restored to original value
   assert alice.age != 99      # True — original value is back

   session.close()

Error handling inside a context manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Any exception raised inside a ``with Session(...) as session:`` block
triggers automatic rollback and close:

.. code-block:: python

   try:
       with Session(graph) as session:
           session.add(Person(name="Charlie", age=40))
           raise ValueError("something went wrong")
   except ValueError:
       pass   # session rolled back and closed; Charlie was NOT saved

Async sessions
--------------

``AsyncSession`` mirrors ``Session`` exactly but uses ``async with`` and
``await`` for all I/O-bound operations. Use it with an async FalkorDB client.

.. code-block:: python

   import asyncio
   import falkordb
   from falkordb_orm import AsyncSession
   from myapp.models import Person

   async def main():
       db    = falkordb.FalkorDB(host="localhost", port=6379)
       graph = await db.select_graph("myapp")

       async with AsyncSession(graph) as session:
           alice = Person(name="Alice", age=30)
           session.add(alice)
       # await commit() called automatically

   asyncio.run(main())

Explicit async flush and rollback:

.. code-block:: python

   async def transfer(graph, from_id: int, to_id: int, amount: float):
       async with AsyncSession(graph) as session:
           src = await session.get(Account, from_id)
           dst = await session.get(Account, to_id)

           if src.balance < amount:
               raise ValueError("Insufficient funds")

           src.balance -= amount
           dst.balance += amount
           session._dirty.update([src, dst])
           # commit() fires both UPDATEs atomically within the flush cycle

Async manual control follows the same pattern as the sync version:

.. code-block:: python

   session = AsyncSession(graph)
   try:
       session.add(Person(name="Dave", age=35))
       await session.commit()
   except Exception:
       await session.rollback()
       raise
   finally:
       await session.close()

API reference
-------------

Both ``Session`` and ``AsyncSession`` expose the same interface. ``AsyncSession``
methods that touch the database are coroutines (prefix with ``await``).

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Method
     - Description
   * - ``add(entity)``
     - Mark entity for INSERT (or UPDATE if re-added after delete)
   * - ``delete(entity)``
     - Mark entity for DETACH DELETE; removes it from the identity map
   * - ``get(cls, id)``
     - Load by primary key; returns cached instance on repeat calls
   * - ``flush()``
     - Execute all pending INSERTs → UPDATEs → DELETEs without closing
   * - ``commit()``
     - Call ``flush()`` and end the unit-of-work
   * - ``rollback()``
     - Discard pending state and restore in-memory entity snapshots
   * - ``close()``
     - Clear all caches and mark session as closed
