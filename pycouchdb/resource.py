# -*- coding: utf-8 -*-

import requests
import exceptions
from . import utils


class Resource(object):
    def __init__(self, base_url, full_commit=True, session=None, credentials=None, authmethod="session"):
        self.base_url = base_url

        if not session:
            self.session = requests.session()

            self.session.headers.update({"accept": "application/json",
                                         "content-type": "application/json"})
            self._authenticate(credentials, authmethod)

            if not full_commit:
                self.session.headers.update({'X-Couch-Full-Commit': 'false'})
        else:
            self.session = session

    def _authenticate(self, credentials, method):
        if not credentials:
            return

        if method == "session":
            data = {"name": credentials[0], "password": credentials[1]}
            data = utils.to_json(data).encode('utf-8')

            post_url = utils.urljoin(self.base_url, "_session")
            r = self.session.post(post_url, data=data)
            if r.status_code != 200:
                raise AuthenticationFailed()

        elif method == "basic":
            self.session.auth = credentials

        else:
            raise RuntimeError("Invalid authentication method")

    def __call__(self, *path):
        base_url = utils.urljoin(self.base_url, *path)
        return self.__class__(base_url, session=self.session)

    def check_result(self, resp, result):
      if ('error' in result):
        print "[DEBUG] pycouchdb resp: %s error: %s" % (resp, result)
        error  = result.get('error', None)
        reason = result.get('reason', None)
        if error == u'not_found':
          raise exceptions.NotFound(reason)
        elif error == u'conflict':
          raise exceptions.Conflict(reason)
        elif error == u'bad_request':
          raise exceptions.BadRequest(reason)
        else:
          # TODO: Make an error class for all possible errors.
          raise exceptions.GenericError(result)
    def request(self, method, path, params=None, data=None, headers={}, **kwargs):
        if path:
            if not isinstance(path, (list, tuple)):
                path = [path]
            url = utils.urljoin(self.base_url, *path)
        else:
            url = self.base_url

        headers.setdefault('Accept', 'application/json')
        
        resp = self.session.request(method, url, data=data, params=params, headers=headers, **kwargs)
        result = utils.as_json(resp)
        print "[DEBUG] pycouchdb, resp: %s, result: %s" % (resp, result)
        if type(result) is list:
          for res in result:
            self.check_result(resp, res)
        else:
          self.check_result(resp, result)
        return (resp, result)

    def get(self, path=None, **kwargs):
        return self.request("GET", path, **kwargs)

    def put(self, path=None, **kwargs):
        return self.request("PUT", path, **kwargs)

    def post(self, path=None, **kwargs):
        return self.request("POST", path, **kwargs)

    def delete(self, path=None, **kwargs):
        return self.request("DELETE", path, **kwargs)

    def head(self, path=None, **kwargs):
        return self.request("HEAD", path, **kwargs)

