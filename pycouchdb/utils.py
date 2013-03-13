# -*- coding: utf-8 -*-

import sys

if sys.version_info[:2] > (2, 7):
    from urllib.parse import quote as _quote
    from urllib.parse import unquote as _unquote
    from urllib.parse import urlunsplit, urlsplit
else:
    from urllib import quote as _quote
    from urllib import unquote as _unquote
    from urlparse import urlunsplit, urlsplit

import json


def _extract_credentials(url):
    """Extract authentication (user name and password) credentials from the
    given URL.

    >>> extract_credentials('http://localhost:5984/_config/')
    ('http://localhost:5984/_config/', None)
    >>> extract_credentials('http://joe:secret@localhost:5984/_config/')
    ('http://localhost:5984/_config/', ('joe', 'secret'))
    >>> extract_credentials('http://joe%40example.com:secret@localhost:5984/_config/')
    ('http://localhost:5984/_config/', ('joe@example.com', 'secret'))
    """
    parts = urlsplit(url)
    netloc = parts[1]
    if '@' in netloc:
        creds, netloc = netloc.split('@')
        credentials = tuple(_unquote(i) for i in creds.split(':'))
        parts = list(parts)
        parts[1] = netloc
    else:
        credentials = None
    return urlunsplit(parts), credentials


def quote(data, safe=b''):
    if isinstance(data, str):
        data = data.encode('utf-8')
    return _quote(data, safe)



def urljoin(base, *path):
    """Assemble a uri based on a base, any number of path segments, and query
    string parameters.

    >>> urljoin('http://example.org', '_all_dbs')
    'http://example.org/_all_dbs'

    A trailing slash on the uri base is handled gracefully:

    >>> urljoin('http://example.org/', '_all_dbs')
    'http://example.org/_all_dbs'

    And multiple positional arguments become path parts:

    >>> urljoin('http://example.org/', 'foo', 'bar')
    'http://example.org/foo/bar'

    All slashes within a path part are escaped:

    >>> urljoin('http://example.org/', 'foo/bar')
    'http://example.org/foo%2Fbar'
    >>> urljoin('http://example.org/', 'foo', '/bar/')
    'http://example.org/foo/%2Fbar%2F'

    >>> urljoin('http://example.org/', None) #doctest:+IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    TypeError: argument 2 to map() must support iteration
    """
    if base and base.endswith('/'):
        base = base[:-1]
    retval = [base]

    # build the path
    path = '/'.join([''] + [quote(s) for s in path])
    if path:
        retval.append(path)

    return ''.join(retval)

def as_json(response):
    if "application/json" in response.headers['content-type']:
        return json.loads(response.text)
    raise RuntimeError()

def to_json(doc):
    return json.dumps(doc)


def _path_from_name(name, type):
    """
    Expand a 'design/foo' style name to its full path as a list of
    segments.
    """
    if name.startswith('_'):
        return name.split('/')
    design, name = name.split('/', 1)
    return ['_design', design, type, name]


def _encode_view_options(options):
    """
    Encode any items in the options dict that are sent as a JSON string to a
    view/list function.
    """
    retval = {}
    for name, value in options.items():
        if name in ('key', 'startkey', 'endkey') \
                or not isinstance(value, str):
            value = json.encode(value)
        retval[name] = value
    return retval
