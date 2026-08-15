"""
Unit tests for pycouchdb.pagination module.
"""

import pytest
from unittest.mock import Mock
from pycouchdb.pagination import view_pages, mango_pages


class TestViewPages:
    """Test view_pages function."""

    def test_view_pages_single_page(self):
        """Test pagination with single page of results."""
        # Mock response with single page
        mock_response = Mock()
        mock_result = {
            'rows': [
                {'id': 'doc1', 'key': 'key1', 'value': 'value1'},
                {'id': 'doc2', 'key': 'key2', 'value': 'value2'}
            ]
        }

        fetch_mock = Mock(return_value=(mock_response, mock_result))

        pages = list(view_pages(fetch_mock, "test/view", 2))

        assert len(pages) == 1
        assert len(pages[0]) == 2
        assert pages[0][0]['id'] == 'doc1'
        assert pages[0][1]['id'] == 'doc2'

        # Should have been called once with limit=3 (page_size + 1)
        fetch_mock.assert_called_once()
        call_args = fetch_mock.call_args[0][0]
        assert call_args['limit'] == 3

    def test_view_pages_multiple_pages(self):
        """Test pagination with multiple pages."""
        # First page - has more results
        page1_response = Mock()
        page1_result = {
            'rows': [
                {'id': 'doc1', 'key': 'key1', 'value': 'value1'},
                {'id': 'doc2', 'key': 'key2', 'value': 'value2'},
                {'id': 'doc3', 'key': 'key3', 'value': 'value3'}  # Extra row indicates more pages
            ]
        }

        # Second page - final page
        page2_response = Mock()
        page2_result = {
            'rows': [
                {'id': 'doc4', 'key': 'key4', 'value': 'value4'}
            ]
        }

        fetch_mock = Mock(side_effect=[
            (page1_response, page1_result),
            (page2_response, page2_result)
        ])

        pages = list(view_pages(fetch_mock, "test/view", 2))

        assert len(pages) == 2
        assert len(pages[0]) == 2  # First page without extra row
        assert len(pages[1]) == 1  # Second page

        # Check that second call has correct pagination parameters
        assert fetch_mock.call_count == 2
        second_call_args = fetch_mock.call_args_list[1][0][0]
        assert second_call_args['startkey'] == '"key2"'  # Last key from first page (JSON-encoded for CouchDB)
        assert second_call_args['startkey_docid'] == 'doc2'  # Last doc id from first page
        assert second_call_args['skip'] == 1

    def test_view_pages_empty_result(self):
        """Test pagination with empty result."""
        mock_response = Mock()
        mock_result = {'rows': []}

        fetch_mock = Mock(return_value=(mock_response, mock_result))

        pages = list(view_pages(fetch_mock, "test/view", 2))

        assert len(pages) == 0
        fetch_mock.assert_called_once()

    def test_view_pages_none_result(self):
        """Test pagination with None result."""
        mock_response = Mock()

        fetch_mock = Mock(return_value=(mock_response, None))

        pages = list(view_pages(fetch_mock, "test/view", 2))

        assert len(pages) == 0
        fetch_mock.assert_called_once()

    def test_view_pages_with_params(self):
        """Test pagination with additional parameters."""
        mock_response = Mock()
        mock_result = {'rows': []}

        fetch_mock = Mock(return_value=(mock_response, mock_result))

        params = {'include_docs': True, 'descending': True}
        list(view_pages(fetch_mock, "test/view", 2, params))

        fetch_mock.assert_called_once()
        call_args = fetch_mock.call_args[0][0]
        assert call_args['include_docs'] is True
        assert call_args['descending'] is True
        assert call_args['limit'] == 3

    def test_view_pages_rejects_keys_option(self):
        fetch_mock = Mock()

        with pytest.raises(ValueError, match="does not support the 'keys' option"):
            list(view_pages(fetch_mock, "test/view", 2, {'keys': ['a', 'b']}))

        fetch_mock.assert_not_called()

    def test_view_pages_rejects_reduced_rows(self):
        fetch_mock = Mock(return_value=(Mock(), {
            'rows': [
                {'key': 'a', 'value': 1},
            ],
        }))

        with pytest.raises(ValueError, match="requires map rows"):
            list(view_pages(fetch_mock, "test/view", 2))

    def test_view_pages_rejects_reduce_option(self):
        fetch_mock = Mock()

        with pytest.raises(ValueError, match="pass reduce=False"):
            list(view_pages(fetch_mock, "test/view", 2, {'reduce': True}))

        fetch_mock.assert_not_called()

    @pytest.mark.parametrize('page_size', [0, -1, 1.5, True, '2'])
    def test_view_pages_rejects_invalid_page_size(self, page_size):
        fetch_mock = Mock()

        with pytest.raises(ValueError, match="page_size must be a positive integer"):
            list(view_pages(fetch_mock, "test/view", page_size))

        fetch_mock.assert_not_called()


