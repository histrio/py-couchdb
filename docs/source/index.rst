.. py-couchdb documentation master file, created by
   sphinx-quickstart on Wed Jan 16 19:57:28 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

py-couchdb
==========

Release v\ |version|.

py-couchdb is an :ref:`BSD Licensed`, modern pure python CouchDB client.

Currently there are several libraries in python to connect to couchdb. **Why one more?** It's very simple. 
All seems not be maintained, all libraries used standard Python libraries for http requests, and are not compatible with python3.

Advantages of py-couchdb
^^^^^^^^^^^^^^^^^^^^^^^^

- Use `requests`_ for http requests (much faster than the standard library)
- 96% test coverage.
- Python2 and Python3 compatible with same codebase.
- Also compatible with pypy.

.. _requests: http://docs.python-requests.org/en/latest/


Example:

.. code-block:: python

    >>> import pycouchdb
    >>> server = pycouchdb.Server("http://admin:admin@localhost:5984/")
    >>> server.info()['version']
    '1.2.1'


User guide
----------

This part of the documentation makes a simple introduction of py-couchdb usage.

.. toctree::
   :maxdepth: 2

   install.rst
   quickstart.rst
   views.rst
   api.rst
