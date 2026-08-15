# py-couchdb

[![CI](https://github.com/histrio/py-couchdb/actions/workflows/main.yml/badge.svg?branch=master)](https://github.com/histrio/py-couchdb/actions/workflows/main.yml)
![PyPI](https://img.shields.io/pypi/v/pycouchdb)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pycouchdb)
[![codecov](https://codecov.io/github/histrio/py-couchdb/graph/badge.svg?token=eXN16KQiEq)](https://codecov.io/github/histrio/py-couchdb)
[![Documentation Status](https://readthedocs.org/projects/pycouchdb/badge/?version=latest)](https://pycouchdb.readthedocs.io/en/latest/?badge=latest)



Modern pure python [CouchDB](https://couchdb.apache.org/) Client.

Currently there are several libraries in python to connect to couchdb. **Why one more?**
It's very simple.

All seems not be maintained, all libraries used standard Python libraries for http requests.



## Advantages of py-couchdb

- Use [requests](http://docs.python-requests.org/en/latest/) for http requests (much faster than the standard library)
- CouchDB 2.x and CouchDB 3.x compatible
- Also compatible with pypy.


Example:

```python
>>> import pycouchdb
>>> server = pycouchdb.Server("http://admin:admin@localhost:5984/")
>>> server.info()['version']
'1.2.1'
```


## Installation

To install py-couchdb, simply:

```bash
pip install pycouchdb
```

## Documentation

Documentation is available at http://pycouchdb.readthedocs.org.

## Logging

py-couchdb is silent by default. Enable its standard-library logger from your
application when needed:

```python
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("pycouchdb").setLevel(logging.DEBUG)
```

DEBUG records include safe HTTP and database-operation metadata; INFO records
summarize bulk results. Request and response bodies, credentials, headers,
hostnames, and query parameter values are never logged. See the
[logging guide](https://pycouchdb.readthedocs.io/en/latest/logging.html) for
formatting and `dictConfig` examples.


## Test

To test py-couchdb, simply run:

``` bash
pytest -v --doctest-modules --cov pycouchdb
```
