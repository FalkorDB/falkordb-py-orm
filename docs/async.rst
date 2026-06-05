Async Usage
===========

``AsyncRepository`` and ``AsyncSession`` are full async counterparts to the
synchronous API. They are built on the FalkorDB async client and designed for
use with FastAPI, aiohttp, or any ``asyncio``-based application.

Every method that touches the database is a coroutine — prefix all calls with
``await``. The programming model is otherwise identical to the synchronous API.

Installation and connection pool
---------------------------------

The async client ships with the ``falkordb`` package. For production use, set
up a ``BlockingConnectionPool`` so that concurrent requests share a bounded
number of connections rather than opening one per coroutine.

.. code-block:: python

   from falkordb.asyncio import FalkorDB
   from redis.asyncio import BlockingConnectionPool

   pool = BlockingConnectionPool(
       host="localhost",
       port=6379,
       max_connections=20,
       timeout=5,          # seconds to wait for a free connection
       decode_responses=True,
   )
   db    = FalkorDB(connection_pool=pool)
   graph = db.select_graph("myapp")

Defining entity models
-----------------------

Model definitions are identical to the synchronous API — decorators and type
annotations are resolved at class-definition time, not at query time.

.. code-block:: python

   from typing import List, Optional
   from falkordb_orm import generated_id, node, relationship, unique
   from falkordb_orm.types import IndexType


   @node("Tag")
   class Tag:
       id: int | None = generated_id()
       name: str = unique(required=True)


   @node("Article")
   class Article:
       id: int | None = generated_id()
       title: str
       body: str
       published: bool = False
       view_count: int = 0

       tags: List[Tag] = relationship("TAGGED_WITH", target=Tag, direction="OUTGOING")

Basic CRUD with AsyncRepository
---------------------------------

.. code-block:: python

   import asyncio
   from falkordb.asyncio import FalkorDB
   from falkordb_orm import AsyncRepository


   async def main():
       db    = FalkorDB(host="localhost", port=6379)
       graph = db.select_graph("myapp")

       articles = AsyncRepository(graph, Article)

       # Create
       intro = await articles.save(
           Article(title="Hello FalkorDB", body="Getting started...", published=True)
       )
       print(intro.id)   # auto-generated graph ID

       # Read by ID
       fetched = await articles.find_by_id(intro.id)

       # Update (MERGE on existing ID)
       fetched.view_count += 1
       await articles.save(fetched)

       # Bulk create
       drafts = await articles.save_all([
           Article(title="Draft 1", body="..."),
           Article(title="Draft 2", body="..."),
       ])

       # Delete
       await articles.delete(fetched)
       await articles.delete_by_id(drafts[0].id)

       # Delete all articles (use with care)
       await articles.delete_all()


   asyncio.run(main())

Derived queries
---------------

Method names are parsed at call time into Cypher — no boilerplate required.
All derived queries are awaitable:

.. code-block:: python

   articles = AsyncRepository(graph, Article)

   # Equality
   results = await articles.find_by_published(True)

   # Comparison operators
   popular = await articles.find_by_view_count_greater_than(1000)

   # Combined conditions
   hits = await articles.find_by_published_and_view_count_greater_than(True, 500)

   # Existence check
   exists = await articles.exists_by_id(42)

   # Count
   total        = await articles.count()
   total_public = await articles.count_by_published(True)

Aggregate operations
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   total_views = await articles.sum("view_count")
   avg_views   = await articles.avg("view_count")
   max_views   = await articles.max("view_count")
   min_views   = await articles.min("view_count")

Relationship loading
---------------------

Lazy loading (default)
~~~~~~~~~~~~~~~~~~~~~~

Relationships are exposed as ``AsyncLazyList`` / ``AsyncLazySingle`` proxies.
Call ``await rel.load()`` to fetch related nodes, or iterate with ``async for``:

.. code-block:: python

   article = await articles.find_by_id(1)

   # Explicit load
   loaded_tags = await article.tags.load()

   # Async iteration (loads on first iteration)
   async for tag in article.tags:
       print(tag.name)

Eager loading
~~~~~~~~~~~~~

Pass ``fetch=["relationship_name"]`` to load relationships in a single query:

.. code-block:: python

   article = await articles.find_by_id(1, fetch=["tags"])
   # article.tags is already a plain list — no await needed

   all_articles = await articles.find_all(fetch=["tags"])

AsyncSession — unit of work
-----------------------------

``AsyncSession`` gives you change tracking, an identity map, and batched
flush/commit semantics. It mirrors ``Session`` exactly but all I/O methods
are coroutines. See :doc:`transactions` for a detailed discussion of the
unit-of-work pattern.

