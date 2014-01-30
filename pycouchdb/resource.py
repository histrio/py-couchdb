# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import requests

from . import utils
from . import exceptions


class Resource(object):
    def __init__(self, base_url, full_commit=True, session=None,
                 credentials=None, authmethod="session", verify=False):

        self.base_url = base_url
#        self.verify = verify

        if not session:
            self.session = requests.session()

            self.session.headers.update({"accept": "application/json",
                                         "content-type": "application/json"})
            self._authenticate(credentials, authmethod)

            if not full_commit:
                self.session.headers.update({'X-Couch-Full-Commit': 'false'})
        else:
            self.session = session
        self.session.verify = verify

    def _authenticate(self, credentials, method):
        if not credentials:
            return

        if method == "session":
            data = {"name": credentials[0], "password": credentials[1]}
            data = utils.force_bytes(utils.to_json(data))

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

    def check_result(self, response, result):
        try:
            error = result.get('error', None)
            reason = result.get('reason', None)
        except AttributeError:
            error = None
            reason = ''

        # This is here because couchdb can return http 201
        # but containing a list of conflict errors
        if error == 'conflict' or error == "file_exists":
            raise exceptions.Conflict(reason or "Conflict")

        if response.status_code > 205:
            if response.status_code == 404 or error == 'not_found':
                raise exceptions.NotFound(reason or 'Not found')
            elif error == 'bad_request':
                raise exceptions.BadRequest(reason or "Bad request")
            raise exceptions.GenericError(result)

    def request(self, method, path, params=None, data=None,
                headers=None, stream=False, **kwargs):

        if headers is None:
            headers = {}

        headers.setdefault('Accept', 'application/json')

        if path:
            if not isinstance(path, (list, tuple)):
                path = [path]
            url = utils.urljoin(self.base_url, *path)
        else:
            url = self.base_url

        response = self.session.request(method, url, stream=stream,
                                        data=data, params=params,
                                        headers=headers, **kwargs)
        # Ignore result validation if
        # request is with stream mode

        if stream:
            result = None
            self.check_result(response, result)
        else:
            result = utils.as_json(response)

        if result is None:
            return (response, result)

        if isinstance(result, list):
            for res in result:
                self.check_result(response, res)
        else:
            self.check_result(response, result)

        return (response, result)

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
