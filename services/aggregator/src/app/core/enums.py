from enum import StrEnum, auto
from dataclasses import dataclass
from typing import Optional, Dict, Any, Self


class ResponseStatus(StrEnum):
    OK = auto()
    UNKNOWN_ERROR = auto()
    UNAUTHORIZED = auto()
    DATABASE_ERROR = auto()
    LIMIT_REACHED = auto()
    ALREADY_SUBSCRIBED = auto()


@dataclass
class UserResponse:
    status: ResponseStatus
    details: Optional[Dict[str, Any]] = None

    @property
    def is_success(self) -> bool:
        return self.status == ResponseStatus.OK

    @classmethod
    def success(cls, **kwargs) -> Self:
        return cls(ResponseStatus.OK, details=kwargs if kwargs else None)

    @classmethod
    def error(cls, status: ResponseStatus, **kwargs) -> Self:
        return cls(status=status, details=kwargs if kwargs else None)
