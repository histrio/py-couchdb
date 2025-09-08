"""
Unit tests for pycouchdb.exceptions module.
"""

import pytest
from pycouchdb import exceptions


class TestExceptions:
    """Test exception classes and their inheritance."""

    def test_error_base_class(self):
        """Test that Error is the base exception class."""
        assert issubclass(exceptions.Error, Exception)
        
        with pytest.raises(exceptions.Error):
            raise exceptions.Error("test error")

    def test_unexpected_error(self):
        """Test UnexpectedError exception."""
        assert issubclass(exceptions.UnexpectedError, exceptions.Error)
        
        with pytest.raises(exceptions.UnexpectedError):
            raise exceptions.UnexpectedError("unexpected error")

    def test_feed_reader_exited(self):
        """Test FeedReaderExited exception."""
        assert issubclass(exceptions.FeedReaderExited, exceptions.Error)
        
        with pytest.raises(exceptions.FeedReaderExited):
            raise exceptions.FeedReaderExited()

    def test_api_error(self):
        """Test ApiError exception."""
        assert issubclass(exceptions.ApiError, exceptions.Error)
        
        with pytest.raises(exceptions.ApiError):
            raise exceptions.ApiError("api error")

    def test_generic_error(self):
        """Test GenericError exception."""
        assert issubclass(exceptions.GenericError, exceptions.ApiError)
        
        with pytest.raises(exceptions.GenericError):
            raise exceptions.GenericError("generic error")

    def test_conflict_error(self):
        """Test Conflict exception."""
        assert issubclass(exceptions.Conflict, exceptions.ApiError)
        
        with pytest.raises(exceptions.Conflict):
            raise exceptions.Conflict("conflict error")

    def test_not_found_error(self):
        """Test NotFound exception."""
        assert issubclass(exceptions.NotFound, exceptions.ApiError)
        
        with pytest.raises(exceptions.NotFound):
            raise exceptions.NotFound("not found error")

    def test_bad_request_error(self):
        """Test BadRequest exception."""
        assert issubclass(exceptions.BadRequest, exceptions.ApiError)
        
        with pytest.raises(exceptions.BadRequest):
            raise exceptions.BadRequest("bad request error")

    def test_authentication_failed_error(self):
        """Test AuthenticationFailed exception."""
        assert issubclass(exceptions.AuthenticationFailed, exceptions.ApiError)
        
        with pytest.raises(exceptions.AuthenticationFailed):
            raise exceptions.AuthenticationFailed("auth failed error")

    def test_exception_message_preservation(self):
        """Test that exception messages are preserved."""
        message = "Custom error message"
        
        with pytest.raises(exceptions.Error, match=message):
            raise exceptions.Error(message)
            
        with pytest.raises(exceptions.Conflict, match=message):
            raise exceptions.Conflict(message)