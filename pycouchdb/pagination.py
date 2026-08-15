# -*- coding: utf-8 -*-

"""
Pagination utilities for CouchDB views and Mango queries.

This module provides convenient pagination functionality for both CouchDB views
and Mango queries, handling the complexity of cursor-based pagination internally.
"""

from typing import Any, Dict, Iterator, Optional, Callable, Tuple
import copy

from . import utils
from .types import ViewRows, MangoDocs, PageSize

__all__ = ['view_pages', 'mango_pages', 'ViewRows', 'MangoDocs', 'PageSize']


def _validate_page_size(page_size: PageSize) -> None:
    """Validate the public pagination page size."""
    if isinstance(page_size, bool) or not isinstance(page_size, int) or page_size < 1:
        raise ValueError("page_size must be a positive integer")


def _validate_view_params(params: Dict[str, Any]) -> None:
    """Reject view options that cannot be combined with cursor pagination."""
    if 'keys' in params:
        raise ValueError("view cursor pagination does not support the 'keys' option")
    if params.get('reduce') is True:
        raise ValueError("view cursor pagination requires map rows; pass reduce=False")


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
        Cursor pagination requires map rows and does not support ``reduce=true``
        or the ``keys`` option. Pass ``reduce=false`` for views that define a
        reduce function.

    :param fetch: Function that makes the actual HTTP request and returns (response, result)
    :param view: View name (e.g., "design/view")
    :param page_size: Number of rows per page
    :param params: Additional query parameters
    :returns: Iterator yielding lists of rows for each page
    """
    _validate_page_size(page_size)

    if params is None:
        params = {}

    _validate_view_params(params)

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

        # Encode view parameters (startkey, key, endkey need to be JSON-encoded for CouchDB)
        current_params = utils.encode_view_options(current_params)

        # Make the request
        response, result = fetch(current_params)

        if result is None or 'rows' not in result:
            break

        rows = result['rows']

        if rows and ('key' not in rows[0] or 'id' not in rows[0]):
            raise ValueError(
                "view cursor pagination requires map rows with 'key' and 'id'; "
                "pass reduce=False for reduced views"
            )

        # If we got fewer rows than requested, this is the last page
        if len(rows) <= page_size:
            if rows:  # Only yield if there are rows
                yield rows
            break

        # Set up for next page using the last row as cursor
        last_row = rows[page_size - 1]
        startkey = last_row['key']
        startkey_docid = last_row['id']
        skip = 1  # Skip cursor row to avoid duplicates.

        # We got more rows than page_size, so there are more pages.
        yield rows[:page_size]


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
    _validate_page_size(page_size)

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
