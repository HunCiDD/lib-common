from __future__ import annotations

from typing import Any, List, Type, Literal, Dict
from abc import ABC, abstractmethod

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..utils.files import ExeclFile
from ..objects import Context
from ..designs.factory import RegisterFactory
from ..logger.configs import loggers
from ..connect.database.base import BaseModel
from ..connect.database.repository import Repository
from .converter import ListConverter


run_logger = loggers.get_logger("run")

# 流(Pipeline)--阶段（Stage）--操作（Option）
"""
Pipeline
|--（Stage）collect 采集
|-----------|------（Option）fetch 获取
|
|--（Stage）clean 清洗
|-----------|------（Option）format 格式化
|
|--（Stage）storage 存储
|-----------|------（Option）write 写入
|
|--（Stage）analyse 分析
|-----------|------（Option）backtest 回测
|
|--（Stage）visual 可视化
|-----------|------（Option）render 渲染
|
|--（Stage）notify 通知
|-----------|------（Option）send 发送
"""


class Option(ABC):
    desc: str = "option"
    category: str = "option"

    def __init__(self, stage: Stage, ctx: Context):
        self.stage = stage
        self.ctx = ctx

    @property
    def session(self) -> Session:
        return self.ctx.get("session", None)

    @abstractmethod
    def run(self, *args, **kwargs) -> None: ...

    def save(self, data: Any, nullable=False):
        """保存数据"""
        if isinstance(data, pd.DataFrame):
            if not nullable and data.empty:
                raise ValueError("数据不能为空")
        else:
            if not nullable and not data:
                raise ValueError("数据不能为空")

        if hasattr(data, "__len__"):
            run_logger.info(f"待保存数据：{len(data)}条记录...")

        self.ctx.set(self.stage.okey, data)
        run_logger.info(f"成功保存到上下文：{self.stage.okey}")

    def _k(self, key: str) -> List[str]:
        if "." not in key:
            return [f"{self.stage.category}.{self.category}.{key}", key]
        return [key]


class OptionFactory(RegisterFactory[Option]):
    _map = {}


class Stage:
    def __init__(self, desc: str, category: str, ikey: str = "in", okey: str = "out"):
        self.desc: str = desc
        self.category: str = category
        self.ikey = ikey
        self.okey = okey
        self._options: List[Type[Option]] = []

    @property
    def options(self) -> List[Type[Option]]:
        return self._options

    @options.setter
    def options(self, options: List[Type[Option]]):
        self._options = options

    def run(self, ctx: Context, *args, **kwargs) -> None:
        run_logger.info(f"开始运行: {self.desc}...")
        for i, option in enumerate(self._options):
            try:
                # 对应操作初始化
                op = option(self, ctx)
                op.run()
            except Exception as e:
                run_logger.exception(f"{i}-运行失败: {e}")


class Pipeline:
    def __init__(self, desc: str):
        self.desc: str = desc
        self._stages: List[Stage] = []

    @property
    def stages(self) -> List[Stage]:
        return self._stages

    @stages.setter
    def stages(self, stages: List[Stage]):
        self._stages = stages

    @classmethod
    def build(cls, params: Dict[str, Any]) -> Pipeline:
        pipeline = cls(desc=params["desc"])
        for stage_params in params["stages"]:
            # 提取 Stage 所需的参数（排除 options）
            stage_kwargs = {k: v for k, v in stage_params.items() if k != "options"}
            stage = Stage(**stage_kwargs)
            # 设置 options（如果存在）
            if "options" in stage_params:
                stage.options = stage_params["options"]

            pipeline.stages.append(stage)
        return pipeline

    def run(self, ctx: Context, *args, **kwargs) -> None:
        run_logger.info(f"开始运行: {self.desc}...")
        for i, stage in enumerate(self._stages):
            try:
                stage.run(ctx, *args, **kwargs)
            except Exception as e:
                run_logger.exception(f"{i}-运行失败: {e}")


@OptionFactory.register("execl.fetch")
class ExeclFetchOption(Option):
    desc = "Execl采集操作"
    category = "fetch"

    def run(self, *args, **kwargs) -> None:
        df_fetched = self.fetch()
        self.save(df_fetched)

    def fetch(self, *args, **kwargs) -> pd.DataFrame:
        method: str = self.ctx.get("collect.fetch.method", default="")
        if method != "execl":
            raise TypeError(f"{self.desc} 仅支持method为 execl")

        file: str = self.ctx.get("collect.fetch.file", default="")
        if not file:
            raise ValueError(f"{self.desc} 待读取文件必须传入 {file}")
        engine: Literal["xlrd", "openpyxl", "odf", "pyxlsb", "calamine"] = self.ctx.get(
            "collect.fetch.engine", "openpyxl"
        )
        dtype: dict = self.ctx.get("collect.fetch.dtype", default=None)
        execl_file = ExeclFile(file, engine, dtype)
        return execl_file.load()


@OptionFactory.register("execl.write")
class ExeclWriteOption(Option):
    """
    通用文件存储接口：根据 pandas DataFrame，存储为 文件扩展名自动读取 CSV 或 Excel 文件为
    """

    desc = "Execl写入操作"
    category = "write"

    def run(self, *args, **kwargs) -> None:
        self.write(*args, **kwargs)

    def write(self, *args, **kwargs) -> None:
        # 检查待写入数据
        df_data = self.ctx.get(self.stage.ikey, default=None)
        if not isinstance(df_data, pd.DataFrame):
            raise ValueError(f"{self.desc} 待写入数据必须是pd.DataFrame类型")

        # excel 文件路径
        file: str = self.ctx.get("collect.write.file", default="")
        if not file:
            raise ValueError(f"{self.desc} 待写入文件必须传入 {file}")
        engine: Literal["xlrd", "openpyxl", "odf", "pyxlsb", "calamine"] = self.ctx.get(
            "collect.write.engine", "openpyxl"
        )
        f = ExeclFile(file, engine)
        f.dump(df_data)


