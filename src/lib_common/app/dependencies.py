from typing import Optional, List, Dict, Type, Any, get_type_hints

from urllib.parse import parse_qs
from pydantic import BaseModel, Field, create_model
from fastapi import Request, Query

from libs.common.funcs import SQLALCHEMY_OPERATOR_MAP


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
            for operator, func in SQLALCHEMY_OPERATOR_MAP.items():
                operate_field_name = f"{field_name}{operator}"
                # 根据操作符确定字段类型
                if operator == "__in":
                    # __in 操作符需要列表类型
                    operate_field_type = Optional[List[field_type]]
                    default_value = None
                elif operator == "__isnull":
                    # __isnull 操作符需要布尔类型
                    operate_field_type = Optional[bool]
                    default_value = None
                else:
                    # 其他操作符使用原字段类型
                    operate_field_type = Optional[field_type]
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
    def _parse_sorter(sort: str) -> dict:
        if not sort:
            return {}

        _sorter = {}
        for field in sort.split(","):
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
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(10, ge=1, le=100, description="每页数量"),
        sort: str | None = Query(None, title="排序字段", description="格式:field1:asc,field2:desc"),
    ) -> Dict[str, Any]:
        query_params = self._parse_query(request)
        # 过滤参数
        _filter = self._model(**query_params).model_dump(exclude_none=True)
        # 分页参数
        _paginator = {"offset": (page - 1) * size, "limit": size, "page": page, "size": size}
        # 排序参数
        _sorter = self._parse_sorter(sort)

        return {"filter": _filter, "paginator": _paginator, "sorter": _sorter}
