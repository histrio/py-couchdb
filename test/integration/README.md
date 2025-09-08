# Integration Tests

This directory contains integration tests for pycouchdb that require a running CouchDB instance.

## Requirements

- CouchDB server running on `http://admin:password@localhost:5984/`
- The server should be accessible and have admin credentials configured

## Running Integration Tests

### Using pytest:
```bash
# Run integration tests
pytest test/integration/ -m integration

# Run with CouchDB requirement check
pytest test/integration/ -m "integration and requires_couchdb"
```

## Test Structure

- `test_integration.py`: Main integration test file containing tests that interact with a real CouchDB instance
- `conftest.py`: Integration-specific fixtures and configuration

## Test Markers

All tests in this directory are automatically marked with:
- `integration`: Identifies these as integration tests
- `requires_couchdb`: Indicates these tests need a running CouchDB instance

## Fixtures

- `server`: Provides a clean Server instance with test database cleanup
- `db`: Creates a temporary database for each test
- `rec`: Sets up test records with design documents
- `rec_with_attachment`: Creates test records with attachments
- `view`: Sets up views for testing
- `view_duplicate_keys`: Creates views with duplicate keys for pagination testing