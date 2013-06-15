# -*- coding: utf-8 -*-


class BaseFeedReader(object):
    """
    Base interface class for changes feed reader.
    """

    def __init__(self, db):
        self.db = db

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


class SimpleFeedReader(BaseFeedReader):
    """
    Simple feed reader that encapsule any callable in
    a valid feed reader interface.
    """

    def __init__(self, db, callback):
        super(SimpleFeedReader, self).__init__(db)
        self.callback = callback

    def on_message(self, message):
        self.callback(message, db=self.db)
