"""
Unit tests for pycouchdb.client.Server class.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pycouchdb import client, exceptions


class TestServer:
    """Test Server class."""

    def test_server_initialization_default(self):
        """Test Server initialization with default parameters."""
        with patch('pycouchdb.client.Resource') as mock_resource:
            server = client.Server()
            
            mock_resource.assert_called_once_with(
                'http://localhost:5984/',
                True,  # full_commit as positional argument
                credentials=None,
                authmethod="basic",
                verify=False
            )

    def test_server_initialization_custom_url(self):
        """Test Server initialization with custom URL."""
        with patch('pycouchdb.client.Resource') as mock_resource:
            server = client.Server("http://example.com:5984/")
            
            mock_resource.assert_called_once_with(
                'http://example.com:5984/',
                True,  # full_commit as positional argument
                credentials=None,
                authmethod="basic",
                verify=False
            )

    def test_server_initialization_with_credentials(self):
        """Test Server initialization with credentials in URL."""
        with patch('pycouchdb.client.Resource') as mock_resource:
            with patch('pycouchdb.client.utils.extract_credentials', return_value=("http://example.com:5984/", ("user", "pass"))):
                server = client.Server("http://user:pass@example.com:5984/")
                
                mock_resource.assert_called_once_with(
                    'http://example.com:5984/',
                    True,  # full_commit as positional argument
                    credentials=("user", "pass"),
                    authmethod="basic",
                    verify=False
                )

    def test_server_initialization_with_verify(self):
        """Test Server initialization with SSL verification."""
        with patch('pycouchdb.client.Resource') as mock_resource:
            server = client.Server("http://example.com:5984/", verify=True)
            
            mock_resource.assert_called_once_with(
                'http://example.com:5984/',
                True,  # full_commit as positional argument
                credentials=None,
                authmethod="basic",
                verify=True
            )

    def test_server_repr(self):
        """Test Server __repr__ method."""
        with patch('pycouchdb.client.Resource'):
            server = client.Server("http://example.com:5984/")
            repr_str = repr(server)
            assert "CouchDB Server" in repr_str
            assert "http://example.com:5984/" in repr_str

    def test_server_info(self):
        """Test Server info method."""
        with patch('pycouchdb.client.Resource') as mock_resource_class:
            mock_resource = Mock()
            mock_resource_class.return_value = mock_resource
            
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"version": "3.2.0", "couchdb": "Welcome"}
            mock_resource.get.return_value = (mock_response, {"version": "3.2.0", "couchdb": "Welcome"})
            
            server = client.Server()
            result = server.info()
            
            assert result == {"version": "3.2.0", "couchdb": "Welcome"}
            mock_resource.get.assert_called_once_with()

    def test_server_version(self):
        """Test Server version method."""
        with patch('pycouchdb.client.Resource') as mock_resource_class:
            mock_resource = Mock()
            mock_resource_class.return_value = mock_resource
            
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"version": "3.2.0"}
            mock_resource.get.return_value = (mock_response, {"version": "3.2.0"})
            
            server = client.Server()
            result = server.version()
            
            assert result == "3.2.0"
            mock_resource.get.assert_called_once_with()

    def test_server_contains_true(self):
        """Test Server __contains__ method when database exists."""
        with patch('pycouchdb.client.Resource') as mock_resource_class:
            mock_resource = Mock()
            mock_resource_class.return_value = mock_resource
            
            # Mock successful HEAD response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_resource.head.return_value = (mock_response, None)
            
            server = client.Server()
            result = "testdb" in server
            
            assert result is True
            mock_resource.head.assert_called_once_with("testdb")

    def test_server_contains_false(self):
        """Test Server __contains__ method when database doesn't exist."""
        with patch('pycouchdb.client.Resource') as mock_resource_class:
            mock_resource = Mock()
            mock_resource_class.return_value = mock_resource
            
            # Mock 404 response
            mock_resource.head.side_effect = exceptions.NotFound()
            
            server = client.Server()
            result = "testdb" in server
            
            assert result is False

    def test_server_iter(self):
        """Test Server __iter__ method."""
        with patch('pycouchdb.client.Resource') as mock_resource_class:
            mock_resource = Mock()
            mock_resource_class.return_value = mock_resource
            
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = ["db1", "db2", "db3"]
            mock_resource.get.return_value = (mock_response, ["db1", "db2", "db3"])
            
            server = client.Server()
            result = list(server)
            
            assert result == ["db1", "db2", "db3"]
            # The method calls get('_all_dbs') once
            mock_resource.get.assert_called_with("_all_dbs")

    def test_server_len(self):
        """Test Server __len__ method."""
        with patch('pycouchdb.client.Resource') as mock_resource_class:
            mock_resource = Mock()
            mock_resource_class.return_value = mock_resource
            
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = ["db1", "db2", "db3"]
            mock_resource.get.return_value = (mock_response, ["db1", "db2", "db3"])
            
            server = client.Server()
            result = len(server)
            
            assert result == 3
            mock_resource.get.assert_called_once_with("_all_dbs")

    def test_server_create_success(self):
        """Test Server create method success."""
        with patch('pycouchdb.client.Resource') as mock_resource_class:
            mock_resource = Mock()
            mock_resource_class.return_value = mock_resource
            
            # Mock successful PUT response
            mock_put_response = Mock()
            mock_put_response.status_code = 201
            mock_put_response.json.return_value = {"ok": True}
            
            # Mock successful HEAD response
            mock_head_response = Mock()
            mock_head_response.status_code = 200
            
            mock_resource.put.return_value = (mock_put_response, {"ok": True})
            mock_resource.head.return_value = (mock_head_response, None)
            
            server = client.Server()
            result = server.create("testdb")
            
            assert isinstance(result, client.Database)
            assert result.name == "testdb"
            mock_resource.put.assert_called_once_with("testdb")
            mock_resource.head.assert_called_once_with("testdb")

    def test_server_create_conflict(self):
        """Test Server create method with conflict."""
        with patch('pycouchdb.client.Resource') as mock_resource_class:
            mock_resource = Mock()
            mock_resource_class.return_value = mock_resource
            
            # Mock conflict response
            mock_resource.put.side_effect = exceptions.Conflict("Database already exists")
            
            server = client.Server()
            
            with pytest.raises(exceptions.Conflict, match="Database already exists"):
                server.create("testdb")

    def test_server_delete_success(self):
        """Test Server delete method success."""
        with patch('pycouchdb.client.Resource') as mock_resource_class:
            mock_resource = Mock()
            mock_resource_class.return_value = mock_resource
            
            # Mock successful DELETE response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}
            mock_resource.delete.return_value = (mock_response, {"ok": True})
            
            server = client.Server()
            result = server.delete("testdb")
            
            assert result is None  # delete method doesn't return anything
            mock_resource.delete.assert_called_once_with("testdb")

    def test_server_delete_not_found(self):
        """Test Server delete method with not found."""
        with patch('pycouchdb.client.Resource') as mock_resource_class:
            mock_resource = Mock()
            mock_resource_class.return_value = mock_resource
            
            # Mock not found response
            mock_resource.delete.side_effect = exceptions.NotFound("Database not found")
            
            server = client.Server()
            
            with pytest.raises(exceptions.NotFound, match="Database not found"):
                server.delete("testdb")

    def test_server_database(self):
        """Test Server database method."""
        with patch('pycouchdb.client.Resource') as mock_resource_class:
            mock_resource = Mock()
            mock_resource_class.return_value = mock_resource
            
            # Mock successful HEAD response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_resource.head.return_value = (mock_response, None)
            
            # Mock the resource(name) call that creates the database resource
            mock_db_resource = Mock()
            mock_resource.return_value = mock_db_resource
            
            server = client.Server()
            result = server.database("testdb")
            
            assert isinstance(result, client.Database)
            assert result.name == "testdb"
            assert result.resource == mock_db_resource
            mock_resource.head.assert_called_once_with("testdb")
            mock_resource.assert_called_with("testdb")

    def test_server_replicate_success(self):
        """Test Server replicate method success."""
        with patch('pycouchdb.client.Resource') as mock_resource_class:
            mock_resource = Mock()
            mock_resource_class.return_value = mock_resource
            
            # Mock successful POST response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True, "session_id": "abc123"}
            mock_resource.post.return_value = (mock_response, {"ok": True, "session_id": "abc123"})
            
            server = client.Server()
            result = server.replicate("http://source:5984/source_db", 
                                    "http://target:5984/target_db")
            
            assert result == {"ok": True, "session_id": "abc123"}
            mock_resource.post.assert_called_once_with("_replicate",
                                                     data=b'{"source": "http://source:5984/source_db", "target": "http://target:5984/target_db"}')

    def test_server_replicate_with_options(self):
        """Test Server replicate method with additional options."""
        with patch('pycouchdb.client.Resource') as mock_resource_class:
            mock_resource = Mock()
            mock_resource_class.return_value = mock_resource
            
            # Mock successful POST response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}
            mock_resource.post.return_value = (mock_response, {"ok": True})
            
            server = client.Server()
            result = server.replicate("http://source:5984/source_db", 
                                    "http://target:5984/target_db",
                                    create_target=True,
                                    continuous=True)
            
            expected_data = {
                "source": "http://source:5984/source_db",
                "target": "http://target:5984/target_db",
                "create_target": True,
                "continuous": True
            }
            mock_resource.post.assert_called_once_with("_replicate",
                                                     data=json.dumps(expected_data).encode())

    def test_server_changes_feed(self):
        """Test Server changes_feed method."""
        with patch('pycouchdb.client.Resource') as mock_resource_class:
            mock_resource = Mock()
            mock_resource_class.return_value = mock_resource
            
            # Mock successful POST response with stream
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.iter_lines.return_value = [
                b'{"seq": 1, "id": "doc1"}',
                b'{"seq": 2, "id": "doc2"}',
                b''  # Empty line (heartbeat)
            ]
            mock_resource.post.return_value = (mock_response, None)
            
            server = client.Server()
            messages_received = []
            
            def mock_feed_reader(message, db):
                messages_received.append(message)
                if len(messages_received) >= 2:
                    raise exceptions.FeedReaderExited()
            
            with patch('pycouchdb.client._listen_feed') as mock_listen:
                server.changes_feed(mock_feed_reader)
                mock_listen.assert_called_once()

    def test_server_changes_feed_with_options(self):
        """Test Server changes_feed method with options."""
        with patch('pycouchdb.client.Resource') as mock_resource_class:
            mock_resource = Mock()
            mock_resource_class.return_value = mock_resource
            
            server = client.Server()
            
            def mock_feed_reader(message, db):
                pass
            
            with patch('pycouchdb.client._listen_feed') as mock_listen:
                server.changes_feed(mock_feed_reader, 
                                  feed="longpoll",
                                  since=100,
                                  limit=50)
                
                mock_listen.assert_called_once()
                call_args = mock_listen.call_args
                assert call_args[1]['feed'] == "longpoll"
                assert call_args[1]['since'] == 100
                assert call_args[1]['limit'] == 50


