==========
py-couchdb
==========

.. image:: https://travis-ci.org/histrio/py-couchdb.svg?branch=master
    :target: https://travis-ci.org/histrio/py-couchdb

.. image:: https://img.shields.io/pypi/v/pycouchdb.svg?style=flat
    :target: https://pypi.python.org/pypi/pycouchdb

.. image:: https://img.shields.io/pypi/dm/pycouchdb.svg?style=flat
    :target: https://pypi.python.org/pypi/pycouchdb

.. image:: https://coveralls.io/repos/histrio/py-couchdb/badge.svg?branch=master&service=github 
    :target: https://coveralls.io/github/histrio/py-couchdb?branch=master 


Modern pure python `CouchDB <https://couchdb.apache.org/>`_ Client.

Currently there are several libraries in python to connect to couchdb. **Why one more?** 
It's very simple.

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
    
Documentation
^^^^^^^^^^^^^

Documentation is available at http://pycouchdb.readthedocs.org.

Test
^^^^
To test py-couchdb, simply run:

.. code-block:: console

   nosetests --cover-package=pycouchdb --with-doctest
