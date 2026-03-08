import functools
from typing import Any, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from ..types import T
from ..configs import loggers, databases
from .exceptions import ServiceException


run_logger = loggers.get_logger("run")
app_db = databases.get_pool("app")


def _conn_wrapper(func: Callable[..., T], transaction: bool) -> Callable[..., T]:
    """创建实际的包装函数"""

    @functools.wraps(func)
    async def wrapper(self, *args: Any, **kwargs: Any) -> T:
        logs = func.__name__.replace("_", " ").title()
        run_logger.info(logs)

        try:
            conn = kwargs.get("conn", None)
            if conn and isinstance(conn, AsyncSession):
                return await func(self, *args, **kwargs)

            # 创建新连接并管理事务
            async with app_db.connection() as conn:
                if not transaction:
                    result = await func(self, *args, conn=conn, **kwargs)
                    run_logger.info(f"{logs}, Success")
                    return result

                # 开始事务
                async with conn.begin():
                    run_logger.debug(f"{logs}, Transaction started")
                    # 将连接注入到kwargs中
                    result = await func(self, *args, conn=conn, **kwargs)
                    run_logger.info(f"{logs}, Success")
                    return result

        except ServiceException:
            raise
        except Exception as e:
            run_logger.exception(f"{logs}, Exception: {e}")
            raise ServiceException(message=f"{logs}, Exception.")

    return wrapper


def with_transaction(func: Callable[..., T]) -> Callable[..., T]:
    return _conn_wrapper(func, transaction=True)


def with_connection(func: Callable[..., T]) -> Callable[..., T]:
    return _conn_wrapper(func, transaction=False)
