Core Concepts
=============

FalkorDB Python ORM is a small object-graph mapping layer on top of the
FalkorDB Python client. Its purpose is to keep application code focused on
Python domain objects while still making the generated Cypher and the underlying
graph model easy to understand.

The ORM is intentionally thin. It covers common entity persistence, repository
queries, relationship loading, schema hints, pagination, and session workflows.
It does not try to hide FalkorDB. Direct ``graph.query()`` remains the right tool
for graph algorithms, complex projections, bulk imports, and query plans that
need exact control.

Design Idea
-----------

The central idea is to separate graph application code into clear roles:

* Entity classes describe the graph shape in Python.
* Metadata records how those classes map to labels, properties, IDs,
  relationships, indexes, and type conversion.
* Repositories provide the application-facing data access boundary for one
  entity type.
* Mapper and query-builder internals translate between objects, Cypher, and
  FalkorDB records.
* Sessions and managers coordinate workflows that span a single operation, such
  as identity maps, staged writes, relationship persistence, and schema checks.

This keeps domain code, query intent, and graph-specific operations in separate
places. A model defines what exists. A repository defines how the application
asks for it. The ORM core handles translation. Raw Cypher remains available when
translation would get in the way.

Layer Architecture
------------------

The project specification describes the ORM as a set of layers over the
FalkorDB client:

.. code-block:: text

   Application code: @node classes, services, repositories
        |
   Repository layer: CRUD, derived queries, @query methods
        |
   ORM core: EntityMapper, QueryBuilder, QueryParser, RelationshipManager, Session
        |
   FalkorDB client: graph.query()
        |
   FalkorDB server

Application code should normally depend on entities and repositories. The
repository layer owns the data access API. The ORM core owns metadata lookup,
Cypher generation, object mapping, relationship persistence, and session state.
The FalkorDB client remains the final execution layer.

Architectural Responsibilities
------------------------------

.. list-table:: Responsibilities
   :header-rows: 1

   * - Area
     - Responsibility
   * - Domain model
     - Defines entity classes and relationships in Python.
   * - Metadata
     - Captures labels, properties, ID strategy, schema hints, converters, and
       relationship declarations.
   * - Repository
     - Exposes entity-centric persistence and query operations to application
       services.
   * - Query parsing
     - Interprets derived repository method names as query specifications.
   * - Query building
     - Turns metadata and query specifications into parameterized Cypher.
   * - Mapping
     - Converts Python values to graph values and FalkorDB records back to
       entity instances.
   * - Relationship management
     - Loads relationships, saves declared edges, and coordinates cascade save
       behavior.
   * - Session management
     - Provides identity-map and staged-workflow behavior around a graph
       connection.
   * - Schema management
     - Uses entity metadata to create or validate indexes and constraints.

How The Pieces Collaborate
--------------------------

A typical write starts with an entity instance. The repository reads the
entity's metadata, asks the mapper and query builder for the appropriate Cypher,
executes it through the FalkorDB client, updates generated identity information,
and then lets the relationship manager persist declared edges.

A typical read starts with repository intent: a built-in method, a derived
method name, a custom ``@query`` method, or direct Cypher. The query builder or
custom query produces Cypher, FalkorDB returns records, and the mapper rebuilds
Python objects from returned nodes and properties.

Sessions sit beside repositories rather than replacing them. They coordinate a
unit-of-work style interaction with identity-map behavior and staged changes,
while normal repository calls remain the simpler option for direct operations.

Boundaries
----------

Use the ORM when the operation is entity-centric and benefits from reusable
metadata, mapping, and repository APIs. Use raw Cypher when the graph query is
the main design object: analytics, grouped projections, multiple returned entity
types, large batch writes, graph algorithms, or planner-specific tuning.

Relationship synchronization also has a boundary. The ORM can persist declared
edges and perform cascade saves, but it does not turn Python objects into a full
bidirectional in-memory graph engine. Model-level invariants that span both
sides of a relationship should still be handled explicitly in application code.

Where To Go Next
----------------

This page is only the architectural map. The operational details live in the
focused guides:

* :doc:`mapping-schema` explains entity mapping, decorators, relationships,
  indexes, and schema validation.
* :doc:`data-access` explains repositories, CRUD, derived queries, custom
  Cypher, aggregates, and pagination.
* :doc:`performance-boundaries` explains performance tradeoffs and what the ORM
  deliberately leaves to raw FalkorDB usage.
* :doc:`migration-guide` explains how to move existing FalkorDB client code
  toward the ORM incrementally.