class TestServerHelperFunctions:
    """Test Server helper functions."""

    def test_id_to_path_regular_id(self):
        """Test _id_to_path with regular document ID."""
        result = client._id_to_path("doc123")
        assert result == ["doc123"]

    def test_id_to_path_design_doc(self):
        """Test _id_to_path with design document ID."""
        result = client._id_to_path("_design/test")
        assert result == ["_design", "test"]

    def test_id_to_path_other_system_doc(self):
        """Test _id_to_path with other system document ID."""
        result = client._id_to_path("_local/doc123")
        assert result == ["_local", "doc123"]

    def test_listen_feed_with_callable(self):
        """Test _listen_feed with callable feed reader."""
        mock_object = Mock()
        mock_resource = Mock()
        mock_object.resource.return_value = mock_resource
        
        # Mock successful POST response with stream
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'',  # Empty line (heartbeat) first
            b'{"seq": 1, "id": "doc1"}'
        ]
        mock_resource.post.return_value = (mock_response, None)
        
        messages_received = []
        
        def mock_feed_reader(message, db):
            messages_received.append(message)
            raise exceptions.FeedReaderExited()
        
        with patch('pycouchdb.client.feedreader.SimpleFeedReader') as mock_reader_class:
            mock_reader = Mock()
            mock_reader_class.return_value.return_value = mock_reader
            mock_reader.on_heartbeat = Mock()
            mock_reader.on_close = Mock()
            
            # Set up the on_message to call the actual callback
            def on_message_side_effect(message):
                mock_feed_reader(message, None)
            mock_reader.on_message.side_effect = on_message_side_effect
            
            client._listen_feed(mock_object, "_changes", mock_feed_reader)
            
            mock_reader.on_message.assert_called_once()
            mock_reader.on_heartbeat.assert_called_once()
            mock_reader.on_close.assert_called_once()

    def test_listen_feed_with_feed_reader_class(self):
        """Test _listen_feed with BaseFeedReader class."""
        mock_object = Mock()
        mock_resource = Mock()
        mock_object.resource.return_value = mock_resource
        
        # Mock successful POST response with stream
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'{"seq": 1, "id": "doc1"}'
        ]
        mock_resource.post.return_value = (mock_response, None)
        
        class MockFeedReader(client.feedreader.BaseFeedReader):
            def __init__(self):
                super().__init__()
                self.messages = []
            
            def on_message(self, message):
                self.messages.append(message)
                raise exceptions.FeedReaderExited()
        
        mock_feed_reader = MockFeedReader()
        
        client._listen_feed(mock_object, "_changes", mock_feed_reader)
        
        assert len(mock_feed_reader.messages) == 1
        assert mock_feed_reader.messages[0] == {"seq": 1, "id": "doc1"}

    def test_listen_feed_invalid_reader(self):
        """Test _listen_feed with invalid feed reader."""
        mock_object = Mock()
        
        with pytest.raises(exceptions.UnexpectedError, match="feed_reader must be callable or class"):
            client._listen_feed(mock_object, "_changes", "invalid_reader")


