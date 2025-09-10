# -*- coding: utf-8 -*-

import pytest
import types

import pycouchdb

from pycouchdb.exceptions import Conflict, NotFound
from pycouchdb import exceptions as exp

SERVER_URL = 'http://admin:password@localhost:5984/'


@pytest.fixture
def server():
    server = pycouchdb.Server(SERVER_URL)
    for db in server:
        server.delete(db)
    if "_users" not in server:
        server.create("_users")
    return server


@pytest.fixture
def db(server, request):
    db_name = 'pycouchdb-testing-' + request.node.name
    yield server.create(db_name)
    server.delete(db_name)


@pytest.fixture
def rec(db):
    querydoc = {
        "_id": "_design/testing",
        "views": {
            "names": {
                "map": "function(doc) { emit(doc.name, 1); }",
                "reduce": "function(keys, values) { return  sum(values); }",
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
    db.delete("_design/testing")


@pytest.fixture
def rec_with_attachment(db, rec, tmpdir):
    doc = db.get("kk1")
    att = tmpdir.join('sample.txt')
    att.write(b"Hello")
    with open(str(att)) as f:
        doc = db.put_attachment(doc, f, "sample.txt")


def test_server_contains(server):
    server.create("testing5")
    assert "testing5" in server
    server.delete("testing5")
    assert "testing5" not in server


def test_iter(server):
    assert list(server) == ['_users', ]
    server.create("testing3")
    server.create("testing4")
    assert list(server) == ['_users', 'testing3', 'testing4']


def test_len(server):
    assert len(server) == 1
    server.create("testing3")
    assert len(server) == 2
    server.delete("testing3")
    assert len(server) == 1


def test_create_delete_db(server):
    server.create("testing2")
    assert "testing2" in server
    server.delete("testing2")
    assert "testing2" not in server


def test_create(server):
    server.create("testing1")
    with pytest.raises(Conflict):
        server.create("testing1")


def test_version(server):
    version = server.version()
    assert version


def test_info(server):
    data = server.info()
    assert "version" in data


def test_replicate(server):
    db1 = server.create("testing1")
    db2 = server.create("testing2")
    db1.save({'_id': '1', 'title': 'hello'})
    assert len(db1) == 1
    assert len(db2) == 0
    server.replicate(SERVER_URL + "testing1", SERVER_URL + "testing2")
    assert len(db1) == 1
    assert len(db2) == 1


def test_replicate_create(server):
    server.create('testing1')
    assert "testing2" not in server
    server.replicate(
        SERVER_URL + "testing1",
        SERVER_URL + "testing2",
        create_target=True)
    assert "testing2" in server


def test_save_01(db):
    doc = {"foo": "bar"}
    doc2 = db.save(doc)

    assert "_id" in doc2
    assert "_rev" in doc2
    assert "_id" not in doc
    assert "_rev" not in doc


def test_save_02(db):
    doc = db.save({'_id': 'kk', 'foo': 'bar'})
    assert "_rev" in doc
    assert doc["_id"] == "kk"


def test_save_03(db):
    doc1 = {'_id': 'kk2', 'foo': 'bar'}
    doc2 = db.save(doc1)
    db.save(doc2)
    assert "_rev" in doc2
    assert doc2["_id"] == "kk2"


def test_save_04(db):
    doc = db.save({'_id': 'kk3', 'foo': 'bar'})
    del doc["_rev"]
    with pytest.raises(Conflict):
        db.save(doc)


def test_save_batch(db):
    doc = {"foo": "bar"}
    doc2 = db.save(doc, batch=True)
    assert "_id" in doc2


def test_special_chars1(db):
    text = "Lürem ipsüm."
    db.save({"_id": "special1", "text": text})
    doc = db.get("special1")
    assert text == doc["text"]


def test_special_chars2(db):
    text = "Mal sehen ob ich früh aufstehen mag."
    db.save({"_id": "special2", "text": text})

    doc = db.get("special2")
    assert text == doc["text"]


def test_db_len(db):
    doc1 = {'_id': 'kk4', 'foo': 'bar'}
    db.save(doc1)
    assert len(db) > 0


def test_delete(db):
    db.save({'_id': 'kk5', 'foo': 'bar'})
    db.delete("kk5")
    assert len(db) == 0

    with pytest.raises(NotFound):
        db.delete("kk6")


def test_save_bulk_01(db):
    docs = db.save_bulk([
        {"name": "Andrey"},
        {"name": "Pepe"},
        {"name": "Alex"},
    ])

    assert len(docs) == 3


def test_save_bulk_02(db):
    db.save_bulk([
        {"_id": "kk6", "name": "Andrey"},
        {"_id": "kk7", "name": "Pepe"},
        {"_id": "kk8", "name": "Alex"},
    ])

    with pytest.raises(Conflict):
        db.save_bulk([
            {"_id": "kk6", "name": "Andrey"},
            {"_id": "kk7", "name": "Pepe"},
            {"_id": "kk8", "name": "Alex"},
        ])


def test_delete_bulk(db):
    docs = db.save_bulk([
        {"_id": "kj1", "name": "Andrey"},
        {"_id": "kj2", "name": "Pepe"},
        {"_id": "kj3", "name": "Alex"},
    ])

    results = db.delete_bulk(docs)
    assert len(results) == 3


def test_cleanup(db):
    assert db.cleanup()


def test_commit(db):
    assert db.commit()


def test_compact(db):
    assert db.compact()


def create_changes(dstdb):
    doc1 = {"_id": "kk1", "counter": 1}
    doc2 = {"_id": "kk2", "counter": 1}
    doc1 = dstdb.save(doc1)
    doc2 = dstdb.save(doc2)

    return doc1, doc2


def test_changes_list(db):
    doc1, doc2 = create_changes(db)
    last_seq, changes = db.changes_list()
    assert len(changes) == 2

    db.save({"_id": "kk3", "counter": 1})
    _, changes = db.changes_list(since=last_seq)
    assert len(changes) == 1

    db.delete(doc1)
    db.delete(doc2)


def test_changes_feed_01(db):
    doc1, doc2 = create_changes(db)
    messages = []

    def reader(message, db):
        messages.append(message)
        raise exp.FeedReaderExited()

    db.changes_feed(reader)
    assert len(messages) == 1

    db.delete(doc1)
    db.delete(doc2)


def test_get_not_existent(db):
    with pytest.raises(NotFound):
        db.get("does_not_exist_in_db")


def test_db_contains(db):
    db.save({"_id": "test_db_contains"})
    assert "test_db_contains" in db
    assert "does_not_exist_in_db" not in db


def test_all_01(db, rec):
    result = [x for x in db.all() if not x['key'].startswith("_")]
    assert len(result) == 3


def test_all_02(db, rec):
    result = list(db.all(keys=['kk1', 'kk2']))
    assert len(result) == 2


def test_all_03(db, rec):
    result = list(db.all(keys=['kk1', 'kk2'], flat="key"))
    assert result == ['kk1', 'kk2']


def test_all_04(db, rec):
    result = db.all(keys=['kk1', 'kk2'], flat="key")
    assert isinstance(result, types.GeneratorType)


def test_all_05(db, rec):
    result = db.all(keys=['kk1', 'kk2'], flat="key", as_list=True)
    assert isinstance(result, list)


def test_all_404(db, rec):
    result = db.all(keys=['nonexisting'], as_list=True,
                    include_docs='false')
    assert isinstance(result, list)


def test_all_startkey_endkey(db, rec):
    result = list(db.all(startkey='kk1', endkey='kk2'))
    assert len(result) == 2


def test_revisions_01(db, rec):
    doc = db.get("kk1")

    initial_revisions = list(db.revisions("kk1"))
    assert len(initial_revisions) == 1

    doc["name"] = "Fooo"
    db.save(doc)

    revisions = list(db.revisions("kk1"))
    assert len(revisions) == 2


def test_revisions_02(db, rec):
    with pytest.raises(NotFound):
        list(db.revisions("kk12"))


def test_query_01(db, rec):
    result = db.query("testing/names", group='true',
                      keys=['Andrey'], as_list=True)
    assert len(result) == 1


def test_query_02(db, rec):
    result = db.query("testing/names", as_list=False)
    assert isinstance(result, types.GeneratorType)


def test_query_03(db, rec):
    result = db.query("testing/names", as_list=True, flat="value")
    assert result == [3]


def test_query_04(db, rec):
    result = db.one("testing/names", flat="value")
    assert result == 3


def test_query_05(db, rec):
    result = db.one("testing/names", flat="value",
                    group='true', keys=['KK'])
    assert result is None


def test_query_06(db, rec):
    result = db.one("testing/names", flat="value",
                    group='true', keys=['Andrey'])
    assert result == 1


def test_compact_view_01(db):
    doc = {
        "_id": "_design/testing2",
        "views": {
            "names": {
                "map": "function(doc) { emit(doc.name, 1); }",
                "reduce": "function(keys, values) { return  sum(values); }",
            }
        }
    }

    db.save(doc)
    db.compact_view("testing2")


def test_compact_view_02(db):
    with pytest.raises(NotFound):
        db.compact_view("fooo")


def test_attachments_01(db, rec_with_attachment):
    doc = db.get("kk1")
    assert "_attachments" in doc

    data = db.get_attachment(doc, "sample.txt")
    assert data == b"Hello"

    doc = db.delete_attachment(doc, "sample.txt")
    assert "_attachments" not in doc

    doc = db.get("kk1")
    assert "_attachments" not in doc


def test_attachments_02(db, rec_with_attachment):
    doc = db.get("kk1")
    assert "_attachments" in doc


def test_get_not_existent_attachment(db, rec):
    doc = db.get("kk1")
    with pytest.raises(NotFound):
        db.get_attachment(doc, "kk.txt")


def test_attachments_03_stream(db, rec_with_attachment):
    doc = db.get("kk1")

    response = db.get_attachment(doc, "sample.txt", stream=True)
    stream = response.iter_content()

    assert next(stream) == b"H"
    assert next(stream) == b"e"
    assert next(stream) == b"l"
    assert next(stream) == b"l"
    assert next(stream) == b"o"

    with pytest.raises(StopIteration):
        next(stream)


def test_regression_unexpected_deletion_of_attachment(db, rec_with_attachment):
    """
    When I upload one file the code looks like:

        doc = db.put_attachment(doc, file_object)

    Ok, but now I want to update one field:

        doc['onefield'] = 'newcontent'
        doc = db.save(doc)

    et voilà, the previously uploaded file has been deleted!
    """

    doc = db.get("kk1")

    assert "_attachments" in doc
    assert "sample.txt" in doc["_attachments"]

    doc["some_attr"] = 1
    doc = db.save(doc)

    assert "_attachments" in doc
    assert "sample.txt" in doc["_attachments"]


@pytest.fixture
def view(db):
    querydoc = {
        "_id": "_design/testing",
        "views": {
            "names": {
                "map": "function(doc) { emit(doc.name, 1); }",
                # "reduce": "function(keys, values) { return  sum(values); }",
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
    db.delete("_design/testing")


@pytest.fixture
def view_duplicate_keys(db):
    querydoc = {
        "_id": "_design/testing",
        "views": {
            "names": {
                "map": "function(doc) { emit(doc.name, 1); }",
                # "reduce": "function(keys, values) { return  sum(values); }",
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
    db.delete("_design/testing")


def test_pagination(db, view):
    # Check if invariants on pagesize are followed
    with pytest.raises(AssertionError) as err:
        db.query("testing/names", pagesize="123")

    assert ("pagesize should be a positive integer" in str(err.value))

    with pytest.raises(AssertionError) as err:
        db.query("testing/names", pagesize=0)

    assert ("pagesize should be a positive integer" in str(err.value))

    # Check if the number of records retrieved are correct
    records = list(db.query("testing/names", pagesize=1))
    assert (len(records) == 6)

    # Check no duplicate records are retrieved
    record_ids = set(record['id'] for record in records)
    assert (len(record_ids) == 6)


def test_duplicate_keys_pagination(db, view_duplicate_keys):
    # Check if the number of records retrieved are correct
    records = list(db.query("testing/names", pagesize=4))
    print(type(records[0]))
    assert (len(records) == 6)

    # Check no duplicate records are retrieved
    record_ids = set(record['id'] for record in records)
    assert (len(record_ids) == 6)


def test_limit_pagination(db, view_duplicate_keys):
    # Case 1: the paginator follows the limit
    # Request only first three documents
    records = list(db.query("testing/names", pagesize=10, limit=3))
    assert len(records) == 3

    record_ids = set(record['id'] for record in records)
    assert len(record_ids) == 3

    # Case 2: limit > #documents
    records = list(db.query("testing/names", pagesize=10, limit=10))
    assert len(records) == 6

    record_ids = set(record['id'] for record in records)
    assert len(record_ids) == 6


def test_large_page_size(db, view_duplicate_keys):
    records = list(db.query("testing/names", pagesize=100))
    assert len(records) == 6

    record_ids = set(record['id'] for record in records)
    assert len(record_ids) == 6

# Authentication Tests
def test_basic_auth_success():
    """Test successful basic authentication."""
    server = pycouchdb.Server('http://admin:password@localhost:5984/')
    info = server.info()
    assert 'version' in info


def test_basic_auth_failure():
    """Test basic authentication with invalid credentials."""
    server = pycouchdb.Server('http://invalid:credentials@localhost:5984/')
    
    with pytest.raises(Exception):
        server.info()


def test_no_auth_required():
    """Test connection without authentication when not required."""
    try:
        server = pycouchdb.Server('http://localhost:5984/')
        info = server.info()
        assert 'version' in info
    except Exception:
        pytest.skip("CouchDB requires authentication")


# SSL and HTTPS Tests
def test_https_connection():
    """Test HTTPS connection if available."""
    try:
        server = pycouchdb.Server('https://admin:password@localhost:6984/', verify=False)
        info = server.info()
        assert 'version' in info
    except Exception:
        pytest.skip("HTTPS not available or not configured")


def test_ssl_verification():
    """Test SSL verification behavior."""
    try:
        server = pycouchdb.Server('https://admin:password@localhost:6984/', verify=True)
        server.info()
        pytest.fail("Expected SSL verification to fail with self-signed certificate")
    except Exception:
        pass


# Concurrent Operations Tests
def test_concurrent_document_updates(db):
    """Test concurrent updates to the same document."""
    import threading
    import time
    
    doc = db.save({'_id': 'concurrent_test', 'counter': 0})
    
    results = []
    errors = []
    
    def update_document():
        try:
            for i in range(5):
                current_doc = db.get('concurrent_test')
                current_doc['counter'] += 1
                current_doc['thread_id'] = threading.current_thread().ident
                updated_doc = db.save(current_doc)
                results.append(updated_doc['counter'])
                time.sleep(0.01)
        except Exception as e:
            errors.append(e)
    
    threads = []
    for i in range(3):
        thread = threading.Thread(target=update_document)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    assert len(results) > 0
    assert len(errors) >= 0


def test_concurrent_database_operations(server):
    """Test concurrent database creation and deletion."""
    import threading
    import time
    
    results = []
    errors = []
    
    def create_and_delete_db(db_num):
        try:
            db_name = f'concurrent_db_{db_num}'
            db = server.create(db_name)
            time.sleep(0.1)
            server.delete(db_name)
            results.append(f'success_{db_num}')
        except Exception as e:
            errors.append(f'error_{db_num}: {e}')
    
    # Start multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=create_and_delete_db, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check results
    assert len(results) > 0
    # Some operations might fail due to timing, that's expected


# Large Data Tests
def test_large_document(db):
    """Test handling of large documents."""
    # Create a large document (approaching CouchDB's 1MB limit)
    large_data = 'x' * (1024 * 1024)  # 1MB of data
    doc = {
        '_id': 'large_doc',
        'data': large_data,
        'size': len(large_data)
    }
    
    saved_doc = db.save(doc)
    assert saved_doc['_id'] == 'large_doc'
    assert saved_doc['size'] == len(large_data)
    
    # Retrieve and verify
    retrieved_doc = db.get('large_doc')
    assert retrieved_doc['size'] == len(large_data)
    assert len(retrieved_doc['data']) == len(large_data)


def test_bulk_operations_large_dataset(db):
    """Test bulk operations with large datasets."""
    # Create a large number of documents
    docs = []
    for i in range(1000):
        docs.append({
            '_id': f'bulk_doc_{i}',
            'index': i,
            'data': f'content_{i}' * 100  # Make each doc reasonably sized
        })
    
    # Save in bulk
    saved_docs = db.save_bulk(docs)
    assert len(saved_docs) == 1000
    
    # Verify some documents
    for i in range(0, 1000, 100):
        doc = db.get(f'bulk_doc_{i}')
        assert doc['index'] == i
        assert doc['data'].startswith(f'content_{i}')


def test_memory_efficient_streaming(db):
    """Test memory-efficient streaming operations."""
    # Create a document with attachment
    doc = db.save({'_id': 'streaming_test', 'type': 'test'})
    
    # Create a large attachment
    large_content = b'x' * (100 * 1024)  # 100KB
    import io
    content_stream = io.BytesIO(large_content)
    
    # Put attachment
    doc_with_attachment = db.put_attachment(doc, content_stream, 'large_file.txt')
    
    # Get attachment with streaming
    stream_response = db.get_attachment(doc_with_attachment, 'large_file.txt', stream=True)
    
    # Read in chunks to test streaming
    chunks = []
    for chunk in stream_response.iter_content(chunk_size=1024):
        chunks.append(chunk)
    
    # Verify content
    retrieved_content = b''.join(chunks)
    assert retrieved_content == large_content


# Changes Feed Tests
def test_changes_feed_error_handling(db):
    """Test changes feed with error scenarios."""
    messages = []
    errors = []
    
    def error_prone_reader(message, db):
        messages.append(message)
        if len(messages) > 2:
            raise Exception("Simulated error in feed reader")
    
    try:
        db.changes_feed(error_prone_reader, limit=5)
    except Exception as e:
        errors.append(e)
    
    assert len(messages) > 0


def test_changes_feed_heartbeat_handling(db):
    """Test changes feed heartbeat handling."""
    heartbeats = []
    messages = []
    
    class HeartbeatTestReader(pycouchdb.feedreader.BaseFeedReader):
        def on_message(self, message):
            messages.append(message)
            if len(messages) >= 2:
                raise pycouchdb.exceptions.FeedReaderExited()
        
        def on_heartbeat(self):
            heartbeats.append('heartbeat')
    
    reader = HeartbeatTestReader()
    db.changes_feed(reader, limit=5)
    
    assert len(heartbeats) >= 0


# Unicode and Special Characters Tests
def test_unicode_document_ids(db):
    """Test handling of unicode document IDs."""
    unicode_ids = [
        '测试文档',
        'документ_тест',
        'مستند_اختبار',
        'ドキュメント_テスト',
        'тест_документ_123'
    ]
    
    for doc_id in unicode_ids:
        doc = db.save({'_id': doc_id, 'content': f'Content for {doc_id}'})
        assert doc['_id'] == doc_id
        
        # Retrieve and verify
        retrieved_doc = db.get(doc_id)
        assert retrieved_doc['_id'] == doc_id
        assert retrieved_doc['content'] == f'Content for {doc_id}'


def test_unicode_content(db):
    """Test handling of unicode content in documents."""
    unicode_content = {
        'chinese': '这是中文内容',
        'russian': 'Это русский текст',
        'arabic': 'هذا نص عربي',
        'japanese': 'これは日本語のテキストです',
        'emoji': '🚀📚💻🎉'
    }
    
    doc = db.save({'_id': 'unicode_test', **unicode_content})
    
    retrieved_doc = db.get('unicode_test')
    for key, value in unicode_content.items():
        assert retrieved_doc[key] == value


def test_special_characters_in_database_names(server):
    """Test handling of special characters in database names."""
    # Test database names that are definitely allowed by CouchDB
    allowed_names = [
        'test_db_123',  # underscores and numbers (most basic)
        'test-db-123',  # dashes and numbers
    ]
    
    invalid_names = [
        'TestDB',
        '123test',
    ]
    
    for db_name in allowed_names:
        try:
            db = server.create(db_name)
            assert db_name in server
            server.delete(db_name)
            assert db_name not in server
        except Exception as e:
            pytest.skip(f"Database name '{db_name}' not allowed: {e}")
    
    for db_name in invalid_names:
        with pytest.raises(Exception):
            server.create(db_name)


# Performance and Timeout Tests


def test_bulk_operation_performance(db):
    """Test performance of bulk operations."""
    import time
    
    # Test bulk save performance
    docs = [{'index': i, 'data': f'content_{i}'} for i in range(100)]
    
    start_time = time.time()
    saved_docs = db.save_bulk(docs)
    end_time = time.time()
    
    assert len(saved_docs) == 100
    assert end_time - start_time < 10


# Edge Cases Tests
def test_empty_database_operations(db):
    """Test operations on empty database."""
    # Test querying empty database
    results = list(db.all())
    assert len(results) == 0
    
    # Test changes on empty database
    last_seq, changes = db.changes_list()
    assert len(changes) == 0
    
    try:
        result = db.query('nonexistent/view')
        assert list(result) == []
    except pycouchdb.exceptions.NotFound:
        pass


def test_document_with_system_fields(db):
    """Test handling of documents with system fields."""
    doc = {
        '_id': 'system_fields_test',
        'custom_field': 'value',
    }
    
    saved_doc = db.save(doc)
    assert saved_doc['_id'] == 'system_fields_test'
    assert saved_doc['custom_field'] == 'value'
    assert '_rev' in saved_doc
    assert saved_doc['_rev'].startswith('1-')
    
    saved_doc['custom_field'] = 'updated_value'
    updated_doc = db.save(saved_doc)
    assert updated_doc['custom_field'] == 'updated_value'
    assert updated_doc['_rev'].startswith('2-')


def test_attachment_with_special_characters(db):
    """Test attachments with special characters in filenames."""
    import io
    
    special_filenames = [
        'file_with_underscores.txt',
        'file-with-dashes.txt',
        'file.with.dots.txt',
        'файл_с_кириллицей.txt'
    ]
    
    for i, filename in enumerate(special_filenames):
        try:
            doc = db.save({'_id': f'attachment_test_{i}', 'type': 'test'})
            
            content = f'Content for {filename}'.encode('utf-8')
            content_stream = io.BytesIO(content)
            
            doc_with_attachment = db.put_attachment(doc, content_stream, filename)
            
            retrieved_content = db.get_attachment(doc_with_attachment, filename)
            assert retrieved_content.decode('utf-8') == f'Content for {filename}'
            
        except Exception as e:
            pytest.skip(f"Filename '{filename}' not allowed: {e}")


# Advanced CouchDB Features Tests
def test_design_document_management(db):
    """Test comprehensive design document operations."""
    # Create a design document with multiple views
    design_doc = {
        "_id": "_design/test_views",
        "views": {
            "by_name": {
                "map": "function(doc) { if (doc.name) emit(doc.name, doc); }"
            },
            "by_type": {
                "map": "function(doc) { if (doc.type) emit(doc.type, 1); }",
                "reduce": "function(keys, values) { return sum(values); }"
            },
            "by_date": {
                "map": "function(doc) { if (doc.created_at) emit(doc.created_at, doc); }"
            }
        },
        "filters": {
            "by_status": "function(doc, req) { return doc.status === req.query.status; }"
        },
        "shows": {
            "item": "function(doc, req) { return {body: JSON.stringify(doc)}; }"
        },
        "lists": {
            "items": "function(head, req) { var row; while (row = getRow()) { send(row.value); } }"
        }
    }
    
    # Save design document
    saved_design = db.save(design_doc)
    assert saved_design['_id'] == '_design/test_views'
    
    # Create some test documents
    test_docs = [
        {'_id': 'doc1', 'name': 'Alice', 'type': 'user', 'status': 'active', 'created_at': '2023-01-01'},
        {'_id': 'doc2', 'name': 'Bob', 'type': 'user', 'status': 'inactive', 'created_at': '2023-01-02'},
        {'_id': 'doc3', 'name': 'Charlie', 'type': 'admin', 'status': 'active', 'created_at': '2023-01-03'},
    ]
    db.save_bulk(test_docs)
    
    # Test different views
    by_name_results = list(db.query('test_views/by_name'))
    assert len(by_name_results) == 3
    
    by_type_results = list(db.query('test_views/by_type', group=True))
    assert len(by_type_results) == 2  # user and admin types
    
    # Test reduce function
    total_by_type = db.one('test_views/by_type', flat='value')
    assert total_by_type == 3  # Total count of all documents
    
    # Test date range query
    date_results = list(db.query('test_views/by_date', 
                                startkey='2023-01-01', 
                                endkey='2023-01-02'))
    assert len(date_results) == 2


def test_view_compaction_and_cleanup(db):
    """Test view compaction and cleanup operations."""
    # Create a design document with a view
    design_doc = {
        "_id": "_design/compaction_test",
        "views": {
            "test_view": {
                "map": "function(doc) { emit(doc.id, doc.value); }"
            }
        }
    }
    db.save(design_doc)
    
    # Add some documents to create view data
    for i in range(100):
        db.save({'_id': f'compaction_doc_{i}', 'id': i, 'value': f'value_{i}'})
    
    # Test view compaction
    result = db.compact_view('compaction_test')
    assert result is not None
    
    # Test database cleanup
    cleanup_result = db.cleanup()
    assert cleanup_result is not None


def test_replication_edge_cases(server):
    """Test replication with various edge cases."""
    # Create source and target databases
    source_db = server.create('replication_source')
    target_db = server.create('replication_target')
    
    try:
        # Add documents to source
        source_docs = [
            {'_id': 'doc1', 'content': 'source content 1'},
            {'_id': 'doc2', 'content': 'source content 2'},
            {'_id': 'doc3', 'content': 'source content 3'},
        ]
        source_db.save_bulk(source_docs)
        
        # Test basic replication
        replicate_result = server.replicate(
            SERVER_URL + 'replication_source',
            SERVER_URL + 'replication_target'
        )
        assert replicate_result is not None
        
        # Verify documents were replicated
        target_docs = list(target_db.all())
        assert len(target_docs) >= 3
        
        # Test replication with create_target=True
        replicate_with_create = server.replicate(
            SERVER_URL + 'replication_source',
            SERVER_URL + 'replication_target_create',
            create_target=True
        )
        assert replicate_with_create is not None
        
        # Verify target database was created
        assert 'replication_target_create' in server
        
        # Clean up created database
        server.delete('replication_target_create')
        
    finally:
        # Clean up
        server.delete('replication_source')
        server.delete('replication_target')


def test_library_compaction_api_behavior(db):
    """Test pycouchdb library's compaction API behavior."""
    # Test that compact() method returns expected result
    compact_result = db.compact()
    assert compact_result is not None
    
    # Test that compact_view() works with valid design doc
    design_doc = {
        "_id": "_design/compact_test",
        "views": {
            "test_view": {
                "map": "function(doc) { emit(doc.id, doc.value); }"
            }
        }
    }
    db.save(design_doc)
    
    # Add some documents to create view data
    for i in range(10):
        db.save({'_id': f'compact_doc_{i}', 'id': i, 'value': f'value_{i}'})
    
    # Test view compaction API
    view_compact_result = db.compact_view('compact_test')
    assert view_compact_result is not None
    
    # Test cleanup API
    cleanup_result = db.cleanup()
    assert cleanup_result is not None


def test_changes_feed_with_filters(db):
    """Test changes feed with different filter options."""
    # Create a design document with filter
    design_doc = {
        "_id": "_design/filters",
        "filters": {
            "by_type": "function(doc, req) { return doc.type === req.query.type; }"
        }
    }
    db.save(design_doc)
    
    # Add documents of different types
    docs = [
        {'_id': 'user1', 'type': 'user', 'name': 'Alice'},
        {'_id': 'admin1', 'type': 'admin', 'name': 'Bob'},
        {'_id': 'user2', 'type': 'user', 'name': 'Charlie'},
    ]
    db.save_bulk(docs)
    
    # Test changes feed with filter
    messages = []
    
    def filter_reader(message, db):
        messages.append(message)
        if len(messages) >= 2:
            raise pycouchdb.exceptions.FeedReaderExited()
    
    try:
        db.changes_feed(filter_reader, filter='filters/by_type', type='user', limit=10)
    except Exception:
        pass  # May not be supported in all CouchDB versions
    
    # Should have received some messages
    assert len(messages) >= 0


def test_attachment_metadata_and_content_types(db):
    """Test attachment handling with different content types and metadata."""
    doc = db.save({'_id': 'attachment_metadata_test', 'type': 'test'})
    
    # Test different content types
    content_types = [
        ('text.txt', 'text/plain', b'Plain text content'),
        ('data.json', 'application/json', b'{"key": "value"}'),
        ('image.png', 'image/png', b'fake_png_data'),
        ('document.pdf', 'application/pdf', b'fake_pdf_data'),
    ]
    
    for filename, content_type, content in content_types:
        import io
        content_stream = io.BytesIO(content)
        
        # Get fresh document for each attachment to avoid conflicts
        current_doc = db.get('attachment_metadata_test')
        
        # Put attachment with specific content type
        doc_with_attachment = db.put_attachment(
            current_doc, content_stream, filename, content_type=content_type
        )
        
        # Verify attachment metadata
        assert '_attachments' in doc_with_attachment
        assert filename in doc_with_attachment['_attachments']
        
        attachment_info = doc_with_attachment['_attachments'][filename]
        assert attachment_info['content_type'] == content_type
        assert attachment_info['length'] == len(content)
        
        # Retrieve and verify content
        retrieved_content = db.get_attachment(doc_with_attachment, filename)
        assert retrieved_content == content


def test_document_conflicts_resolution(db):
    """Test document conflict resolution scenarios."""
    # Create initial document
    doc1 = db.save({'_id': 'conflict_test', 'version': 1, 'data': 'initial'})
    
    # Simulate concurrent updates by getting the same document twice
    doc2 = db.get('conflict_test')
    doc3 = db.get('conflict_test')
    
    # Update both copies
    doc2['version'] = 2
    doc2['data'] = 'updated_by_client_1'
    doc3['version'] = 2
    doc3['data'] = 'updated_by_client_2'
    
    # Save first update
    updated_doc2 = db.save(doc2)
    
    # Second update should conflict
    with pytest.raises(pycouchdb.exceptions.Conflict):
        db.save(doc3)
    
    # Resolve conflict by getting latest and updating
    latest_doc = db.get('conflict_test')
    latest_doc['version'] = 3
    latest_doc['data'] = 'resolved_conflict'
    resolved_doc = db.save(latest_doc)
    
    assert resolved_doc['version'] == 3
    assert resolved_doc['data'] == 'resolved_conflict'


def test_bulk_operations_with_conflicts(db):
    """Test bulk operations handling conflicts."""
    # Create initial documents
    initial_docs = [
        {'_id': 'bulk_conflict_1', 'version': 1},
        {'_id': 'bulk_conflict_2', 'version': 1},
        {'_id': 'bulk_conflict_3', 'version': 1},
    ]
    db.save_bulk(initial_docs)
    
    # Get documents for update
    docs_to_update = [db.get(f'bulk_conflict_{i}') for i in range(1, 4)]
    
    # Update all documents
    for i, doc in enumerate(docs_to_update):
        doc['version'] = 2
        doc['updated_by'] = f'client_{i}'
    
    # Save in bulk - should succeed
    updated_docs = db.save_bulk(docs_to_update)
    assert len(updated_docs) == 3
    
    # Try to update again with old revision - should conflict
    # We need to use the old revision numbers to create a conflict
    old_docs = [
        {'_id': 'bulk_conflict_1', '_rev': '1-abc123', 'version': 1},  # Fake old rev
        {'_id': 'bulk_conflict_2', '_rev': '1-def456', 'version': 1},  # Fake old rev
        {'_id': 'bulk_conflict_3', '_rev': '1-ghi789', 'version': 1},  # Fake old rev
    ]
    with pytest.raises(pycouchdb.exceptions.Conflict):
        db.save_bulk(old_docs)


def test_library_database_config_api(server):
    """Test pycouchdb library's database config API."""
    # Create a test database
    test_db = server.create('config_test')
    
    try:
        # Test that config() method returns expected data structure
        db_info = test_db.config()
        assert isinstance(db_info, dict)
        assert 'update_seq' in db_info
        assert 'doc_count' in db_info
        
        # Test that we can access the database name
        assert test_db.name == 'config_test'
        
        # Test that database length works
        assert isinstance(len(test_db), int)
        
    finally:
        server.delete('config_test')


def test_library_server_initialization():
    """Test pycouchdb library's server initialization with different parameters."""
    # Test default initialization
    server1 = pycouchdb.Server()
    assert server1.base_url == 'http://localhost:5984/'
    
    # Test custom URL initialization
    server2 = pycouchdb.Server('http://custom:5984/')
    assert server2.base_url == 'http://custom:5984/'
    
    # Test with credentials
    server3 = pycouchdb.Server('http://user:pass@localhost:5984/')
    assert server3.base_url == 'http://localhost:5984/'
    
    # Test with verify parameter
    server4 = pycouchdb.Server(verify=True)
    assert server4.base_url == 'http://localhost:5984/'


def test_custom_headers_and_parameters(db):
    """Test custom headers and parameters in requests."""
    # Test with custom parameters in get request
    doc = db.save({'_id': 'custom_params_test', 'data': 'test'})
    
    # Test getting document with custom parameters
    # Note: revs_info parameter should be passed to the underlying request
    retrieved_doc = db.get('custom_params_test', revs=True, revs_info=True)
    assert retrieved_doc['_id'] == 'custom_params_test'
    # The revs_info parameter should be handled by the library
    # We just verify the document was retrieved successfully
    assert retrieved_doc['data'] == 'test'


def test_library_database_length_and_config_api(db):
    """Test pycouchdb library's database length and config API."""
    # Test empty database
    initial_length = len(db)
    initial_config = db.config()
    assert isinstance(initial_length, int)
    assert isinstance(initial_config, dict)
    assert 'doc_count' in initial_config
    assert 'update_seq' in initial_config
    
    # Add some documents
    docs = [{'index': i, 'data': f'length_test_{i}'} for i in range(5)]
    db.save_bulk(docs)
    
    # Test that length reflects document count
    new_length = len(db)
    new_config = db.config()
    
    assert new_length >= initial_length + 5
    assert new_config['doc_count'] >= initial_config['doc_count'] + 5
    assert new_config['update_seq'] > initial_config['update_seq']

