# -*- coding: utf-8 -*-

from typing import Final


class Error(Exception):
    """Base exception class for all pycouchdb errors."""
    pass


class UnexpectedError(Error):
    """Raised when an unexpected error occurs."""
    pass


class FeedReaderExited(Error):
    """Raised when a feed reader exits unexpectedly."""
    pass


class ApiError(Error):
    """Base class for API-related errors."""
    pass


class GenericError(ApiError):
    """Raised for generic API errors."""
    pass


class Conflict(ApiError):
    """Raised when a conflict occurs (e.g., document revision conflict)."""
    pass


class NotFound(ApiError):
    """Raised when a resource is not found."""
    pass


class BadRequest(ApiError):
    """Raised when a bad request is made."""
    pass


class AuthenticationFailed(ApiError):
    """Raised when authentication fails."""
    pass
