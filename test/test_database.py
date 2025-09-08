"""
Unit tests for pycouchdb.client.Database class.
"""

import pytest
import json
import uuid
from unittest.mock import Mock, patch, MagicMock, call
from pycouchdb import client, exceptions


class TestDatabase:
    """Test Database class."""

    def test_database_initialization(self):
        """Test Database initialization."""
        mock_resource = Mock()
        db = client.Database(mock_resource, "testdb")
        
        assert db.resource == mock_resource
        assert db.name == "testdb"

    def test_database_repr(self):
        """Test Database __repr__ method."""
        mock_resource = Mock()
        db = client.Database(mock_resource, "testdb")
        
        repr_str = repr(db)
        assert "CouchDB Database" in repr_str
        assert "testdb" in repr_str

    def test_database_contains_true(self):
        """Test Database __contains__ method when document exists."""
        mock_resource = Mock()
        mock_resource.head.return_value = (Mock(status_code=200), None)
        
        db = client.Database(mock_resource, "testdb")
        result = "doc123" in db
        
        assert result is True
        mock_resource.head.assert_called_once_with(["doc123"])

    def test_database_contains_false(self):
        """Test Database __contains__ method when document doesn't exist."""
        mock_resource = Mock()
        mock_resource.head.side_effect = exceptions.NotFound()
        
        db = client.Database(mock_resource, "testdb")
        result = "doc123" in db
        
        assert result is False

    def test_database_config(self):
        """Test Database config method."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"doc_count": 100, "update_seq": 200}
        mock_resource.get.return_value = (mock_response, {"doc_count": 100, "update_seq": 200})
        
        db = client.Database(mock_resource, "testdb")
        result = db.config()
        
        assert result == {"doc_count": 100, "update_seq": 200}
        mock_resource.get.assert_called_once_with()

    def test_database_nonzero_true(self):
        """Test Database __nonzero__ method when database is available."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_resource.head.return_value = (mock_response, None)
        
        # Mock the config method that gets called by __len__ (which is called by bool() in Python 3)
        mock_config_response = Mock()
        mock_config_response.status_code = 200
        mock_config_response.json.return_value = {"doc_count": 100}
        mock_resource.get.return_value = (mock_config_response, {"doc_count": 100})
        
        db = client.Database(mock_resource, "testdb")
        result = bool(db)
        
        assert result is True
        # bool() calls __len__ which calls config(), not __nonzero__ which calls head()
        mock_resource.get.assert_called_once_with()

    def test_database_nonzero_false(self):
        """Test Database __nonzero__ method when database is not available."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_resource.head.return_value = (mock_response, None)
        
        # Mock the config method that gets called by __len__ (which is called by bool() in Python 3)
        # For a database to be "false", it needs to have 0 documents
        mock_config_response = Mock()
        mock_config_response.status_code = 200
        mock_config_response.json.return_value = {"doc_count": 0}
        mock_resource.get.return_value = (mock_config_response, {"doc_count": 0})
        
        db = client.Database(mock_resource, "testdb")
        result = bool(db)
        
        assert result is False

    def test_database_len(self):
        """Test Database __len__ method."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"doc_count": 150}
        mock_resource.get.return_value = (mock_response, {"doc_count": 150})
        
        db = client.Database(mock_resource, "testdb")
        result = len(db)
        
        assert result == 150

    def test_database_get_success(self):
        """Test Database get method success."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"_id": "doc123", "_rev": "1-abc", "name": "test"}
        mock_resource.return_value.get.return_value = (mock_response, {"_id": "doc123", "_rev": "1-abc", "name": "test"})
        
        db = client.Database(mock_resource, "testdb")
        result = db.get("doc123")
        
        assert result == {"_id": "doc123", "_rev": "1-abc", "name": "test"}
        mock_resource.assert_called_once_with("doc123")

    def test_database_get_with_params(self):
        """Test Database get method with parameters."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"_id": "doc123", "_rev": "1-abc", "name": "test"}
        mock_resource.return_value.get.return_value = (mock_response, {"_id": "doc123", "_rev": "1-abc", "name": "test"})
        
        db = client.Database(mock_resource, "testdb")
        result = db.get("doc123", revs=True, conflicts=True)
        
        assert result == {"_id": "doc123", "_rev": "1-abc", "name": "test"}
        mock_resource.assert_called_once_with("doc123")
        mock_resource.return_value.get.assert_called_once_with(params={"revs": True, "conflicts": True})

    def test_database_get_with_deprecated_params(self):
        """Test Database get method with deprecated params parameter."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"_id": "doc123", "_rev": "1-abc", "name": "test"}
        mock_resource.return_value.get.return_value = (mock_response, {"_id": "doc123", "_rev": "1-abc", "name": "test"})
        
        db = client.Database(mock_resource, "testdb")
        
        with pytest.warns(DeprecationWarning):
            result = db.get("doc123", params={"revs": True})
        
        assert result == {"_id": "doc123", "_rev": "1-abc", "name": "test"}

    def test_database_get_not_found(self):
        """Test Database get method with not found."""
        mock_resource = Mock()
        mock_resource.return_value.get.side_effect = exceptions.NotFound("Document not found")
        
        db = client.Database(mock_resource, "testdb")
        
        with pytest.raises(exceptions.NotFound, match="Document not found"):
            db.get("doc123")

    def test_database_save_new_document(self):
        """Test Database save method with new document."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"ok": True, "id": "doc123", "rev": "1-abc"}
        mock_resource.return_value.put.return_value = (mock_response, {"ok": True, "id": "doc123", "rev": "1-abc"})
        
        db = client.Database(mock_resource, "testdb")
        doc = {"name": "test"}
        result = db.save(doc)
        
        assert result["_id"] is not None
        assert result["_rev"] == "1-abc"
        assert result["name"] == "test"
        assert "_id" not in doc  # Original doc should not be modified
        assert "_rev" not in doc

    def test_database_save_existing_document(self):
        """Test Database save method with existing document."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"ok": True, "id": "doc123", "rev": "2-def"}
        mock_resource.return_value.put.return_value = (mock_response, {"ok": True, "id": "doc123", "rev": "2-def"})
        
        db = client.Database(mock_resource, "testdb")
        doc = {"_id": "doc123", "_rev": "1-abc", "name": "test"}
        result = db.save(doc)
        
        assert result["_id"] == "doc123"
        assert result["_rev"] == "2-def"
        assert result["name"] == "test"

    def test_database_save_batch_mode(self):
        """Test Database save method in batch mode."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.json.return_value = {"ok": True, "id": "doc123", "rev": "1-abc"}
        mock_resource.return_value.put.return_value = (mock_response, {"ok": True, "id": "doc123", "rev": "1-abc"})
        
        db = client.Database(mock_resource, "testdb")
        doc = {"name": "test"}
        result = db.save(doc, batch=True)
        
        assert result["_id"] is not None
        assert result["_rev"] == "1-abc"
        mock_resource.return_value.put.assert_called_once()
        call_args = mock_resource.return_value.put.call_args
        assert call_args[1]['params'] == {'batch': 'ok'}

    def test_database_save_conflict(self):
        """Test Database save method with conflict."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 409
        mock_response.json.return_value = {"error": "conflict", "reason": "Document conflict"}
        mock_resource.return_value.put.return_value = (mock_response, {"error": "conflict", "reason": "Document conflict"})
        
        db = client.Database(mock_resource, "testdb")
        doc = {"_id": "doc123", "_rev": "1-abc", "name": "test"}
        
        with pytest.raises(exceptions.Conflict, match="Document conflict"):
            db.save(doc)

    def test_database_save_bulk_success(self):
        """Test Database save_bulk method success."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = [
            {"ok": True, "id": "doc1", "rev": "1-abc"},
            {"ok": True, "id": "doc2", "rev": "1-def"}
        ]
        mock_resource.post.return_value = (mock_response, [
            {"ok": True, "id": "doc1", "rev": "1-abc"},
            {"ok": True, "id": "doc2", "rev": "1-def"}
        ])
        
        db = client.Database(mock_resource, "testdb")
        docs = [{"name": "doc1"}, {"name": "doc2"}]
        result = db.save_bulk(docs)
        
        assert len(result) == 2
        assert result[0]["_id"] is not None
        assert result[0]["_rev"] == "1-abc"
        assert result[1]["_id"] is not None
        assert result[1]["_rev"] == "1-def"
        # The method sends docs without _rev, then adds _rev from response
        expected_docs = [{"name": "doc1", "_id": result[0]["_id"]}, {"name": "doc2", "_id": result[1]["_id"]}]
        mock_resource.post.assert_called_once_with("_bulk_docs", 
                                                 data=json.dumps({"docs": expected_docs}).encode(),
                                                 params={"all_or_nothing": "true"})

    def test_database_save_bulk_with_existing_ids(self):
        """Test Database save_bulk method with existing document IDs."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = [
            {"ok": True, "id": "doc1", "rev": "1-abc"},
            {"ok": True, "id": "doc2", "rev": "1-def"}
        ]
        mock_resource.post.return_value = (mock_response, [
            {"ok": True, "id": "doc1", "rev": "1-abc"},
            {"ok": True, "id": "doc2", "rev": "1-def"}
        ])
        
        db = client.Database(mock_resource, "testdb")
        docs = [{"_id": "doc1", "name": "doc1"}, {"_id": "doc2", "name": "doc2"}]
        result = db.save_bulk(docs, try_setting_ids=False)
        
        assert len(result) == 2
        assert result[0]["_id"] == "doc1"
        assert result[1]["_id"] == "doc2"

    def test_database_save_bulk_without_transaction(self):
        """Test Database save_bulk method without transaction."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = [{"ok": True, "id": "doc1", "rev": "1-abc"}]
        mock_resource.post.return_value = (mock_response, [{"ok": True, "id": "doc1", "rev": "1-abc"}])
        
        db = client.Database(mock_resource, "testdb")
        docs = [{"name": "doc1"}]
        result = db.save_bulk(docs, transaction=False)
        
        # The method sends docs without _rev, then adds _rev from response
        expected_docs = [{"name": "doc1", "_id": result[0]["_id"]}]
        mock_resource.post.assert_called_once_with("_bulk_docs", 
                                                 data=json.dumps({"docs": expected_docs}).encode(),
                                                 params={"all_or_nothing": "false"})

    def test_database_delete_by_id(self):
        """Test Database delete method by document ID."""
        mock_resource = Mock()
        mock_head_response = Mock()
        mock_head_response.status_code = 200
        mock_head_response.headers = {"etag": '"1-abc"'}
        mock_resource.return_value.head.return_value = (mock_head_response, None)
        
        mock_delete_response = Mock()
        mock_delete_response.status_code = 200
        mock_delete_response.json.return_value = {"ok": True, "id": "doc123", "rev": "2-def"}
        mock_resource.return_value.delete.return_value = (mock_delete_response, {"ok": True, "id": "doc123", "rev": "2-def"})
        
        db = client.Database(mock_resource, "testdb")
        result = db.delete("doc123")
        
        assert result is None  # delete method doesn't return anything
        mock_resource.assert_called_once_with("doc123")
        mock_resource.return_value.head.assert_called_once()
        mock_resource.return_value.delete.assert_called_once_with(params={"rev": "1-abc"})

    def test_database_delete_by_document(self):
        """Test Database delete method by document object."""
        mock_resource = Mock()
        mock_head_response = Mock()
        mock_head_response.status_code = 200
        mock_head_response.headers = {"etag": '"1-abc"'}
        mock_resource.return_value.head.return_value = (mock_head_response, None)
        
        mock_delete_response = Mock()
        mock_delete_response.status_code = 200
        mock_delete_response.json.return_value = {"ok": True, "id": "doc123", "rev": "2-def"}
        mock_resource.return_value.delete.return_value = (mock_delete_response, {"ok": True, "id": "doc123", "rev": "2-def"})
        
        db = client.Database(mock_resource, "testdb")
        doc = {"_id": "doc123", "_rev": "1-abc", "name": "test"}
        result = db.delete(doc)
        
        assert result is None  # delete method doesn't return anything
        mock_resource.assert_called_once_with("doc123")

    def test_database_delete_invalid_document(self):
        """Test Database delete method with invalid document."""
        db = client.Database(Mock(), "testdb")
        doc = {"name": "test"}  # Missing _id
        
        with pytest.raises(ValueError, match="Invalid document, missing _id attr"):
            db.delete(doc)

    def test_database_delete_not_found(self):
        """Test Database delete method with not found."""
        mock_resource = Mock()
        mock_resource.return_value.head.side_effect = exceptions.NotFound("Document not found")
        
        db = client.Database(mock_resource, "testdb")
        
        with pytest.raises(exceptions.NotFound, match="Document not found"):
            db.delete("doc123")

    def test_database_delete_bulk_success(self):
        """Test Database delete_bulk method success."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = [
            {"ok": True, "id": "doc1", "rev": "2-abc"},
            {"ok": True, "id": "doc2", "rev": "2-def"}
        ]
        mock_resource.post.return_value = (mock_response, [
            {"ok": True, "id": "doc1", "rev": "2-abc"},
            {"ok": True, "id": "doc2", "rev": "2-def"}
        ])
        
        db = client.Database(mock_resource, "testdb")
        docs = [
            {"_id": "doc1", "_rev": "1-abc", "name": "doc1"},
            {"_id": "doc2", "_rev": "1-def", "name": "doc2"}
        ]
        result = db.delete_bulk(docs)
        
        assert len(result) == 2
        assert result[0]["ok"] is True
        assert result[1]["ok"] is True
        
        # Check that _deleted flag was added
        expected_docs = [
            {"_id": "doc1", "_rev": "1-abc", "name": "doc1", "_deleted": True},
            {"_id": "doc2", "_rev": "1-def", "name": "doc2", "_deleted": True}
        ]
        mock_resource.post.assert_called_once_with("_bulk_docs", 
                                                 data=json.dumps({"docs": expected_docs}).encode(),
                                                 params={"all_or_nothing": "true"})

    def test_database_delete_bulk_without_transaction(self):
        """Test Database delete_bulk method without transaction."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = [{"ok": True, "id": "doc1", "rev": "2-abc"}]
        mock_resource.post.return_value = (mock_response, [{"ok": True, "id": "doc1", "rev": "2-abc"}])
        
        db = client.Database(mock_resource, "testdb")
        docs = [{"_id": "doc1", "_rev": "1-abc", "name": "doc1"}]
        result = db.delete_bulk(docs, transaction=False)
        
        # The method sends docs with _rev included
        expected_docs = [{"_id": "doc1", "_rev": "1-abc", "name": "doc1", "_deleted": True}]
        mock_resource.post.assert_called_once_with("_bulk_docs", 
                                                 data=json.dumps({"docs": expected_docs}).encode(),
                                                 params={"all_or_nothing": "false"})

    def test_database_delete_bulk_conflict(self):
        """Test Database delete_bulk method with conflict."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = [
            {"ok": True, "id": "doc1", "rev": "2-abc"},
            {"error": "conflict", "reason": "Document conflict"}
        ]
        mock_resource.post.return_value = (mock_response, [
            {"ok": True, "id": "doc1", "rev": "2-abc"},
            {"error": "conflict", "reason": "Document conflict"}
        ])
        
        db = client.Database(mock_resource, "testdb")
        docs = [
            {"_id": "doc1", "_rev": "1-abc", "name": "doc1"},
            {"_id": "doc2", "_rev": "1-def", "name": "doc2"}
        ]
        
        with pytest.raises(exceptions.Conflict, match="one or more docs are not saved"):
            db.delete_bulk(docs)

    def test_database_all_success(self):
        """Test Database all method success."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rows": [
                {"id": "doc1", "key": "doc1", "value": {"rev": "1-abc"}, "doc": {"_id": "doc1", "name": "doc1"}},
                {"id": "doc2", "key": "doc2", "value": {"rev": "1-def"}, "doc": {"_id": "doc2", "name": "doc2"}}
            ]
        }
        mock_resource.get.return_value = (mock_response, {
            "rows": [
                {"id": "doc1", "key": "doc1", "value": {"rev": "1-abc"}, "doc": {"_id": "doc1", "name": "doc1"}},
                {"id": "doc2", "key": "doc2", "value": {"rev": "1-def"}, "doc": {"_id": "doc2", "name": "doc2"}}
            ]
        })
        
        db = client.Database(mock_resource, "testdb")
        result = list(db.all())
        
        assert len(result) == 2
        assert result[0]["id"] == "doc1"
        assert result[1]["id"] == "doc2"
        mock_resource.get.assert_called_once_with("_all_docs", params={"include_docs": "true"})

    def test_database_all_with_keys(self):
        """Test Database all method with keys parameter."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"rows": []}
        mock_resource.post.return_value = (mock_response, {"rows": []})
        
        db = client.Database(mock_resource, "testdb")
        result = list(db.all(keys=["doc1", "doc2"]))
        
        assert result == []
        mock_resource.post.assert_called_once_with("_all_docs", 
                                                 params={"include_docs": "true"},
                                                 data=json.dumps({"keys": ["doc1", "doc2"]}).encode())

    def test_database_all_with_flat(self):
        """Test Database all method with flat parameter."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rows": [
                {"id": "doc1", "key": "doc1", "value": {"rev": "1-abc"}},
                {"id": "doc2", "key": "doc2", "value": {"rev": "1-def"}}
            ]
        }
        mock_resource.get.return_value = (mock_response, {
            "rows": [
                {"id": "doc1", "key": "doc1", "value": {"rev": "1-abc"}},
                {"id": "doc2", "key": "doc2", "value": {"rev": "1-def"}}
            ]
        })
        
        db = client.Database(mock_resource, "testdb")
        result = list(db.all(flat="id"))
        
        assert result == ["doc1", "doc2"]

    def test_database_all_as_list(self):
        """Test Database all method with as_list=True."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rows": [
                {"id": "doc1", "key": "doc1", "value": {"rev": "1-abc"}}
            ]
        }
        mock_resource.get.return_value = (mock_response, {
            "rows": [
                {"id": "doc1", "key": "doc1", "value": {"rev": "1-abc"}}
            ]
        })
        
        db = client.Database(mock_resource, "testdb")
        result = db.all(as_list=True)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "doc1"

    def test_database_cleanup(self):
        """Test Database cleanup method."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_resource.return_value.post.return_value = (mock_response, {"ok": True})
        
        db = client.Database(mock_resource, "testdb")
        result = db.cleanup()
        
        assert result == {"ok": True}
        mock_resource.assert_called_once_with("_view_cleanup")

    def test_database_commit(self):
        """Test Database commit method."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_resource.post.return_value = (mock_response, {"ok": True})
        
        db = client.Database(mock_resource, "testdb")
        result = db.commit()
        
        assert result == {"ok": True}
        mock_resource.post.assert_called_once_with("_ensure_full_commit")

    def test_database_compact(self):
        """Test Database compact method."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_resource.return_value.post.return_value = (mock_response, {"ok": True})
        
        db = client.Database(mock_resource, "testdb")
        result = db.compact()
        
        assert result == {"ok": True}
        mock_resource.assert_called_once_with("_compact")

    def test_database_compact_view_success(self):
        """Test Database compact_view method success."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_resource.return_value.post.return_value = (mock_response, {"ok": True})
        
        db = client.Database(mock_resource, "testdb")
        result = db.compact_view("test_design")
        
        assert result == {"ok": True}
        mock_resource.assert_called_once_with("_compact", "test_design")

    def test_database_compact_view_not_found(self):
        """Test Database compact_view method with not found."""
        mock_resource = Mock()
        mock_resource.return_value.post.side_effect = exceptions.NotFound("Design document not found")
        
        db = client.Database(mock_resource, "testdb")
        
        with pytest.raises(exceptions.NotFound, match="Design document not found"):
            db.compact_view("nonexistent_design")

    def test_database_revisions_success(self):
        """Test Database revisions method success."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "_id": "doc123",
            "_rev": "3-ghi",
            "_revs_info": [
                {"rev": "3-ghi", "status": "available"},
                {"rev": "2-def", "status": "available"},
                {"rev": "1-abc", "status": "available"}
            ]
        }
        # Mock the initial call to get _revs_info
        mock_resource.return_value.get.return_value = (mock_response, {
            "_id": "doc123",
            "_rev": "3-ghi",
            "_revs_info": [
                {"rev": "3-ghi", "status": "available"},
                {"rev": "2-def", "status": "available"},
                {"rev": "1-abc", "status": "available"}
            ]
        })
        
        # Mock the subsequent calls to get each revision
        def mock_get_side_effect(*args, **kwargs):
            if 'rev' in kwargs.get('params', {}):
                rev = kwargs['params']['rev']
                if rev == "3-ghi":
                    return (Mock(status_code=200), {"_id": "doc123", "_rev": "3-ghi"})
                elif rev == "2-def":
                    return (Mock(status_code=200), {"_id": "doc123", "_rev": "2-def"})
                elif rev == "1-abc":
                    return (Mock(status_code=200), {"_id": "doc123", "_rev": "1-abc"})
            # Default response for _revs_info call
            return (mock_response, {
                "_id": "doc123",
                "_rev": "3-ghi",
                "_revs_info": [
                    {"rev": "3-ghi", "status": "available"},
                    {"rev": "2-def", "status": "available"},
                    {"rev": "1-abc", "status": "available"}
                ]
            })
        
        mock_resource.return_value.get.side_effect = mock_get_side_effect
        
        db = client.Database(mock_resource, "testdb")
        result = list(db.revisions("doc123"))
        
        assert len(result) == 3
        assert result[0]["_id"] == "doc123"
        assert result[0]["_rev"] == "3-ghi"
        assert result[1]["_rev"] == "2-def"
        assert result[2]["_rev"] == "1-abc"
        # The method calls resource 4 times: once for _revs_info, then once for each revision
        assert mock_resource.call_count == 4

    def test_database_revisions_not_found(self):
        """Test Database revisions method with not found."""
        mock_resource = Mock()
        mock_resource.return_value.get.side_effect = exceptions.NotFound("Document not found")
        
        db = client.Database(mock_resource, "testdb")
        
        with pytest.raises(exceptions.NotFound, match="Document not found"):
            list(db.revisions("doc123"))

    def test_database_revisions_with_params(self):
        """Test Database revisions method with parameters."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "_id": "doc123",
            "_rev": "1-abc",
            "_revs_info": [
                {"rev": "1-abc", "status": "available"}
            ]
        }
        # Mock the initial call to get _revs_info
        mock_resource.return_value.get.return_value = (mock_response, {
            "_id": "doc123",
            "_rev": "1-abc",
            "_revs_info": [
                {"rev": "1-abc", "status": "available"}
            ]
        })
        
        # Mock the subsequent call to get the revision
        def mock_get_side_effect(*args, **kwargs):
            if 'rev' in kwargs.get('params', {}):
                rev = kwargs['params']['rev']
                if rev == "1-abc":
                    return (Mock(status_code=200), {"_id": "doc123", "_rev": "1-abc"})
            # Default response for _revs_info call
            return (mock_response, {
                "_id": "doc123",
                "_rev": "1-abc",
                "_revs_info": [
                    {"rev": "1-abc", "status": "available"}
                ]
            })
        
        mock_resource.return_value.get.side_effect = mock_get_side_effect
        
        db = client.Database(mock_resource, "testdb")
        result = list(db.revisions("doc123", status="available", limit=10))
        
        assert len(result) == 1
        # The method calls get twice: once for _revs_info, once for the actual revision
        assert mock_resource.return_value.get.call_count == 2

    def test_database_put_attachment_success(self):
        """Test Database put_attachment method success."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"ok": True, "id": "doc123", "rev": "2-def"}
        mock_resource.return_value.put.return_value = (mock_response, {"ok": True, "id": "doc123", "rev": "2-def"})
        
        # Mock the get call that happens at the end of put_attachment
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"_id": "doc123", "_rev": "2-def", "name": "test", "_attachments": {"test.txt": {"content_type": "text/plain"}}}
        mock_resource.return_value.get.return_value = (mock_get_response, {"_id": "doc123", "_rev": "2-def", "name": "test", "_attachments": {"test.txt": {"content_type": "text/plain"}}})
        
        db = client.Database(mock_resource, "testdb")
        doc = {"_id": "doc123", "_rev": "1-abc", "name": "test"}
        content = b"Hello, World!"
        
        with patch('pycouchdb.client.mimetypes.guess_type', return_value=('text/plain', None)):
            result = db.put_attachment(doc, content, "test.txt")
        
        assert result["_id"] == "doc123"
        assert result["_rev"] == "2-def"
        assert "_attachments" in result
        assert "test.txt" in result["_attachments"]
        # The method calls resource twice: once for PUT, once for GET
        assert mock_resource.call_count == 2
        # Check that resource was called with doc123 twice
        assert mock_resource.call_args_list == [call("doc123"), call("doc123")]

    def test_database_put_attachment_with_content_type(self):
        """Test Database put_attachment method with explicit content type."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"ok": True, "id": "doc123", "rev": "2-def"}
        mock_resource.return_value.put.return_value = (mock_response, {"ok": True, "id": "doc123", "rev": "2-def"})
        
        # Mock the get call that happens at the end of put_attachment
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"_id": "doc123", "_rev": "2-def", "name": "test", "_attachments": {"test.txt": {"content_type": "text/plain"}}}
        mock_resource.return_value.get.return_value = (mock_get_response, {"_id": "doc123", "_rev": "2-def", "name": "test", "_attachments": {"test.txt": {"content_type": "text/plain"}}})
        
        db = client.Database(mock_resource, "testdb")
        doc = {"_id": "doc123", "_rev": "1-abc", "name": "test"}
        content = b"Hello, World!"
        
        result = db.put_attachment(doc, content, "test.txt", content_type="text/plain")
        
        assert result["_attachments"]["test.txt"]["content_type"] == "text/plain"

    def test_database_get_attachment_success(self):
        """Test Database get_attachment method success."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"Hello, World!"
        mock_resource.return_value.get.return_value = (mock_response, None)
        
        db = client.Database(mock_resource, "testdb")
        doc = {"_id": "doc123", "_rev": "1-abc", "_attachments": {"test.txt": {"content_type": "text/plain"}}}
        
        result = db.get_attachment(doc, "test.txt")
        
        assert result == b"Hello, World!"
        mock_resource.assert_called_once_with("doc123")
        mock_resource.return_value.get.assert_called_once_with("test.txt", stream=False, params={"rev": "1-abc"})

    def test_database_get_attachment_stream(self):
        """Test Database get_attachment method with stream=True."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"Hello, World!"
        mock_resource.return_value.get.return_value = (mock_response, None)
        
        db = client.Database(mock_resource, "testdb")
        doc = {"_id": "doc123", "_rev": "1-abc", "_attachments": {"test.txt": {"content_type": "text/plain"}}}
        
        result = db.get_attachment(doc, "test.txt", stream=True)
        
        assert hasattr(result, 'iter_content')
        assert hasattr(result, 'iter_lines')
        assert hasattr(result, 'raw')
        assert hasattr(result, 'url')

    def test_database_get_attachment_not_found(self):
        """Test Database get_attachment method with not found."""
        mock_resource = Mock()
        mock_resource.return_value.get.side_effect = exceptions.NotFound("Attachment not found")
        
        db = client.Database(mock_resource, "testdb")
        doc = {"_id": "doc123", "_rev": "1-abc", "_attachments": {"test.txt": {"content_type": "text/plain"}}}
        
        with pytest.raises(exceptions.NotFound, match="Attachment not found"):
            db.get_attachment(doc, "test.txt")

    def test_database_delete_attachment_success(self):
        """Test Database delete_attachment method success."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "id": "doc123", "rev": "2-def"}
        mock_resource.return_value.delete.return_value = (mock_response, {"ok": True, "id": "doc123", "rev": "2-def"})
        
        db = client.Database(mock_resource, "testdb")
        doc = {
            "_id": "doc123", 
            "_rev": "1-abc", 
            "_attachments": {"test.txt": {"content_type": "text/plain"}}
        }
        
        result = db.delete_attachment(doc, "test.txt")
        
        assert result["_id"] == "doc123"
        assert result["_rev"] == "2-def"
        assert "_attachments" not in result
        mock_resource.assert_called_once_with("doc123")
        mock_resource.return_value.delete.assert_called_once_with("test.txt", params={'rev': '1-abc'})

    def test_database_delete_attachment_not_found(self):
        """Test Database delete_attachment method with not found."""
        mock_resource = Mock()
        mock_resource.return_value.delete.side_effect = exceptions.NotFound("Attachment not found")
        
        db = client.Database(mock_resource, "testdb")
        doc = {"_id": "doc123", "_rev": "1-abc"}
        
        with pytest.raises(exceptions.NotFound, match="Attachment not found"):
            db.delete_attachment(doc, "test.txt")

    def test_database_one_success(self):
        """Test Database one method success."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rows": [
                {"id": "doc1", "key": "doc1", "value": 1}
            ]
        }
        mock_resource.return_value.get.return_value = (mock_response, {
            "rows": [
                {"id": "doc1", "key": "doc1", "value": 1}
            ]
        })
        
        db = client.Database(mock_resource, "testdb")
        result = db.one("test/view")
        
        assert result == {"id": "doc1", "key": "doc1", "value": 1}
        mock_resource.assert_called_once_with("_design", "test", "_view", "view")

    def test_database_one_not_found(self):
        """Test Database one method with no results."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"rows": []}
        mock_resource.return_value.get.return_value = (mock_response, {"rows": []})
        
        db = client.Database(mock_resource, "testdb")
        result = db.one("test/view")
        
        assert result is None

    def test_database_one_with_flat(self):
        """Test Database one method with flat parameter."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rows": [
                {"id": "doc1", "key": "doc1", "value": 1}
            ]
        }
        mock_resource.return_value.get.return_value = (mock_response, {
            "rows": [
                {"id": "doc1", "key": "doc1", "value": 1}
            ]
        })
        
        db = client.Database(mock_resource, "testdb")
        result = db.one("test/view", flat="value")
        
        assert result == 1

    def test_database_query_success(self):
        """Test Database query method success."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rows": [
                {"id": "doc1", "key": "doc1", "value": 1},
                {"id": "doc2", "key": "doc2", "value": 2}
            ]
        }
        mock_resource.return_value.get.return_value = (mock_response, {
            "rows": [
                {"id": "doc1", "key": "doc1", "value": 1},
                {"id": "doc2", "key": "doc2", "value": 2}
            ]
        })
        
        db = client.Database(mock_resource, "testdb")
        result = list(db.query("test/view"))
        
        assert len(result) == 2
        assert result[0]["id"] == "doc1"
        assert result[1]["id"] == "doc2"
        mock_resource.assert_called_once_with("_design", "test", "_view", "view")

    def test_database_query_with_pagination(self):
        """Test Database query method with pagination."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rows": [
                {"id": "doc1", "key": "doc1", "value": 1}
            ]
        }
        mock_resource.return_value.get.return_value = (mock_response, {
            "rows": [
                {"id": "doc1", "key": "doc1", "value": 1}
            ]
        })
        
        db = client.Database(mock_resource, "testdb")
        result = list(db.query("test/view", pagesize=1))
        
        assert len(result) == 1
        assert result[0]["id"] == "doc1"

    def test_database_query_invalid_pagesize(self):
        """Test Database query method with invalid pagesize."""
        db = client.Database(Mock(), "testdb")
        
        with pytest.raises(AssertionError, match="pagesize should be a positive integer"):
            list(db.query("test/view", pagesize="invalid"))
        
        with pytest.raises(AssertionError, match="pagesize should be a positive integer"):
            list(db.query("test/view", pagesize=0))

    def test_database_query_with_limit(self):
        """Test Database query method with limit."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rows": [
                {"id": "doc1", "key": "doc1", "value": 1}
            ]
        }
        mock_resource.return_value.get.return_value = (mock_response, {
            "rows": [
                {"id": "doc1", "key": "doc1", "value": 1}
            ]
        })
        
        db = client.Database(mock_resource, "testdb")
        result = list(db.query("test/view", pagesize=10, limit=1))
        
        assert len(result) == 1
        assert result[0]["id"] == "doc1"

    def test_database_changes_list_success(self):
        """Test Database changes_list method success."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "last_seq": 100,
            "results": [
                {"seq": 1, "id": "doc1", "changes": [{"rev": "1-abc"}]},
                {"seq": 2, "id": "doc2", "changes": [{"rev": "1-def"}]}
            ]
        }
        mock_resource.return_value.get.return_value = (mock_response, {
            "last_seq": 100,
            "results": [
                {"seq": 1, "id": "doc1", "changes": [{"rev": "1-abc"}]},
                {"seq": 2, "id": "doc2", "changes": [{"rev": "1-def"}]}
            ]
        })
        
        db = client.Database(mock_resource, "testdb")
        last_seq, changes = db.changes_list()
        
        assert last_seq == 100
        assert len(changes) == 2
        assert changes[0]["id"] == "doc1"
        assert changes[1]["id"] == "doc2"
        mock_resource.assert_called_once_with("_changes")

    def test_database_changes_list_with_params(self):
        """Test Database changes_list method with parameters."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"last_seq": 100, "results": []}
        mock_resource.return_value.get.return_value = (mock_response, {"last_seq": 100, "results": []})
        
        db = client.Database(mock_resource, "testdb")
        last_seq, changes = db.changes_list(since=50, limit=10)
        
        assert last_seq == 100
        assert changes == []
        mock_resource.assert_called_once_with("_changes")
        mock_resource.return_value.get.assert_called_once_with(params={"since": 50, "limit": 10})

    def test_database_changes_feed(self):
        """Test Database changes_feed method."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'{"seq": 1, "id": "doc1"}',
            b'{"seq": 2, "id": "doc2"}',
            b''  # Empty line (heartbeat)
        ]
        mock_resource.post.return_value = (mock_response, None)
        
        db = client.Database(mock_resource, "testdb")
        messages_received = []
        
        def mock_feed_reader(message, db):
            messages_received.append(message)
            if len(messages_received) >= 2:
                raise exceptions.FeedReaderExited()
        
        with patch('pycouchdb.client._listen_feed') as mock_listen:
            db.changes_feed(mock_feed_reader)
            mock_listen.assert_called_once()

    def test_database_changes_feed_with_options(self):
        """Test Database changes_feed method with options."""
        mock_resource = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = []
        mock_resource.post.return_value = (mock_response, None)
        
        db = client.Database(mock_resource, "testdb")
        
        def mock_feed_reader(message, db):
            pass
        
        with patch('pycouchdb.client._listen_feed') as mock_listen:
            db.changes_feed(mock_feed_reader, 
                          feed="longpoll",
                          since=100,
                          limit=50)
            
            mock_listen.assert_called_once()
            call_args = mock_listen.call_args
            assert call_args[1]['feed'] == "longpoll"
            assert call_args[1]['since'] == 100
            assert call_args[1]['limit'] == 50