# -*- coding: utf-8 -*-

import os
import requests
import json
import uuid
import copy
import mimetypes

from . import utils
from .resource import Resource
from .exceptions import ConflictException, NotFound

DEFAULT_BASE_URL = os.environ.get('COUCHDB_URL', 'http://localhost:5984/')


class Server(object):
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
        r = self.resource.get()
        return utils.as_json(r)

    def delete(self, name):
        r = self.resource.delete(name)
        if r.status_code == 404:
            raise NotFound("database {0} not found".format(name))

    def database(self, name):
        db = Database(self.resource(name), name)
        return db

    def config(self):
        r = self.resource.get("_config")
        return utils.as_json(r)

    def version(self):
        r = self.resource.get()
        return utils.as_json(r)["version"]

    def stats(self, name=None):
        if not name:
            r = self.resource.get("_stats")
            return utils.as_json(r)

        resource = self.resource("_stats", "couchdb")
        r = resource.get(name)
        data = utils.as_json(r)
        return data['couchdb'][name]

    def create(self, name):
        r = self.resource.put(name)
        return self.database(name)


def _id_to_path(id):
    if id[:1] == "_":
        return id.split("/", 1)
    return [id]


class Database(object):
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
        resource = self.resource(*_id_to_path(id))

        r = resource.head()
        if r.status_code > 205:
            raise NotFound("doc not found")

        r = resource.delete(params={"rev": r.headers["etag"].strip('"')})
        return r.status_code < 205

    def get(self, id, params={}):
        r = self.resource(*_id_to_path(id)).get(params=params)
        return utils.as_json(r)

    def save(self, doc):
        if "_id" not in doc:
            doc['_id'] = uuid.uuid4().hex

        data = utils.to_json(doc).encode('utf-8')
        r = self.resource(doc['_id']).put(data=data)
        d = utils.as_json(r)

        if r.status_code == 409:
            raise ConflictException(d['reason'])

        if "rev" in d and d["rev"] is not None:
            doc["_rev"] = d["rev"]

        return d['ok']

    def save_bulk(self, docs, transaction=True):
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
        r = self.resource('_view_cleanup').post()
        return utils.as_json(r)

    def commit(self):
        r = self.resource.post('_ensure_full_commit')
        return utils.as_json(r)

    def conflicts(self, id):
        r = self.resource.get(id, params={"conflicts": "true"})
        return utils.as_json(r)

    def compact(self):
        r = self.resource("_compact").post()
        return utils.as_json(r)

    def compact_view(self, ddoc):
        r = self.resource("_compact", ddoc).post()
        if r.status_code == 404:
            raise NotFound("view {0} not found".format(ddoc))
        return utils.as_json(r)

    def revisions(self, id, params={}):
        resource = self.resource(id)
        r = resource.get(params={'revs_info': 'true'})
        if r.status_code == 404:
            raise NotFound("docid {0} not found".format(id))

        data = utils.as_json(r)
        for rev in data['_revs_info']:
            if rev['status'] == 'available':
                yield self.get(id, params=params)

    def delete_attachment(self, doc, filename):
        resource = self.resource(doc['_id'])
        r = resource.delete(filename, params={'rev': doc['_rev']})
        data = utils.as_json(r)

        doc['_rev'] = data['rev']
        return data['ok']

    def get_attachment(self, doc, filename):
        r = self.resource(doc['_id']).get(filename, stream=False)
        return r.content

    def put_attachment(self, doc, content, filename=None, content_type=None):
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
        params = copy.copy(kwargs)
        path = utils._path_from_name(name, '_view')
        data = None

        if "keys" in params:
            data = {"keys": params.pop('keys')}

        if data:
            data = utils.to_json(data).encode("utf-8")

        params = utils._encode_view_options(params)
        return self._query(self.resource(*path), wrapper=wrapper, params=params, data=data)
