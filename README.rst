==========
py-couchdb
==========

Modern pure python CouchDB Client.

Currently there are several libraries in python to connect to couchdb. **Why one more?** It's very simple. 
All seems not be maintained, all libraries used standard Python libraries for http requests, and are not compatible with python3.

Advantages of py-couchdb
^^^^^^^^^^^^^^^^^^^^^^^^

- Use `requests`_ for http requests (much faster than the standard library)
- Python2 and Python3 compatible with same codebase (with one exception, python view server that uses 2to3)
- Also compatible with pypy.

.. _requests: http://docs.python-requests.org/en/latest/


Example:

.. code-block:: python

    >>> import pycouchdb
    >>> server = pycouchdb.Server("http://admin:admin@localhost:5984/")
    >>> server.info()['version']
    '1.2.1'


Installation
^^^^^^^^^^^^

To install py-couchdb, simply:

.. code-block:: console

    pip install pycouchdb

Test
^^^^
To test py-couchdb, simply run:

.. code-block:: console

   python tests.py
 
This command assumes a couchdb account with username "admin" and
password "admin". Otherwise change "SERVER_URL" in tests.py.
