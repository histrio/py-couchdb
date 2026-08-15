=======
Logging
=======

py-couchdb uses Python's standard :mod:`logging` package. It never configures
the root logger or installs an output handler, so applications that do not
configure logging remain silent.

Enable logging
==============

Configure handlers and formatting in the application, then choose the desired
level for the ``pycouchdb`` logger:

.. code-block:: python

   import logging

   logging.basicConfig(level=logging.INFO)
   logging.getLogger("pycouchdb").setLevel(logging.DEBUG)

``DEBUG`` records show high-level database operations and HTTP request,
response, and transport-error metadata. HTTP records include the method,
relative path, status, declared response size, and elapsed milliseconds.
``INFO`` records provide one aggregate result for each ``save_bulk`` and
``delete_bulk`` call.

Formatting example
==================

Applications can use :func:`logging.config.dictConfig` like any other Python
logger:

.. code-block:: python

   import logging.config

   logging.config.dictConfig({
       "version": 1,
       "formatters": {
           "default": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
       },
       "handlers": {
           "console": {"class": "logging.StreamHandler", "formatter": "default"},
       },
       "loggers": {
           "pycouchdb": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
       },
   })

Privacy
=======

Request and response bodies, HTTP headers, hostnames, credentials, and query
parameter values are never logged. HTTP request records include parameter
names only. Relative paths and document or database identifiers can appear in
DEBUG records.
