# -*- coding: utf-8 -*-

"""
Integration tests for pycouchdb.pagination module.

These tests require a running CouchDB instance and test the pagination
functionality with real database operations.
"""

import pytest
import json
from pycouchdb.pagination import view_pages, mango_pages
from pycouchdb import utils


class TestViewPagesIntegration:
    """Integration tests for view_pages function."""

    def test_view_pages_single_page(self, db):
        """Test view_pages integration with single page of results."""
        # Create a design document with a view
        design_doc = {
            "_id": "_design/pagination_test",
            "views": {
                "by_name": {
                    "map": "function(doc) { if (doc.name) emit(doc.name, doc); }"
                }
            }
        }
        db.save(design_doc)

        # Create test documents
        test_docs = [
            {'_id': 'doc1', 'name': 'Alice'},
            {'_id': 'doc2', 'name': 'Bob'},
        ]
        db.save_bulk(test_docs)

        # Create a fetch function that uses the database's resource directly
        def fetch_view(params):
            path = ['_design', 'pagination_test', '_view', 'by_name']
            resource = db.resource(*path)
            response, result = resource.get(params=params)
            return response, result

        # Test pagination with page size larger than total documents
        pages = list(view_pages(fetch_view, 'pagination_test/by_name', 10))

        assert len(pages) == 1
        assert len(pages[0]) == 2
        assert pages[0][0]['id'] == 'doc1'
        assert pages[0][1]['id'] == 'doc2'

        # Cleanup
        db.delete('_design/pagination_test')

    def test_view_pages_multiple_pages(self, db):
        """Test view_pages integration with multiple pages."""
        # Create a design document with a view
        design_doc = {
            "_id": "_design/pagination_test",
            "views": {
                "by_name": {
                    "map": "function(doc) { if (doc.name) emit(doc.name, doc); }"
                }
            }
        }
        db.save(design_doc)

        # Create test documents (more than page size)
        test_docs = [
            {'_id': f'doc{i}', 'name': f'User{i}'} for i in range(1, 8)  # 7 documents
        ]
        db.save_bulk(test_docs)

        # Create a fetch function that uses the database's resource directly
        def fetch_view(params):
            path = ['_design', 'pagination_test', '_view', 'by_name']
            resource = db.resource(*path)
            response, result = resource.get(params=params)
            return response, result

        # Test pagination with small page size
        pages = list(view_pages(fetch_view, 'pagination_test/by_name', 3))

        assert len(pages) == 3  # 3, 3, 1 documents
        assert len(pages[0]) == 3
        assert len(pages[1]) == 3
        assert len(pages[2]) == 1

        # Verify all documents are retrieved
        all_docs = []
        for page in pages:
            all_docs.extend(page)

        doc_ids = [doc['id'] for doc in all_docs]
        expected_ids = [f'doc{i}' for i in range(1, 8)]
        assert set(doc_ids) == set(expected_ids)

        # Cleanup
        db.delete('_design/pagination_test')

    def test_view_pages_with_params(self, db):
        """Test view_pages integration with additional parameters."""
        # Create a design document with a view
        design_doc = {
            "_id": "_design/pagination_test",
            "views": {
                "by_name": {
                    "map": "function(doc) { if (doc.name) emit(doc.name, doc); }"
                }
            }
        }
        db.save(design_doc)

        # Create test documents
        test_docs = [
            {'_id': 'doc1', 'name': 'Alice', 'age': 25},
            {'_id': 'doc2', 'name': 'Bob', 'age': 30},
            {'_id': 'doc3', 'name': 'Charlie', 'age': 35},
        ]
        db.save_bulk(test_docs)

        # Create a fetch function that uses the database's resource directly
        def fetch_view(params):
            path = ['_design', 'pagination_test', '_view', 'by_name']
            resource = db.resource(*path)
            response, result = resource.get(params=params)
            return response, result

        # Test pagination with include_docs parameter
        params = {'include_docs': True}
        pages = list(view_pages(fetch_view, 'pagination_test/by_name', 2, params))

        assert len(pages) == 2
        assert len(pages[0]) == 2
        assert len(pages[1]) == 1

        # Verify documents are included
        for page in pages:
            for doc in page:
                assert 'doc' in doc
                assert doc['doc']['name'] in ['Alice', 'Bob', 'Charlie']

        # Cleanup
        db.delete('_design/pagination_test')

    def test_view_pages_large_dataset(self, db):
        """Test view_pages with a large dataset."""
        # Create a large number of documents
        large_docs = [
            {'_id': f'large_doc_{i}', 'name': f'User{i}', 'type': 'user', 'index': i}
            for i in range(1, 51)  # 50 documents
        ]
        db.save_bulk(large_docs)

        # Create a design document for view pagination
        design_doc = {
            "_id": "_design/large_test",
            "views": {
                "by_index": {
                    "map": "function(doc) { if (doc.index) emit(doc.index, doc); }"
                }
            }
        }
        db.save(design_doc)

        # Test view pagination with large dataset
        def fetch_view(params):
            path = ['_design', 'large_test', '_view', 'by_index']
            resource = db.resource(*path)
            response, result = resource.get(params=params)
            return response, result

        pages = list(view_pages(fetch_view, 'large_test/by_index', 10))

        # Should have 5 pages of 10 documents each
        assert len(pages) == 5
        for page in pages:
            assert len(page) == 10

        # Cleanup
        db.delete('_design/large_test')

    def test_view_pages_empty_results(self, db):
        """Test view_pages with empty results."""
        # Create a design document
        design_doc = {
            "_id": "_design/empty_test",
            "views": {
                "by_name": {
                    "map": "function(doc) { if (doc.name) emit(doc.name, doc); }"
                }
            }
        }
        db.save(design_doc)

        # Test view pagination with no matching documents
        def fetch_view(params):
            path = ['_design', 'empty_test', '_view', 'by_name']
            resource = db.resource(*path)
            response, result = resource.get(params=params)
            return response, result

        pages = list(view_pages(fetch_view, 'empty_test/by_name', 10))
        assert len(pages) == 0

        # Cleanup
        db.delete('_design/empty_test')

    def test_view_pages_edge_cases(self, db):
        """Test view_pages edge cases."""
        # Create a design document
        design_doc = {
            "_id": "_design/edge_test",
            "views": {
                "by_name": {
                    "map": "function(doc) { if (doc.name) emit(doc.name, doc); }"
                }
            }
        }
        db.save(design_doc)

        # Create exactly one document
        db.save({'_id': 'single_doc', 'name': 'Single'})

        # Test view pagination with single document
        def fetch_view(params):
            path = ['_design', 'edge_test', '_view', 'by_name']
            resource = db.resource(*path)
            response, result = resource.get(params=params)
            return response, result

        pages = list(view_pages(fetch_view, 'edge_test/by_name', 1))
        assert len(pages) == 1
        assert len(pages[0]) == 1
        assert pages[0][0]['id'] == 'single_doc'

        # Cleanup
        db.delete('_design/edge_test')


