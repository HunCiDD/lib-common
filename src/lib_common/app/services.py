from typing import Type, Any, Generic, List

from sqlalchemy.ext.asyncio import AsyncSession

from ..types import SchemaAddT, SchemaSetT, SchemaGeTT
from .schemas import PageData
from ..configs import loggers
from .exceptions import ServiceException
from .repositories import BaseRepository, M
from .decorators import with_transaction

run_logger = loggers.get_logger("run")


class BaseService(Generic[M, SchemaAddT, SchemaSetT, SchemaGeTT]):
    def __init__(self, repo: BaseRepository[M], schema_cls: Type[SchemaGeTT]):
        self.repo = repo
        self.schema_cls = schema_cls

    def _get_schema(self, model: M) -> SchemaGeTT:
        return self.schema_cls(**model.as_dict())

    async def _add_m(self, schema: SchemaAddT, conn: AsyncSession = None, **kwargs) -> M:
        run_logger.debug(f"Schema: {schema}")
        # 转换并排除未设置字段
        entity = schema.model_dump(exclude_unset=True)
        model = await self.repo.add(conn, entity=entity, **kwargs)
        if not model:
            raise ServiceException(message="Failed add to db")
        return model

    async def _del_m(self, pk: str, conn: AsyncSession = None, **kwargs: Any):
        """删除实体并返回操作状态"""
        run_logger.debug(f"PK: {pk}")
        await self.repo.delete(conn, pk, **kwargs)

    async def _set_m(self, pk: str, schema: SchemaSetT, conn: AsyncSession = None, **kwargs: Any) -> M:
        """更新实体并返回更新后的完整表示"""
        run_logger.debug(f"Pk: {pk}, Schema: {schema}")
        entity = schema.model_dump(exclude_unset=True)
        model = await self.repo.set(conn, pk, entity, **kwargs)
        if not model:
            raise ServiceException(message="Failed set to db, Not found")
        return model

    async def _get_m(self, pk: str, conn: AsyncSession = None, **kwargs: Any) -> M:
        """根据ID获取单个实体"""
        run_logger.debug(f"Pk: {pk}")
        model = await self.repo.get(conn, pk, **kwargs)
        if not model:
            raise ServiceException(message=f"Failed get from db, Not found {pk}")
        return model

    async def _count_m(self, conn: AsyncSession = None, **kwargs: Any) -> int:
        """统计符合条件的实体数量"""
        return await self.repo.count(conn, **kwargs)

    async def _list_m(self, conn: AsyncSession = None, **kwargs) -> List[M]:
        run_logger.debug(f"Params: {kwargs}")
        models = await self.repo.list(conn, **kwargs)
        return models

    @staticmethod
    def _page_data(items: List[SchemaGeTT] = None, total: int = 0, **kwargs) -> PageData[SchemaGeTT]:
        paginator = kwargs.get("paginator", {"page": 1, "size": 10})
        page = paginator.get("page", 1)
        size = paginator.get("size", 10)
        pages = (total + size - 1) // size
        return PageData(items=items, page=page, size=size, total=total, pages=pages)

    @staticmethod
    async def _list_relations(name: str, relations_id: List[str], repo: BaseRepository[M], conn: AsyncSession) -> dict:
        """
        获取关系字段
        :param name: 关系字段名称
        :param relations_id: 关系id
        :param repo:
        :param conn:
        :return:
        """
        if not relations_id:
            return {}

        relations = await repo.list(conn, filter={"id__in": relations_id})
        if not relations:
            raise ServiceException(message=f"Failed, {name.title()} not found in [{relations_id}]")
        return {name: relations}

    @staticmethod
    async def _get_relations(name: str, relation_id: str, repo: BaseRepository[M], conn: AsyncSession) -> dict:
        if not relation_id:
            return {}

        relation = await repo.get(conn, entity_id=relation_id)
        if not relation:
            raise ServiceException(message=f"Failed, {name.title()} not found in [{relation_id}]")
        return {name: relation}

    @with_transaction
    async def add(self, schema: SchemaAddT, conn: AsyncSession = None, **kwargs) -> SchemaGeTT:
        model = await self._add_m(schema, conn=conn, **kwargs)
        return self._get_schema(model)

    @with_transaction
    async def delete(self, pk: str, conn: AsyncSession = None, **kwargs: Any) -> bool:
        await self._get_m(pk, conn=conn, **kwargs)
        await self._del_m(pk, conn=conn, **kwargs)
        return True

    @with_transaction
    async def set(self, pk: str, schema: SchemaSetT, conn: AsyncSession = None, **kwargs: Any) -> SchemaGeTT:
        await self._get_m(pk, conn=conn, **kwargs)
        model = await self._set_m(pk, schema, conn=conn, **kwargs)
        return self._get_schema(model)

    @with_transaction
    async def get(self, pk: str, conn: AsyncSession = None, **kwargs: Any) -> SchemaGeTT:
        model = await self._get_m(pk, conn=conn, **kwargs)
        return self._get_schema(model)

    @with_transaction
    async def count(self, conn: AsyncSession = None, **kwargs: Any) -> int:
        return await self._count_m(conn=conn, **kwargs)

    @with_transaction
    async def list(self, conn: AsyncSession = None, **kwargs) -> PageData[SchemaGeTT]:
        total = await self._count_m(conn=conn, **kwargs)
        models = await self._list_m(conn=conn, **kwargs)
        items = [self._get_schema(m) for m in models]
        return self._page_data(items, total, **kwargs)
