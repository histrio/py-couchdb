==========
py-couchdb
==========

Modern pure python CouchDB Client.

Currently there are several libraries in python to connect to couchdb. **Why one more?** It's very simple. 
All seems not be maintained, all libraries used standard Python libraries for http requests, and are not compatible with python3.

Advantages of py-couchdb
^^^^^^^^^^^^^^^^^^^^^^^^

- Use `requests`_ for http requests (much faster than the standard library)
- 96% test coverage.
- Python2 and Python3 compatible with same codebase.

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

    pip install py-couchdb