@OptionFactory.register("db.fetch")
class DBFetchOption(Option):
    desc = "DB采集操作"
    category = "fetch"

    def run(self, *args, **kwargs) -> None:
        df_fetched = self.fetch(*args, **kwargs)
        self.save(df_fetched)

    def fetch(self, *args, **kwargs) -> pd.DataFrame:
        session = self.ctx.get(*self._k("session"), default=None)
        if not isinstance(session, Session):
            raise ValueError(f"{self.desc}")
        method: str = self.ctx.get("collect.fetch.method", default="")
        if method == "sql":
            df_fetched = self.fetch_by_sql(session, *args, **kwargs)
        elif method == "model":
            df_fetched = self.fetch_by_model(session, *args, **kwargs)
        else:
            raise ValueError(f"{self.desc} 不支持该采集方式 {method}")

        return df_fetched

    def fetch_by_sql(self, session: Session, *args, **kwargs) -> pd.DataFrame:
        sql = self.ctx.get("collect.fetch.sql", default="")
        params = self.ctx.get("collect.fetch.params", default={})
        if not sql:
            raise ValueError(f"{self.desc} 必须存在 sql ")

        result = session.execute(text(sql), params)
        rows = result.fetchall()
        if not rows:
            return pd.DataFrame()

        # 提取列名并构造字典列表
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in rows]
        df_fetched = ListConverter.to_dataframe(data)
        return df_fetched

    def fetch_by_model(self, session: Session, *args, **kwargs) -> pd.DataFrame:
        model: Type[BaseModel] = self.ctx.get("collect.fetch.model", default=None)
        if not model:
            raise ValueError(f"{self.desc} 必须存在 model")
        columns: List[str] = self.ctx.get("collect.fetch.columns", default=[])
        filters: Dict[str, Any] = self.ctx.get("collect.fetch.filters", default={})
        orders: Dict[str, Any] = self.ctx.get("collect.fetch.orders", default={})
        offset: int = self.ctx.get("collect.fetch.offset", default=0)
        limit: int = self.ctx.get("collect.fetch.limit", default=100)

        rows = Repository.list(session, model, filters, orders, offset, limit)
        if columns:
            df_fetched = ListConverter.to_dataframe([row.as_dict() for row in rows], columns=columns)
        else:
            df_fetched = ListConverter.to_dataframe([row.as_dict() for row in rows])
        return df_fetched


@OptionFactory.register("db.write")
class DBWriteOption(Option):
    desc = "DB写入操作"
    category = "write"

    def run(self, *args, **kwargs) -> None:
        self.write(*args, **kwargs)

    def write(self, *args, **kwargs) -> None:
        # 检查待写入数据
        df_data = self.ctx.get(self.stage.ikey, default=None)
        if not isinstance(df_data, pd.DataFrame):
            raise ValueError(f"{self.desc} 待写入数据必须是pd.DataFrame类型")

        session = self.ctx.get(*self._k("session"), default=None)
        if not isinstance(session, Session):
            raise ValueError(f"{self.desc} 必须传入Session")

        method = self.ctx.get("storage.write.method", default="model")
        if method == "model":
            self.write_by_model(session, df_data, *args, **kwargs)
        elif method == "sql":
            self.write_by_sql(session, df_data, *args, **kwargs)
        else:
            raise ValueError(f"{self.desc} method方式只支持 model, sql")
        self.write_by_model(session, df_data, *args, *kwargs)

    def write_by_model(self, session: Session, df_data: pd.DataFrame, *args, **kwargs):
        model: Type[BaseModel] = self.ctx.get("storage.write.model", default=None)
        if not model or not issubclass(model, BaseModel):
            raise TypeError(f"{self.desc} 模型参数不合法")

        conflict_columns: List[str] = self.ctx.get("storage.write.conflict_columns", default=[])
        if not conflict_columns:
            raise ValueError(f"{self.desc} conflict_columns 必须存在")

        records = df_data.to_dict(orient="records")
        Repository.upsert(session, model, records, conflict_columns)
        run_logger.info(f"成功写入 {len(records)}条数据.")

    def write_by_sql(self, session: Session, df_data: pd.DataFrame, *args, **kwargs):
        """使用原始 SQL 语句写入数据（支持批量 executemany）"""
        sql = self.ctx.get("storage.write.sql", default="")
        if not sql:
            raise ValueError(f"{self.desc} 使用 sql 方式时必须配置 storage.write.sql")

        if df_data.empty:
            run_logger.info(f"{self.desc} 待写入数据为空，跳过 SQL 执行")
            return

        # 将 DataFrame 转换为字典列表，每行作为 SQL 命名参数的来源
        records = df_data.to_dict(orient="records")

        # 可选：分批提交，避免单次数据量过大（若未配置则不分批）
        batch_size = self.ctx.get("storage.write.batch_size", default=0)
        total = len(records)

        if batch_size > 0:
            for i in range(0, total, batch_size):
                batch = records[i : i + batch_size]
                session.execute(text(sql), batch)
                run_logger.debug(f"已写入 {len(batch)} 条数据 (批次 {i // batch_size + 1})")
        else:
            session.execute(text(sql), records)

        run_logger.info(f"成功通过 SQL 写入 {total} 条数据.")
