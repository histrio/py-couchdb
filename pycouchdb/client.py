# -*- coding: utf-8 -*-

import os
import requests
import json
import uuid
import copy
import mimetypes

from . import utils
from .resource import Resource
from .exceptions import Conflict, NotFound

DEFAULT_BASE_URL = os.environ.get('COUCHDB_URL', 'http://localhost:5984/')


class Server(object):
    """
    Class that represents a couchdb connection.

    :param base_url: a full url to couchdb (can contain auth data).
    :param full_commit: If ``False``, couchdb not commits all data on a request is finished.
    :param authmethod: specify a authentication method. By default use a "session" method but also exists
            "basic" (that uses http basic auth).
    """

    def __init__(self, base_url=DEFAULT_BASE_URL, full_commit=True, authmethod="session"):
        self.base_url = base_url
        self.base_url, credentials = utils._extract_credentials(base_url)
        self.resource = Resource(base_url, full_commit, credentials=credentials, authmethod=authmethod)

    def __contains__(self, name):
        r = self.resource.head(name)
        return r.status_code == 200

    def __iter__(self):
        r = self.resource.get('_all_dbs')
        return iter(utils.as_json(r))

    def __len__(self):
        rs = self.resource.get('_all_dbs')
        return len(utils.as_json(rs))

    def info(self):
        """
        Get server info.

        :returns: dict with all data that couchdb returns.
        :rtype: dict
        """
        r = self.resource.get()
        return utils.as_json(r)

    def delete(self, name):
        """
        Delete some database.

        :param name: database name
        :raises: :py:exc:`~pycouchdb.exceptions.NotFound` if a database does not exists
        """

        r = self.resource.delete(name)
        if r.status_code == 404:
            raise NotFound("database {0} not found".format(name))

    def database(self, name):
        """
        Get a database instance.

        :param name: database name
        :raises: :py:exc:`~pycouchdb.exceptions.NotFound` if a database does not exists

        :returns: a :py:class:`~pycouchdb.client.Database` instance
        """
        r = self.resource.head(name)
        if r.status_code == 404:
            raise NotFound("Database '{0}' does not exists".format(name))

        db = Database(self.resource(name), name)
        return db

    def config(self):
        """
        Get a current config data.
        """
        r = self.resource.get("_config")
        return utils.as_json(r)

    def version(self):
        """
        Get the current version of a couchdb server.
        """
        r = self.resource.get()
        return utils.as_json(r)["version"]

    def stats(self, name=None):
        """
        Get runtime stats.

        :param name: if is not None, get stats identified by a name.
        :returns: dict
        """

        if not name:
            r = self.resource.get("_stats")
            return utils.as_json(r)

        resource = self.resource("_stats", "couchdb")
        r = resource.get(name)
        data = utils.as_json(r)
        return data['couchdb'][name]

    def create(self, name):
        """
        Create a database.

        :param name: database name
        :raises: :py:exc:`~pycouchdb.exceptions.Conflict` if a database already exists
        :returns: a :py:class:`~pycouchdb.client.Database` instance
        """
        r = self.resource.put(name)
        if r.status_code in (200, 201):
            return self.database(name)

        data = utils.as_json(r)
        raise Conflict(data["reason"])


def _id_to_path(id):
    if id[:1] == "_":
        return id.split("/", 1)
    return [id]