class TestStreamResponse:
    """Test _StreamResponse class."""

    def test_stream_response_initialization(self):
        """Test _StreamResponse initialization."""
        mock_response = Mock()
        stream_response = client._StreamResponse(mock_response)
        
        assert stream_response._response == mock_response

    def test_stream_response_iter_content(self):
        """Test _StreamResponse iter_content method."""
        mock_response = Mock()
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        
        stream_response = client._StreamResponse(mock_response)
        result = list(stream_response.iter_content(chunk_size=1024, decode_unicode=True))
        
        assert result == [b"chunk1", b"chunk2"]
        mock_response.iter_content.assert_called_once_with(chunk_size=1024, decode_unicode=True)

    def test_stream_response_iter_lines(self):
        """Test _StreamResponse iter_lines method."""
        mock_response = Mock()
        mock_response.iter_lines.return_value = [b"line1", b"line2"]
        
        stream_response = client._StreamResponse(mock_response)
        result = list(stream_response.iter_lines(chunk_size=512, decode_unicode=True))
        
        assert result == [b"line1", b"line2"]
        mock_response.iter_lines.assert_called_once_with(chunk_size=512, decode_unicode=True)

    def test_stream_response_raw_property(self):
        """Test _StreamResponse raw property."""
        mock_response = Mock()
        mock_raw = Mock()
        mock_response.raw = mock_raw
        
        stream_response = client._StreamResponse(mock_response)
        
        assert stream_response.raw == mock_raw

    def test_stream_response_url_property(self):
        """Test _StreamResponse url property."""
        mock_response = Mock()
        mock_response.url = "http://example.com/test"
        
        stream_response = client._StreamResponse(mock_response)
        
        assert stream_response.url == "http://example.com/test"