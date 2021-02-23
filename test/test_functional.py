"""
File: functional_tests.py
Author: Rinat Sabitov
Description:
"""

import pytest
import responses
import pycouchdb

from pycouchdb.exceptions import Conflict, BadRequest


@pytest.fixture
def server():
    return pycouchdb.Server("http://example.com/")


def test_server_info(server):
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "http://example.com/",
            body='{"version": "1.2.1"}',
            content_type="application/json"
        )
        result = server.info()
        assert result['version'] == '1.2.1'


def test_server_iter(server):
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "http://example.com/_all_dbs",
            body='["_replicator","_users","bsdp_v2"]',
            content_type="application/json"
        )
        assert len(server) > 0


def test_create_db(server):
    with responses.RequestsMock() as rsps:
        rsps.add(responses.PUT, "http://example.com/testing1")
        rsps.add(responses.HEAD, "http://example.com/testing1")
        server.create("testing1")


def test_delete_db(server):
    with responses.RequestsMock() as rsps:
        rsps.add(responses.DELETE, "http://example.com/testing1")
        server.delete("testing1")


def test_create_db_conflict(server):
    with responses.RequestsMock() as rsps:
        rsps.add(responses.PUT, "http://example.com/testing1")
        rsps.add(responses.HEAD, "http://example.com/testing1")
        server.create("testing1")

    with responses.RequestsMock() as rsps:
        rsps.add(responses.PUT, "http://example.com/testing1",
                 content_type="application/json",
                 body='{"error":"file_exists"}', status=409)
        with pytest.raises(Conflict):
            server.create("testing1")


def test_bad_request(server):
    with responses.RequestsMock() as rsps:
        rsps.add(responses.GET, "http://example.com/",
                 content_type="application/json",
                 body='{"error":"bad_request"}', status=400)
        with pytest.raises(BadRequest):
            server.info()
