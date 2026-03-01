from typing import Type, List, Dict, Any, Iterable, Set
from sqlalchemy import inspect, update, delete, select, desc
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from ...logger.configs import loggers
from .types import M

run_logger = loggers.get_logger("run")

# 操作符映射，用于动态构建过滤条件
operators = {
    "__in": lambda col, val: col.in_(val),
    "__gt": lambda col, val: col > val,
    "__ge": lambda col, val: col >= val,
    "__lt": lambda col, val: col < val,
    "__le": lambda col, val: col <= val,
    "__ne": lambda col, val: col != val,
    "__eq": lambda col, val: col == val,
    "__like": lambda col, val: col.like(f"%{val}%"),
    "__ilike": lambda col, val: col.ilike(f"%{val}%"),
    "__startswith": lambda col, val: col.startswith(val),
    "__endswith": lambda col, val: col.endswith(val),
    "__isnull": lambda col, val: col.is_(None) if val else col.isnot(None),
}


def set_model(model: M, entity: dict) -> M:
    """
    动态为模型实例设置属性（忽略模型中不存在的字段）
    :param model: 模型实例
    :param entity: 属性字典
    :return: 更新后的模型实例
    """
    for k, v in entity.items():
        if hasattr(model, k):
            setattr(model, k, v)
    return model

def to_model(model_cls: Type[M], record: Dict[str, Any], relation: Dict[str, Any] | None = None) -> M:
    """
    记录转换成对应 SQLAlchemy 数据库模型
    :param model_cls: 数据库模型
    :param record: 记录数据
    :param relation: 记录关系属性
    :return:
    """
    _model = model_cls(**record)
    if relation:
        _model = set_model(_model, relation)
    return _model


def to_models(model_cls: Type[M], records: Iterable[Dict[str, Any]], relations: Iterable[Dict[str, Any]]) -> List[M]:
    """
    多条记录转换成对应 SQLAlchemy 数据库模型
    :param model_cls: 数据库模型
    :param records: 多条记录数据
    :param relations: 记录关系属性
    :return:
    """
    _models = []
    if not relations:
        relations = []
    for i, record in enumerate(records):
        _model = model_cls(**record)
        if i < len(relations):
            _model = set_model(_model, relations[i])
        elif relations:
            _model = set_model(_model, relations[-1])
        _models.append(_model)
    return _models


def build_filter_conditions(model_cls: Type[M], filters: Dict[str, Any]) -> list:
    """
    根据过滤条件字典动态生成 SQLAlchemy 条件列表
    :param model_cls: 模型类
    :param filters: 过滤字典，支持操作符后缀（如 {"id__in": [1,2,3], "name__like": "test"}）
    :return: 条件列表，可直接用于 .where(*conditions)
    """
    conditions = []
    for k, v in filters.items():
        matched = False
        for op, op_func in operators.items():
            if k.endswith(op):
                field_name = k[: -len(op)]
                if hasattr(model_cls, field_name):
                    column = getattr(model_cls, field_name)
                    conditions.append(op_func(column, v))
                    matched = True
                break
        if not matched and hasattr(model_cls, k):
            column = getattr(model_cls, k)
            conditions.append(column == v)
    return conditions


def build_order_conditions(model_cls: Type[M], orders: Dict[str, Any]) -> list:
    """
    根据排序条件字典动态生成 SQLAlchemy 排序列表
    :param model_cls: 模型类
    :param orders: 排序字典，支持操作符后缀（如 {"id": "desc"}）
    :return: 排序列表，可直接用于 .where(*conditions)
    """
    conditions = []
    for sort_field, descending in orders.items():
        if not hasattr(model_cls, sort_field):
            continue

        field = getattr(model_cls, sort_field)
        if descending == "desc":
            conditions.append(desc(field))
        else:
            conditions.append(field)
    return conditions


def build_stmt_insert(model_cls: Type[M], values: Dict[str, Any] | List[Dict[str, Any]], returning: bool = False) -> Any:
    """
    构建插入stmt
    :param model_cls: 模型类
    :param values:  插入数据
    :param returning: 是否返回对象 True 返回地对象，False 返回影响行数
    :return:
    """
    if not values:
        raise ValueError("values is empty")

    if returning:
        stmt = insert(model_cls).returning(model_cls).values(values)
    else:
        stmt = insert(model_cls).values(values)
    return stmt


