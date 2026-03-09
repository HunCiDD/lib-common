from typing import Callable, AsyncContextManager
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..logger.configs import loggers

# 必须导入loggers 否则新增的logger无法注册
from .middlewares import RequestIDMiddleware
from .exceptions import (
    HTTPException,
    RequestValidationError,
    ServiceException,
    http_exception_handler,
    validation_exception_handler,
    service_exception_handler,
)

run_logger = loggers.get_logger("run")


@asynccontextmanager
async def default_lifespan(app: FastAPI):
    run_logger.info("启动前执行..")
    yield
    run_logger.info("关闭前执行..")


def init_app(lifespan: Callable[[FastAPI], AsyncContextManager] | None = default_lifespan) -> FastAPI:
    """初始化并返回配置好的 FastAPI 应用实例

    Args:
        lifespan: 生命周期上下文管理器，默认为模块内定义的 lifespan

    Returns:
        配置好的 FastAPI 实例
    """
    app = FastAPI(lifespan=lifespan)

    # noinspection PyTypeChecker
    app.add_middleware(RequestIDMiddleware)

    # 全局异常处理
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ServiceException, service_exception_handler)

    return app
