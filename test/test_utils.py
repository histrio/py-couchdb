"""
Unit tests for pycouchdb.utils module.
"""

import json
import pytest
from pycouchdb import utils


class TestUtils:
    """Test utility functions."""

    def test_extract_credentials_no_auth(self):
        """Test extracting credentials from URL without authentication."""
        url = 'http://localhost:5984/_config/'
        clean_url, credentials = utils.extract_credentials(url)
        
        assert clean_url == 'http://localhost:5984/_config/'
        assert credentials is None

    def test_extract_credentials_basic_auth(self):
        """Test extracting credentials from URL with basic authentication."""
        url = 'http://joe:secret@localhost:5984/_config/'
        clean_url, credentials = utils.extract_credentials(url)
        
        assert clean_url == 'http://localhost:5984/_config/'
        assert credentials == ('joe', 'secret')

    def test_extract_credentials_encoded_auth(self):
        """Test extracting credentials from URL with encoded authentication."""
        url = 'http://joe%40example.com:secret@localhost:5984/_config/'
        clean_url, credentials = utils.extract_credentials(url)
        
        assert clean_url == 'http://localhost:5984/_config/'
        assert credentials == ('joe@example.com', 'secret')

    def test_urljoin_simple(self):
        """Test simple URL joining."""
        result = utils.urljoin('http://localhost:5984/', 'test')
        assert result == 'http://localhost:5984/test'

    def test_urljoin_multiple_paths(self):
        """Test URL joining with multiple path segments."""
        result = utils.urljoin('http://localhost:5984/', 'db', 'doc', 'id')
        assert result == 'http://localhost:5984/db/doc/id'

    def test_urljoin_with_trailing_slash(self):
        """Test URL joining with trailing slash in base URL."""
        result = utils.urljoin('http://localhost:5984/', '/test')
        assert result == 'http://localhost:5984/test'

    def test_urljoin_with_leading_slash(self):
        """Test URL joining with leading slash in path."""
        result = utils.urljoin('http://localhost:5984', '/test')
        assert result == 'http://localhost:5984/test'

    def test_urljoin_empty_paths(self):
        """Test URL joining with empty path segments."""
        result = utils.urljoin('http://localhost:5984/', '', 'test')
        assert result == 'http://localhost:5984/test'

    def test_force_bytes_string(self):
        """Test force_bytes with string input."""
        result = utils.force_bytes('hello world')
        assert result == b'hello world'
        assert isinstance(result, bytes)

    def test_force_bytes_already_bytes(self):
        """Test force_bytes with bytes input."""
        input_bytes = b'hello world'
        result = utils.force_bytes(input_bytes)
        assert result == input_bytes
        assert result is input_bytes

    def test_force_text_bytes(self):
        """Test force_text with bytes input."""
        result = utils.force_text(b'hello world')
        assert result == 'hello world'
        assert isinstance(result, str)

    def test_force_text_already_string(self):
        """Test force_text with string input."""
        input_str = 'hello world'
        result = utils.force_text(input_str)
        assert result == input_str
        assert result is input_str

    def test_as_json_valid_json(self):
        """Test as_json with valid JSON response."""
        class MockResponse:
            def __init__(self):
                self.headers = {'content-type': 'application/json'}
                self.content = b'{"key": "value"}'
        
        response = MockResponse()
        result = utils.as_json(response)
        assert result == {'key': 'value'}

    def test_as_json_invalid_json(self):
        """Test as_json with invalid JSON response."""
        class MockResponse:
            def __init__(self):
                self.headers = {'content-type': 'application/json'}
                self.content = b'invalid json'
        
        response = MockResponse()
        # The function doesn't handle JSON decode errors, so it raises an exception
        with pytest.raises(json.JSONDecodeError):  # json.loads raises JSONDecodeError for invalid JSON
            utils.as_json(response)

    def test_encode_view_options(self):
        """Test encoding view options."""
        options = {
            'key': 'value',
            'startkey': 'start',
            'endkey': 'end',
            'limit': 10,
            'skip': 5,
            'descending': True,
            'include_docs': True
        }
        
        result = utils.encode_view_options(options)
        
        assert result['key'] == '"value"'
        assert result['startkey'] == '"start"'
        assert result['endkey'] == '"end"'
        assert result['limit'] == 10
        assert result['skip'] == 5
        assert result['descending'] == True  # Boolean values are not converted
        assert result['include_docs'] == True

    def test_encode_view_options_with_list(self):
        """Test encoding view options with list values."""
        options = {
            'keys': ['key1', 'key2', 'key3']
        }
        
        result = utils.encode_view_options(options)
        assert result['keys'] == ['key1', 'key2', 'key3']  # 'keys' is not in the special list, so it's not converted

    def test_encode_view_options_with_dict(self):
        """Test encoding view options with dict values."""
        options = {
            'key': {'nested': 'value'}
        }
        
        result = utils.encode_view_options(options)
        assert result['key'] == '{"nested": "value"}'

    def test_encode_view_options_boolean_values(self):
        """Test encoding view options with boolean values."""
        options = {
            'descending': False,
            'include_docs': True,
            'reduce': False
        }
        
        result = utils.encode_view_options(options)
        assert result['descending'] == False  # Boolean values are not converted to strings
        assert result['include_docs'] == True
        assert result['reduce'] == False

    def test_encode_view_options_numeric_values(self):
        """Test encoding view options with numeric values."""
        options = {
            'limit': 100,
            'skip': 0,
            'group_level': 2
        }
        
        result = utils.encode_view_options(options)
        assert result['limit'] == 100
        assert result['skip'] == 0
        assert result['group_level'] == 2