class TestMangoPages:
    """Test mango_pages function."""

    def test_mango_pages_single_page(self):
        """Test pagination with single page of results."""
        mock_response = Mock()
        mock_result = {
            'docs': [
                {'_id': 'doc1', 'name': 'Alice'},
                {'_id': 'doc2', 'name': 'Bob'}
            ],
            'bookmark': None  # No more pages
        }

        fetch_mock = Mock(return_value=(mock_response, mock_result))

        selector = {'name': {'$exists': True}}
        pages = list(mango_pages(fetch_mock, selector, 2))

        assert len(pages) == 1
        assert len(pages[0]) == 2
        assert pages[0][0]['_id'] == 'doc1'
        assert pages[0][1]['_id'] == 'doc2'

        fetch_mock.assert_called_once()
        call_args = fetch_mock.call_args[0][0]
        assert call_args['selector'] == selector
        assert call_args['limit'] == 2

    def test_mango_pages_multiple_pages(self):
        """Test pagination with multiple pages."""
        # First page
        page1_response = Mock()
        page1_result = {
            'docs': [
                {'_id': 'doc1', 'name': 'Alice'},
                {'_id': 'doc2', 'name': 'Bob'}
            ],
            'bookmark': 'bookmark123'  # More pages available
        }

        # Second page
        page2_response = Mock()
        page2_result = {
            'docs': [
                {'_id': 'doc3', 'name': 'Charlie'}
            ],
            'bookmark': None  # No more pages
        }

        fetch_mock = Mock(side_effect=[
            (page1_response, page1_result),
            (page2_response, page2_result)
        ])

        selector = {'name': {'$exists': True}}
        pages = list(mango_pages(fetch_mock, selector, 2))

        assert len(pages) == 2
        assert len(pages[0]) == 2
        assert len(pages[1]) == 1

        # Check that second call has bookmark
        assert fetch_mock.call_count == 2
        second_call_args = fetch_mock.call_args_list[1][0][0]
        assert second_call_args['bookmark'] == 'bookmark123'

    def test_mango_pages_empty_result(self):
        """Test pagination with empty result."""
        mock_response = Mock()
        mock_result = {'docs': []}

        fetch_mock = Mock(return_value=(mock_response, mock_result))

        selector = {'name': {'$exists': True}}
        pages = list(mango_pages(fetch_mock, selector, 2))

        assert len(pages) == 0
        fetch_mock.assert_called_once()

    def test_mango_pages_none_result(self):
        """Test pagination with None result."""
        mock_response = Mock()

        fetch_mock = Mock(return_value=(mock_response, None))

        selector = {'name': {'$exists': True}}
        pages = list(mango_pages(fetch_mock, selector, 2))

        assert len(pages) == 0
        fetch_mock.assert_called_once()

    def test_mango_pages_with_params(self):
        """Test pagination with additional parameters."""
        mock_response = Mock()
        mock_result = {'docs': []}

        fetch_mock = Mock(return_value=(mock_response, mock_result))

        selector = {'name': {'$exists': True}}
        params = {'sort': [{'name': 'asc'}], 'fields': ['_id', 'name']}
        list(mango_pages(fetch_mock, selector, 2, params))

        fetch_mock.assert_called_once()
        call_args = fetch_mock.call_args[0][0]
        assert call_args['selector'] == selector
        assert call_args['sort'] == [{'name': 'asc'}]
        assert call_args['fields'] == ['_id', 'name']
        assert call_args['limit'] == 2

    def test_mango_pages_stops_on_empty_bookmark(self):
        """Test that pagination stops when bookmark is empty string."""
        # First page with empty bookmark
        page1_response = Mock()
        page1_result = {
            'docs': [
                {'_id': 'doc1', 'name': 'Alice'}
            ],
            'bookmark': ''  # Empty bookmark should stop pagination
        }

        fetch_mock = Mock(return_value=(page1_response, page1_result))

        selector = {'name': {'$exists': True}}
        pages = list(mango_pages(fetch_mock, selector, 2))

        assert len(pages) == 1
        assert len(pages[0]) == 1
        fetch_mock.assert_called_once()  # Should not make second call

    @pytest.mark.parametrize('page_size', [0, -1, 1.5, True, '2'])
    def test_mango_pages_rejects_invalid_page_size(self, page_size):
        fetch_mock = Mock()

        with pytest.raises(ValueError, match="page_size must be a positive integer"):
            list(mango_pages(fetch_mock, {'name': {'$exists': True}}, page_size))

        fetch_mock.assert_not_called()