class TestMangoPagesIntegration:
    """Integration tests for mango_pages function."""

    def test_mango_pages_single_page(self, db):
        """Test mango_pages integration with single page of results."""
        # Create test documents
        test_docs = [
            {'_id': 'doc1', 'name': 'Alice', 'type': 'user'},
            {'_id': 'doc2', 'name': 'Bob', 'type': 'user'},
        ]
        db.save_bulk(test_docs)

        # Create a fetch function that uses the database's resource directly
        def fetch_find(params):
            data = utils.force_bytes(json.dumps(params))
            response, result = db.resource.post('_find', data=data)
            return response, result

        # Test pagination with page size larger than total documents
        selector = {'type': 'user'}
        pages = list(mango_pages(fetch_find, selector, 10))

        assert len(pages) == 1
        assert len(pages[0]) == 2
        assert pages[0][0]['_id'] == 'doc1'
        assert pages[0][1]['_id'] == 'doc2'

    def test_mango_pages_multiple_pages(self, db):
        """Test mango_pages integration with multiple pages."""
        # Create test documents (more than page size)
        test_docs = [
            {'_id': f'doc{i}', 'name': f'User{i}', 'type': 'user', 'index': i}
            for i in range(1, 8)  # 7 documents
        ]
        db.save_bulk(test_docs)

        # Create a fetch function that uses the database's resource directly
        def fetch_find(params):
            data = utils.force_bytes(json.dumps(params))
            response, result = db.resource.post('_find', data=data)
            return response, result

        # Test pagination with small page size
        selector = {'type': 'user'}
        pages = list(mango_pages(fetch_find, selector, 3))

        assert len(pages) == 3  # 3, 3, 1 documents
        assert len(pages[0]) == 3
        assert len(pages[1]) == 3
        assert len(pages[2]) == 1

        # Verify all documents are retrieved
        all_docs = []
        for page in pages:
            all_docs.extend(page)

        doc_ids = [doc['_id'] for doc in all_docs]
        expected_ids = [f'doc{i}' for i in range(1, 8)]
        assert set(doc_ids) == set(expected_ids)

    def test_mango_pages_with_params(self, db):
        """Test mango_pages integration with additional parameters."""
        # Create test documents
        test_docs = [
            {'_id': 'doc1', 'name': 'Alice', 'type': 'user', 'age': 25},
            {'_id': 'doc2', 'name': 'Bob', 'type': 'user', 'age': 30},
            {'_id': 'doc3', 'name': 'Charlie', 'type': 'user', 'age': 35},
        ]
        db.save_bulk(test_docs)

        # Create index for the sort field
        index_def = {
            "index": {
                "fields": ["type", "age"]
            },
            "name": "test_index"
        }
        db.resource.post('_index', data=utils.force_bytes(json.dumps(index_def)))

        # Create a fetch function that uses the database's resource directly
        def fetch_find(params):
            data = utils.force_bytes(json.dumps(params))
            response, result = db.resource.post('_find', data=data)
            return response, result

        # Test pagination with sort and fields parameters
        selector = {'type': 'user'}
        params = {
            'sort': [{'age': 'asc'}],
            'fields': ['_id', 'name', 'age']
        }
        pages = list(mango_pages(fetch_find, selector, 2, params))

        assert len(pages) == 2
        assert len(pages[0]) == 2
        assert len(pages[1]) == 1

        # Verify documents are sorted by age
        all_docs = []
        for page in pages:
            all_docs.extend(page)

        ages = [doc['age'] for doc in all_docs]
        assert ages == [25, 30, 35]  # Should be sorted by age

    def test_mango_pages_large_dataset(self, db):
        """Test mango_pages with a large dataset."""
        # Create a large number of documents
        large_docs = [
            {'_id': f'large_doc_{i}', 'name': f'User{i}', 'type': 'user', 'index': i}
            for i in range(1, 101)  # 100 documents
        ]
        db.save_bulk(large_docs)

        # Test mango pagination with large dataset
        def fetch_find(params):
            data = utils.force_bytes(json.dumps(params))
            response, result = db.resource.post('_find', data=data)
            return response, result

        selector = {'type': 'user'}
        pages = list(mango_pages(fetch_find, selector, 25))

        # Should have 4 pages of 25 documents each
        assert len(pages) == 4
        for page in pages:
            assert len(page) == 25

    def test_mango_pages_empty_results(self, db):
        """Test mango_pages with empty results."""
        # Test mango pagination with no matching documents
        def fetch_find(params):
            data = utils.force_bytes(json.dumps(params))
            response, result = db.resource.post('_find', data=data)
            return response, result

        selector = {'type': 'nonexistent'}
        pages = list(mango_pages(fetch_find, selector, 10))
        assert len(pages) == 0

    def test_mango_pages_edge_cases(self, db):
        """Test mango_pages edge cases."""
        # Create exactly one document
        db.save({'_id': 'single_doc', 'name': 'Single', 'type': 'user'})

        # Test mango pagination with single document
        def fetch_find(params):
            data = utils.force_bytes(json.dumps(params))
            response, result = db.resource.post('_find', data=data)
            return response, result

        selector = {'name': 'Single'}
        pages = list(mango_pages(fetch_find, selector, 1))
        assert len(pages) == 1
        assert len(pages[0]) == 1
        assert pages[0][0]['_id'] == 'single_doc'


