import logging
from actions.action_base import ActionBase
import shutil

_LOGGER = logging.getLogger(__name__)


class CopyFileAction(ActionBase):

    def __init__(self, source_file, dest_file):
        super().__init__()
        self.source_file = source_file
        self.dest_file = dest_file
        _LOGGER.info(f"source_file {source_file} dest_file {dest_file}")

    def can_execute_now(self, services):
        super().can_execute_now(services)
        # always run
        return True

    def execute_impl(self, services):
        super().execute_impl(services)
        _LOGGER.info("execute_impl")
        _LOGGER.debug("from %s to %s" % (self.source_file, self.dest_file))

        shutil.copyfile(self.source_file, self.dest_file)

        _LOGGER.info("execute_impl done")
