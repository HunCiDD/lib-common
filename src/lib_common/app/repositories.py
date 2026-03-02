# 数据访问层
from typing import Generic, List, Any, TypeVar
from abc import ABC, abstractmethod

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..types import T
from ..connect.database.base import BaseModel
from ..connect.database.repository import AsyncBaseRepository
from ..logger.configs import loggers

run_logger = loggers.get_logger("run")


class IRepository(ABC, Generic[T]):
    """存储接口"""

    @abstractmethod
    async def add(self, conn: AsyncSession, entity: dict, **kwargs) -> T: ...

    @abstractmethod
    async def delete(self, conn: AsyncSession, entity_id: Any, **kwargs) -> T | None: ...

    @abstractmethod
    async def set(self, conn: AsyncSession, entity_id: Any, entity: dict, **kwargs) -> T | None: ...

    @abstractmethod
    async def get(self, conn: AsyncSession, entity_id: Any, **kwargs) -> T | None: ...

    @abstractmethod
    async def count(self, conn: AsyncSession, **kwargs) -> int: ...

    @abstractmethod
    async def list(self, conn: AsyncSession, **kwargs) -> List[T]: ...


M = TypeVar("M", bound=BaseModel)


class AppRepository(IRepository[M], Generic[M]):
    """基础存储实现"""

    def __init__(self, model_type: type[M]):
        self.model_type = model_type

    async def add(self, conn: AsyncSession, entity: dict, relation: dict = None, **kwargs) -> M:
        run_logger.debug(f"Add {self.model_type.__name__}")
        return await AsyncBaseRepository.insert_one(conn, self.model_type, entity, relation, **kwargs)

    async def delete(self, conn: AsyncSession, entity_id: Any, **kwargs) -> int:
        run_logger.debug(f"Delete {self.model_type.__name__}")
        return await AsyncBaseRepository.delete(conn, self.model_type, filters={"id": entity_id})

    async def set(self, conn: AsyncSession, entity_id: Any, entity: dict, relation: dict = None, **kwargs) -> int:
        run_logger.debug(f"Set {self.model_type.__name__}")
        return await AsyncBaseRepository.update(
            conn, self.model_type, entity, relation, filters={"id": entity_id}, **kwargs
        )
        _model = await conn.get(self.model_type, entity_id)
        if not _model:
            return _model

        if entity:
            # 设置自有属性
            _model = self._set_model_attr(_model, entity)

        if relation:
            # 动态设置关系属性
            _model = self._set_model_attr(_model, relation)

        await conn.flush()
        return _model

    async def get(self, conn: AsyncSession, entity_id: Any, **kwargs) -> M | None:
        run_logger.debug(f"Get {self.model_type.__name__}")
        return await conn.get(self.model_type, entity_id)

    async def count(self, conn: AsyncSession, **kwargs) -> int:
        run_logger.debug(f"Count {self.model_type.__name__}")
        stmt = select(func.count()).select_from(self.model_type)
        # 动态构建 WHERE 子句
        _filter = kwargs.get("filter", {})
        _f_conditions = self._filter_conditions(**_filter) if _filter else None
        if _f_conditions:
            stmt = stmt.where(*_f_conditions)

        result = await conn.execute(stmt)
        return result.scalar_one()

    async def list(self, conn: AsyncSession, **kwargs) -> List[M]:
        """
        根据条件过滤查询结构
        :param conn:
        :param kwargs: id=1, id__in=[1, 2, 3], id__gt=25,
        {"id__in": [], "offset": 1, "limit": 2, "_sort": {"id": "desc"}}
        :return:
        """
        run_logger.debug(f"List {self.model_type.__name__}")
        stmt = select(self.model_type)
        # 动态构建 WHERE 子句
        _filter = kwargs.get("filter", {})
        _f_conditions = self._filter_conditions(**_filter) if _filter else None
        if _f_conditions:
            stmt = stmt.where(*_f_conditions)

        _sorter = kwargs.get("sorter", {})
        if _sorter:
            _s_conditions = self._sorted_conditions(**_sorter)
            stmt = stmt.order_by(*_s_conditions)

        _paginator = kwargs.get("paginator", {})
        if _paginator:
            if "offset" in _paginator:
                stmt = stmt.offset(_paginator["offset"])
            if "limit" in _paginator:
                stmt = stmt.limit(_paginator["limit"])

        result = await conn.execute(stmt)
        return list(result.scalars().unique().all())
