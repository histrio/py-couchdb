"""
Unit tests for pycouchdb.resource module.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pycouchdb import resource, exceptions


class TestResource:
    """Test Resource class."""

    def test_resource_initialization_without_session(self):
        """Test Resource initialization without existing session."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            res = resource.Resource("http://localhost:5984/")
            
            assert res.base_url == "http://localhost:5984/"
            assert res.session == mock_session_instance
            assert res.session.verify is False
            mock_session_instance.headers.update.assert_called_with({
                "accept": "application/json",
                "content-type": "application/json"
            })

    def test_resource_initialization_with_session(self):
        """Test Resource initialization with existing session."""
        mock_session = Mock()
        mock_session.verify = True
        
        res = resource.Resource("http://localhost:5984/", session=mock_session, verify=True)
        
        assert res.base_url == "http://localhost:5984/"
        assert res.session == mock_session
        assert res.session.verify is True

    def test_resource_initialization_with_credentials_basic(self):
        """Test Resource initialization with basic auth credentials."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            credentials = ("user", "password")
            res = resource.Resource("http://localhost:5984/", 
                                  credentials=credentials, 
                                  authmethod="basic")
            
            assert res.session.auth == credentials

    def test_resource_initialization_with_credentials_session(self):
        """Test Resource initialization with session auth credentials."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            # Mock successful authentication
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'application/json'}
            mock_session_instance.post.return_value = mock_response
            
            credentials = ("user", "password")
            res = resource.Resource("http://localhost:5984/", 
                                  credentials=credentials, 
                                  authmethod="session")
            
            # Verify session authentication was called
            mock_session_instance.post.assert_called_once()
            call_args = mock_session_instance.post.call_args
            assert "_session" in call_args[0][0]

    def test_resource_initialization_with_credentials_session_failure(self):
        """Test Resource initialization with failed session auth."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            # Mock failed authentication
            mock_response = Mock()
            mock_response.status_code = 401
            mock_session_instance.post.return_value = mock_response
            
            credentials = ("user", "password")
            
            with pytest.raises(exceptions.AuthenticationFailed):
                resource.Resource("http://localhost:5984/", 
                                credentials=credentials, 
                                authmethod="session")

    def test_resource_initialization_invalid_auth_method(self):
        """Test Resource initialization with invalid auth method."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            credentials = ("user", "password")
            
            with pytest.raises(RuntimeError, match="Invalid authentication method"):
                resource.Resource("http://localhost:5984/", 
                                credentials=credentials, 
                                authmethod="invalid")

    def test_resource_initialization_full_commit_false(self):
        """Test Resource initialization with full_commit=False."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            res = resource.Resource("http://localhost:5984/", full_commit=False)
            
            # Verify full commit header was set
            calls = mock_session_instance.headers.update.call_args_list
            assert any('X-Couch-Full-Commit' in str(call) for call in calls)

    def test_resource_call(self):
        """Test Resource __call__ method."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            res = resource.Resource("http://localhost:5984/")
            new_res = res("db", "doc")
            
            assert isinstance(new_res, resource.Resource)
            assert new_res.base_url == "http://localhost:5984/db/doc"
            assert new_res.session == mock_session_instance

    def test_resource_request_get(self):
        """Test Resource request method with GET."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.content = b'{"result": "success"}'
            mock_response.json.return_value = {"result": "success"}
            mock_session_instance.request.return_value = mock_response
            
            res = resource.Resource("http://localhost:5984/")
            response, result = res.request("GET", "test")
            
            assert response == mock_response
            assert result == {"result": "success"}
            mock_session_instance.request.assert_called_once()

    def test_resource_request_with_stream(self):
        """Test Resource request method with stream=True."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'application/json'}
            mock_session_instance.request.return_value = mock_response
            
            res = resource.Resource("http://localhost:5984/")
            response, result = res.request("GET", "test", stream=True)
            
            assert response == mock_response
            assert result is None  # Should be None for stream requests

    def test_resource_request_with_conflict_error(self):
        """Test Resource request method with conflict error."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            # Mock conflict response
            mock_response = Mock()
            mock_response.status_code = 409
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.content = b'{"error": "conflict", "reason": "Document conflict"}'
            mock_response.json.return_value = {"error": "conflict", "reason": "Document conflict"}
            mock_session_instance.request.return_value = mock_response
            
            res = resource.Resource("http://localhost:5984/")
            
            with pytest.raises(exceptions.Conflict, match="Document conflict"):
                res.request("PUT", "test")

    def test_resource_request_with_not_found_error(self):
        """Test Resource request method with not found error."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            # Mock not found response
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.content = b'{"error": "not_found", "reason": "Document not found"}'
            mock_response.json.return_value = {"error": "not_found", "reason": "Document not found"}
            mock_session_instance.request.return_value = mock_response
            
            res = resource.Resource("http://localhost:5984/")
            
            with pytest.raises(exceptions.NotFound, match="Document not found"):
                res.request("GET", "test")

    def test_resource_request_with_bad_request_error(self):
        """Test Resource request method with bad request error."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            # Mock bad request response
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.content = b'{"error": "bad_request", "reason": "Invalid request"}'
            mock_response.json.return_value = {"error": "bad_request", "reason": "Invalid request"}
            mock_session_instance.request.return_value = mock_response
            
            res = resource.Resource("http://localhost:5984/")
            
            with pytest.raises(exceptions.BadRequest, match="Invalid request"):
                res.request("POST", "test")

    def test_resource_request_with_generic_error(self):
        """Test Resource request method with generic error."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            # Mock generic error response
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.content = b'{"error": "unknown", "reason": "Server error"}'
            mock_response.json.return_value = {"error": "unknown", "reason": "Server error"}
            mock_session_instance.request.return_value = mock_response
            
            res = resource.Resource("http://localhost:5984/")
            
            with pytest.raises(exceptions.GenericError):
                res.request("GET", "test")

    def test_resource_request_with_list_result(self):
        """Test Resource request method with list result containing errors."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            # Mock response with list containing errors
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.content = b'[{"id": "doc1", "rev": "1-abc"}, {"error": "conflict", "reason": "Document conflict"}]'
            mock_response.json.return_value = [
                {"id": "doc1", "rev": "1-abc"},
                {"error": "conflict", "reason": "Document conflict"}
            ]
            mock_session_instance.request.return_value = mock_response
            
            res = resource.Resource("http://localhost:5984/")
            
            with pytest.raises(exceptions.Conflict, match="Document conflict"):
                res.request("POST", "test")

    def test_resource_http_methods(self):
        """Test Resource HTTP method shortcuts."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.content = b'{"result": "success"}'
            mock_response.json.return_value = {"result": "success"}
            mock_session_instance.request.return_value = mock_response
            
            res = resource.Resource("http://localhost:5984/")
            
            # Test GET
            res.get("test")
            mock_session_instance.request.assert_called_with("GET", "http://localhost:5984/test", 
                                                           stream=False, data=None, params=None, 
                                                           headers={'Accept': 'application/json'})
            
            # Test PUT
            res.put("test", data='{"test": "data"}')
            mock_session_instance.request.assert_called_with("PUT", "http://localhost:5984/test", 
                                                           stream=False, data='{"test": "data"}', 
                                                           params=None, headers={'Accept': 'application/json'})
            
            # Test POST
            res.post("test", data='{"test": "data"}')
            mock_session_instance.request.assert_called_with("POST", "http://localhost:5984/test", 
                                                           stream=False, data='{"test": "data"}', 
                                                           params=None, headers={'Accept': 'application/json'})
            
            # Test DELETE
            res.delete("test")
            mock_session_instance.request.assert_called_with("DELETE", "http://localhost:5984/test", 
                                                           stream=False, data=None, params=None, 
                                                           headers={'Accept': 'application/json'})
            
            # Test HEAD
            res.head("test")
            mock_session_instance.request.assert_called_with("HEAD", "http://localhost:5984/test", 
                                                           stream=False, data=None, params=None, 
                                                           headers={'Accept': 'application/json'})

    def test_resource_request_with_custom_headers(self):
        """Test Resource request method with custom headers."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.content = b'{"result": "success"}'
            mock_response.json.return_value = {"result": "success"}
            mock_session_instance.request.return_value = mock_response
            
            res = resource.Resource("http://localhost:5984/")
            custom_headers = {"Custom-Header": "value"}
            
            res.request("GET", "test", headers=custom_headers)
            
            expected_headers = {"Accept": "application/json", "Custom-Header": "value"}
            mock_session_instance.request.assert_called_with("GET", "http://localhost:5984/test", 
                                                           stream=False, data=None, params=None, 
                                                           headers=expected_headers)

    def test_resource_request_with_params(self):
        """Test Resource request method with parameters."""
        with patch('pycouchdb.resource.requests.session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.content = b'{"result": "success"}'
            mock_response.json.return_value = {"result": "success"}
            mock_session_instance.request.return_value = mock_response
            
            res = resource.Resource("http://localhost:5984/")
            params = {"limit": 10, "skip": 5}
            
            res.request("GET", "test", params=params)
            
            mock_session_instance.request.assert_called_with("GET", "http://localhost:5984/test", 
                                                           stream=False, data=None, params=params, 
                                                           headers={'Accept': 'application/json'})