def build_stmt_update(model_cls: Type[M], filters: Dict[str, Any], values: Dict[str, Any], returning: bool = False) -> Any:
    """
    构建插入stmt
    :param model_cls: 模型类
    :param filters: 过滤条件
    :param values: 更新数据
    :param returning: 是否返回对象 True 返回地对象，False 返回影响行数
    :return:
    """
    if not filters or not values:
        raise ValueError("filters or values is empty")

    conditions = build_filter_conditions(model_cls, filters)
    if not conditions:
        raise ValueError("No valid filter conditions could be built from the provided filters")

    if returning:
        stmt = update(model_cls).returning(model_cls).where(*conditions).values(values)
    else:
        stmt = update(model_cls).where(*conditions).values(values)
    return stmt


def build_stmt_delete(model_cls: Type[M], filters: Dict[str, Any], returning: bool = False) -> Any:
    """
    构建删除stmt
    :param model_cls: 模型类
    :param filters: 过滤条件
    :param returning: 是否返回对象 True 返回地对象，False 返回影响行数
    :return:
    """
    if not filters:
        raise ValueError("filters is empty")

    conditions = build_filter_conditions(model_cls, filters)
    if not conditions:
        raise ValueError("No valid filter conditions could be built from the provided filters")

    if returning:
        stmt = delete(model_cls).returning(model_cls).where(*conditions)
    else:
        stmt = delete(model_cls).where(*conditions)
    return stmt


def build_stmt_upsert(model_cls: Type[M],
                      values: Dict[str, Any] | List[Dict[str, Any]],
                      conflict_columns: List[str] | None = None,
                      set_: Dict[str, Any] | None = None,
                      returning: bool = False) -> Any:
    """
    构建 upsert (插入或更新) stmt，使用 PostgreSQL 的 ON CONFLICT 功能

    :param model_cls: 模型类
    :param values: 插入数据，可以是单条字典或多条字典列表
    :param conflict_columns: 冲突检测的列名列表，通常为唯一约束列。
                            如果为 None，则使用主键作为冲突目标。
    :param set_: 自定义更新字典。如果为 None，则自动排除冲突列后更新所有其他列。
    :param returning: 是否返回插入/更新的对象
    :return: 构建好的 SQLAlchemy upsert 语句
    """
    mapper = inspect(model_cls)
    primary_keys = [col.name for col in mapper.primary_key]

    if conflict_columns:
        conflict_target = conflict_columns
    else:
        conflict_target = primary_keys
        if len(primary_keys) == 1 and mapper.primary_key[0].autoincrement:
            raise ValueError(
                "Model has a single autoincrement primary key. Please specify conflict_columns explicitly."
            )

    stmt = insert(model_cls).values(values)

    if set_ is not None:
        update_dict = set_
    else:
        all_columns = [col.name for col in mapper.columns]
        cols_to_update = [col for col in all_columns if col not in conflict_target]
        update_dict = {col: getattr(stmt.excluded, col) for col in cols_to_update}
    stmt = stmt.on_conflict_do_update(index_elements=conflict_target, set_=update_dict)
    if returning:
        stmt = stmt.returning(model_cls)
    return stmt


def build_stmt_select(model_cls: Type[M],
                      filters: Dict[str, Any] = None,
                      orders: Dict[str, Any] = None,
                      offset: int = 0,
                      limit: int = 100) -> Any:
    """
    构建查询stmt
    :param model_cls: 模型类
    :param filters: 过滤条件字典（支持操作符后缀，如 {"id__in": [1,2,3], "name__like": "test"}）
    :param orders: 排序字段列表，格式如 {"id": "desc"}
    :param offset: 偏移量
    :param limit: 返回条数
    :return:
    """
    stmt = select(model_cls)
    if filters:
        conditions = build_filter_conditions(model_cls, filters)
        if conditions:
            stmt = stmt.where(*conditions)

    if orders:
        conditions = build_order_conditions(model_cls, orders)
        if conditions:
            stmt = stmt.order_by(*conditions)
    stmt = stmt.offset(offset).limit(limit)
    return stmt


