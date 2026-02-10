from typing import List

from sqlalchemy.orm import DeclarativeBase

from ..core.interface import IRequest, IResponse
from ..core.factory import RequestFactory, ResponseFactory
from ..core.base import BaseRequest, BaseResponse


class Base(DeclarativeBase): ...


class BaseModel(Base):
    __abstract__ = True

    def as_dict(self, relations: List[str] = None, **kwargs) -> dict:
        # 将基础列转换成字典
        _dict = {name: getattr(self, name) for name, _ in self.__table__.columns.items()}
        if not relations:
            return _dict

        # 将关系属性转换成字典
        for key in relations:
            _dict[key] = None
            try:
                relations_value = getattr(self, key)
                if not relations_value:
                    continue

                if isinstance(relations_value, BaseModel):
                    _dict[key] = relations_value.as_dict()
                elif isinstance(relations_value, list):
                    _dict[key] = [relation.as_dict() for relation in relations_value]

            except Exception:
                pass

        return _dict


@RequestFactory.register("SqlRequest")
class SqlRequest(BaseRequest, IRequest):
    def __init__(self, sql: str, params: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.sql = sql
        self.params = params

    def validate(self) -> bool:
        pass

    def build(self):
        pass


@ResponseFactory.register("SqlResponse")
class SqlResponse(BaseResponse, IResponse):
    def __init__(self, code: int, msg: str = "", data: dict = None, **kwargs):
        super().__init__(code, msg, data)

    def validate(self) -> bool:
        pass

    def process(self):
        pass
