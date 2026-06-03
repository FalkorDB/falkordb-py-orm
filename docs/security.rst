Security and RBAC
=================

The security package provides role-based access-control primitives around ORM
repositories and sessions. It includes security metadata models, declarative
decorators, in-memory policy storage, permission checks, secure repositories,
secure sessions, impersonation support, query rewriting helpers, RBAC management,
and audit logging classes.

Secure an entity
----------------

.. code-block:: python

   from falkordb_orm import generated_id, node
   from falkordb_orm.security import secured


   @node("Person")
   @secured(
       read=["reader", "admin"],
       write=["editor", "admin"],
       deny_read_properties={"ssn": ["*"], "salary": ["reader"]},
   )
   class Person:
       id: int | None = generated_id()
       name: str
       email: str
       ssn: str
       salary: float

Use secure sessions
-------------------

.. code-block:: python

   from falkordb_orm.security import SecureSession

   session = SecureSession(graph, alice)
   people = session.get_repository(Person)
   person = people.find_by_id(1)

Roles and policies
------------------

Security policies support actions such as ``READ``, ``WRITE``, ``CREATE``,
``DELETE``, and ``TRAVERSE``. Denies take precedence over grants.

Implementation status
---------------------

The public API exports ``RBACManager``, ``SecurityPolicy``, ``SecureRepository``,
``SecureSession``, ``SecurityContext``, models, decorators, exceptions, query
rewriting helpers, and audit logging classes. The older security README includes
planned roadmap notes, so public docs should distinguish shipped APIs from future
storage or policy enhancements.