class TestPaginationIntegration:
    """General pagination integration tests."""

    def test_pagination_different_page_sizes(self, db):
        """Test pagination with different page sizes."""
        # Create test documents
        test_docs = [
            {'_id': f'doc{i}', 'name': f'User{i}', 'type': 'user'}
            for i in range(1, 11)  # 10 documents
        ]
        db.save_bulk(test_docs)

        # Create a design document
        design_doc = {
            "_id": "_design/size_test",
            "views": {
                "by_name": {
                    "map": "function(doc) { if (doc.name) emit(doc.name, doc); }"
                }
            }
        }
        db.save(design_doc)

        # Test different page sizes for view pagination
        def fetch_view(params):
            path = ['_design', 'size_test', '_view', 'by_name']
            resource = db.resource(*path)
            response, result = resource.get(params=params)
            return response, result

        # Test with page size 1
        pages = list(view_pages(fetch_view, 'size_test/by_name', 1))
        assert len(pages) == 10
        for page in pages:
            assert len(page) == 1

        # Test with page size 3
        pages = list(view_pages(fetch_view, 'size_test/by_name', 3))
        assert len(pages) == 4  # 3, 3, 3, 1
        assert len(pages[0]) == 3
        assert len(pages[1]) == 3
        assert len(pages[2]) == 3
        assert len(pages[3]) == 1

        # Test different page sizes for mango pagination
        def fetch_find(params):
            data = utils.force_bytes(json.dumps(params))
            response, result = db.resource.post('_find', data=data)
            return response, result

        selector = {'type': 'user'}

        # Test with page size 2
        pages = list(mango_pages(fetch_find, selector, 2))
        assert len(pages) == 5  # 2, 2, 2, 2, 2
        for page in pages:
            assert len(page) == 2

        # Test with page size 7
        pages = list(mango_pages(fetch_find, selector, 7))
        assert len(pages) == 2  # 7, 3
        assert len(pages[0]) == 7
        assert len(pages[1]) == 3

        # Cleanup
        db.delete('_design/size_test')

    def test_pagination_performance(self, db):
        """Test pagination performance with medium-sized dataset."""
        import time

        # Create a medium number of documents
        medium_docs = [
            {'_id': f'perf_doc_{i}', 'name': f'User{i}', 'type': 'user', 'index': i}
            for i in range(1, 201)  # 200 documents
        ]
        db.save_bulk(medium_docs)

        # Create a design document
        design_doc = {
            "_id": "_design/perf_test",
            "views": {
                "by_index": {
                    "map": "function(doc) { if (doc.index) emit(doc.index, doc); }"
                }
            }
        }
        db.save(design_doc)

        # Test view pagination performance
        def fetch_view(params):
            path = ['_design', 'perf_test', '_view', 'by_index']
            resource = db.resource(*path)
            response, result = resource.get(params=params)
            return response, result

        start_time = time.time()
        pages = list(view_pages(fetch_view, 'perf_test/by_index', 20))
        end_time = time.time()

        # Should have 10 pages of 20 documents each
        assert len(pages) == 10
        for page in pages:
            assert len(page) == 20

        # Performance should be reasonable (less than 10 seconds for 200 docs)
        assert end_time - start_time < 10

        # Test mango pagination performance
        def fetch_find(params):
            data = utils.force_bytes(json.dumps(params))
            response, result = db.resource.post('_find', data=data)
            return response, result

        start_time = time.time()
        selector = {'type': 'user'}
        pages = list(mango_pages(fetch_find, selector, 25))
        end_time = time.time()

        # Should have 8 pages of 25 documents each
        assert len(pages) == 8
        for page in pages:
            assert len(page) == 25

        # Performance should be reasonable
        assert end_time - start_time < 10

        # Cleanup
        db.delete('_design/perf_test')

    def test_pagination_consistency(self, db):
        """Test that pagination returns consistent results."""
        # Create test documents with predictable ordering
        test_docs = [
            {'_id': f'doc{i:03d}', 'name': f'User{i:03d}', 'type': 'user', 'order': i}
            for i in range(1, 21)  # 20 documents with zero-padded IDs
        ]
        db.save_bulk(test_docs)

        # Create a design document
        design_doc = {
            "_id": "_design/consistency_test",
            "views": {
                "by_order": {
                    "map": "function(doc) { if (doc.order) emit(doc.order, doc); }"
                }
            }
        }
        db.save(design_doc)

        # Test view pagination consistency
        def fetch_view(params):
            path = ['_design', 'consistency_test', '_view', 'by_order']
            resource = db.resource(*path)
            response, result = resource.get(params=params)
            return response, result

        # Run pagination multiple times and verify consistency
        for _ in range(3):
            pages = list(view_pages(fetch_view, 'consistency_test/by_order', 5))
            assert len(pages) == 4  # 5, 5, 5, 5 documents

            # Verify all documents are retrieved
            all_docs = []
            for page in pages:
                all_docs.extend(page)

            doc_ids = [doc['id'] for doc in all_docs]
            expected_ids = [f'doc{i:03d}' for i in range(1, 21)]
            assert set(doc_ids) == set(expected_ids)

        # Test mango pagination consistency
        def fetch_find(params):
            data = utils.force_bytes(json.dumps(params))
            response, result = db.resource.post('_find', data=data)
            return response, result

        selector = {'type': 'user'}

        # Run pagination multiple times and verify consistency
        for _ in range(3):
            pages = list(mango_pages(fetch_find, selector, 7))
            assert len(pages) == 3  # 7, 7, 6 documents

            # Verify all documents are retrieved
            all_docs = []
            for page in pages:
                all_docs.extend(page)

            doc_ids = [doc['_id'] for doc in all_docs]
            expected_ids = [f'doc{i:03d}' for i in range(1, 21)]
            assert set(doc_ids) == set(expected_ids)

        # Cleanup
        db.delete('_design/consistency_test')
