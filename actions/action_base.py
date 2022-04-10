from abc import ABC, abstractmethod
import datetime


class ActionBase(ABC):

    def __init__(self):
        self.pre_actions = []
        self.post_actions = []
        self.last_run = None

    def add_pre_action(self, pre_action):
        self.pre_actions.append(pre_action)

    def add_post_action(self, post_action):
        self.post_actions.append(post_action)

    @abstractmethod
    def can_execute_now(self, services):
        pass

    @abstractmethod
    def execute_impl(self, services):
        pass

    def is_in_last_run_limit_secs(self, limit_secs):
        if self.last_run is None:
            return True
        else:
            now = datetime.datetime.now()
            duration = now - self.last_run
            secs_since_last_run = duration.total_seconds()
            if secs_since_last_run > limit_secs:
                return True
            else:
                return False

    def execute(self, services):
        # execute pre-actions
        for pre_action in self.pre_actions:
            pre_action.execute(services)
        # execute implementation
        self.execute_impl(services)
        # set last run, so know when to run again
        self.last_run = datetime.datetime.now()
        # execute post-actions
        for post_action in self.post_actions:
            post_action.execute(services)

