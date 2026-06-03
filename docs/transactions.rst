Transactions and Sessions
=========================

``Session`` implements a unit-of-work style boundary with an identity map,
pending inserts, dirty updates, deletes, and context-manager rollback behavior.

.. code-block:: python

   from falkordb_orm import Session


   with Session(graph) as session:
       person = session.get(Person, 1)
       person.age = 31
       session._dirty.add(person)
       session.commit()

Identity map
------------

Repeated ``session.get(Entity, id)`` calls return the same Python object while
the session is open.

Change tracking
---------------

New entities are tracked with ``session.add(entity)`` and deleted entities with
``session.delete(entity)``. Loaded entity modifications currently need explicit
dirty marking before ``commit()``.

Context manager behavior
------------------------

On normal exit, the session commits. On exception, it rolls back and closes.

Async sessions
--------------

Use ``AsyncSession`` in async applications. The same identity-map and unit-of-
work concepts apply.
