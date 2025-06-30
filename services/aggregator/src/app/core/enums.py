from enum import StrEnum, auto
from dataclasses import dataclass
from typing import Optional, Dict, Any, Self


class ResponseStatus(StrEnum):
    # Success statuses
    OK = auto()

    # User/Auth related
    UNAUTHORIZED = auto()
    LIMIT_REACHED = auto()
    ALREADY_SUBSCRIBED = auto()

    # Database specific
    DATABASE_ERROR = auto()
    ALREADY_EXISTS = auto()
    VALIDATION_ERROR = auto()
    CONNECTION_ERROR = auto()
    CONSTRAINT_VIOLATION = auto()

    # General errors
    UNKNOWN_ERROR = auto()


@dataclass
class Response:
    status: ResponseStatus
    message: str = ""
    details: Optional[Dict[str, Any]] = None

    @property
    def is_success(self) -> bool:
        return self.status == ResponseStatus.OK

    @property
    def is_duplicate(self) -> bool:
        return self.status in (ResponseStatus.ALREADY_EXISTS, ResponseStatus.ALREADY_SUBSCRIBED)

    @classmethod
    def success(cls, message: str = "Operation successful", **kwargs) -> Self:
        return cls(ResponseStatus.OK, message=message, details=kwargs if kwargs else None)

    @classmethod
    def error(cls, status: ResponseStatus, message: str = "", **kwargs) -> Self:
        return cls(status=status, message=message, details=kwargs if kwargs else None)

    @classmethod
    def already_exists(cls, message: str = "Resource already exists", **kwargs) -> Self:
        return cls(ResponseStatus.ALREADY_EXISTS, message=message, details=kwargs if kwargs else None)

    @classmethod
    def already_subscribed(cls, message: str = "User already subscribed", **kwargs) -> Self:
        return cls(ResponseStatus.ALREADY_SUBSCRIBED, message=message, details=kwargs if kwargs else None)

    @classmethod
    def unauthorized(cls, message: str = "Unauthorized access", **kwargs) -> Self:
        return cls(ResponseStatus.UNAUTHORIZED, message=message, details=kwargs if kwargs else None)

    @classmethod
    def limit_reached(cls, message: str = "Limit reached", **kwargs) -> Self:
        return cls(ResponseStatus.LIMIT_REACHED, message=message, details=kwargs if kwargs else None)

    @classmethod
    def validation_error(cls, message: str = "Validation failed", **kwargs) -> Self:
        return cls(ResponseStatus.VALIDATION_ERROR, message=message, details=kwargs if kwargs else None)

    @classmethod
    def database_error(cls, message: str = "Database operation failed", **kwargs) -> Self:
        return cls(ResponseStatus.DATABASE_ERROR, message=message, details=kwargs if kwargs else None)
