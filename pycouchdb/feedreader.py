# -*- coding: utf-8 -*-

from typing import Any, Dict, Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Database

# Type aliases for message callback functions
MessageCallback = Callable[[Dict[str, Any]], None]
MessageCallbackWithDb = Callable[..., None]  # Uses *args, **kwargs for flexibility


class BaseFeedReader:
    """
    Base interface class for changes feed reader.
    """

    def __call__(self, db: Any) -> "BaseFeedReader":
        self.db = db
        return self

    def on_message(self, message: Dict[str, Any]) -> None:
        """
        Callback method that is called when change
        message is received from couchdb.

        :param message: change object
        :returns: None
        """
        raise NotImplementedError()

    def on_close(self) -> None:
        """
        Callback method that is received when connection
        is closed with a server. By default, does nothing.
        """
        pass

    def on_heartbeat(self) -> None:
        """
        Callback method invoked when a hearbeat (empty line) is received
        from the _changes stream. Override this to purge the reader's internal
        buffers (if any) if it waited too long without receiving anything.
        """
        pass


class SimpleFeedReader(BaseFeedReader):
    """
    Simple feed reader that encapsule any callable in
    a valid feed reader interface.
    """

    def __init__(self, db: Any = None, callback: Optional[MessageCallbackWithDb] = None) -> None:
        if db is not None:
            self.db = db
        if callback is not None:
            self.callback = callback

    def __call__(self, db: Any, callback: Optional[MessageCallbackWithDb] = None) -> "SimpleFeedReader":
        self.db = db
        if callback is not None:
            self.callback = callback
        return self

    def on_message(self, message: Dict[str, Any]) -> None:
        if hasattr(self, 'callback') and self.callback is not None:
            self.callback(message, db=self.db)
