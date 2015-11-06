"""
File: functional_tests.py
Author: Rinat Sabitov
Description:
"""


# import mock
import responses
import pycouchdb


def get_resp_mock():
    resp = mock.Mock()
    resp.headers = {}
    resp.body = bytes(0)
    resp.raw.data = bytes(0)
    resp.status_code = 200
    return resp


# @mock.patch('pycouchdb.resource.requests.session')
@responses.activate
def test_test():
    responses.add(
        responses.GET,
        "http://example.com/",
        body='[{"title": "Test Deal"}]',
        content_type="application/json"
    )
    server = pycouchdb.Server("http://example.com/")
    result = server.info()

    assert result==[{'title': 'Test Deal'}]
