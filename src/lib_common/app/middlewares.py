# 中间件
import time

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

from libs.common.data.generator import UuidGenerator
from libs.common.configs import LOGGERS
from .loggers import AppLogContextVar


run_logger = LOGGERS.get_logger("run")


class RequestIDMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Try to load request ID from the request headers
        headers = MutableHeaders(scope=scope)
        path = scope["path"]
        # 请求ID获取或生成
        request_id = headers.get("X-Request-ID", str(UuidGenerator.by_time()))
        AppLogContextVar.request_id_var.set(request_id)
        run_logger.info(f"Request started for {path}")
        start_time = time.time()
        try:
            scope["X-Request-ID"] = request_id
            await self.app(scope, receive, send)
        except Exception as e:
            run_logger.error(f"Request failed for {path}", exc_info=e)
            raise
        finally:
            end_time = time.time()
            run_logger.info(f"Request end for {path}, total time: {end_time - start_time}")
