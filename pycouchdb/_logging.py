"""Internal logging helpers for pycouchdb.

The library deliberately only installs a ``NullHandler``.  Applications own
handler, formatter, and level configuration through the standard ``logging``
package.
"""

import logging
from typing import Any, Iterable, Mapping, Sequence, Tuple, Union
from urllib.parse import urlsplit


logger = logging.getLogger("pycouchdb")
logger.addHandler(logging.NullHandler())


def parameter_names(
        params: Union[Mapping[Any, Any], Sequence[Tuple[Any, Any]]]
) -> Tuple[str, ...]:
    """Return parameter names without exposing any query values."""
    names: Iterable[Any]
    if isinstance(params, Mapping):
        names = params.keys()
    else:
        names = (
            parameter[0]
            for parameter in params
            if isinstance(parameter, (list, tuple)) and parameter
        )
    return tuple(sorted(str(name) for name in names))


def safe_path(url: str) -> str:
    """Return the URL path only, excluding host, credentials, and query data."""
    path = urlsplit(url).path
    return path or "/"


def response_size(headers: Mapping[str, Any]) -> Any:
    """Return the declared response length without consuming streamed content."""
    return headers.get("Content-Length") or headers.get("content-length") or "unknown"
