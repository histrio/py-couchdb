# py-couchdb

[![Build Status](https://travis-ci.org/histrio/py-couchdb.svg?branch=master)](https://travis-ci.org/histrio/py-couchdb)
![PyPI](https://img.shields.io/pypi/v/pycouchdb)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pycouchdb)
[![Coverage Status](https://coveralls.io/repos/github/histrio/py-couchdb/badge.svg?branch=master)](https://coveralls.io/github/histrio/py-couchdb?branch=master)



Modern pure python [CouchDB](https://couchdb.apache.org/) Client.

Currently there are several libraries in python to connect to couchdb. **Why one more?**
It's very simple.

All seems not be maintained, all libraries used standard Python libraries for http requests, and are not compatible with python3.



## Advantages of py-couchdb

- Use [requests](http://docs.python-requests.org/en/latest/) for http requests (much faster than the standard library)
- Python2 and Python3 compatible with same codebase (with one exception, python view server that uses 2to3)
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


## Test

To test py-couchdb, simply run:

``` bash
    nosetests --cover-package=pycouchdb --with-doctest
```
