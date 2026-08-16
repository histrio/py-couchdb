.. _quickstart:

Quickstart
==========

This page gives a good introduction in how to get started with py-couchdb. This assumes you already have it
installed. If you do not, head over to the :ref:`Installation <install>` section.


Connect to a server
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

py-couchdb have two methods for authentication: with session or basic auth. By default, "basic" method
is used but if you like, can specify the method on create a server instance:

.. code-block:: python

    >>> server = pycouchdb.Server("http://username:password@localhost:5984/",
                                                          authmethod="session")

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
more information see :py:exc:`pycouchdb.exceptions.NotFound`.

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


You can create an own document:

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

Query a design document view with :meth:`~pycouchdb.client.Database.query`:

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


For CouchDB view configuration, see the `CouchDB views documentation
<https://docs.couchdb.org/en/stable/ddocs/views/index.html>`_. This is a way to
make a query using predefined views with Python:

.. code-block:: python

    >>> _doc = {
    ...    "_id": "_design/testing",
    ...    "language": "python3",
    ...    "views": {
    ...        "names": {
    ...            "map": "def fun(doc): yield doc.name, 1",
    ...            "reduce": "def fun(k, v): return  sum(v)",
    ...        }
    ...    }
    ...}
    >>> doc = db.save(_doc)
    >>> list(db.query("testing/names", group='true', language='python3'))
    [{'value': 1, 'key': 'Fooo'}]


Subscribe to a changes stream feed
----------------------------------

CouchDB exposes a fantastic stream API for push change notifications,
and with **pycouchdb** you can subscribe to these changes in a very
simple way:

.. code-block:: python

    >>> def feed_reader(message, db):
    ...     print(message)
    ...
    >>> db.changes_feed(feed_reader)

``changes_feed`` blocks until a stream is closed or :py:class:`~pycouchdb.exceptions.FeedReaderExited`
is raised inside of reader function.

Also, you can make reader as class. This have some advantage, because it exposes often useful
close callback.

Example:

.. code-block:: python

    >>> from pycouchdb.feedreader import BaseFeedReader
    >>> from pycouchdb.exceptions import FeedReaderExited
    >>>
    >>> class MyReader(BaseFeedReader):
    ...     def on_message(self, message):
    ...         # self.db is a current Database instance
    ...         # process message
    ...         raise FeedReaderExited()
    ...
    ...     def on_close(self):
    ...         # This is executed after a exception
    ...         # is raised on on_message method
    ...         print("Feed reader end")
    ...
    >>> db.changes_feed(MyReader())


Pagination
----------

py-couchdb provides convenient pagination functionality for both CouchDB views and Mango queries. This eliminates the need to manually manage `skip` parameters and provides stable, cursor-based pagination.

View Pagination
~~~~~~~~~~~~~~~

Use `view_pages()` for paginating through CouchDB view results:

.. code-block:: python

    >>> # Paginate through view results
    >>> for page in db.view_pages("design/view", page_size=10):
    ...     print(f"Page with {len(page)} rows")
    ...     for row in page:
    ...         print(f"  {row['id']}: {row['key']}")

Mango Query Pagination
~~~~~~~~~~~~~~~~~~~~~~

Use `mango_pages()` for paginating through Mango query results:

.. code-block:: python

    >>> # Paginate through Mango query results
    >>> selector = {"type": "user", "active": True}
    >>> for page in db.mango_pages(selector, page_size=10):
    ...     print(f"Page with {len(page)} documents")
    ...     for doc in page:
    ...         print(f"  {doc['_id']}: {doc['name']}")

Key Benefits
~~~~~~~~~~~~

- **Cursor-based pagination**: Avoids the offset drift caused by ``skip``
- **Automatic cursor management**: No manual `skip` parameter handling
- **Memory efficient**: Process large datasets page by page
- **Consistent API**: Same interface for both view and Mango pagination