class BaseRepository:
    """
    同步 SQLAlchemy 基础仓库类，提供通用的 CRUD 操作。
    所有方法均不自动提交事务，由调用方控制 session.commit()。
    """

    @staticmethod
    def insert(
        session: Session,
        model_cls: Type[M],
        values: Dict[str, Any] | List[Dict[str, Any]],
        returning: bool = True
    ) -> Any:
        """
        统一插入接口，自动识别单条或多条
        :param session: Session 实例
        :param model_cls: 模型类
        :param values: 单条数据字典或字典列表
        :param returning: 对应的关联字段（单条或列表）
        :return: 插入后的实例或实例列表
        """
        stmt = build_stmt_insert(model_cls, values, returning=returning)
        result = session.execute(stmt)
        session.flush()
        if returning:
            scalars = result.scalars().all()
            if isinstance(values, dict):
                return scalars[0] if scalars else None
            else:
                return scalars
        else:
            return result.rowcount

    @staticmethod
    def update(session: Session, model_cls: Type[M], filters: Dict[str, Any], values: Dict[str, Any]) -> int:
        """
        根据条件更新记录（支持复杂过滤条件）
        :param session: Session 实例
        :param model_cls: 模型类
        :param filters: 过滤条件字典，支持操作符后缀（如 {"id__in": [1,2,3], "name__like": "test"}）
        :param values: 待更新的字段字典
        :return: 影响的行数
        :raises ValueError: 如果 filters 为空或无法构建有效条件
        """
        stmt = build_stmt_update(model_cls, filters, values, returning=False)
        result = session.execute(stmt)
        session.flush()
        return result.rowcount

    @staticmethod
    def delete(session: Session, model_cls: Type[M], filters: Dict[str, Any]) -> int:
        """
        根据条件删除记录（支持复杂过滤条件）
        :param session: Session 实例
        :param model_cls: 模型类
        :param filters: 过滤条件字典，支持操作符后缀（如 {"id__in": [1,2,3], "name__like": "test"}）
        :return: 影响的行数
        :raises ValueError: 如果 filters 为空或无法构建有效条件
        """
        stmt = build_stmt_delete(model_cls, filters, returning=False)
        result = session.execute(stmt)
        session.flush()
        return result.rowcount

    @staticmethod
    def upsert(
        session: Session,
        model_cls: Type[M],
        records: Dict[str, Any] | List[Dict[str, Any]],
        conflict_columns: List[str] | None = None,
        set_: Dict[str, Any] | None = None,
    ) -> M | List[M]:
        """
        插入或更新单条或多条记录（依赖数据库的 ON CONFLICT 功能，如 PostgreSQL）
        :param session: Session 实例
        :param model_cls: 模型类
        :param records: 单条数据字典或字典列表
        :param conflict_columns: 冲突检测的列名列表（通常为唯一约束列）
        :param set_: 自定义更新字典，若为 None 则自动排除冲突列后更新所有其他列
        :return: 插入或更新后的模型实例或实例列表（通过 RETURNING 获取）
        """
        stmt = build_stmt_upsert(model_cls, records, conflict_columns, set_, returning=True)
        result = session.execute(stmt)
        session.flush()
        scalars = result.scalars().all()
        if isinstance(records, dict):
            return scalars[0] if scalars else None
        else:
            return scalars

    @staticmethod
    def get(session: Session, model_cls: Type[M], pk: Any) -> M | None:
        """
        根据主键获取单条记录
        :param session: Session 实例
        :param model_cls: 模型类
        :param pk: 主键值
        :return: 模型实例或 None
        """
        run_logger.debug(f"Get {model_cls.__name__} by primary key")
        return session.get(model_cls, pk)

    @staticmethod
    def list(
        session: Session,
        model_cls: Type[M],
        filters: Dict[str, Any] | None = None,
        orders: Dict[str, Any] | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[M]:
        """
        条件查询，支持过滤、排序、分页
        :param session: Session 实例
        :param model_cls: 模型类
        :param filters: 过滤条件字典（支持操作符后缀，如 {"id__in": [1,2,3], "name__like": "test"}）
        :param orders: 排序字段列表，格式如 {"id" "desc"}
        :param offset: 偏移量
        :param limit: 返回条数
        :return: 模型实例列表
        """
        # 将 order_by 列表转换为 orders 字

        stmt = build_stmt_select(model_cls, filters, orders, offset, limit)
        result = session.execute(stmt)
        return result.scalars().all()
