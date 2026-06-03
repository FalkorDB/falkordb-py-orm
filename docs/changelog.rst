Changelog
=========

The project changelog is maintained in ``CHANGELOG.md`` at the repository root.

v1.2.x
------

The current package version is ``1.2.2``. See the repository changelog for the
full release history.

v1.1.0 highlights
-----------------

Version 1.1.0 added the advanced features that shape much of this documentation:

* ``Session`` and ``AsyncSession`` transaction support with identity map and
  change tracking.
* ``@indexed`` and ``@unique`` decorators, ``IndexManager``, and ``SchemaManager``.
* ``Pageable`` and ``Page[T]`` pagination support.
* Relationship update handling that removes old edges before creating new ones.
* Integration tests and examples for advanced workflows.

Known v1.1.0 limitations
------------------------

The v1.1.0 release notes also document manual session dirty marking,
manual bidirectional synchronization, lack of composite indexes, and edge cases
around clearing some relationship values.
