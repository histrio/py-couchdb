# -*- coding: utf-8 -*-

import unittest
import tempfile
import pycouchdb as couchdb

from pycouchdb.exceptions import ConflictException, NotFound

SERVER_URL = 'http://admin:admin@localhost:5984/'

class ServerTests(unittest.TestCase):
    def setUp(self):
        self.s = couchdb.Server(SERVER_URL, authmethod="basic")

    def test_contains(self):
        self.assertIn("_users", self.s)

    def test_iter(self):
        self.assertNotEqual(len(list(self.s)), 0)

    def test_len(self):
        self.assertNotEqual(len(self.s), 0)

    def test_create_delete_db(self):
        db = self.s.create("testing")
        self.assertIn("testing", self.s)
        self.assertTrue(self.s.delete("testing"))
        self.assertNotIn("testing", self.s)

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


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.s = couchdb.Server(SERVER_URL)
        self.db = self.s.create('testing')

    def tearDown(self):
        self.s.delete("testing")

    def test_save_01(self):
        doc = {"foo": "bar"}
        ok = self.db.save(doc)

        self.assertIn("_id", doc)
        self.assertIn("_rev", doc)
        self.assertTrue(ok)

    def test_save_02(self):
        doc = {'_id': 'kk', 'foo':'bar'}
        ok = self.db.save(doc)

        self.assertIn("_rev", doc)
        self.assertTrue(ok)
        self.assertEqual(doc["_id"], "kk")

    def test_save_03(self):
        doc = {'_id': 'kk', 'foo':'bar'}
        ok1 = self.db.save(doc)
        ok2 = self.db.save(doc)

        self.assertTrue(ok1)
        self.assertTrue(ok2)

    def test_save_04(self):
        doc = {'_id': 'kk', 'foo':'bar'}
        ok = self.db.save(doc)
        self.assertTrue(ok)

        del doc["_rev"]
        with self.assertRaises(ConflictException):
            ok2 = self.db.save(doc)

    def test_len(self):
        doc = {'_id': 'kk', 'foo':'bar'}
        self.db.save(doc)
        self.assertEqual(len(self.db), 1)

    def test_delete_01(self):
        doc = {'_id': 'kk', 'foo':'bar'}
        self.db.save(doc)
        self.db.delete("kk")
        self.assertEqual(len(self.db), 0)

    def test_delete_02(self):
        with self.assertRaises(NotFound):
            self.db.delete("kk")

    def test_save_bulk_01(self):
        ok, results = self.db.save_bulk([
            {"name":"Andrey"},
            {"name":"Pepe"},
            {"name": "Alex"},
        ])

        self.assertTrue(ok)
        self.assertEqual(len(results), 3)

    def test_save_bulk_02(self):
        ok, results = self.db.save_bulk([
            {"_id": "kk1", "name":"Andrey"},
            {"_id": "kk2", "name":"Pepe"},
            {"_id": "kk3", "name": "Alex"},
        ])

        ok, results = self.db.save_bulk([
            {"_id": "kk1", "name":"Andrey"},
            {"_id": "kk2", "name":"Pepe"},
            {"_id": "kk3", "name": "Alex"},
        ])

        self.assertFalse(ok)
        self.assertEqual(len(results), 3)

    def test_cleanup(self):
        self.assertTrue(self.db.cleanup())

    def test_commit(self):
        self.assertTrue(self.db.commit())

    def test_compact(self):
        self.assertTrue(self.db.compact())


class DatabaseQueryTests(unittest.TestCase):
    def setUp(self):
        self.s = couchdb.Server(SERVER_URL)
        self.db = self.s.create('testing')
        ok, _ = self.db.save_bulk([
            {"_id": "kk1", "name":"Andrey"},
            {"_id": "kk2", "name":"Pepe"},
            {"_id": "kk3", "name": "Alex"},
        ])

        self.assertTrue(ok)

    def tearDown(self):
        self.s.delete("testing")

    def test_contains(self):
        self.assertIn("kk1", self.db)

    def test_query_01(self):
        result = list(self.db.all())
        self.assertEqual(len(result), 3)

    def test_query_02(self):
        result = list(self.db.all(keys=['kk1','kk2']))
        self.assertEqual(len(result), 2)

    def test_get_conflicts(self):
        self.assertTrue(self.db.conflicts("kk1"))

    def test_revisions_01(self):
        doc = self.db.get("kk1")

        initial_revisions = list(self.db.revisions("kk1"))
        self.assertEqual(len(initial_revisions), 1)

        doc["name"] = "Fooo"
        ok = self.db.save(doc)
        self.assertTrue(ok)

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
        doc = {
            "_id": "_design/testing",
            "views": {
                "names": {
                    "map": "function(doc) { emit(doc.name, 1); }",
                    "reduce": "function(keys, values) { return  sum(values); }",
                }
            }
        }

        ok = self.db.save(doc)
        self.assertTrue(ok)

        result = self.db.query("testing/names", group='true', keys=['Andrey'])
        result = list(result)
        self.assertEqual(len(result), 1)

    def test_compact_view_01(self):
        doc = {
            "_id": "_design/testing",
            "views": {
                "names": {
                    "map": "function(doc) { emit(doc.name, 1); }",
                    "reduce": "function(keys, values) { return  sum(values); }",
                }
            }
        }

        ok = self.db.save(doc)
        self.assertTrue(ok)

        ok = self.db.compact_view("testing")

    def test_compact_view_02(self):
        with self.assertRaises(NotFound):
            self.db.compact_view("fooo")

class DatabaseTests3(unittest.TestCase):
    def setUp(self):
        self.s = couchdb.Server(SERVER_URL)
        self.db = self.s.create('testing')
        ok, _ = self.db.save_bulk([
            {"_id": "kk1", "name":"Andrey"},
        ])

        self.assertTrue(ok)

    def tearDown(self):
        self.s.delete("testing")

    def test_attachments_01(self):
        doc = self.db.get("kk1")

        with tempfile.NamedTemporaryFile() as f:
            f.write(b"Hello World")
            f.seek(0)

            ok = self.db.put_attachment(doc, f, "sample.txt")
            self.assertTrue(ok)

        doc = self.db.get("kk1")
        self.assertIn("_attachments", doc)

        data = self.db.get_attachment(doc, "sample.txt")
        self.assertEqual(data, b"Hello World")

        ok = self.db.delete_attachment(doc, "sample.txt")
        self.assertTrue(ok)

        doc = self.db.get("kk1")
        self.assertNotIn("_attachments", doc)

    def test_attachments_02(self):
        doc = self.db.get("kk1")

        with tempfile.NamedTemporaryFile() as f:
            f.write(b"Hello World")
            f.seek(0)

            ok = self.db.put_attachment(doc, f)
            self.assertTrue(ok)

        doc = self.db.get("kk1")
        self.assertIn("_attachments", doc)

if __name__ == '__main__':
    unittest.main()
