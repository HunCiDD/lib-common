# 存储策略
from typing import Type, List, Dict, Any
import pandas as pd
from pathlib import Path

from sqlalchemy.orm import Session

from ...logger.configs import loggers
from ...connect.database.types import M
from ...connect.database.repository import BaseRepository
from .base import DataStrategy, DataStrategyFactory

run_logger = loggers.get_logger("run")


# 基础存储策略
class BaseStorageStrategy(DataStrategy):
    def __init__(self, name: str, in_key: str, out_key: str, **kwargs):
        super().__init__(name=name, in_key=in_key, out_key=out_key, category="storage", **kwargs)
        # 待存储的数据
        self.df_storage: pd.DataFrame = pd.DataFrame()

    def execute(self, context: Dict[str, Any]) -> None:
        run_logger.info("Begin storage...")
        self.begin(context)
        run_logger.info("Start storage...")
        self.store(context)

    def begin(self, context: Dict[str, Any]) -> None:
        df_storage = context.get(self.in_key, pd.DataFrame())
        if df_storage is None or df_storage.empty:
            raise ValueError("df_storage cannot be None or empty")
        self.df_storage = df_storage

    def store(self, context: Dict[str, Any]) -> None: ...


@DataStrategyFactory.register("ExeclStorageStrategy")
class ExeclStorageStrategy(BaseStorageStrategy):
    """
    通用文件存储接口：根据 pandas DataFrame，存储为 文件扩展名自动读取 CSV 或 Excel 文件为
    """

    def __init__(
        self, name: str, in_key: str, out_key: str, file: str | Path, engine: str = "openpyxl", **kwargs
    ):
        """
        :param file: str or Path 文件路径，支持 .csv, .xls, .xlsx 等常见格式。
        :param kwargs:
        """
        super().__init__(name=name, in_key=in_key, out_key=out_key, **kwargs)
        self.path = Path(file)
        self.suffix = self.path.suffix.lower()
        self.engine = engine
        self.kwargs = kwargs

    def store(self, context: Dict[str, Any]) -> None:
        if self.suffix == ".csv":
            self.df_storage.to_csv(self.path)
        elif self.suffix in (".xls", ".xlsx"):
            with pd.ExcelWriter(self.path, engine=self.engine) as writer:
                self.df_storage.to_excel(writer, sheet_name="Sheet1")
        else:
            raise ValueError(f"不支持的文件格式: {self.suffix}，仅支持 .csv, .xls, .xlsx")


@DataStrategyFactory.register("DBStorageStrategy")
class DBStorageStrategy(BaseStorageStrategy):
    """
    通用数据库存储接口：根据 pandas DataFrame，存储到对应表
    """

    def __init__(
        self,
        name: str,
        in_key: str,
        out_key: str,
        session: Session,
        model_cls: Type[M],
        conflict_columns: List[str] = None,
        **kwargs,
    ):
        """
        :param name: str
        :param in_key: str
        :param out_key: str
        :param session: SQLAlchemy session
        :param model_cls: SQLAlchemy 模型类
        :param conflict_columns: 冲突列
        :param kwargs: dict
        """
        super().__init__(name=name, in_key=in_key, out_key=out_key, **kwargs)
        self.session = session
        self.model_cls = model_cls
        self.conflict_columns = conflict_columns

    def store(self, context: Dict[str, Any]) -> None:
        records = self.df_storage.to_dict(orient="records")
        BaseRepository.upsert(self.session, self.model_cls, records, self.conflict_columns)