class Database(object):
    """
    Class that represents a couchdb database.
    """

    def __init__(self, resource, name):
        self.resource = resource
        self.name = name

    def __contains__(self, id):
        r = self.resource.head(_id_to_path(id))
        return r.status_code < 206

    def __len__(self):
        r = self.resource.get()
        return utils.as_json(r)['doc_count']

    def delete(self, id):
        """
        Delete document by id.

        :param id: document id
        :raises: :py:exc:`~pycouchdb.exceptions.NotFound` if a document not exists

        :returns: document (dict)
        """
        resource = self.resource(*_id_to_path(id))

        r = resource.head()
        if r.status_code == 404:
            raise NotFound("doc not found")

        r = resource.delete(params={"rev": r.headers["etag"].strip('"')})
        return r.status_code < 206

    def get(self, id, params={}):
        """
        Get a document by id.

        :param id: document id
        :raises: :py:exc:`~pycouchdb.exceptions.NotFound` if a document not exists

        :returns: document (dict)
        """

        r = self.resource(*_id_to_path(id)).get(params=params)
        return utils.as_json(r)

    def save(self, doc):
        """
        Save or update a document.

        :param doc: document
        :raises: :py:exc:`~pycouchdb.exceptions.Conflict` if save with wrong revision.
        """
        if "_id" not in doc:
            doc['_id'] = uuid.uuid4().hex

        data = utils.to_json(doc).encode('utf-8')
        r = self.resource(doc['_id']).put(data=data)
        d = utils.as_json(r)

        if r.status_code == 409:
            raise Conflict(d['reason'])

        if "rev" in d and d["rev"] is not None:
            doc["_rev"] = d["rev"]

    def save_bulk(self, docs, transaction=True):
        """
        Save a bulk of documents.

        :param docs: list of docs
        :param transaction: if ``True``, couchdb do a insert in transaction model
        :returns: (ok, results)
        """

        for doc in docs:
            if "_id" not in doc:
                doc["_id"] = uuid.uuid4().hex

        data = utils.to_json({"docs": docs}).encode("utf-8")
        params = {"all_or_nothing": "true" if transaction else "false"}
        r = self.resource.post("_bulk_docs", data=data, params=params)

        ok = True
        results = utils.as_json(r)
        for result, doc in zip(results, docs):
            if "error" in result:
                ok = False
                break

        return ok, results

    def all(self, wrapper=None, **kwargs):
        """
        Execute a builtin view for get all documents.

        :returns: generator object
        """

        params = copy.copy(kwargs)
        params.update({"include_docs": "true"})
        data = None

        if "keys" in params:
            data = {"keys": params.pop("keys")}
            data = utils.to_json(data).encode('utf-8')

        params = utils._encode_view_options(params)
        if data:
            r = self.resource.post("_all_docs", params=params, data=data)
        else:
            r = self.resource.get("_all_docs", params=params)

        data = utils.as_json(r)

        if wrapper is None:
            wrapper = lambda doc: doc

        for row in data["rows"]:
            yield wrapper(row['doc'])

    def cleanup(self):
        """
        Execute a cleanup operation.
        """
        r = self.resource('_view_cleanup').post()
        return utils.as_json(r)

    def commit(self):
        """
        Send commit message to server.
        """
        r = self.resource.post('_ensure_full_commit')
        return utils.as_json(r)

    def compact(self):
        """
        Send compact message to server.
        """
        r = self.resource("_compact").post()
        return utils.as_json(r)

    def compact_view(self, ddoc):
        """
        Execute compact over design view.

        :raises: :py:exc:`~pycouchdb.exceptions.NotFound` if a view does not exists.
        """
        r = self.resource("_compact", ddoc).post()
        if r.status_code == 404:
            raise NotFound("view {0} not found".format(ddoc))
        return utils.as_json(r)

    def revisions(self, id, params={}):
        """
        Get all revisions of one document.

        :param id: document id
        :raises: :py:exc:`~pycouchdb.exceptions.NotFound` if a view does not exists.

        :returns: generator object
        """

        resource = self.resource(id)
        r = resource.get(params={'revs_info': 'true'})
        if r.status_code == 404:
            raise NotFound("docid {0} not found".format(id))

        data = utils.as_json(r)
        for rev in data['_revs_info']:
            if rev['status'] == 'available':
                yield self.get(id, params=params)

    def delete_attachment(self, doc, filename):
        """
        Delete attachment by filename from document.
        """
        resource = self.resource(doc['_id'])
        r = resource.delete(filename, params={'rev': doc['_rev']})
        if r.status_code == 404:
            raise NotFound("filename {0} not found".format(filename))

        data = utils.as_json(r)
        doc['_rev'] = data['rev']
        return data['ok']

    def get_attachment(self, doc, filename):
        """
        Get attachment by filename from document.

        :returns: binary data
        """
        r = self.resource(doc['_id']).get(filename, stream=False)
        return r.content

    def put_attachment(self, doc, content, filename=None, content_type=None):
        """
        Put a attachment to a document.

        :param doc: document dict.
        :param content: the content to upload, either a file-like object or bytes
        :param filename: the name of the attachment file; if omitted, this
                         function tries to get the filename from the file-like
                         object passed as the `content` argument value

        :raises: ValueError
        """

        if filename is None:
            if hasattr(content, 'name'):
                filename = os.path.basename(content.name)
            else:
                raise ValueError('no filename specified for attachment')

        if content_type is None:
            content_type = ';'.join(
                filter(None, mimetypes.guess_type(filename)))

        headers = {"Content-Type": content_type}
        resource = self.resource(doc['_id'])

        r = resource.put(filename, data=content,
            params={'rev': doc['_rev']}, headers=headers)

        data = utils.as_json(r)
        doc['_rev'] = data['rev']
        return data['ok']

    def _query(self, resource, data=None, params={}, headers={}, wrapper=None):
        if data is None:
            r = resource.get(params=params, headers=headers)
        else:
            r = resource.post(data=data, params=params, headers=headers)

        if wrapper is None:
            wrapper = lambda row: row

        for row in utils.as_json(r)["rows"]:
            yield wrapper(row)

    def temporary_query(self, map_func, reduce_func=None,
                        language='javascript', wrapper=None, **kwargs):
        """
        Execute a temporary view.

        :param map_func: unicode string with a map function definition.
        :param reduce_func: unicode string with a reduce function definition.
        :param language: language used for define above functions.

        :returns: generator object
        """
        params = copy.copy(kwargs)
        data = {'map': map_func, 'language': language}

        if "keys" in params:
            data["keys"] = params.pop("keys")

        if reduce_func:
            data["reduce"] = reduce_func

        params = utils._encode_view_options(params)
        data = utils.to_json(data).encode("utf-8")

        return self._query(self.resource("_temp_view"), params=params,
                                            data=data, wrapper=wrapper)

    def query(self, name, wrapper=None, **kwargs):
        """
        Execute a design document view query.

        :param name: name of the view (eg: docidname/viewname)
        :returns: generator object
        """
        params = copy.copy(kwargs)
        path = utils._path_from_name(name, '_view')
        data = None

        if "keys" in params:
            data = {"keys": params.pop('keys')}

        if data:
            data = utils.to_json(data).encode("utf-8")

        params = utils._encode_view_options(params)
        return self._query(self.resource(*path), wrapper=wrapper, params=params, data=data)
