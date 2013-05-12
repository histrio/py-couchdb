# -*- coding: utf-8 -*-

import os
import requests
import json
import uuid
import copy
import mimetypes

from . import utils
from .resource import Resource
from .exceptions import Conflict, NotFound, GenericError

DEFAULT_BASE_URL = os.environ.get('COUCHDB_URL', 'http://localhost:5984/')


class Server(object):
    """
    Class that represents a couchdb connection.

    :param base_url: a full url to couchdb (can contain auth data).
    :param full_commit: If ``False``, couchdb not commits all data on a request is finished.
    :param authmethod: specify a authentication method. By default "basic" method is used but also exists
            "session" (that requires some server configuration changes).

    .. versionchanged: 1.4
       Set basic auth method as default instead of session method.

    """

    def __init__(self, base_url=DEFAULT_BASE_URL, full_commit=True, authmethod="basic"):
        self.base_url, credentials = utils._extract_credentials(base_url)
        self.resource = Resource(self.base_url, full_commit, credentials=credentials, authmethod=authmethod)

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
        (r, result) = self.resource.head(name)
        if r.status_code == 404:
            raise NotFound("Database '{0}' does not exists".format(name))

        db = Database(self.resource(name), name)
        return db

    def config(self):
        """
        Get a current config data.
        """
        (resp, result) = self.resource.get("_config")
        return result

    def version(self):
        """
        Get the current version of a couchdb server.
        """
        (resp, result) = self.resource.get()
        return result["version"]

    def stats(self, name=None):
        """
        Get runtime stats.

        :param name: if is not None, get stats identified by a name.
        :returns: dict
        """

        if not name:
            (resp, result) = self.resource.get("_stats")
            return result

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
        (resp, result) = self.resource.put(name)
        if resp.status_code in (200, 201):
            return self.database(name)

    def replicate(self, source, target, **kwargs):
        """
        Replicate the source database to the target one.

        .. versionadded:: 1.3

        :param source: URL to the source database
        :param target: URL to the target database
        """
        data = copy.copy(kwargs)
        data.update({'source': source, 'target': target})
        data = utils.to_json(data).encode('utf-8')
        (resp, result) = self.resource.post('_replicate', data=data)
        return result


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
        (resp, result) = self.resource.head(_id_to_path(id))
        return resp.status_code < 206

    def __len__(self):
        (resp, result) = self.resource.get()
        return result['doc_count']

    def delete(self, doc_or_id):
        """
        Delete document by id.

        .. versionchanged:: 1.2
            Accept document or id.

        :param doc_or_id: document or id
        :raises: :py:exc:`~pycouchdb.exceptions.NotFound` if a document not exists
        :raises: :py:exc:`~pycouchdb.exceptions.Conflict` if delete with wrong revision.
        """

        _id = None
        if isinstance(doc_or_id, dict):
            if "_id" not in doc_or_id:
                raise ValueError("Invalid document, missing _id attr")
            _id = doc_or_id['_id']
        else:
            _id = doc_or_id

        resource = self.resource(*_id_to_path(_id))

        (resp, result) = resource.head()
        if resp.status_code == 404:
            raise NotFound("doc not found")

        (resp, result) = resource.delete(params={"rev": r.headers["etag"].strip('"')})
        if resp.status_code > 206:
            raise Conflict(result['reason'])

    def delete_bulk(self, docs, transaction=True):
        """
        Delete a bulk of documents.

        .. versionadded:: 1.2

        :param docs: list of docs
        :raises: :py:exc:`~pycouchdb.exceptions.Conflict` if a delete is not success
        :returns: raw results from server
        """

        _docs = copy.copy(docs)
        for doc in _docs:
            if "_deleted" not in doc:
                doc["_deleted"] = True

        data = utils.to_json({"docs" : _docs}).encode("utf-8")
        params = {"all_or_nothing": "true" if transaction else "false"}
        (resp, results) = self.resource.post("_bulk_docs", data=data, params=params)

        for result, doc in zip(results, _docs):
          if "error" in result:
            raise Conflict("one or more docs are not saved")

        return results

    def get(self, id, params={}):
        """
        Get a document by id.

        :param id: document id
        :raises: :py:exc:`~pycouchdb.exceptions.NotFound` if a document not exists

        :returns: document (dict)
        """

        (resp, result) = self.resource(*_id_to_path(id)).get(params=params)
        return result

    def save(self, doc):
        """
        Save or update a document.

        .. versionchanged:: 1.2
            Now returns a new document instead of modify the original.

        :param doc: document
        :raises: :py:exc:`~pycouchdb.exceptions.Conflict` if save with wrong revision.
        :returns: doc
        """

        _doc = copy.copy(doc)
        if "_id" not in _doc:
            _doc['_id'] = uuid.uuid4().hex

        data = utils.to_json(_doc).encode('utf-8')
        (resp, result) = self.resource(_doc['_id']).put(data=data)

        if resp.status_code == 409:
            raise Conflict(result['reason'])

        if "rev" in result and result["rev"] is not None:
            _doc["_rev"] = result["rev"]

        return _doc

    def save_bulk(self, docs, transaction=True):
        """
        Save a bulk of documents.

        .. versionchanged:: 1.2
            Now returns a new document list instead of modify the original.

        :param docs: list of docs
        :param transaction: if ``True``, couchdb do a insert in transaction model
        :returns: docs
        """

        _docs = copy.copy(docs)
        for doc in _docs:
            if "_id" not in doc:
                doc["_id"] = uuid.uuid4().hex

        data = utils.to_json({"docs": _docs}).encode("utf-8")
        params = {"all_or_nothing": "true" if transaction else "false"}
        (resp, results) = self.resource.post("_bulk_docs", data=data, params=params)

        for result, doc in zip(results, _docs):
            if "rev" in result:
                doc['_rev'] = result['rev']

        return _docs

    def all(self, wrapper=None, flat=None, as_list=False, **kwargs):
        """
        Execute a builtin view for get all documents.

        :param wrapper: wrap result into a specific class.
        :param as_list: return a list of results instead of a default lazy generator.
        :param flat: get a specific field from a object instead of a complete object.

        .. versionadded: 1.4
           Add as_list parameter.
           Add flat parameter.

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
            (resp, result) = self.resource.post("_all_docs", params=params, data=data)
        else:
            (resp, result) = self.resource.get("_all_docs", params=params)

        if wrapper is None:
            wrapper = lambda doc: doc

        if flat is not None:
            wrapper = lambda doc: doc[flat]

        def _iterate():
            for row in result["rows"]:
                yield wrapper(row['doc'])

        if as_list:
            return list(_iterate())
        return _iterate()


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
        (resp, result) = self.resource.post('_ensure_full_commit')
        return result

    def compact(self):
        """
        Send compact message to server. Compacting write-heavy databases
        should be avoided, otherwise the process may not catch up with
        the writes. Read load has no effect.
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
        (resp, result) = resource.get(params={'revs_info': 'true'})
        if resp.status_code == 404:
            raise NotFound("docid {0} not found".format(id))

        for rev in result['_revs_info']:
            if rev['status'] == 'available':
                yield self.get(id, params=params)

    def delete_attachment(self, doc, filename):
        """
        Delete attachment by filename from document.

        .. versionchanged:: 1.2
            Now returns a new document instead of modify the original.

        :param doc: document dict
        :param filename: name of attachment.
        :raises: :py:exc:`~pycouchdb.exceptions.Conflict` if save with wrong revision.
        :returns: doc
        """

        _doc = copy.copy(doc)
        resource = self.resource(_doc['_id'])
        (resp, result) = resource.delete(filename, params={'rev': _doc['_rev']})
        if resp.status_code == 404:
            raise NotFound("filename {0} not found".format(filename))

        if resp.status_code < 206:
            _doc['_rev'] = result['rev']
            return _doc

        raise Conflict(result['reason'])

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

        .. versionchanged:: 1.2
            Now returns a new document instead of modify the original.

        :param doc: document dict.
        :param content: the content to upload, either a file-like object or bytes
        :param filename: the name of the attachment file; if omitted, this
                         function tries to get the filename from the file-like
                         object passed as the `content` argument value
        :raises: :py:exc:`~pycouchdb.exceptions.Conflict` if save with wrong revision.
        :raises: ValueError
        :returns: doc
        """
        _doc = copy.copy(doc)

        if filename is None:
            if hasattr(content, 'name'):
                filename = os.path.basename(content.name)
            else:
                raise ValueError('no filename specified for attachment')

        if content_type is None:
            content_type = ';'.join(
                filter(None, mimetypes.guess_type(filename)))

        headers = {"Content-Type": content_type}
        resource = self.resource(_doc['_id'])

        (resp, result) = resource.put(filename, data=content,
            params={'rev': _doc['_rev']}, headers=headers)

        if resp.status_code < 206:
            _doc['_rev'] = result['rev']
            return _doc

        raise Conflict(result['reason'])

    def one(self, name, flat=None, wrapper=None, **kwargs):
        """
        Execute a design document view query and returns a firts
        result.

        :param name: name of the view (eg: docidname/viewname).
        :param wrapper: wrap result into a specific class.
        :param flat: get a specific field from a object instead of a complete object.

        .. versionadded: 1.4

        :returns: object or None
        """

        params = copy.copy(kwargs)
        params["limit"] = 1

        path = utils._path_from_name(name, '_view')
        data = None

        if "keys" in params:
            data = {"keys": params.pop('keys')}

        if data:
            data = utils.to_json(data).encode("utf-8")

        params = utils._encode_view_options(params)
        result = list(self._query(self.resource(*path), wrapper=wrapper,
                           flat=flat, params=params, data=data))

        return result[0] if len(result) > 0 else None


    def _query(self, resource, data=None, params={}, headers={},
               flat=None, wrapper=None):

        if data is None:
            (resp, result) = resource.get(params=params, headers=headers)
        else:
            (resp, result) = resource.post(data=data, params=params, headers=headers)

        if wrapper is None:
            wrapper = lambda row: row

        if flat is not None:
            wrapper = lambda row: row[flat]

        resp.raise_for_status()

        for row in result["rows"]:
            yield wrapper(row)

    def temporary_query(self, map_func, reduce_func=None, language='javascript',
                        wrapper=None, as_list=False, **kwargs):
        """
        Execute a temporary view.

        :param map_func: unicode string with a map function definition.
        :param reduce_func: unicode string with a reduce function definition.
        :param language: language used for define above functions.
        :param wrapper: wrap result into a specific class.
        :param as_list: return a list of results instead of a default lazy generator.
        :param flat: get a specific field from a object instead of a complete object.

        .. versionchanged: 1.4
           Add as_list parameter.
           Add flat parameter.

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

        result = self._query(self.resource("_temp_view"), params=params,
                             data=data, wrapper=wrapper)
        if as_list:
            return list(result)
        return result


    def query(self, name, wrapper=None, flat=None, as_list=False, **kwargs):
        """
        Execute a design document view query.

        :param name: name of the view (eg: docidname/viewname).
        :param wrapper: wrap result into a specific class.
        :param as_list: return a list of results instead of a default lazy generator.
        :param flat: get a specific field from a object instead of a complete object.

        .. versionadded: 1.4
           Add as_list parameter.
           Add flat parameter.

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
        result =  self._query(self.resource(*path), wrapper=wrapper,
                              flat=flat, params=params, data=data)

        if as_list:
            return list(result)
        return result
