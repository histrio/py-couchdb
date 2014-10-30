# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

import unittest
import tempfile
import types
import pycouchdb as couchdb

from pycouchdb.exceptions import Conflict, NotFound
from pycouchdb import exceptions as exp

SERVER_URL = 'http://admin:admin@localhost:5984/'
SERVER_URL = 'http://localhost:5984/'

class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = couchdb.Server(SERVER_URL, authmethod="basic")

    def test_contains(self):
        self.assertIn("_users", self.s)

    def test_iter(self):
        self.assertNotEqual(len(list(self.s)), 0)

    def test_len(self):
        self.assertNotEqual(len(self.s), 0)

    def test_create_delete_db(self):
        db = self.s.create("testing2")
        self.assertIn("testing2", self.s)
        self.s.delete("testing2")
        self.assertNotIn("testing2", self.s)

    def test_create(self):
        db = self.s.create("testing1")
        with self.assertRaises(Conflict):
            self.s.create("testing1")
        self.s.delete("testing1")

    def test_stats_01(self):
        stats = self.s.stats()
        self.assertIn("httpd_status_codes", stats)

    def test_stats_02(self):
        stats = self.s.stats("httpd_status_codes")
        self.assertIn("description", stats)

    def test_version(self):
        version = self.s.version()
        self.assertTrue(version)

    def test_info(self):
        data = self.s.info()
        self.assertIn("version", data)

    def test_config(self):
        data = self.s.config()
        self.assertIn("view_compaction", data)

    def test_replicate(self):
        db1 = self.s.create("testing1")
        db2 = self.s.create("testing2")
        db1.save({'_id': '1', 'title': 'hello'})
        self.assertEqual(len(db1), 1)
        self.assertEqual(len(db2), 0)
        self.s.replicate("testing1", "testing2")
        self.assertEqual(len(db1), 1)
        self.assertEqual(len(db2), 1)
        self.s.delete("testing1")
        self.s.delete("testing2")

    def test_replicate_create(self):
        self.s.create('testing1')
        self.assertNotIn("testing2", self.s)
        self.s.replicate("testing1", "testing2", create_target=True)
        self.assertIn("testing2", self.s)
        self.s.delete("testing1")
        self.s.delete("testing2")


class DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = couchdb.Server(SERVER_URL)
        cls.db = cls.s.create('testing5')

    @classmethod
    def tearDownClass(cls):
        cls.s.delete("testing5")

    def test_save_01(self):
        doc = {"foo": "bar"}
        doc2 = self.db.save(doc)

        self.assertIn("_id", doc2)
        self.assertIn("_rev", doc2)
        self.assertNotIn("_id", doc)
        self.assertNotIn("_rev", doc)

    def test_save_02(self):
        doc = self.db.save({'_id': 'kk', 'foo':'bar'})
        self.assertIn("_rev", doc)
        self.assertEqual(doc["_id"], "kk")

    def test_save_03(self):
        doc1 = {'_id': 'kk2', 'foo':'bar'}
        doc2 = self.db.save(doc1)
        doc3 = self.db.save(doc2)

    def test_save_04(self):
        doc = self.db.save({'_id': 'kk3', 'foo':'bar'})

        del doc["_rev"]
        with self.assertRaises(Conflict):
            doc2 = self.db.save(doc)

    def test_special_chars1(self):
        text="Lürem ipsüm."
        self.db.save({"_id": "special1", "text": text})

        doc = self.db.get("special1")
        self.assertEqual(text, doc["text"])

    def test_special_chars2(self):
        text="Mal sehen ob ich früh aufstehen mag."
        self.db.save({"_id": "special2", "text": text})

        doc = self.db.get("special2")
        self.assertEqual(text, doc["text"])

    def test_len(self):
        doc1 = {'_id': 'kk4', 'foo':'bar'}
        doc2 = self.db.save(doc1)
        self.assertTrue(len(self.db) > 0)

    def test_delete(self):
        doc = self.db.save({'_id': 'kk5', 'foo':'bar'})
        self.db.delete("kk5")
        self.assertEqual(len(self.db), 0)

        with self.assertRaises(NotFound):
            self.db.delete("kk6")

    def test_save_bulk_01(self):
        docs = self.db.save_bulk([
            {"name":"Andrey"},
            {"name":"Pepe"},
            {"name": "Alex"},
        ])

        self.assertEqual(len(docs), 3)

    def test_save_bulk_02(self):
        docs = self.db.save_bulk([
            {"_id": "kk6", "name": "Andrey"},
            {"_id": "kk7", "name": "Pepe"},
            {"_id": "kk8", "name": "Alex"},
        ])

        with self.assertRaises(Conflict):
            docs = self.db.save_bulk([
                {"_id": "kk6", "name": "Andrey"},
                {"_id": "kk7", "name": "Pepe"},
                {"_id": "kk8", "name": "Alex"},
            ])

    def test_delete_bulk(self):
        docs = self.db.save_bulk([
            {"_id": "kj1", "name": "Andrey"},
            {"_id": "kj2", "name": "Pepe"},
            {"_id": "kj3", "name": "Alex"},
        ])

        results = self.db.delete_bulk(docs)
        self.assertEqual(len(results), 3)

    def test_cleanup(self):
        self.assertTrue(self.db.cleanup())

    def test_commit(self):
        self.assertTrue(self.db.commit())

    def test_compact(self):
        self.assertTrue(self.db.compact())


class DatabaseChangesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = couchdb.Server(SERVER_URL, authmethod="basic")
        cls.db = cls.s.create('testing_changes')

    @classmethod
    def tearDownClass(cls):
        cls.s.delete("testing_changes")

    def create_changes(self):
        doc1 = {"_id": "kk1", "counter": 1}
        doc2 = {"_id": "kk2", "counter": 1}
        doc1 = self.db.save(doc1)
        doc2 = self.db.save(doc2)

        return doc1, doc2

    def test_changes_list(self):
        doc1, doc2 = self.create_changes()
        last_seq, changes = self.db.changes_list()
        self.assertEqual(len(changes), 2)

        _, changes = self.db.changes_list(since=last_seq-1)
        self.assertEqual(len(changes), 1)

        self.db.delete(doc1)
        self.db.delete(doc2)

    def test_changes_feed_01(self):
        doc1, doc2 = self.create_changes()
        messages = []

        def reader(message, db):
            messages.append(message)
            raise exp.FeedReaderExited()

        self.db.changes_feed(reader)
        self.assertEqual(len(messages), 1)

        self.db.delete(doc1)
        self.db.delete(doc2)


class DatabaseQueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = couchdb.Server(SERVER_URL)
        try:
            cls.db = cls.s.create('testing3')
        except Conflict:
            cls.s.delete("testing3")
            cls.db = cls.s.create('testing3')

        docs = cls.db.save_bulk([
            {"_id": "kk1", "name":"Andrey"},
            {"_id": "kk2", "name":"Pepe"},
            {"_id": "kk3", "name": "Alex"},
        ])


        querydoc = {
            "_id": "_design/testing",
            "views": {
                "names": {
                    "map": "function(doc) { emit(doc.name, 1); }",
                    "reduce": "function(keys, values) { return  sum(values); }",
                }
            }
        }

        cls.db.save(querydoc)

    @classmethod
    def tearDownClass(cls):
        cls.s.delete("testing3")


    def test_get_not_existent(self):
        with self.assertRaises(NotFound):
            doc = self.db.get("kk4")

    def test_contains(self):
        self.assertIn("kk1", self.db)

    def test_all_01(self):
        result = [x for x in self.db.all() if not x['_id'].startswith("_")]
        self.assertEqual(len(result), 3)

    def test_all_02(self):
        result = list(self.db.all(keys=['kk1','kk2']))
        self.assertEqual(len(result), 2)

    def test_all_03(self):
        result = list(self.db.all(keys=['kk1','kk2'], flat="_id"))
        self.assertEqual(result, ['kk1', 'kk2'])

    def test_all_04(self):
        result = self.db.all(keys=['kk1','kk2'], flat="_id")
        self.assertIsInstance(result, types.GeneratorType)

    def test_all_05(self):
        result = self.db.all(keys=['kk1','kk2'], flat="_id", as_list=True)
        self.assertIsInstance(result, list)

    def test_all_startkey_endkey(self):
        result = list(self.db.all(startkey='kk1',endkey='kk2'))
        self.assertEqual(len(result), 2)

    def test_revisions_01(self):
        doc = self.db.get("kk1")

        initial_revisions = list(self.db.revisions("kk1"))
        self.assertEqual(len(initial_revisions), 1)

        doc["name"] = "Fooo"
        self.db.save(doc)

        revisions = list(self.db.revisions("kk1"))
        self.assertEqual(len(revisions), 2)

    def test_revisions_02(self):
        with self.assertRaises(NotFound):
            revisions = list(self.db.revisions("kk12"))

    def test_temporary_query_01(self):
        map_func = "function(doc) { emit(doc._id, doc.name); }"

        result = self.db.temporary_query(map_func)
        result = list(result)
        self.assertEqual(len(result), 3)

    def test_temporary_query_02(self):
        map_func = "function(doc) { emit(doc._id, doc.name); }"
        red_func = "function(keys, values, rereduce) { return values.length; }"

        result = self.db.temporary_query(map_func, red_func)
        result = list(result)
        self.assertEqual(len(result), 1)

    def test_temporary_query_03(self):
        map_func = "function(doc) { emit(doc._id, doc.name); }"

        result = self.db.temporary_query(map_func, keys=['kk1'])
        result = list(result)
        self.assertEqual(len(result), 1)

    def test_query_01(self):
        result = self.db.query("testing/names", group='true', keys=['Andrey'], as_list=True)
        self.assertEqual(len(result), 1)

    def test_query_02(self):
        result = self.db.query("testing/names", as_list=False)
        self.assertIsInstance(result, types.GeneratorType)

    def test_query_03(self):
        result = self.db.query("testing/names", as_list=True, flat="value")
        self.assertEqual(result, [3])

    def test_query_04(self):
        result = self.db.one("testing/names", flat="value")
        self.assertEqual(result, 3)

    def test_query_05(self):
        result = self.db.one("testing/names", flat="value", group='true', keys=['KK'])
        self.assertEqual(result, None)

    def test_query_06(self):
        result = self.db.one("testing/names", flat="value", group='true', keys=['Andrey'])
        self.assertEqual(result, 1)

    def test_compact_view_01(self):
        doc = {
            "_id": "_design/testing2",
            "views": {
                "names": {
                    "map": "function(doc) { emit(doc.name, 1); }",
                    "reduce": "function(keys, values) { return  sum(values); }",
                }
            }
        }

        self.db.save(doc)
        self.db.compact_view("testing2")

    def test_compact_view_02(self):
        with self.assertRaises(NotFound):
            self.db.compact_view("fooo")

class DatabaseAttachmentsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = couchdb.Server(SERVER_URL)
        try:
            cls.db = cls.s.create('testing4')
        except Conflict:
            cls.s.delete("testing4")
            cls.db = cls.s.create('testing4')

        docs = cls.db.save_bulk([
            {"_id": "kk1", "name":"Andrey"},
        ])

    @classmethod
    def tearDownClass(cls):
        cls.s.delete("testing4")

    def test_attachments_01(self):
        doc = self.db.get("kk1")

        with tempfile.NamedTemporaryFile() as f:
            f.write(b"Hello World")
            f.seek(0)

            self.db.put_attachment(doc, f, "sample.txt")

        doc = self.db.get("kk1")
        self.assertIn("_attachments", doc)

        data = self.db.get_attachment(doc, "sample.txt")
        self.assertEqual(data, b"Hello World")

        doc = self.db.delete_attachment(doc, "sample.txt")
        self.assertNotIn("_attachments", doc)

        doc = self.db.get("kk1")
        self.assertNotIn("_attachments", doc)

    def test_attachments_02(self):
        doc = self.db.get("kk1")

        with tempfile.NamedTemporaryFile() as f:
            f.write(b"Hello World")
            f.seek(0)

            self.db.put_attachment(doc, f)

        doc = self.db.get("kk1")
        self.assertIn("_attachments", doc)

    def test_get_not_existent_attachment(self):
        doc = self.db.get("kk1")
        with self.assertRaises(NotFound):
            self.db.get_attachment(doc, "kk.txt")

    def test_attachments_03_stream(self):
        doc = self.db.get("kk1")

        with tempfile.NamedTemporaryFile() as f:
            f.write(b"Hello")
            f.seek(0)

            doc = self.db.put_attachment(doc, f, "sample.txt")

        response = self.db.get_attachment(doc, "sample.txt", stream=True)
        stream = response.iter_content()

        self.assertEqual(next(stream), b"H")
        self.assertEqual(next(stream), b"e")
        self.assertEqual(next(stream), b"l")
        self.assertEqual(next(stream), b"l")
        self.assertEqual(next(stream), b"o")

        with self.assertRaises(StopIteration):
            next(stream)

    def test_regression_unexpected_deletion_of_attachment(self):
        """
        When I upload one file the code looks like:

            doc = db.put_attachment(doc, file_object)

        Ok, but now I want to update one field:

            doc['onefield'] = 'newcontent'
            doc = db.save(doc)

        et voilà, the previously uploaded file has been deleted!
        """

        doc = self.db.save({"_id": "kk2"})

        with tempfile.NamedTemporaryFile() as f:
            f.write(b"Hello World")
            f.seek(0)

            doc = self.db.put_attachment(doc, f, "sample.txt")

        self.assertIn("_attachments", doc)
        self.assertIn("sample.txt", doc["_attachments"])

        doc["some_attr"] = 1
        doc = self.db.save(doc)

        self.assertIn("_attachments", doc)
        self.assertIn("sample.txt", doc["_attachments"])


class UtilsTest(unittest.TestCase):

    def test_quote(self):
        #
        self.assertEqual(couchdb.utils.quote('Š'), '%C5%A0')


if __name__ == '__main__':
    unittest.main()
