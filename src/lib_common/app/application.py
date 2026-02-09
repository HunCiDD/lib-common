from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..configs import LOGGERS

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

run_logger = LOGGERS.get_logger("run")


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_logger.info("启动前执行..")
    yield
    run_logger.info("关闭前执行..")


app = FastAPI(lifespan=lifespan)
# 全局中间件
# noinspection PyTypeChecker
app.add_middleware(RequestIDMiddleware)

# 全局异常处理
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ServiceException, service_exception_handler)
