# -*- coding: utf-8 -*-

import os
import json
import uuid
import copy
import mimetypes
import warnings

from . import utils
from . import feedreader
from . import exceptions as exp
from .resource import Resource


DEFAULT_BASE_URL = os.environ.get('COUCHDB_URL', 'http://localhost:5984/')


def _id_to_path(id):
    if id[:1] == "_":
        return id.split("/", 1)
    return [id]


class _StreamResponse(object):
    """
    Proxy object for python-requests stream response.

    See more on: http://docs.python-requests.org/en/latest/user/advanced/#streaming-requests
    """
    def __init__(self, response):
        self._response = response

    def iter_content(self, chunk_size=1, decode_unicode=False):
        return self._response.iter_content(chunk_size=chunk_size,
                                           decode_unicode=decode_unicode)

    def iter_lines(self, chunk_size=512, decode_unicode=None):
        return self._response.iter_lines(chunk_size=chunk_size,
                                         decode_unicode=decode_unicode)

    @property
    def raw(self):
        return self._response.raw

    @property
    def url(self):
        return self._response.url


class Server(object):
    """
    Class that represents a couchdb connection.

    :param verify: setup ssl verifycation.
    :param base_url: a full url to couchdb (can contain auth data).
    :param full_commit: If ``False``, couchdb not commits all data on a
                        request is finished.
    :param authmethod: specify a authentication method. By default "basic"
                       method is used but also exists "session" (that requires
                       some server configuration changes).

    .. versionchanged: 1.4
       Set basic auth method as default instead of session method.

    .. versionchanged: 1.5
        Add verify parameter for setup ssl verifycaton

    """

    def __init__(self, base_url=DEFAULT_BASE_URL, full_commit=True,
                 authmethod="basic", verify=False):

        self.base_url, credentials = utils._extract_credentials(base_url)
        self.resource = Resource(self.base_url, full_commit,
                                 credentials=credentials,
                                 authmethod=authmethod,
                                 verify=verify)

    def __contains__(self, name):
        try:
            self.resource.head(name)
        except exp.NotFound:
            return False
        else:
            return True

    def __iter__(self):
        (r, result) = self.resource.get('_all_dbs')
        return iter(result)

    def __len__(self):
        (r, result) = self.resource.get('_all_dbs')
        return len(result)

    def info(self):
        """
        Get server info.

        :returns: dict with all data that couchdb returns.
        :rtype: dict
        """
        (r, result) = self.resource.get()
        return result

    def delete(self, name):
        """
        Delete some database.

        :param name: database name
        :raises: :py:exc:`~pycouchdb.exceptions.NotFound` if a database does not exists
        """

        self.resource.delete(name)

    def database(self, name):
        """
        Get a database instance.

        :param name: database name
        :raises: :py:exc:`~pycouchdb.exceptions.NotFound` if a database does not exists

        :returns: a :py:class:`~pycouchdb.client.Database` instance
        """
        (r, result) = self.resource.head(name)
        if r.status_code == 404:
            raise exp.NotFound("Database '{0}' does not exists".format(name))

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
        (r, result) = resource.get(name)
        return result['couchdb'][name]

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

        data = {'source': source, 'target': target}
        data.update(kwargs)

        data = utils.force_bytes(utils.to_json(data))

        (resp, result) = self.resource.post('_replicate', data=data)
        return result


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
        :raises: :py:exc:`~pycouchdb.exceptions.NotFound` if a document
                 not exists
        :raises: :py:exc:`~pycouchdb.exceptions.Conflict` if delete with
                 wrong revision.
        """

        _id = None
        if isinstance(doc_or_id, dict):
            if "_id" not in doc_or_id:
                raise ValueError("Invalid document, missing _id attr")
            _id = doc_or_id['_id']
        else:
            _id = doc_or_id

        resource = self.resource(*_id_to_path(_id))

        (r, result) = resource.head()
        (r, result) = resource.delete(params={"rev": r.headers["etag"].strip('"')})

    def delete_bulk(self, docs, transaction=True):
        """
        Delete a bulk of documents.

        .. versionadded:: 1.2

        :param docs: list of docs
        :raises: :py:exc:`~pycouchdb.exceptions.Conflict` if a delete
                 is not success
        :returns: raw results from server
        """

        _docs = copy.copy(docs)
        for doc in _docs:
            if "_deleted" not in doc:
                doc["_deleted"] = True

        data = utils.force_bytes(utils.to_json({"docs" : _docs}))
        params = {"all_or_nothing": "true" if transaction else "false"}
        (resp, results) = self.resource.post("_bulk_docs", data=data, params=params)

        for result, doc in zip(results, _docs):
          if "error" in result:
            raise exp.Conflict("one or more docs are not saved")

        return results

    def get(self, id, params=None, **kwargs):
        """
        Get a document by id.

        .. versionadded: 1.5
            Now the prefered method to pass params is via **kwargs
            instead of params argument. **params** argument is now
            deprecated and will be deleted in future versions.

        :param id: document id
        :raises: :py:exc:`~pycouchdb.exceptions.NotFound` if a document
                 not exists

        :returns: document (dict)
        """

        if params:
            warnings.warn("params parameter is now deprecated in favor to"
                          "**kwargs usage.", DeprecationWarning)

        if params is None:
            params = {}

        params.update(kwargs)

        (resp, result) = self.resource(*_id_to_path(id)).get(params=params)
        return result

    def save(self, doc):
        """
        Save or update a document.

        .. versionchanged:: 1.2
            Now returns a new document instead of modify the original.

        :param doc: document
        :raises: :py:exc:`~pycouchdb.exceptions.Conflict` if save with wrong
                 revision.
        :returns: doc
        """

        _doc = copy.copy(doc)
        if "_id" not in _doc:
            _doc['_id'] = uuid.uuid4().hex

        data = utils.force_bytes(utils.to_json(_doc))
        (resp, result) = self.resource(_doc['_id']).put(data=data)

        if resp.status_code == 409:
            raise exp.Conflict(result['reason'])

        if "rev" in result and result["rev"] is not None:
            _doc["_rev"] = result["rev"]

        return _doc

    def save_bulk(self, docs, transaction=True):
        """
        Save a bulk of documents.

        .. versionchanged:: 1.2
            Now returns a new document list instead of modify the original.

        :param docs: list of docs
        :param transaction: if ``True``, couchdb do a insert in transaction
                            model.
        :returns: docs
        """

        _docs = copy.deepcopy(docs)

        # Insert _id field if it not exists
        for doc in _docs:
            if "_id" not in doc:
                doc["_id"] = uuid.uuid4().hex

        data = utils.force_bytes(utils.to_json({"docs": _docs}))
        params = {"all_or_nothing": "true" if transaction else "false"}

        (resp, results) = self.resource.post("_bulk_docs", data=data,
                                             params=params)

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

        params = {"include_docs": "true"}
        params.update(kwargs)

        data = None

        if "keys" in params:
            data = {"keys": params.pop("keys")}
            data = utils.force_bytes(utils.to_json(data))

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

        def _iterate_no_docs():
            for row in result["rows"]:
                doc = {"id": row['id'], "rev": row['value']['rev']}
                yield wrapper(doc)

        if params["include_docs"].upper() == "FALSE":
            if as_list:
                return list(_iterate_no_docs())
            return _iterate_no_docs()

        if as_list:
            return list(_iterate())
        return _iterate()

    def cleanup(self):
        """
        Execute a cleanup operation.
        """
        (r, result) = self.resource('_view_cleanup').post()
        return result

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
        (r, result) = self.resource("_compact").post()
        return result

    def compact_view(self, ddoc):
        """
        Execute compact over design view.

        :raises: :py:exc:`~pycouchdb.exceptions.NotFound` if a view does not exists.
        """
        (r, result) = self.resource("_compact", ddoc).post()
        return result

    def revisions(self, id, status='available', params=None, **kwargs):
        """
        Get all revisions of one document.

        :param id:      document id
        :param status:  filter of reverion status, set empty to list all
        :raises: :py:exc:`~pycouchdb.exceptions.NotFound` if a view does not exists.

        :returns: generator object
        """
        if params:
            warnings.warn("params parameter is now deprecated in favor to"
                          "**kwargs usage.", DeprecationWarning)

        if params is None:
            params = {}

        params.update(kwargs)

        if not params.get('revs_info'):
            params['revs_info'] = 'true'

        resource = self.resource(id)
        (resp, result) = resource.get(params=params)
        if resp.status_code == 404:
            raise exp.NotFound("docid {0} not found".format(id))

        for rev in result['_revs_info']:
            if status and rev['status'] == status:
                yield self.get(id, rev=rev['rev'])
            elif not status:
                yield self.get(id, rev=rev['rev'])

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

        _doc = copy.deepcopy(doc)
        resource = self.resource(_doc['_id'])

        (resp, result) = resource.delete(filename, params={'rev': _doc['_rev']})
        if resp.status_code == 404:
            raise exp.NotFound("filename {0} not found".format(filename))

        if resp.status_code > 205:
            raise exp.Conflict(result['reason'])

        _doc['_rev'] = result['rev']
        try:
            del _doc['_attachments'][filename]

            if not _doc['_attachments']:
                del _doc['_attachments']
        except KeyError:
            pass

        return _doc

    def get_attachment(self, doc, filename, stream=False, **kwargs):
        """
        Get attachment by filename from document.

        :param doc: document dict
        :param filename: attachment file name.
        :param stream: setup streaming output (default: False)

        .. versionchanged: 1.5
            Add stream parameter for obtain very large attachments
            without load all file to the memory.

        :returns: binary data or
        """

        params = {"rev": doc["_rev"]}
        params.update(kwargs)

        r, result = self.resource(doc['_id']).get(filename, stream=stream,
                                                  params=params)
        if stream:
            return _StreamResponse(r)

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

        (resp, result) = resource.put(filename, data=content,
            params={'rev': doc['_rev']}, headers=headers)

        if resp.status_code < 206:
            return self.get(doc["_id"])

        raise exp.Conflict(result['reason'])

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

        params = {"limit": 1}
        params.update(kwargs)

        path = utils._path_from_name(name, '_view')
        data = None

        if "keys" in params:
            data = {"keys": params.pop('keys')}

        if data:
            data = utils.force_bytes(utils.to_json(data))

        params = utils._encode_view_options(params)
        result = list(self._query(self.resource(*path), wrapper=wrapper,
                           flat=flat, params=params, data=data))

        return result[0] if len(result) > 0 else None


    def _query(self, resource, data=None, params=None, headers=None,
               flat=None, wrapper=None):

        if data is None:
            (resp, result) = resource.get(params=params, headers=headers)
        else:
            (resp, result) = resource.post(data=data, params=params, headers=headers)

        if wrapper is None:
            wrapper = lambda row: row

        if flat is not None:
            wrapper = lambda row: row[flat]

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
        data = utils.force_bytes(utils.to_json(data))

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
            data = utils.force_bytes(utils.to_json(data))

        params = utils._encode_view_options(params)
        result = self._query(self.resource(*path), wrapper=wrapper,
                              flat=flat, params=params, data=data)

        if as_list:
            return list(result)
        return result

    def changes_feed(self, feed_reader, **kwargs):
        """
        Subscribe to changes feed of couchdb.

        Note: this method is blocking.


        :param feed_reader: callable or :py:class:`~BaseFeedReader`
                            instance

        .. versionadded: 1.5
        """

        if not callable(feed_reader):
            raise exp.UnexpectedError("feed_reader must be callable or class")

        if isinstance(feed_reader, feedreader.BaseFeedReader):
            reader = feed_reader(self)
        else:
            reader = feedreader.SimpleFeedReader()(self, feed_reader)

        # Possible options: "continuous", "longpoll"
        kwargs.setdefault("feed", "continuous")
        kwargs.setdefault("since", 1)

        (resp, result) = self.resource("_changes").get(params=kwargs, stream=True)
        try:
            for line in resp.iter_lines(chunk_size=1):
                reader.on_message(json.loads(utils.force_text(line)))
        except exp.FeedReaderExited as e:
            reader.on_close()

    def changes_list(self, **kwargs):
        """
        Obtain a list of changes from couchdb.

        .. versionadded: 1.5
        """

        (resp, result) = self.resource("_changes").get(params=kwargs)
        return result['last_seq'], result['results']
