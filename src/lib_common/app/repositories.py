# 数据访问层
from typing import Generic, List, Any, TypeVar
from abc import ABC, abstractmethod

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..types import T
from ..connect.database.funcs import SQLALCHEMY_OPERATOR_MAP
from ..connect.database.base import BaseModel
from ..configs import loggers

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


class BaseRepository(IRepository[M], Generic[M]):
    """基础存储实现"""

    # 支持的查询操作符映射
    OPERATOR_MAP = SQLALCHEMY_OPERATOR_MAP

    def __init__(self, model_type: type[M]):
        self.model_type = model_type

    @staticmethod
    def _set_model_attr(model: M, entity: dict) -> M:
        """
        给模型动态设置属性
        :param model: 模型对象
        :param entity: 属性字典
        :return:
        """
        for k, v in entity.items():
            if not hasattr(model, k):
                continue
            setattr(model, k, v)
        return model

    async def add(self, conn: AsyncSession, entity: dict, relation: dict = None, **kwargs) -> M:
        run_logger.debug(f"Add {self.model_type.__name__}")
        _model = self.model_type(**entity)
        # 动态设置关系属性
        if relation:
            _model = self._set_model_attr(_model, relation)

        conn.add(_model)
        await conn.flush()
        return _model

    async def delete(self, conn: AsyncSession, entity_id: Any, **kwargs) -> M | None:
        run_logger.debug(f"Delete {self.model_type.__name__}")
        _model = await conn.get(self.model_type, entity_id)
        if _model:
            await conn.delete(_model)
            await conn.flush()
        return _model

    async def set(self, conn: AsyncSession, entity_id: Any, entity: dict, relation: dict = None, **kwargs) -> M | None:
        run_logger.debug(f"Set {self.model_type.__name__}")
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

    def _filter_conditions(self, **kwargs) -> List:
        """
        获取过滤条件
        :param kwargs:
        :return:
        """
        conditions = []
        for k, v in kwargs.items():
            # 尝试匹配__操作
            operator_found = False
            for op, op_func in self.OPERATOR_MAP.items():
                if op not in k:
                    continue

                if op != k[-len(op) :]:
                    continue

                bk = k[: -len(op)]
                if not hasattr(self.model_type, bk):
                    continue

                column = getattr(self.model_type, bk)
                conditions.append(op_func(column, v))
                operator_found = True
                break

            if not operator_found and hasattr(self.model_type, k):
                column = getattr(self.model_type, k)
                conditions.append(column == v)

        return conditions

    def _sorted_conditions(self, **kwargs) -> List:
        """
        获取排序条件
        """
        conditions = []
        for sort_field, descending in kwargs.items():
            if not hasattr(self.model_type, sort_field):
                continue

            field = getattr(self.model_type, sort_field)
            if descending == "desc":
                conditions.append(desc(field))
            else:
                conditions.append(field)
        return conditions
