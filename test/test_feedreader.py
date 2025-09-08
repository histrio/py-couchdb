"""
Unit tests for pycouchdb.feedreader module.
"""

import pytest
from pycouchdb import feedreader, exceptions


class TestBaseFeedReader:
    """Test BaseFeedReader class."""

    def test_base_feed_reader_initialization(self):
        """Test BaseFeedReader initialization."""
        reader = feedreader.BaseFeedReader()
        assert not hasattr(reader, 'db')

    def test_base_feed_reader_call(self):
        """Test BaseFeedReader __call__ method."""
        reader = feedreader.BaseFeedReader()
        mock_db = "mock_database"
        
        result = reader(mock_db)
        
        assert result is reader
        assert reader.db == mock_db

    def test_base_feed_reader_on_message_not_implemented(self):
        """Test that on_message raises NotImplementedError."""
        reader = feedreader.BaseFeedReader()
        reader.db = "mock_db"
        
        with pytest.raises(NotImplementedError):
            reader.on_message({"test": "message"})

    def test_base_feed_reader_on_close_default(self):
        """Test that on_close does nothing by default."""
        reader = feedreader.BaseFeedReader()
        reader.db = "mock_db"
        
        # Should not raise any exception
        reader.on_close()

    def test_base_feed_reader_on_heartbeat_default(self):
        """Test that on_heartbeat does nothing by default."""
        reader = feedreader.BaseFeedReader()
        reader.db = "mock_db"
        
        # Should not raise any exception
        reader.on_heartbeat()


class TestSimpleFeedReader:
    """Test SimpleFeedReader class."""

    def test_simple_feed_reader_initialization(self):
        """Test SimpleFeedReader initialization."""
        reader = feedreader.SimpleFeedReader()
        assert not hasattr(reader, 'db')
        assert not hasattr(reader, 'callback')

    def test_simple_feed_reader_call(self):
        """Test SimpleFeedReader __call__ method."""
        reader = feedreader.SimpleFeedReader()
        mock_db = "mock_database"
        mock_callback = lambda msg, db: None
        
        result = reader(mock_db, mock_callback)
        
        assert result is reader
        assert reader.db == mock_db
        assert reader.callback is mock_callback

    def test_simple_feed_reader_on_message(self):
        """Test SimpleFeedReader on_message method."""
        reader = feedreader.SimpleFeedReader()
        mock_db = "mock_database"
        messages_received = []
        
        def mock_callback(message, db):
            messages_received.append((message, db))
        
        reader(mock_db, mock_callback)
        
        test_message = {"id": "test_doc", "seq": 1}
        reader.on_message(test_message)
        
        assert len(messages_received) == 1
        assert messages_received[0] == (test_message, mock_db)

    def test_simple_feed_reader_on_message_multiple_calls(self):
        """Test SimpleFeedReader on_message with multiple calls."""
        reader = feedreader.SimpleFeedReader()
        mock_db = "mock_database"
        messages_received = []
        
        def mock_callback(message, db):
            messages_received.append(message)
        
        reader(mock_db, mock_callback)
        
        # Send multiple messages
        for i in range(3):
            test_message = {"id": f"test_doc_{i}", "seq": i}
            reader.on_message(test_message)
        
        assert len(messages_received) == 3
        assert messages_received[0]["id"] == "test_doc_0"
        assert messages_received[1]["id"] == "test_doc_1"
        assert messages_received[2]["id"] == "test_doc_2"

    def test_simple_feed_reader_inheritance(self):
        """Test that SimpleFeedReader inherits from BaseFeedReader."""
        reader = feedreader.SimpleFeedReader()
        assert isinstance(reader, feedreader.BaseFeedReader)

    def test_simple_feed_reader_on_close_inherited(self):
        """Test that SimpleFeedReader inherits on_close from BaseFeedReader."""
        reader = feedreader.SimpleFeedReader()
        mock_db = "mock_database"
        reader(mock_db, lambda msg, db: None)
        
        # Should not raise any exception (inherited from BaseFeedReader)
        reader.on_close()

    def test_simple_feed_reader_on_heartbeat_inherited(self):
        """Test that SimpleFeedReader inherits on_heartbeat from BaseFeedReader."""
        reader = feedreader.SimpleFeedReader()
        mock_db = "mock_database"
        reader(mock_db, lambda msg, db: None)
        
        # Should not raise any exception (inherited from BaseFeedReader)
        reader.on_heartbeat()


class TestFeedReaderIntegration:
    """Test feed reader integration scenarios."""

    def test_custom_feed_reader_implementation(self):
        """Test custom feed reader implementation."""
        class CustomFeedReader(feedreader.BaseFeedReader):
            def __init__(self):
                super().__init__()
                self.messages = []
                self.heartbeats = 0
                self.closed = False
            
            def on_message(self, message):
                self.messages.append(message)
            
            def on_heartbeat(self):
                self.heartbeats += 1
            
            def on_close(self):
                self.closed = True
        
        reader = CustomFeedReader()
        mock_db = "mock_database"
        reader(mock_db)
        
        # Test message handling
        test_message = {"id": "test", "seq": 1}
        reader.on_message(test_message)
        assert len(reader.messages) == 1
        assert reader.messages[0] == test_message
        
        # Test heartbeat handling
        reader.on_heartbeat()
        assert reader.heartbeats == 1
        
        # Test close handling
        reader.on_close()
        assert reader.closed is True

    def test_simple_feed_reader_with_exception_handling(self):
        """Test SimpleFeedReader with callback that raises exceptions."""
        reader = feedreader.SimpleFeedReader()
        mock_db = "mock_database"
        
        def failing_callback(message, db):
            raise ValueError("Callback failed")
        
        reader(mock_db, failing_callback)
        
        # Should propagate the exception
        with pytest.raises(ValueError, match="Callback failed"):
            reader.on_message({"test": "message"})