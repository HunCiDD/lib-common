from ...designs.factory import RegisterFactory
from .interface import IRequest, IResponse, IConnectionPool, IAsyncConnectionPool, ICaller, IAsyncCaller


class RequestFactory(RegisterFactory[IRequest]):
    # 每个子类初始化自己的 _map
    _map = {}


class ResponseFactory(RegisterFactory[IResponse]):
    _map = {}


class ConnectionPoolFactory(RegisterFactory[IConnectionPool | IAsyncConnectionPool]):
    _map = {}


class CallerFactory(RegisterFactory[ICaller | IAsyncCaller]):
    _map = {}
