
from ...mixins import TypeMixin

from ..base.interface import IRequest, ICaller, IAsyncCaller
from ..base.factory import CallerFactory
from .core import SqlRequest,
from .pool import SQLAlchemyDBConnectionPool, AsyncSQLAlchemyDBConnectionPool


@CallerFactory.register("SQLAlchemyDBCaller")
class SQLAlchemyDBCaller(TypeMixin, ICaller):
    def __init__(self, pool: SQLAlchemyDBConnectionPool, **kwargs):
        self.pool = pool
        self.kwargs = kwargs

    def send(self, request: SqlRequest) -> ResponseM: ...


@CallerFactory.register("AsyncSQLAlchemyDBCaller")
class AsyncSQLAlchemyDBCaller(TypeMixin, IAsyncCaller):
    def __init__(self, pool: AsyncSQLAlchemyDBConnectionPool, **kwargs):
        self.pool = pool
        self.kwargs = kwargs

    async def send(self, request: IRequest) -> ResponseM: ...
