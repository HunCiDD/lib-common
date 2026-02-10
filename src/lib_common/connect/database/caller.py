from ...mixins import TypeMixin

from ..core.interface import IRequest, ICaller, IAsyncCaller
from ..core.factory import CallerFactory
from .base import SqlRequest, SqlResponse
from .pool import SQLAlchemyDBConnectionPool, AsyncSQLAlchemyDBConnectionPool


@CallerFactory.register("SQLAlchemyDBCaller")
class SQLAlchemyDBCaller(TypeMixin, ICaller):
    def __init__(self, pool: SQLAlchemyDBConnectionPool, **kwargs):
        self.pool = pool
        self.kwargs = kwargs

    def send(self, request: SqlRequest) -> SqlResponse: ...


@CallerFactory.register("AsyncSQLAlchemyDBCaller")
class AsyncSQLAlchemyDBCaller(TypeMixin, IAsyncCaller):
    def __init__(self, pool: AsyncSQLAlchemyDBConnectionPool, **kwargs):
        self.pool = pool
        self.kwargs = kwargs

    async def send(self, request: IRequest) -> SqlResponse: ...
