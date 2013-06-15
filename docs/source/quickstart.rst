.. _quickstart:

Quickstart
==========

This page gives a good introduction in how to get started with py-couchdb. This assumes you already have it
installed. If you do not, head over to the :ref:`Installation <install>` section.


Connecto to a server
--------------------

Connect to a couchdb server is very simple. Begin by importing ``pycouchdb`` module and instance
a server class:

.. code-block:: python

    >>> import pycouchdb
    >>> server = pycouchdb.Server()


Authentication
--------------

By default, py-couchdb connects to a ``http://localhost:5984/`` but if your couchdb requieres
authentication,  you can pass ``http://username:password@localhost:5984/`` to server constructor:

.. code-block:: python

    >>> server = pycouchdb.Server("http://username:password@localhost:5984/")

py-couchdb have two methods for authentication: with session or basic auth. By default, "session" method
is used but if you like, can specify the method on create a server instance:

.. code-block:: python

    >>> server = pycouchdb.Server("http://username:password@localhost:5984/",
                                                          authmethod="basic")

Create, obtain and delete a database
-------------------------------------

CouchDB can contains multiple databases. For access to one, this is a simple example:

.. code-block:: python

    >>> db = server.database("foo")
    >>> db
    <pycouchdb.client.Database object at 0x7fd4ae835dd0>


Can create one new db:

.. code-block:: python

    >>> server.create("foo2")
    <pycouchdb.client.Database object at 0x7f9c46059310>

And can remove a database:

.. code-block:: python

   >>> server.delete("foo2")


If you intent remove not existent database, `NotFound` exception is raised. For
more information see :ref:`Èxceptions API <exceptions>`.

.. code-block:: python

    >>> server.delete("foo")
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "./pycouchdb/client.py", line 42, in delete
        raise NotFound("database {0} not found".format(name))
    pycouchdb.exceptions.NotFound: database foo not found


Create, obtain and delete a document
------------------------------------

The simplest way for get a document is using its ``id``.

.. code-block:: python

    >>> db = server.database("foo")
    >>> doc = db.get("b1536a237d8d14f3bfde54b41b036d8a")
    >>> doc
    {'_rev': '1-d62e11770282e4fcc5f6311dae6c80ee', 'name': 'Bar',
                        '_id': 'b1536a237d8d14f3bfde54b41b036d8a'}


You can create a own document:

.. code-block:: python

    >>> doc = db.save({"name": "FOO"})
    >>> doc
    {'_rev': '1-6a1be826ddbd67649df8aa1e0bf12da1',
    '_id': 'ef9e608db6434dd39ab3dc4cf35d22b7', 'name': 'FOO'}


Delete a document:

.. code-block:: python

    >>> db.delete("ef9e608db6434dd39ab3dc4cf35d22b7")
    >>> "ef9e608db6434dd39ab3dc4cf35d22b7" not in db
    True


Querying a database
-------------------

With couchdb you can make two type of query: temporary o a view. This is a simple way to make
a temporary query:

.. code-block:: python

    >>> map_func = "function(doc) { emit(doc.name, 1); }"
    >>> db.temporary_query(map_func)
    <generator object _query at 0x7f65bd292870>
    >>> list(db.temporary_query(map_func))
    [{'value': 1, 'id': '8b588fa0a3b74a299c6d958467994b9a', 'key': 'Fooo'}]


And this is a way for make a query using a predefined views:

.. code-block:: python

    >>> _doc = {
    ...    "_id": "_design/testing",
    ...    "views": {
    ...        "names": {
    ...            "map": "function(doc) { emit(doc.name, 1); }",
    ...            "reduce": "function(k, v) { return  sum(v); }",
    ...        }
    ...    }
    ...}
    >>> doc = db.save(_doc)
    >>> list(db.query("testing/names", group='true'))
    [{'value': 1, 'key': 'Fooo'}]
