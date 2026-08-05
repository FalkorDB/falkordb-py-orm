Security and RBAC
=================

The security package provides role-based access control (RBAC) around ORM
repositories and sessions. It is built around three interlocking layers:

1. **Entity metadata** — declarative decorators mark which roles may read,
   write, create, or delete each node or edge class, and which individual
   properties are restricted.
2. **Runtime enforcement** — ``SecureRepository`` and ``SecureSession``
   intercept every ORM call, resolve the caller's effective privileges, and
   either filter returned data or raise ``AccessDeniedException``.
3. **Administration** — ``RBACManager`` provides transactional user/role/
   privilege management, while ``AuditLogger`` records every access decision
   to a dedicated graph sub-schema.


Core concepts
-------------

Actions and resources
~~~~~~~~~~~~~~~~~~~~~

Every privilege is expressed as an ``(action, resource)`` pair.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Action
     - Meaning
   * - ``READ``
     - Query or fetch a node / relationship
   * - ``WRITE``
     - Update an existing node / relationship
   * - ``CREATE``
     - Insert a new node / relationship
   * - ``DELETE``
     - Remove a node / relationship
   * - ``TRAVERSE``
     - Follow a relationship edge (without reading its properties)

Resources are written as ``Label``, ``Label.property``, or ``*`` for
"all labels". A resource is always interpreted relative to a FalkorDB graph.

Roles
~~~~~

Roles are stored as ``_Security_Role`` nodes in the graph and support single
inheritance (``INHERITS_FROM`` edges). The built-in virtual role ``PUBLIC`` is
automatically added to every authenticated user, making it a convenient slot for
"anyone can read metadata" rules.

Privilege precedence
~~~~~~~~~~~~~~~~~~~~

When a user holds roles with conflicting rules for the same resource, **denies
always take precedence over grants**. This makes it safe to start from a
permissive base role and narrow access via deny rules, without risk of a
mistakenly broad grant overriding an intentional deny.

Defining secured entities
--------------------------

Use the ``@secured`` decorator on any ``@node`` or ``@relationship`` class to
attach security metadata. The decorator accepts separate role lists for each
action and an optional per-property deny map.

Basic example
~~~~~~~~~~~~~

.. code-block:: python

   from falkordb_orm import generated_id, node
   from falkordb_orm.security import secured


   @node("Person")
   @secured(
       read=["reader", "editor", "admin"],
       write=["editor", "admin"],
       create=["admin"],
       delete=["admin"],
   )
   class Person:
       id: int | None = generated_id()
       name: str
       email: str

Property-level restrictions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``deny_read_properties`` and ``deny_write_properties`` keys accept a
mapping of ``{property_name: [roles_that_are_denied]}``. Use ``"*"`` to deny
**all** roles (including admin) and rely on programmatic checks instead.

.. code-block:: python

   @node("Employee")
   @secured(
       read=["hr", "manager", "admin"],
       write=["hr", "admin"],
       create=["admin"],
       delete=["admin"],
       deny_read_properties={
           "ssn":    ["*"],       # nobody can read via ORM
           "salary": ["manager"], # managers see everything except salary
       },
       deny_write_properties={
           "ssn": ["hr"],         # even HR cannot overwrite SSN
       },
   )
   class Employee:
       id: int | None = generated_id()
       name: str
       email: str
       ssn: str
       salary: float
       department: str

Row-level security
~~~~~~~~~~~~~~~~~~

For per-row filtering (e.g., users may only see records they own), add
``@row_level_security`` with a predicate:

.. code-block:: python

   from falkordb_orm.security import row_level_security


   @node("Document")
   @secured(read=["user", "admin"], write=["user", "admin"])
   @row_level_security(
       filter_func=lambda user, doc: (
           doc.owner_id == user.id or "admin" in [r.name for r in user.roles]
       )
   )
   class Document:
       id: int | None = generated_id()
       title: str
       content: str
       owner_id: int

Property-level field decorator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For fine-grained, field-by-field control you can use ``secured_property``
directly on individual annotations:

