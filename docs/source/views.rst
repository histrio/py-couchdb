.. _views:

Views in python
===============

The pycouchdb package comes with a view server to allow you to write views in Python instead of JavaScript.
When pycouchdb is installed, it will install a script called couchpy that runs the view server.
To enable this for your CouchDB server, add the following section to local.ini:

.. code-block:: ini

    [query_servers]
    python3 = /path/to/couchpy


After restarting CouchDB, the Futon view editor should show **python3** in the language pull-down menu.
Here’s some sample view code to get you started:

.. code-block:: python

    def fun(doc):
        if "name" in doc:
            yield doc['name'], None

.. note::
    The view server also works with python 2.7 and pypy.
