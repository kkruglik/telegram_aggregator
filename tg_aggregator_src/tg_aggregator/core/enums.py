from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any


class ResponseStatus(str, Enum):
    OK = "OK"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    DATABASE_ERROR = "DATABASE_ERROR"
    LIMIT_REACHED = "LIMIT_REACHED"
    ALREADY_SUBSCRIBED = "ALREADY_SUBSCRIBED"


@dataclass
class UserResponse:
    status: ResponseStatus
    details: Optional[Dict[str, Any]] = None

    @property
    def is_success(self) -> bool:
        return self.status == ResponseStatus.OK

    @classmethod
    def success(cls, **kwargs) -> 'UserResponse':
        return cls(ResponseStatus.OK, details=kwargs if kwargs else None)

    @classmethod
    def error(cls, status: ResponseStatus, **kwargs) -> 'UserResponse':
        return cls(status=status, details=kwargs if kwargs else None)
