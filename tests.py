# -*- coding: utf-8 -*-

import unittest
import tempfile
import pycouchdb as couchdb

from pycouchdb.exceptions import Conflict, NotFound

SERVER_URL = 'http://admin:admin@localhost:5984/'

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

    def test_len(self):
        doc1 = {'_id': 'kk4', 'foo':'bar'}
        doc2 = self.db.save(doc1)
        self.assertTrue(len(self.db) > 0)

    def test_delete_01(self):
        doc = self.db.save({'_id': 'kk5', 'foo':'bar'})
        self.db.delete("kk5")
        self.assertEqual(len(self.db), 0)

    def test_delete_02(self):
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

    @classmethod
    def tearDownClass(cls):
        cls.s.delete("testing3")

    def test_contains(self):
        self.assertIn("kk1", self.db)

    def test_query_01(self):
        result = [x for x in self.db.all() if not x['_id'].startswith("_")]
        self.assertEqual(len(result), 3)

    def test_query_02(self):
        result = list(self.db.all(keys=['kk1','kk2']))
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

    def test_query(self):
        doc1 = {
            "_id": "_design/testing",
            "views": {
                "names": {
                    "map": "function(doc) { emit(doc.name, 1); }",
                    "reduce": "function(keys, values) { return  sum(values); }",
                }
            }
        }

        doc2 = self.db.save(doc1)

        result = self.db.query("testing/names", group='true', keys=['Andrey'])
        result = list(result)
        self.assertEqual(len(result), 1)

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

        self.db.delete_attachment(doc, "sample.txt")
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

if __name__ == '__main__':
    unittest.main()
