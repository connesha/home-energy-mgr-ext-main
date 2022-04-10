import logging
from abc import ABC
import mysql.connector
from mysql.connector import Error

_LOGGER = logging.getLogger(__name__)


class DbBase(ABC):

    def __init__(self, host, database, user, password):
        super().__init__()
        self._connection = None   # TODO: share the connection across multiple subclasses
        self._host = host
        self._database = database
        self._user = user
        self._password = password
        return

    def _connect_if_necessary(self):
        try:
            if self._connection is None or not self._connection.is_connected():
                self._connection = mysql.connector.connect(host=self._host,
                                                           database=self._database,
                                                           user=self._user,
                                                           password=self._password)
                if self._connection is None or not self._connection.is_connected():
                    raise Exception("Couldn't connect to DB %s" % self._database)
                _LOGGER.debug("Connected to DB %s" % self._database)
        except Error:
            _LOGGER.exception("Error connecting DB %s" % self._database)
            exit(1)
        return

    def commit(self):
        self._connection.commit()
        return

    def close(self):
        if self._connection is not None and self._connection.is_connected():
            self._connection.close()
            _LOGGER.debug("Closed DB connection to %s" % self._database)
        self._connection = None
        return
