# -*- coding: utf-8 -*-

import json
import time
import requests
from typing import Optional, Tuple, Any, Dict, List, Sequence, Union

from . import utils
from . import exceptions
from .types import Credentials, AuthMethod
from ._logging import logger, parameter_names, response_size, safe_path

# Type aliases for cleaner HTTP method signatures
HttpPath = Optional[Union[str, List[str]]]
HttpParams = Optional[Union[Dict[str, Any], Sequence[Tuple[str, Any]]]]
HttpHeaders = Optional[Dict[str, str]]
HttpResponse = Tuple[requests.Response, Optional[Any]]


class Resource:
    def __init__(self, base_url: str, full_commit: bool = True, session: Optional[requests.Session] = None,
                 credentials: Optional[Credentials] = None, authmethod: AuthMethod = "session", verify: bool = False,
                 timeout: Optional[float] = None) -> None:

        self.base_url = base_url
        self.timeout = timeout
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
            r = self.session.post(post_url, data=data, timeout=self.timeout)
            if r.status_code != 200:
                raise exceptions.AuthenticationFailed()

        elif method == "basic":
            self.session.auth = credentials

        else:
            raise RuntimeError("Invalid authentication method")

    def __call__(self, *path: str) -> "Resource":
        base_url = utils.urljoin(self.base_url, *path)
        return self.__class__(base_url, session=self.session, timeout=self.timeout)

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
                data: Optional[Any] = None, headers: HttpHeaders = None,
                stream: bool = False, **kwargs: Any) -> HttpResponse:
        response, result = self._request_response(
            method, path, params, data, headers, stream, **kwargs)

        if result is None:
            return response, result

        if isinstance(result, list):
            for res in result:
                self._check_result(response, res)
        else:
            self._check_result(response, result)

        return response, result

    def _request_response(self, method: str, path: HttpPath = None,
                          params: HttpParams = None, data: Optional[Any] = None,
                          headers: HttpHeaders = None, stream: bool = False,
                          **kwargs: Any) -> HttpResponse:
        """Dispatch a request and parse its response without validation.

        Bulk endpoints use this private primitive to log their aggregate result
        before preserving the normal validation and exception behaviour.
        """

        if headers is None:
            headers = {}

        headers.setdefault('Accept', 'application/json')

        if path:
            if not isinstance(path, (list, tuple)):
                path = [path]
            url = utils.urljoin(self.base_url, *path)
        else:
            url = self.base_url

        # Add timeout to kwargs if not already specified
        if self.timeout is not None and 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout

        log_path = safe_path(url)
        param_names = parameter_names(params) if params is not None else ()
        logger.debug("http request method=%s path=%s param_keys=%r",
                     method, log_path, param_names)
        start = time.perf_counter()
        try:
            response = self.session.request(method, url, stream=stream,
                                            data=data, params=params,
                                            headers=headers, **kwargs)
        except Exception as error:
            elapsed = (time.perf_counter() - start) * 1000.0
            logger.debug("http error method=%s path=%s elapsed_ms=%.1f error=%s",
                         method, log_path, elapsed, type(error).__name__)
            raise

        elapsed = (time.perf_counter() - start) * 1000.0
        logger.debug("http response method=%s path=%s status=%s elapsed_ms=%.1f response_bytes=%s",
                     method, log_path, response.status_code, elapsed,
                     response_size(response.headers))
        # Ignore result validation if
        # request is with stream mode

        if stream and response.status_code < 400:
            result = None
            self._check_result(response, result)
        else:
            result = utils.as_json(response)

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
