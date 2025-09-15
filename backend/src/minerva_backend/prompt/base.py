from abc import ABC, abstractmethod
from typing import Type, Any

from pydantic import BaseModel


class Prompt(ABC):
    @staticmethod
    @abstractmethod
    def response_model() -> Type[BaseModel]:
        """Each subclass must provide a BaseModel class"""
        pass

    @staticmethod
    @abstractmethod
    def system_prompt() -> str:
        pass

    @staticmethod
    @abstractmethod
    def user_prompt(context: dict[str, str]) -> str:
        pass
