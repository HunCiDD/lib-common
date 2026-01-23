from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError


class ServiceException(Exception):
    def __init__(self, message: str = "", details: Any = None, code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message: str = message
        self.code: int = code
        self.details: Any = details


class BadRequestException(ServiceException):
    def __init__(self, message: str = "", details: Any = None):
        super().__init__(message=message, details=details, code=status.HTTP_400_BAD_REQUEST)


class UnauthorizedException(ServiceException):
    def __init__(self, message: str = "", details: Any = None):
        super().__init__(message=message, details=details, code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(ServiceException):
    def __init__(self, message: str = "", details: Any = None):
        super().__init__(message=message, details=details, code=status.HTTP_403_FORBIDDEN)


class ManyRequestException(ServiceException):
    def __init__(self, message: str = "", details: Any = None):
        super().__init__(message=message, details=details, code=status.HTTP_429_TOO_MANY_REQUESTS)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": "Validation error", "details": exc.errors()},
    )


async def service_exception_handler(request: Request, exc: ServiceException) -> JSONResponse:
    content = {"message": exc.message}
    if exc.details is not None:
        content["details"] = exc.details
    return JSONResponse(status_code=exc.code, content=content)


# 全局异常处理器，捕获所有未处理异常
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "Internal server error"})
