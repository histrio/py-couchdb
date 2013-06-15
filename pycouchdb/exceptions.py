# -*- coding: utf-8 -*-


class Conflict(Exception):
    pass

class GenericError(Exception):
    pass

class NotFound(Exception):
    pass

class BadRequest(Exception):
    pass

class AuthenticationFailed(Exception):
    pass
