# -*- coding: utf-8 -*-

"""
Pagination utilities for CouchDB views and Mango queries.

This module provides convenient pagination functionality for both CouchDB views
and Mango queries, handling the complexity of cursor-based pagination internally.
"""

from typing import Any, Dict, List, Iterator, Optional, Callable, Union, Tuple
import json
import copy

from . import utils
from .types import Row, Document, Json, ViewRows, MangoDocs, PageSize

__all__ = ['view_pages', 'mango_pages', 'ViewRows', 'MangoDocs', 'PageSize']


def view_pages(
    fetch: Callable[[Dict[str, Any]], Tuple[Any, Optional[Dict[str, Any]]]],
    view: str,
    page_size: PageSize,
    params: Optional[Dict[str, Any]] = None
) -> Iterator[ViewRows]:
    """
    Paginate through CouchDB view results using startkey/startkey_docid cursor.

    This function handles the complexity of CouchDB view pagination by automatically
    managing startkey and startkey_docid parameters for stable pagination.

    .. warning::
        Pagination with grouped and reduced views (group=true, reduce=true) is
        inefficient and unreliable. CouchDB must process all preceding groups
        for skip operations, and total_rows/offset values are inconsistent with
        reduced output. Consider fetching all results at once for reduced views.

    :param fetch: Function that makes the actual HTTP request and returns (response, result)
    :param view: View name (e.g., "design/view")
    :param page_size: Number of rows per page
    :param params: Additional query parameters
    :returns: Iterator yielding lists of rows for each page
    """
    if params is None:
        params = {}

    # Create a copy to avoid modifying the original
    query_params = copy.deepcopy(params)
    query_params['limit'] = page_size + 1  # Request one extra to detect if there are more pages

    # Track pagination state
    startkey = None
    startkey_docid = None
    skip = 0

    while True:
        # Build current page parameters
        current_params = copy.deepcopy(query_params)

        if startkey is not None:
            current_params['startkey'] = startkey
            current_params['startkey_docid'] = startkey_docid
            current_params['skip'] = skip

        # Encode view parameters properly
        current_params = _encode_view_params(current_params)

        # Make the request
        response, result = fetch(current_params)

        if result is None or 'rows' not in result:
            break

        rows = result['rows']

        # If we got fewer rows than requested, this is the last page
        if len(rows) <= page_size:
            if rows:  # Only yield if there are rows
                yield rows
            break

        # We got more rows than page_size, so there are more pages
        # Yield current page (excluding the extra row)
        current_page = rows[:page_size]
        yield current_page

        # Set up for next page using the last row as cursor
        last_row = rows[page_size - 1]
        startkey = last_row['key']
        startkey_docid = last_row['id']
        skip = 1  # Skip the row used as the cursor to avoid returning it again (prevents duplicate results in cursor-based pagination)


def mango_pages(
    fetch_find: Callable[[Dict[str, Any]], Tuple[Any, Optional[Dict[str, Any]]]],
    selector: Dict[str, Any],
    page_size: PageSize,
    params: Optional[Dict[str, Any]] = None
) -> Iterator[MangoDocs]:
    """
    Paginate through Mango query results using bookmark cursor.

    This function handles Mango query pagination by automatically managing
    the bookmark parameter for stable pagination.

    :param fetch_find: Function that makes the actual HTTP request and returns (response, result)
    :param selector: Mango query selector
    :param page_size: Number of documents per page
    :param params: Additional query parameters
    :returns: Iterator yielding lists of documents for each page
    """
    if params is None:
        params = {}

    # Create a copy to avoid modifying the original
    query_params = copy.deepcopy(params)
    query_params['limit'] = page_size
    query_params['selector'] = selector

    bookmark = None

    while True:
        # Build current page parameters
        current_params = copy.deepcopy(query_params)

        if bookmark is not None:
            current_params['bookmark'] = bookmark

        # Make the request
        response, result = fetch_find(current_params)

        if result is None or 'docs' not in result:
            break

        docs = result['docs']

        # If no documents, we're done
        if not docs:
            break

        # Yield current page
        yield docs

        # Check if there are more pages
        bookmark = result.get('bookmark')
        if not bookmark:
            break


def _encode_view_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Encode view parameters using the same logic as the main client."""
    return utils.encode_view_options(params)
