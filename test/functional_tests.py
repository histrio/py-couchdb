"""
File: functional_tests.py
Author: Rinat Sabitov
Description:
"""


# import mock
import responses
import pycouchdb

from pycouchdb.exceptions import Conflict
from nose.tools import raises


class TestServer:

    def setup(self):
        self.server = pycouchdb.Server("http://example.com/")

    def test_server_info(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                "http://example.com/",
                body='{"version": "1.2.1"}',
                content_type="application/json"
            )
            result = self.server.info()
            assert result['version'] == '1.2.1'

    def test_server_iter(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                "http://example.com/_all_dbs",
                body='["_replicator","_users","bsdp_v2"]',
                content_type="application/json"
            )
            assert len(self.server) > 0

    def test_create_db(self):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.PUT, "http://example.com/testing1")
            rsps.add(responses.HEAD, "http://example.com/testing1")
            self.server.create("testing1")

    def test_delete_db(self):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.DELETE, "http://example.com/testing1")
            self.server.delete("testing1")

    @raises(Conflict)
    def test_create_db_conflict(self):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.PUT, "http://example.com/testing1")
            rsps.add(responses.HEAD, "http://example.com/testing1")
            self.server.create("testing1")
            rsps.add(responses.PUT, "http://example.com/testing1",
                    content_type="application/json",
                    body='{"error":"file_exists"}', status=409)
            self.server.create("testing1")
