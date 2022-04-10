import logging
from pymyenergi.client import MyenergiClient
from pymyenergi.connection import Connection
from services.service_base import ServiceBase

_LOGGER = logging.getLogger(__name__)


class MyeConnection(ServiceBase):

    def __init__(self, user, password):
        super().__init__()
        self.conn = None
        self.client = None
        self._user = user
        self._password = password
        return

    def refresh(self):
        super().refresh()
        self._setup_connection_if_necessary()
        return

    def close(self):
        super().close()
        self._teardown_connection()
        return

    def _teardown_connection(self):
        _LOGGER.info('teardown_connection')
        self.conn = None
        self.client = None

    def _setup_connection_if_necessary(self):
        if self.conn is None or self.client is None:
            _LOGGER.info('setup_connection')
            self.conn = Connection(self._user, self._password)
            self.client = MyenergiClient(self.conn)