.. code-block:: python

   from falkordb_orm.security import secured_property


   class MedicalRecord:
       id: int | None = generated_id()
       patient_name: str
       # Only "doctor" and "admin" roles may read; nobody may write via ORM
       diagnosis: str = secured_property(
           deny_read=["nurse", "receptionist"],
           deny_write=["*"],
       )

Setting up roles and policies
------------------------------

Declarative policy DSL
~~~~~~~~~~~~~~~~~~~~~~~

``SecurityPolicy`` provides a concise DSL for defining and persisting rules.
Rules are written to the graph and cached in memory for fast evaluation.

.. code-block:: python

   import falkordb
   from falkordb_orm.security import SecurityPolicy

   db = falkordb.FalkorDB(host="localhost", port=6379)
   graph = db.select_graph("hr")

   policy = SecurityPolicy(graph)

   # Grant broad read to analysts
   policy.grant("READ", "Employee", to="analyst")
   policy.grant("READ", "Department", to="analyst")

   # Grant full HR access
   policy.grant("READ",   "Employee", to="hr")
   policy.grant("WRITE",  "Employee", to="hr")
   policy.grant("CREATE", "Employee", to="hr")

   # Deny sensitive fields for the analyst role
   policy.deny("READ", "Employee.ssn",    to="analyst")
   policy.deny("READ", "Employee.salary", to="analyst")

   # Grant with conditions (template variables resolved at runtime)
   policy.grant(
       "WRITE",
       "Document",
       to="user",
       conditions={"owner_id": "{{user.id}}"},
   )

   # Revoke a previously granted rule
   policy.revoke("READ", "Employee", from_role="analyst")

RBACManager — admin operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``RBACManager`` wraps the policy primitives with user/role lifecycle methods.
Instantiating it requires a ``SecurityContext`` whose effective roles include
``"admin"``; any other caller receives ``UnauthorizedException`` immediately.

.. code-block:: python

   import falkordb
   from falkordb_orm.security import (
       RBACManager,
       SecureSession,
       User,
       Role,
   )

   db    = falkordb.FalkorDB(host="localhost", port=6379)
   graph = db.select_graph("hr")

   # Bootstrap: the first admin must exist in the graph already
   admin_user = User(id=1, username="admin", email="admin@corp.com",
                     is_active=True, roles=[])

   admin_session = SecureSession(graph, admin_user)
   # Temporarily assign the admin role so RBACManager accepts the context
   from falkordb_orm.security import Role
   admin_role = Role(name="admin", description="Superuser")
   admin_user.roles = [admin_role]

   mgr = RBACManager(graph, admin_session.security_context)

   # Create supporting roles
   mgr.create_role("reader",  description="Read-only access")
   mgr.create_role("editor",  description="Read and write access")
   mgr.create_role("analyst", description="Read access without PII")

   # Create users
   alice = mgr.create_user("alice", "alice@corp.com", roles=["editor"])
   bob   = mgr.create_user("bob",   "bob@corp.com",   roles=["analyst"])

   # Promote alice later
   mgr.assign_role("alice", "admin")

   # Disable a leaver
   mgr.update_user("bob", is_active=False)

   # Inspect current state
   users = mgr.list_users(active_only=True)
   roles = mgr.list_roles()

Using secure sessions
---------------------

Basic read and write
~~~~~~~~~~~~~~~~~~~~

``SecureSession`` wraps a regular ``Session`` and returns ``SecureRepository``
instances that enforce all security checks transparently.

.. code-block:: python

   import falkordb
   from falkordb_orm.security import SecureSession, AccessDeniedException
   from myapp.models import Employee

   db    = falkordb.FalkorDB(host="localhost", port=6379)
   graph = db.select_graph("hr")

   session  = SecureSession(graph, alice)           # alice has "editor" role
   employees = session.get_repository(Employee)

   # Fetch — denied properties are silently set to None
   emp = employees.find_by_id(42)
   print(emp.name)     # "Jane Doe"
   print(emp.salary)   # None  (editor role has deny_read for salary)

   # Write — raises AccessDeniedException if role lacks WRITE permission
   emp.department = "Engineering"
   try:
       employees.save(emp)
   except AccessDeniedException as exc:
       print(f"Blocked: {exc}")

