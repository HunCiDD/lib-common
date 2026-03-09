from typing import Type, Any, Generic, List, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from ..types import SchemaAddT, SchemaSetT, SchemaGeTT
from ..logger.configs import loggers
from ..connect.database.types import M
from ..connect.database.repository import BaseAsyncRepository
from .exceptions import ServiceException
from .decorators import with_transaction

run_logger = loggers.get_logger("run")


class BaseService(Generic[M, SchemaAddT, SchemaSetT, SchemaGeTT]):
    def __init__(self, model_cls: Type[M], schema_cls: Type[SchemaGeTT]):
        self.model_cls = model_cls
        self.schema_cls = schema_cls

    async def _add(self, conn: AsyncSession, schema: SchemaAddT) -> M:
        run_logger.debug(f"Add, schema: {schema}")
        # 转换并排除未设置字段
        entity = schema.model_dump(exclude_unset=True)
        model = await BaseAsyncRepository.insert(conn, self.model_cls, values=entity)
        return model

    async def _delete(self, conn: AsyncSession, pk: str, pk_name: str = "id") -> int:
        run_logger.debug(f"Delete, {pk_name}: {pk}")
        count = await BaseAsyncRepository.delete(conn, self.model_cls, filters={pk_name: pk})
        return count

    async def _set(self, conn: AsyncSession, pk: str, schema: SchemaSetT, pk_name: str = "id") -> int:
        run_logger.debug(f"Set, {pk_name}: {pk}, schema: {schema}")
        entity = schema.model_dump(exclude_unset=True)
        count = await BaseAsyncRepository.update(conn, self.model_cls, filters={pk_name: pk}, values=entity)
        return count

    async def _get(self, conn: AsyncSession, pk: str, pk_name: str = "id") -> M:
        run_logger.debug(f"Get, {pk_name}: {pk}")
        model = await BaseAsyncRepository.get(conn, self.model_cls, pk=pk)
        return model

    async def _list(
        self,
        conn: AsyncSession,
        filters: Dict[str, Any] | None = None,
        orders: Dict[str, Any] | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[M]:

        run_logger.debug(f"List, filters: {filters}, orders: {orders}, offset: {offset}, limit: {limit}")
        models = await BaseAsyncRepository.list(
            conn, self.model_cls, filters=filters, orders=orders, offset=offset, limit=limit
        )
        return models

    @with_transaction
    async def add(self, schema: SchemaAddT, conn: AsyncSession = None) -> SchemaGeTT:
        model = await self._add(conn, schema)
        return model.to_schema(schema_cls=self.schema_cls)

    @with_transaction
    async def delete(self, pk: str, conn: AsyncSession = None, **kwargs: Any) -> bool:
        model = await self._get(conn, pk)
        if not model:
            raise ServiceException("Failed delete, not found")

        await self._delete(conn, pk)
        return True

    @with_transaction
    async def set(self, pk: str, schema: SchemaSetT, conn: AsyncSession = None) -> int:
        model = await self._get(conn, pk)
        if not model:
            raise ServiceException("Failed set, not found")
        return await self._set(conn, pk=pk, schema=schema)

    @with_transaction
    async def get(self, pk: str, conn: AsyncSession = None) -> SchemaGeTT:
        model = await self._get(conn, pk)
        if not model:
            raise ServiceException("Failed get, not found")
        return model.to_schema(schema_cls=self.schema_cls)

    @with_transaction
    async def list(
        self,
        conn: AsyncSession = None,
        filters: Dict[str, Any] | None = None,
        orders: Dict[str, Any] | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[M]:

        models = await self._list(conn, filters, orders, offset, limit)
        return models
