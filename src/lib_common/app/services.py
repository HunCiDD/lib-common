from typing import Type, Any, Generic, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from ..types import SchemaAddT, SchemaSetT, SchemaGetT
from ..logger.configs import loggers
from ..connect.database.types import M
from ..app.schemas import PageData
from ..app.repositories import BaseRepository
from .exceptions import ServiceException
from .decorators import with_transaction

run_logger = loggers.get_logger("run")


class BaseService(Generic[M, SchemaAddT, SchemaSetT, SchemaGetT]):
    def __init__(self, repo: BaseRepository[M], schema_cls: Type[SchemaGetT]):
        self.repo = repo
        self.schema_cls = schema_cls

    @with_transaction
    async def add(self, schema: SchemaAddT, conn: AsyncSession = None) -> SchemaGetT:
        entity = schema.model_dump(exclude_unset=True)
        model = await self.repo.add(conn, entity=entity)
        return model.to_schema(schema_cls=self.schema_cls)

    @with_transaction
    async def delete(self, pk: str, conn: AsyncSession = None, **kwargs: Any) -> bool:
        model = await self.repo.get(conn, pk)
        if not model:
            raise ServiceException("Failed delete, not found")

        await self.repo.delete(conn, pk)
        return True

    @with_transaction
    async def set(self, pk: str, schema: SchemaSetT, conn: AsyncSession = None) -> int:
        model = await self.repo.get(conn, pk)
        if not model:
            raise ServiceException("Failed set, not found")
        entity = schema.model_dump(exclude_unset=True)
        return await self.repo.set(conn, pk=pk, entity=entity)

    @with_transaction
    async def get(self, pk: str, conn: AsyncSession = None) -> SchemaGetT:
        model = await self.repo.get(conn, pk)
        if not model:
            raise ServiceException("Failed get, not found")
        return model.to_schema(schema_cls=self.schema_cls)

    @with_transaction
    async def list(
            self,
            conn: AsyncSession = None,
            filters: Dict[str, Any] | None = None,
            orders: Dict[str, Any] | None = None,
            page: int = 1,
            size: int = 20,
    ) -> PageData[SchemaGetT]:
        offset, limit = (page - 1) * size, size
        models = await self.repo.list(conn, filters, orders, offset, limit)
        items = [m.to_schema(self.schema_cls) for m in models]
        total = len(items)
        pages = (total + size - 1) // size
        return PageData(items=items, page=page, size=size, total=total, pages=pages)
