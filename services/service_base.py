from abc import ABC, abstractmethod


class ServiceBase(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def refresh(self):
        pass

    @abstractmethod
    def close(self):
        pass
