# from typing import Any
# import redis
# import redis.asyncio as aioredis
#
# # from .schemas import RedisModel
#
#
# class BaseRedis:
#     def __init__(self, host: str, port: int, username: str, password: str, **kwargs: Any):
#         self._host = host
#         self._port = port
#         self._username = username
#         self._password = password
#         self._kwargs = kwargs
#
#
# class SyncClientContext:
#     __slots__ = ("pool", "client")
#
#     def __init__(self, pool: redis.ConnectionPool):
#         self.pool = pool
#         self.client: redis.Redis | None = None
#
#     def __enter__(self) -> redis.Redis:
#         self.client = redis.Redis(connection_pool=self.pool)
#         return self.client
#
#     def __exit__(self, exc_type, exc_val, exc_tb) -> None:
#         if self.client is None:
#             return
#
#         if exc_type is None and self.client.ping():
#             self.client.connection_pool.release(self.client.connection)
#         else:
#             self.client.close()
#
#
# class SyncRedis(BaseRedis):
#     def __init__(self, host: str, port: int, username: str, password: str, **kwargs: Any):
#         super().__init__(host, port, username, password, **kwargs)
#         self.pool = redis.ConnectionPool(host=host, port=port, username=username, password=password)
#
#     def client(self) -> SyncClientContext:
#         return SyncClientContext(self.pool)
#
#
# class AsyncClientContext:
#     __slots__ = ("pool", "client")
#
#     def __init__(self, pool: aioredis.ConnectionPool):
#         self.pool = pool
#         self.client: aioredis.Redis | None = None
#
#     async def __aenter__(self) -> aioredis.Redis:
#         self.client = aioredis.Redis(connection_pool=self.pool, decode_responses=True)
#         return self.client
#
#     async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
#         if self.client is None:
#             return
#
#         if exc_type is None and await self.client.ping():
#             await self.client.connection_pool.release(self.client.connection)
#         else:
#             await self.client.close()
#
#
# class AsyncRedis(BaseRedis):
#     def __init__(self, host: str, port: int, username: str, password: str, **kwargs: Any):
#         super().__init__(host, port, username, password, **kwargs)
#         self.pool = aioredis.ConnectionPool(host=host, port=port, username=username, password=password)
#
#     async def client(self) -> AsyncClientContext:
#         return AsyncClientContext(self.pool)
#
#
# # class Redis:
# #     def __init__(self, redis_settings: RedisSettings):
# #         self._redis_settings = redis_settings
# #         self._maps = {}
# #         if self._redis_settings.primary:
# #             _model = RedisModel(**self._redis_settings.primary)
# #             self._maps["primary"] = SyncRedis(
# #                 host=_model.host,
# #                 port=_model.port,
# #                 username=_model.username,
# #                 password=_model.password,
# #                 db=_model.db,
# #             )
# #             self._maps["primary_async"] = AsyncRedis(
# #                 host=_model.host,
# #                 port=_model.port,
# #                 username=_model.username,
# #                 password=_model.password,
# #                 db=_model.db,
# #             )
# #
# #     @property
# #     def primary(self) -> SyncRedis:
# #         return self._maps.get("primary", None)
# #
# #     @property
# #     def primary_async(self) -> AsyncRedis:
# #         return self._maps.get("primary_async", None)