Impersonation
~~~~~~~~~~~~~

Administrators can temporarily act as another user using
``ImpersonationContext``. The original security context is restored when the
``with`` block exits, even on exceptions.

.. code-block:: python

   from falkordb_orm.security import SecureSession

   admin_session = SecureSession(graph, admin_user)

   target_user = mgr.get_user("alice")

   with admin_session.impersonate(target_user) as alice_session:
       repo = alice_session.get_repository(Document)
       docs = repo.find_all()   # enforces alice's permissions, not admin's

   # Back to admin context here
   admin_repo = admin_session.get_repository(Document)

Manual permission checks
~~~~~~~~~~~~~~~~~~~~~~~~

Use ``SecurityContext.can()`` for imperative checks outside the repository
layer, e.g., to gate a UI control before the user even submits a request.

.. code-block:: python

   from falkordb_orm.security import SecureSession

   session = SecureSession(graph, current_user)
   ctx     = session.security_context

   if ctx.can("DELETE", "Employee"):
       show_delete_button()

   if ctx.can("READ", "Employee.salary"):
       show_salary_column()

Audit logging
-------------

Every access decision made by ``SecureRepository`` or ``RBACManager`` is
written to ``_Security_AuditLog`` nodes in the graph. You can query them
directly via ``AuditLogger``:

.. code-block:: python

   from falkordb_orm.security import AuditLogger, SecureSession
   from datetime import datetime, timedelta

   logger  = AuditLogger(graph)

   # All denied access attempts in the last 24 hours
   denials = logger.query_logs(
       granted=False,
       start_date=datetime.now() - timedelta(hours=24),
       limit=200,
   )
   for entry in denials:
       print(f"{entry.timestamp}  {entry.username}  {entry.action}  "
             f"{entry.resource}  reason={entry.reason}")

   # All activity for a specific user
   alice_log = logger.query_logs(username="alice", limit=50)

   # All CREATE operations
   creates = logger.query_logs(action="CREATE")

Exception reference
-------------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Exception
     - Raised when
   * - ``SecurityException``
     - Base class; catch-all for unexpected security errors
   * - ``UnauthorizedException``
     - Caller lacks the required role (e.g., non-admin calls ``RBACManager``)
   * - ``AccessDeniedException``
     - Caller's role exists but the privilege is denied for this resource
   * - ``PrivilegeException``
     - Privilege creation or lookup fails (e.g., duplicate rule)
   * - ``RoleException``
     - Role creation or lookup fails (e.g., unknown role name)

.. code-block:: python

   from falkordb_orm.security import (
       AccessDeniedException,
       UnauthorizedException,
   )

   try:
       employees.save(new_employee)
   except AccessDeniedException:
       # Current user lacks CREATE on Employee
       return 403
   except UnauthorizedException:
       # Not authenticated at all
       return 401

Public API summary
------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Symbol
     - Purpose
   * - ``secured``
     - Decorator to attach RBAC metadata to a node/relationship class
   * - ``row_level_security``
     - Decorator to add a per-row filter predicate to a class
   * - ``secured_property``
     - Field descriptor for per-property deny rules
   * - ``SecurityPolicy``
     - DSL for grant / deny / revoke rules
   * - ``PolicyRule``
     - Dataclass representing one policy rule
   * - ``RBACManager``
     - Admin API for users, roles, and privileges
   * - ``SecureSession``
     - Session wrapper that enforces RBAC on all repository calls
   * - ``SecureRepository``
     - Repository wrapper returned by ``SecureSession.get_repository()``
   * - ``SecurityContext``
     - Resolves effective roles and privilege cache for one user
   * - ``ImpersonationContext``
     - Context manager for temporary role switching
   * - ``QueryRewriter``
     - Rewrites raw Cypher queries to inject row-level WHERE clauses
   * - ``AuditLogger``
     - Writes and queries ``_Security_AuditLog`` nodes
   * - ``InMemoryRBACStore``
     - In-process store for testing without a live graph
   * - ``Role``, ``User``, ``Privilege``, ``AuditLog``
     - Graph model classes for security entities
