Async Usage
===========

``AsyncRepository`` and ``AsyncSession`` provide async counterparts for projects
using the FalkorDB async client, FastAPI, aiohttp, or other async application
stacks.

.. code-block:: python

   import asyncio

   from falkordb.asyncio import FalkorDB
   from redis.asyncio import BlockingConnectionPool

   from falkordb_orm import AsyncRepository, generated_id, node


   @node("Person")
   class Person:
       id: int | None = generated_id()
       name: str
       age: int


   async def main():
       pool = BlockingConnectionPool(
           max_connections=16,
           timeout=None,
           decode_responses=True,
       )
       db = FalkorDB(connection_pool=pool)
       graph = db.select_graph("myapp")

       people = AsyncRepository(graph, Person)
       alice = await people.save(Person(name="Alice", age=30))
       adults = await people.find_by_age_greater_than(18)
       count = await people.count()


   asyncio.run(main())

Async relationship loading follows the same concepts as synchronous loading,
but lazy relationship containers need to be awaited according to their async
interfaces.
