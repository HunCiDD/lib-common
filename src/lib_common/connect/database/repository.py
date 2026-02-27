from typing import Type, List, Dict, Any, Union, Optional
from sqlalchemy import inspect, update, delete, select, insert
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


def build_filters(model_cls: Type[M], filters: Dict[str, Any]) -> list:
    """
    根据过滤条件字典动态生成 SQLAlchemy 条件列表
    :param model_cls: 模型类
    :param filters: 过滤字典，支持操作符后缀（如 id__in、name__like）
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


def build_orders(model_cls: Type[M], orders: Dict[str, Any]) -> list:
    ...






class AsyncBaseRepository:
    """
    异步 SQLAlchemy 基础仓库类，提供通用的 CRUD 操作。
    所有方法均不自动提交事务，由调用方控制 session.commit()。
    """

    @staticmethod
    async def insert_one(
        session: AsyncSession,
        model_cls: Type[M],
        record: Dict[str, Any],
        relations: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> M:
        """
        插入单条记录
        :param session: AsyncSession 实例
        :param model_cls: 模型类
        :param record: 数据字典
        :param relations: 关联关系字段（如外键对象）
        :return: 插入后的模型实例
        """
        run_logger.debug(f"Insert one {model_cls.__name__}")
        _model = model_cls(**record)
        if relations:
            _model = set_model(_model, relations)
        session.add(_model)
        await session.flush()
        return _model

    @staticmethod
    async def insert_many(
        session: AsyncSession,
        model_cls: Type[M],
        records: List[Dict[str, Any]],
        relations: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> List[M]:
        """
        插入多条记录
        :param session: AsyncSession 实例
        :param model_cls: 模型类
        :param records: 数据字典列表
        :param relations: 关联关系字段列表（长度应与 records 一致，或至少一个元素）
        :return: 插入后的模型实例列表
        """
        run_logger.debug(f"Insert many {model_cls.__name__}, size={len(records)}")
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
        session.add_all(_models)
        await session.flush()
        return _models

    @staticmethod
    async def insert(
        session: AsyncSession,
        model_cls: Type[M],
        records: Union[Dict[str, Any], List[Dict[str, Any]]],
        relations: Union[Dict[str, Any], List[Dict[str, Any]], None] = None,
        **kwargs
    ) -> Union[M, List[M], None]:
        """
        统一插入接口，自动识别单条或多条
        :param session: AsyncSession 实例
        :param model_cls: 模型类
        :param records: 单条数据字典或字典列表
        :param relations: 对应的关联字段（单条或列表）
        :return: 插入后的实例或实例列表
        """
        if isinstance(records, dict):
            rel = relations if isinstance(relations, dict) else None
            return await AsyncBaseRepository.insert_one(session, model_cls, records, rel, **kwargs)
        elif isinstance(records, list):
            rel_list = relations if isinstance(relations, list) else []
            return await AsyncBaseRepository.insert_many(session, model_cls, records, rel_list, **kwargs)
        else:
            raise ValueError("records must be a dict or a list of dicts")

    @staticmethod
    async def update(
        session: AsyncSession,
        model_cls: Type[M],
        filters: Dict[str, Any],
        values: Dict[str, Any]
    ) -> int:
        """
        根据条件更新记录（支持复杂过滤条件）
        :param session: AsyncSession 实例
        :param model_cls: 模型类
        :param filters: 过滤条件字典，支持操作符后缀（如 {"id__in": [1,2,3], "name__like": "test"}）
        :param values: 待更新的字段字典
        :return: 影响的行数
        :raises ValueError: 如果 filters 为空或无法构建有效条件
        """
        if not filters:
            raise ValueError("Filters cannot be empty for update operation")

        conditions = build_filters(model_cls, filters)
        if not conditions:
            raise ValueError("No valid filter conditions could be built from the provided filters")

        stmt = (
            update(model_cls)
            .where(*conditions)
            .values(values)
            .returning(model_cls)
        )
        result = await session.execute(stmt)
        await session.flush()
        return result.rowcount

    @staticmethod
    async def delete(
        session: AsyncSession,
        model_cls: Type[M],
        filters: Dict[str, Any]
    ) -> int:
        """
        根据条件删除记录（支持复杂过滤条件）
        :param session: AsyncSession 实例
        :param model_cls: 模型类
        :param filters: 过滤条件字典，支持操作符后缀（如 {"id__in": [1,2,3], "name__like": "test"}）
        :return: 影响的行数
        :raises ValueError: 如果 filters 为空或无法构建有效条件
        """
        if not filters:
            raise ValueError("Filters cannot be empty for delete operation")

        conditions = build_filters(model_cls, filters)
        if not conditions:
            raise ValueError("No valid filter conditions could be built from the provided filters")

        stmt = delete(model_cls).where(*conditions)
        result = await session.execute(stmt)
        await session.flush()
        return result.rowcount

    @staticmethod
    async def upsert(
        session: AsyncSession,
        model_cls: Type[M],
        record: Dict[str, Any],
        conflict_columns: Optional[List[str]] = None,
        set_: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> M:
        """
        插入或更新单条记录（依赖数据库的 ON CONFLICT 功能，如 PostgreSQL）
        :param session: AsyncSession 实例
        :param model_cls: 模型类
        :param record: 数据字典
        :param conflict_columns: 冲突检测的列名列表（通常为唯一约束列）
        :param set_: 自定义更新字典，若为 None 则自动排除冲突列后更新所有其他列
        :return: 插入或更新后的模型实例（通过 RETURNING 获取）
        """
        mapper = inspect(model_cls)
        primary_keys = [col.name for col in mapper.primary_key]

        if conflict_columns:
            conflict_target = conflict_columns
        else:
            conflict_target = primary_keys
            if len(primary_keys) == 1 and mapper.primary_key[0].autoincrement:
                raise ValueError(
                    "Model has a single autoincrement primary key. "
                    "Please specify conflict_columns explicitly."
                )

        stmt = insert(model_cls).values(record)

        if set_ is not None:
            update_dict = set_
        else:
            all_columns = [col.name for col in mapper.columns]
            cols_to_update = [col for col in all_columns if col not in conflict_target]
            update_dict = {col: getattr(stmt.excluded, col) for col in cols_to_update}

        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_target,
            set_=update_dict,
        ).returning(model_cls)

        result = await session.execute(stmt)
        await session.flush()
        return result.scalar_one()

    @staticmethod
    async def get(
        session: AsyncSession,
        model_cls: Type[M],
        pk: Any
    ) -> Optional[M]:
        """
        根据主键获取单条记录
        :param session: AsyncSession 实例
        :param model_cls: 模型类
        :param pk: 主键值
        :return: 模型实例或 None
        """
        run_logger.debug(f"Get {model_cls.__name__} by primary key")
        return await session.get(model_cls, pk)

    @staticmethod
    async def list(
        session: AsyncSession,
        model_cls: Type[M],
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[M]:
        """
        条件查询，支持过滤、排序、分页
        :param session: AsyncSession 实例
        :param model_cls: 模型类
        :param filters: 过滤条件字典（支持操作符后缀，如 {"id__in": [1,2,3], "name__like": "test"}）
        :param order_by: 排序字段列表，格式如 ["id", "name desc", "created_at asc"]
        :param offset: 偏移量
        :param limit: 返回条数
        :return: 模型实例列表
        """
        stmt = select(model_cls)

        if filters:
            conditions = build_filters(model_cls, filters)
            if conditions:
                stmt = stmt.where(*conditions)

        if order_by:
            for expr in order_by:
                expr = expr.strip()
                if expr.endswith(" desc"):
                    col_name = expr[:-5]
                    order_col = getattr(model_cls, col_name).desc()
                elif expr.endswith(" asc"):
                    col_name = expr[:-4]
                    order_col = getattr(model_cls, col_name).asc()
                else:
                    order_col = getattr(model_cls, expr).asc()
                stmt = stmt.order_by(order_col)

        stmt = stmt.offset(offset).limit(limit)

        result = await session.execute(stmt)
        return result.scalars().all()


class BaseRepository:
    """
    同步 SQLAlchemy 基础仓库类，提供通用的 CRUD 操作。
    所有方法均不自动提交事务，由调用方控制 session.commit()。
    """

    @staticmethod
    def insert_one(
        session: Session,
        model_cls: Type[M],
        record: Dict[str, Any],
        relations: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> M:
        """
        插入单条记录
        :param session: Session 实例
        :param model_cls: 模型类
        :param record: 数据字典
        :param relations: 关联关系字段（如外键对象）
        :return: 插入后的模型实例
        """
        run_logger.debug(f"Insert one {model_cls.__name__}")
        _model = model_cls(**record)
        if relations:
            _model = set_model(_model, relations)
        session.add(_model)
        session.flush()
        return _model

    @staticmethod
    def insert_many(
        session: Session,
        model_cls: Type[M],
        records: List[Dict[str, Any]],
        relations: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> List[M]:
        """
        插入多条记录
        :param session: Session 实例
        :param model_cls: 模型类
        :param records: 数据字典列表
        :param relations: 关联关系字段列表（长度应与 records 一致，或至少一个元素）
        :return: 插入后的模型实例列表
        """
        run_logger.debug(f"Insert many {model_cls.__name__}, size={len(records)}")
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
        session.add_all(_models)
        session.flush()
        return _models

    @staticmethod
    def insert(
        session: Session,
        model_cls: Type[M],
        records: Union[Dict[str, Any], List[Dict[str, Any]]],
        relations: Union[Dict[str, Any], List[Dict[str, Any]], None] = None,
        **kwargs
    ) -> Union[M, List[M], None]:
        """
        统一插入接口，自动识别单条或多条
        :param session: Session 实例
        :param model_cls: 模型类
        :param records: 单条数据字典或字典列表
        :param relations: 对应的关联字段（单条或列表）
        :return: 插入后的实例或实例列表
        """
        if isinstance(records, dict):
            rel = relations if isinstance(relations, dict) else None
            return BaseRepository.insert_one(session, model_cls, records, rel, **kwargs)
        elif isinstance(records, list):
            rel_list = relations if isinstance(relations, list) else []
            return BaseRepository.insert_many(session, model_cls, records, rel_list, **kwargs)
        else:
            raise ValueError("records must be a dict or a list of dicts")

    @staticmethod
    def update(
        session: Session,
        model_cls: Type[M],
        filters: Dict[str, Any],
        values: Dict[str, Any]
    ) -> int:
        """
        根据条件更新记录（支持复杂过滤条件）
        :param session: Session 实例
        :param model_cls: 模型类
        :param filters: 过滤条件字典，支持操作符后缀（如 {"id__in": [1,2,3], "name__like": "test"}）
        :param values: 待更新的字段字典
        :return: 影响的行数
        :raises ValueError: 如果 filters 为空或无法构建有效条件
        """
        if not filters:
            raise ValueError("Filters cannot be empty for update operation")

        conditions = build_filters(model_cls, filters)
        if not conditions:
            raise ValueError("No valid filter conditions could be built from the provided filters")

        stmt = (
            update(model_cls)
            .where(*conditions)
            .values(values)
            .returning(model_cls)
        )
        result = session.execute(stmt)
        session.flush()
        return result.rowcount

    @staticmethod
    def delete(
        session: Session,
        model_cls: Type[M],
        filters: Dict[str, Any]
    ) -> int:
        """
        根据条件删除记录（支持复杂过滤条件）
        :param session: Session 实例
        :param model_cls: 模型类
        :param filters: 过滤条件字典，支持操作符后缀（如 {"id__in": [1,2,3], "name__like": "test"}）
        :return: 影响的行数
        :raises ValueError: 如果 filters 为空或无法构建有效条件
        """
        if not filters:
            raise ValueError("Filters cannot be empty for delete operation")

        conditions = build_filters(model_cls, filters)
        if not conditions:
            raise ValueError("No valid filter conditions could be built from the provided filters")

        stmt = delete(model_cls).where(*conditions)
        result = session.execute(stmt)
        session.flush()
        return result.rowcount

    @staticmethod
    def upsert(
        session: Session,
        model_cls: Type[M],
        record: Dict[str, Any],
        conflict_columns: Optional[List[str]] = None,
        set_: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> M:
        """
        插入或更新单条记录（依赖数据库的 ON CONFLICT 功能，如 PostgreSQL）
        :param session: Session 实例
        :param model_cls: 模型类
        :param record: 数据字典
        :param conflict_columns: 冲突检测的列名列表（通常为唯一约束列）
        :param set_: 自定义更新字典，若为 None 则自动排除冲突列后更新所有其他列
        :return: 插入或更新后的模型实例（通过 RETURNING 获取）
        """
        mapper = inspect(model_cls)
        primary_keys = [col.name for col in mapper.primary_key]

        if conflict_columns:
            conflict_target = conflict_columns
        else:
            conflict_target = primary_keys
            if len(primary_keys) == 1 and mapper.primary_key[0].autoincrement:
                raise ValueError(
                    "Model has a single autoincrement primary key. "
                    "Please specify conflict_columns explicitly."
                )

        stmt = insert(model_cls).values(record)

        if set_ is not None:
            update_dict = set_
        else:
            all_columns = [col.name for col in mapper.columns]
            cols_to_update = [col for col in all_columns if col not in conflict_target]
            update_dict = {col: getattr(stmt.excluded, col) for col in cols_to_update}

        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_target,
            set_=update_dict,
        ).returning(model_cls)

        result = session.execute(stmt)
        session.flush()
        return result.scalar_one()

    @staticmethod
    def get(
        session: Session,
        model_cls: Type[M],
        pk: Any
    ) -> Optional[M]:
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
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        offset: int = 0,
        limit: int = 100
    ) -> List[M]:
        """
        条件查询，支持过滤、排序、分页
        :param session: Session 实例
        :param model_cls: 模型类
        :param filters: 过滤条件字典（支持操作符后缀，如 {"id__in": [1,2,3], "name__like": "test"}）
        :param order_by: 排序字段列表，格式如 ["id", "name desc", "created_at asc"]
        :param offset: 偏移量
        :param limit: 返回条数
        :return: 模型实例列表
        """
        stmt = select(model_cls)

        if filters:
            conditions = build_filters(model_cls, filters)
            if conditions:
                stmt = stmt.where(*conditions)

        if order_by:
            for expr in order_by:
                expr = expr.strip()
                if expr.endswith(" desc"):
                    col_name = expr[:-5]
                    order_col = getattr(model_cls, col_name).desc()
                elif expr.endswith(" asc"):
                    col_name = expr[:-4]
                    order_col = getattr(model_cls, col_name).asc()
                else:
                    order_col = getattr(model_cls, expr).asc()
                stmt = stmt.order_by(order_col)

        stmt = stmt.offset(offset).limit(limit)

        result = session.execute(stmt)
        return result.scalars().all()