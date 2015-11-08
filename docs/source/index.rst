.. py-couchdb documentation master file, created by
   sphinx-quickstart on Wed Jan 16 19:57:28 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

==========
py-couchdb
==========

Release v\ |version|.

py-couchdb is a :ref:`BSD Licensed`, modern pure `Python`_ `CouchDB`_ client.

Currently there are several libraries for Python to connect to CouchDB. **Why one more?** It's very simple.
All seem to be not maintained, all libraries use standard Python libraries for http requests, and are not compatible with Python3.

Advantages of py-couchdb
========================

- Uses `requests`_ for http requests (much faster than the standard library)
- Python2 and Python3 compatible with same codebase (with one exception, Python view server that uses 2to3)
- Also compatible with pypy.

.. _python: http://python.org
.. _couchdb: http://couchdb.apache.org/
.. _requests: http://docs.python-requests.org/en/latest/

.. note::
   requests 1.2 seems buggy with Python3 and I strongly recommend use request 1.1 if you use Python3


Example:

.. code-block:: python

    >>> import pycouchdb
    >>> server = pycouchdb.Server("http://admin:admin@localhost:5984/")
    >>> server.info()['version']
    '1.2.1'

User guide
==========

This part of the documentation gives a simple introduction on py-couchdb usage.

.. toctree::
   :maxdepth: 2

   install.rst
   quickstart.rst
   api.rst
