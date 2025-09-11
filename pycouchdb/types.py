# -*- coding: utf-8 -*-

from typing import Union, Dict, List, Any, Optional, TypedDict, Iterator, Iterable, Callable, Protocol
from typing_extensions import Final

# JSON type alias for all valid JSON values
Json = Union[Dict[str, Any], List[Any], str, int, float, bool, None]

# Document type - represents a CouchDB document
Document = Dict[str, Any]

# Row type for view results
class Row(TypedDict, total=False):
    id: str
    key: Any
    value: Any
    doc: Optional[Document]

# Bulk operation result item
class BulkItem(TypedDict, total=False):
    id: str
    rev: str
    ok: bool
    error: str
    reason: str

# Server info response
class ServerInfo(TypedDict, total=False):
    couchdb: str
    version: str
    git_sha: str
    uuid: str
    features: List[str]
    vendor: Dict[str, str]

# Database info response
class DatabaseInfo(TypedDict, total=False):
    db_name: str
    doc_count: int
    doc_del_count: int
    update_seq: str
    purge_seq: int
    compact_running: bool
    disk_size: int
    data_size: int
    instance_start_time: str
    disk_format_version: int
    committed_update_seq: int

# Changes feed result
class ChangeResult(TypedDict, total=False):
    seq: str
    id: str
    changes: List[Dict[str, str]]
    deleted: bool
    doc: Optional[Document]

# View query result
class ViewResult(TypedDict, total=False):
    total_rows: int
    offset: int
    rows: List[Row]

# HTTP client protocol for dependency injection
class HTTPClient(Protocol):
    def get(self, url: str, **kwargs: Any) -> Any: ...
    def post(self, url: str, **kwargs: Any) -> Any: ...
    def put(self, url: str, **kwargs: Any) -> Any: ...
    def delete(self, url: str, **kwargs: Any) -> Any: ...
    def head(self, url: str, **kwargs: Any) -> Any: ...

# Feed reader protocol
class FeedReader(Protocol):
    def on_message(self, message: Dict[str, Any]) -> None: ...
    def on_close(self) -> None: ...
    def on_heartbeat(self) -> None: ...

# Type aliases for common patterns
Credentials = tuple[str, str]
AuthMethod = str
ViewName = str
DocId = str
Rev = str

# Constants
DEFAULT_BASE_URL: Final[str] = "http://localhost:5984/"
DEFAULT_AUTH_METHOD: Final[str] = "basic"