.. code-block:: python

   from falkordb_orm import AsyncSession

   async with AsyncSession(graph) as session:
       # Identity map: same object returned on repeated gets
       article = await session.get(Article, 1)
       same    = await session.get(Article, 1)
       assert article is same

       # Track a new entity
       session.add(Article(title="New post", body="...", published=False))

       # Modify and mark dirty
       article.view_count += 1
       session._dirty.add(article)

       # Delete
       old = await session.get(Article, 99)
       session.delete(old)

   # commit() (flush + end) called automatically on clean exit

FastAPI integration
-------------------

The recommended pattern for FastAPI is to create the connection pool once at
startup, store it in ``app.state``, and open a fresh ``AsyncRepository`` (or
``AsyncSession``) per request via a dependency.

.. code-block:: python

   # main.py
   from contextlib import asynccontextmanager
   from typing import Annotated, AsyncGenerator

   from fastapi import Depends, FastAPI, HTTPException
   from pydantic import BaseModel
   from redis.asyncio import BlockingConnectionPool
   from falkordb.asyncio import FalkorDB

   from falkordb_orm import AsyncRepository, AsyncSession, generated_id, node, unique


   # ── Models ────────────────────────────────────────────────────────────────

   @node("Article")
   class Article:
       id: int | None = generated_id()
       title: str
       body: str
       published: bool = False
       view_count: int = 0


   class ArticleIn(BaseModel):
       title: str
       body: str
       published: bool = False


   class ArticleOut(BaseModel):
       id: int
       title: str
       body: str
       published: bool
       view_count: int


   # ── Application lifespan (startup / shutdown) ─────────────────────────────

   @asynccontextmanager
   async def lifespan(app: FastAPI):
       pool = BlockingConnectionPool(
           host="localhost",
           port=6379,
           max_connections=20,
           timeout=5,
           decode_responses=True,
       )
       app.state.db    = FalkorDB(connection_pool=pool)
       app.state.graph = app.state.db.select_graph("blog")
       yield
       await pool.aclose()


   app = FastAPI(lifespan=lifespan)


   # ── Dependencies ──────────────────────────────────────────────────────────

   async def get_articles(
   ) -> AsyncGenerator[AsyncRepository, None]:
       """Yield a per-request AsyncRepository."""
       yield AsyncRepository(app.state.graph, Article)


   async def get_session(
   ) -> AsyncGenerator[AsyncSession, None]:
       """Yield a per-request AsyncSession with auto commit/rollback."""
       async with AsyncSession(app.state.graph) as session:
           yield session


   Articles = Annotated[AsyncRepository[Article], Depends(get_articles)]
   Sess     = Annotated[AsyncSession,             Depends(get_session)]


   # ── Endpoints ─────────────────────────────────────────────────────────────

   @app.get("/articles", response_model=list[ArticleOut])
   async def list_articles(repo: Articles):
       return await repo.find_all()


   @app.get("/articles/{article_id}", response_model=ArticleOut)
   async def get_article(article_id: int, repo: Articles):
       article = await repo.find_by_id(article_id)
       if article is None:
           raise HTTPException(status_code=404, detail="Article not found")
       article.view_count += 1
       await repo.save(article)
       return article


   @app.post("/articles", response_model=ArticleOut, status_code=201)
   async def create_article(body: ArticleIn, repo: Articles):
       article = Article(title=body.title, body=body.body, published=body.published)
       return await repo.save(article)


   @app.patch("/articles/{article_id}/publish", response_model=ArticleOut)
   async def publish_article(article_id: int, session: Sess):
       article = await session.get(Article, article_id)
       if article is None:
           raise HTTPException(status_code=404, detail="Article not found")
       article.published = True
       session._dirty.add(article)
       # session commits automatically when the dependency context exits
       return article

   @app.delete("/articles/{article_id}", status_code=204)
   async def delete_article(article_id: int, repo: Articles):
       article = await repo.find_by_id(article_id)
       if article is None:
           raise HTTPException(status_code=404, detail="Article not found")
       await repo.delete(article)

API reference
-------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Method
     - Description
   * - ``await save(entity)``
     - CREATE or MERGE depending on whether the entity has an ID
   * - ``await save_all(entities)``
     - Save each entity in sequence; returns list of saved instances
   * - ``await find_by_id(id, fetch=[...])``
     - Load by primary key; optional eager relationship fetch
   * - ``await find_all(fetch=[...])``
     - Load every node of this type; optional eager fetch
   * - ``await find_all_by_id([ids])``
     - Load a specific set of IDs
   * - ``await exists_by_id(id)``
     - Return ``True`` / ``False`` without loading the entity
   * - ``await count()``
     - Count all nodes of this type
   * - ``await sum / avg / min / max(property)``
     - Numeric aggregations over a single property
   * - ``await delete(entity)``
     - Delete by entity instance
   * - ``await delete_by_id(id)``
     - Delete by primary key
   * - ``await delete_all(entities?)``
     - Delete a collection, or all nodes of this type if omitted
   * - ``await find_by_*(…)``
     - Derived query — any attribute combination with operators
