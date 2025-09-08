"""
Pytest configuration and shared fixtures for pycouchdb unit tests.
"""

import pytest
import os
from unittest.mock import Mock, patch
import pycouchdb.client as client


@pytest.fixture
def mock_server():
    """Create a mock Server instance for testing."""
    with patch('pycouchdb.client.Resource') as mock_resource_class:
        mock_resource = Mock()
        mock_resource_class.return_value = mock_resource
        server = client.Server("http://localhost:5984/")
        yield server, mock_resource


@pytest.fixture
def mock_database():
    """Create a mock Database instance for testing."""
    mock_resource = Mock()
    db = client.Database(mock_resource, "testdb")
    yield db, mock_resource


@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        "_id": "doc123",
        "_rev": "1-abc",
        "name": "Test Document",
        "value": 42,
        "nested": {
            "key": "value"
        }
    }


@pytest.fixture
def sample_documents():
    """Sample documents for bulk testing."""
    return [
        {"_id": "doc1", "name": "Document 1", "value": 1},
        {"_id": "doc2", "name": "Document 2", "value": 2},
        {"_id": "doc3", "name": "Document 3", "value": 3}
    ]


@pytest.fixture
def sample_attachment():
    """Sample attachment content for testing."""
    return b"Hello, World! This is a test attachment."


@pytest.fixture
def mock_couchdb_response():
    """Mock CouchDB response for testing."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"ok": True}
    response.headers = {"etag": '"1-abc"'}
    response.content = b"test content"
    response.iter_lines.return_value = []
    response.iter_content.return_value = []
    return response


@pytest.fixture
def mock_couchdb_error_response():
    """Mock CouchDB error response for testing."""
    response = Mock()
    response.status_code = 404
    response.json.return_value = {"error": "not_found", "reason": "Document not found"}
    return response


@pytest.fixture
def mock_feed_reader():
    """Mock feed reader for testing changes feed."""
    class MockFeedReader:
        def __init__(self):
            self.messages = []
            self.heartbeats = 0
            self.closed = False
        
        def on_message(self, message):
            self.messages.append(message)
        
        def on_heartbeat(self):
            self.heartbeats += 1
        
        def on_close(self):
            self.closed = True
    
    return MockFeedReader()


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    # Store original environment
    original_env = os.environ.copy()
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def temp_database_name():
    """Generate a temporary database name for testing."""
    import uuid
    return f"test_db_{uuid.uuid4().hex[:8]}"


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_couchdb: mark test as requiring a running CouchDB instance"
    )


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add unit marker to unit tests (all tests in main test directory)
        if "test/" in item.nodeid and "integration" not in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Add slow marker to tests that might be slow
        if any(keyword in item.name for keyword in ["bulk", "feed", "stream", "pagination"]):
            item.add_marker(pytest.mark.slow)


# Test reporting
def pytest_html_report_title(report):
    """Set the title of the HTML report."""
    report.title = "pycouchdb Test Report"


def pytest_html_results_summary(prefix, summary, postfix):
    """Customize the HTML report summary."""
    prefix.extend([f"<p>pycouchdb Test Suite</p>"])