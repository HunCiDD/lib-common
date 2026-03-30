from typing import List, Dict, Type, Any, get_type_hints

import jwt
from urllib.parse import parse_qs

from .schemas import AppConfigsM
from pydantic import BaseModel, Field, create_model
from fastapi import Request, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..connect.database.repository import operators
from ..settings import get_settings
from ..logger.configs import loggers
from ..cryptor.configs import cryptors
from .exceptions import UnauthorizedException, ForbiddenException

settings = get_settings()
run_logger = loggers.get_logger("run")
cryptor = cryptors.get_cryptor("default")


# 假设这是一个验证 API Key 并返回客户端信息的函数（需根据实际情况实现）
def validate_api_key(api_key: str) -> dict | None:
    """
    验证 API Key 的有效性，返回客户端信息。
    实际实现中应查询数据库，检查 API Key 是否存在、是否过期，并获取对应的权限列表。
    """
    # 示例实现：从配置或数据库读取
    # 这里仅作演示，实际请替换为真实逻辑
    if api_key == "test_machine_key":
        return {
            "client_id": "machine_001",
            "permissions": ["read:data", "write:data"],  # 机机专用权限
        }
    return None


def get_auth_payload(
    request: Request, security: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
) -> dict:
    """
    获取认证载荷，支持两种方式：
    1. Bearer Token (JWT) - 用于用户调用
    2. API Key (通过自定义 Header) - 用于机机调用
    """
    # 开发环境直接返回全权限载荷
    if settings.app.environment == "dev":
        return {"type": "dev", "permissions": ["all"]}

        # 2. 尝试 API Key（机机调用）
    api_key_header = getattr(settings.app, "api_key_header", "X-API-Key")
    api_key = request.headers.get(api_key_header)
    if api_key:
        try:
            client_info = validate_api_key(api_key)
            if client_info:
                return {
                    "type": "machine",
                    "sub": client_info.get("client_id"),
                    "permissions": client_info.get("permissions", []),
                }
            else:
                raise UnauthorizedException(message="Invalid API Key")
        except Exception as e:
            run_logger.exception(e)
            raise UnauthorizedException(message="API Key validation failed")


def get_jwt_payload(security: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> dict:
    """
    获取jwt中 payload数据
    :param security:
    :return:
    """
    app_configs: AppConfigsM = settings.app
    if app_configs.environment == "dev":
        return {}
    try:
        token = security.credentials
        secret = app_configs.api_secret.get_secret_value()
        payload = jwt.decode(token, secret, algorithms=[app_configs.algorithm])
        if payload.get("type") != "access":
            raise UnauthorizedException(message="Invalid token type, must be access")

        return payload
    except jwt.ExpiredSignatureError as e:
        run_logger.exception(e)
        raise UnauthorizedException(message="Token has expired")
    except jwt.InvalidTokenError as e:
        run_logger.exception(e)
        raise UnauthorizedException(message="Token invalid")
    except Exception as e:
        run_logger.exception(e)
        raise UnauthorizedException(message="Internal server error")


# 权限校验
class PermissionChecker:
    def __init__(self, required_permission):
        self.required_permission = required_permission

    def __call__(self, jwt_payload: dict = Depends(get_jwt_payload)):
        if settings.app.environment == "dev":
            return

        permissions = jwt_payload.get("permissions", [])
        if "all" in permissions:
            return

        if self.required_permission in permissions:
            return

        raise ForbiddenException("Permission denied")


# 条件过滤参数构建
class ConditionParams:
    def __init__(self, base_model: Type[BaseModel]):
        self._model_name = f"{base_model.__name__}FilterParams"
        self._model_fields = {}
        self._base_model_fields = base_model.model_fields
        self._add_operate_field(base_model)
        self._model: Type[BaseModel] = create_model(self._model_name, **self._model_fields)

    def _add_operate_field(self, base_model: Type[BaseModel]):
        # 获取基础模型的类型提示和字段信息
        fields = base_model.model_fields
        fields_type_hint = get_type_hints(base_model)
        for field_name, field_info in fields.items():
            field_type = fields_type_hint.get(field_name, Any)
            # 基础类型
            self._model_fields[field_name] = (field_type, field_info)
            # 操作类型
            for operator, func in operators.items():
                operate_field_name = f"{field_name}{operator}"
                # 根据操作符确定字段类型
                if operator == "__in":
                    # __in 操作符需要列表类型
                    operate_field_type = List[field_type] | None
                    default_value = None
                elif operator == "__isnull":
                    # __isnull 操作符需要布尔类型
                    operate_field_type = bool | None
                    default_value = None
                else:
                    # 其他操作符使用原字段类型
                    operate_field_type = field_type | None
                    default_value = None

                # 创建字段描述
                description = f"Filter by {field_name} with {operator} operator"
                # 添加到模型字段字典
                self._model_fields[operate_field_name] = (
                    operate_field_type,
                    Field(default=default_value, description=description),
                )

    @staticmethod
    def _parse_query(request: Request) -> dict:
        if isinstance(request.query_params, dict):
            parsed_query = request.query_params
        else:
            parsed_query = parse_qs(str(request.query_params))
        _query = {}
        for k, v in parsed_query.items():
            if len(v) == 1:
                _query[k] = v[0]
            else:
                _query[k] = v
        return _query

    @staticmethod
    def _parse_orders(orders: str) -> dict:
        if not orders:
            return {}

        _sorter = {}
        for field in orders.split(","):
            field = field.strip()
            if ":" in field:
                field_describe = [x.strip() for x in field.split(":")]
                field_name, sort_direction = field_describe[0], field_describe[1]
            else:
                field_name = field
                sort_direction = "asc"

            if field_name:
                _sorter[field_name] = sort_direction
        return _sorter

    def __call__(
        self,
        request: Request,
        orders: str | None = Query(None, title="排序字段", description="格式:field1:asc,field2:desc"),
    ) -> Dict[str, Any]:
        query_params = self._parse_query(request)
        # 过滤参数
        _filter = self._model(**query_params).model_dump(exclude_none=True)
        # 排序参数
        _orders = self._parse_orders(orders)
        return {"filters": _filter, "orders": _orders}


# 分页加条件过滤参数构建
class PageConditionParams(ConditionParams):
    def __call__(
        self,
        request: Request,
        orders: str | None = Query(None, title="排序字段", description="格式:field1:asc,field2:desc"),
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(10, ge=1, le=100, description="每页数量"),
    ) -> Dict[str, Any]:
        query_params = self._parse_query(request)
        # 过滤参数
        _filter = self._model(**query_params).model_dump(exclude_none=True)
        # 排序参数
        _orders = self._parse_orders(orders)
        return {"filters": _filter, "orders": _orders, "page": page, "size": size}
