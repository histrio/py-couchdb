# -*- coding: utf-8 -*-


class Error(Exception):
    pass

class UnexpectedError(Error):
    pass

class FeedReaderExited(Error):
    pass

class ApiError(Error):
    pass

class GenericError(ApiError):
    pass

class Conflict(ApiError):
    pass

class NotFound(ApiError):
    pass

class BadRequest(ApiError):
    pass

class AuthenticationFailed(ApiError):
    pass
