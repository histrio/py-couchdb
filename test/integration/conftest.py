"""
Integration test configuration and fixtures for pycouchdb tests.

This module provides fixtures and configuration specifically for integration tests
that require a running CouchDB instance.
"""

import pytest
import os
import time
import requests
from pycouchdb import Server


# CouchDB connection settings
SERVER_URL = 'http://admin:password@localhost:5984/'


def is_couchdb_running():
    """Check if CouchDB is running and accessible."""
    try:
        response = requests.get(SERVER_URL, timeout=5)
        return response.status_code == 200
    except (requests.exceptions.RequestException, requests.exceptions.Timeout):
        return False


@pytest.fixture(scope="session")
def couchdb_available():
    """Check if CouchDB is available for integration tests."""
    if not is_couchdb_running():
        pytest.skip("CouchDB is not running or not accessible. "
                   "Please start CouchDB and ensure it's accessible at "
                   f"{SERVER_URL}")


@pytest.fixture
def server(couchdb_available):
    """Create a clean Server instance for integration tests."""
    server = Server(SERVER_URL)
    
    # Clean up existing test databases
    for db_name in list(server):
        if db_name.startswith('pycouchdb-testing-'):
            try:
                server.delete(db_name)
            except Exception:
                pass  # Ignore errors during cleanup
    
    # Ensure _users database exists
    if "_users" not in server:
        server.create("_users")
    
    yield server
    
    # Cleanup after test
    for db_name in list(server):
        if db_name.startswith('pycouchdb-testing-'):
            try:
                server.delete(db_name)
            except Exception:
                pass  # Ignore errors during cleanup


@pytest.fixture
def db(server, request):
    """Create a temporary database for testing."""
    db_name = 'pycouchdb-testing-' + request.node.name
    yield server.create(db_name)
    try:
        server.delete(db_name)
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture
def rec(db):
    """Create test records with a design document."""
    querydoc = {
        "_id": "_design/testing",
        "views": {
            "names": {
                "map": "function(doc) { emit(doc.name, 1); }",
                "reduce": "function(keys, values) { return sum(values); }",
            }
        }
    }
    db.save(querydoc)
    db.save_bulk([
        {"_id": "kk1", "name": "Andrey"},
        {"_id": "kk2", "name": "Pepe"},
        {"_id": "kk3", "name": "Alex"},
    ])
    yield
    try:
        db.delete("_design/testing")
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture
def rec_with_attachment(db, rec, tmpdir):
    """Create test records with an attachment."""
    doc = db.get("kk1")
    att = tmpdir.join('sample.txt')
    att.write(b"Hello")
    with open(str(att)) as f:
        doc = db.put_attachment(doc, f, "sample.txt")
    yield doc


@pytest.fixture
def view(db):
    """Create a view for testing."""
    querydoc = {
        "_id": "_design/testing",
        "views": {
            "names": {
                "map": "function(doc) { emit(doc.name, 1); }",
            }
        }
    }
    db.save(querydoc)
    db.save_bulk([
        {"_id": "kk1", "name": "Florian"},
        {"_id": "kk2", "name": "Raphael"},
        {"_id": "kk3", "name": "Jaideep"},
        {"_id": "kk4", "name": "Andrew"},
        {"_id": "kk5", "name": "Pepe"},
        {"_id": "kk6", "name": "Alex"},
    ])
    yield
    try:
        db.delete("_design/testing")
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture
def view_duplicate_keys(db):
    """Create a view with duplicate keys for testing."""
    querydoc = {
        "_id": "_design/testing",
        "views": {
            "names": {
                "map": "function(doc) { emit(doc.name, 1); }",
            }
        }
    }
    db.save(querydoc)
    db.save_bulk([
        {"_id": "kk1", "name": "Andrew"},
        {"_id": "kk2", "name": "Andrew"},
        {"_id": "kk3", "name": "Andrew"},
        {"_id": "kk4", "name": "Andrew"},
        {"_id": "kk5", "name": "Andrew"},
        {"_id": "kk6", "name": "Andrew"},
    ])
    yield
    try:
        db.delete("_design/testing")
    except Exception:
        pass  # Ignore cleanup errors


# Mark all tests in this directory as integration tests
def pytest_collection_modifyitems(config, items):
    """Mark all tests in this directory as integration tests."""
    for item in items:
        item.add_marker(pytest.mark.integration)
        item.add_marker(pytest.mark.requires_couchdb)