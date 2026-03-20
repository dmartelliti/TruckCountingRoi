from abc import ABC, abstractmethod
from typing import Generic, TypeVar

C = TypeVar("C")  # Command type


class BaseHandler(ABC, Generic[C]):

    @abstractmethod
    def handle(self, command: C) -> None:
        """
        Execute the command.
        Must be implemented by subclasses.
        """
        raise NotImplementedError