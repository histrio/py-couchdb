# -*- coding: utf-8 -*-


class BaseFeedReader(object):
    """
    Base interface class for changes feed reader.
    """

    def __call__(self, db):
        self.db = db
        return self

    def on_message(self, message):
        """
        Callback method that is called when change
        message is received from couchdb.

        :param message: change object
        :returns: None
        """

        raise NotImplementedError()

    def on_close(self):
        """
        Callback method that is received when connection
        is closed with a server. By default, does nothing.
        """
        pass

    def on_heartbeat(self):
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

    def __call__(self, db, callback):
        self.callback = callback
        return super(SimpleFeedReader, self).__call__(db)

    def on_message(self, message):
        self.callback(message, db=self.db)
