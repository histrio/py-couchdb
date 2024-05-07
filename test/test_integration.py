# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

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
        {"_id": "kk1", "name": "Florian"},
        {"_id": "kk2", "name": "Raphael"},
        {"_id": "kk3", "name": "Jaideep"},
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
    records = list(db.query("testing/names", pagesize=1))
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

