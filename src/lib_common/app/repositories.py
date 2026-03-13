# 数据访问层
from typing import Generic, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..connect.database.types import M
from ..connect.database.repository import AsyncRepository
from ..logger.configs import loggers

run_logger = loggers.get_logger("run")


class BaseRepository(Generic[M]):
    """基础存储实现"""

    def __init__(self, model_cls: type[M]):
        self.model_cls = model_cls

    async def add(self, conn: AsyncSession, entity: dict) -> M:
        run_logger.debug(f"Add {self.model_cls.__name__}, values: {entity}")
        return await AsyncRepository.insert(conn, self.model_cls, values=entity)

    async def delete(self, conn: AsyncSession, pk: str, pk_name: str = "id") -> int:
        run_logger.debug(f"Delete {self.model_cls.__name__}, {pk_name}: {pk}")
        return await AsyncRepository.delete(conn, self.model_cls, filters={pk_name: pk})

    async def set(self, conn: AsyncSession, entity: dict, pk: str, pk_name: str = "id") -> int:
        run_logger.debug(f"Set {self.model_cls.__name__}, {pk_name}: {pk}, values: {entity}")
        return await AsyncRepository.update(conn, self.model_cls, filters={pk_name: pk}, values=entity)

    async def get(self, conn: AsyncSession, pk: str, pk_name: str = "id") -> M | None:
        run_logger.debug(f"Get {self.model_cls.__name__}, {pk_name}: {pk}")
        return await AsyncRepository.get(conn, self.model_cls, pk=pk)

    async def list(
        self,
        conn: AsyncSession,
        filters: Dict[str, Any] | None = None,
        orders: Dict[str, Any] | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[M]:
        """
        根据条件过滤查询结构
        :param conn:
        :param filters: id=1, id__in=[1, 2, 3], id__gt=25,
        :param orders:{"id__in": [], "offset": 1, "limit": 2, "_sort": {"id": "desc"}}
        :param offset:
        :param limit:
        :return:
        """
        run_logger.debug(
            f"List {self.model_cls.__name__}, filters: {filters}, orders: {orders}, offset: {offset}, limit: {limit}"
        )
        models = await AsyncRepository.list(
            conn, self.model_cls, filters=filters, orders=orders, offset=offset, limit=limit
        )
        return models
