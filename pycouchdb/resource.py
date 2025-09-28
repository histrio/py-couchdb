# -*- coding: utf-8 -*-

import json
import requests
from typing import Optional, Tuple, Any, Dict, List, Union

from . import utils
from . import exceptions
from .types import Credentials, AuthMethod

# Type aliases for cleaner HTTP method signatures
HttpPath = Optional[Union[str, List[str]]]
HttpParams = Optional[Dict[str, Any]]
HttpHeaders = Optional[Dict[str, str]]
HttpResponse = Tuple[requests.Response, Optional[Any]]


class Resource:
    def __init__(self, base_url: str, full_commit: bool = True, session: Optional[requests.Session] = None,
                 credentials: Optional[Credentials] = None, authmethod: AuthMethod = "session", verify: bool = False) -> None:

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

    def _authenticate(self, credentials: Optional[Credentials], method: AuthMethod) -> None:
        if not credentials:
            return

        if method == "session":
            data_dict = {"name": credentials[0], "password": credentials[1]}
            data = utils.force_bytes(json.dumps(data_dict))

            post_url = utils.urljoin(self.base_url, "_session")
            r = self.session.post(post_url, data=data)
            if r.status_code != 200:
                raise exceptions.AuthenticationFailed()

        elif method == "basic":
            self.session.auth = credentials

        else:
            raise RuntimeError("Invalid authentication method")

    def __call__(self, *path: str) -> "Resource":
        base_url = utils.urljoin(self.base_url, *path)
        return self.__class__(base_url, session=self.session)

    def _check_result(self, response: requests.Response, result: Optional[Any]) -> None:
        try:
            error = result.get('error', None) if result else None
            reason = result.get('reason', None) if result else None
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

    def request(self, method: str, path: HttpPath = None, params: HttpParams = None, 
                data: Optional[Any] = None, headers: HttpHeaders = None, stream: bool = False, **kwargs: Any) -> HttpResponse:

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

        if stream and response.status_code < 400:
            result = None
            self._check_result(response, result)
        else:
            result = utils.as_json(response)

        if result is None:
            return response, result

        if isinstance(result, list):
            for res in result:
                self._check_result(response, res)
        else:
            self._check_result(response, result)

        return response, result

    def get(self, path: HttpPath = None, **kwargs: Any) -> HttpResponse:
        return self.request("GET", path, **kwargs)

    def put(self, path: HttpPath = None, **kwargs: Any) -> HttpResponse:
        return self.request("PUT", path, **kwargs)

    def post(self, path: HttpPath = None, **kwargs: Any) -> HttpResponse:
        return self.request("POST", path, **kwargs)

    def delete(self, path: HttpPath = None, **kwargs: Any) -> HttpResponse:
        return self.request("DELETE", path, **kwargs)

    def head(self, path: HttpPath = None, **kwargs: Any) -> HttpResponse:
        return self.request("HEAD", path, **kwargs)
