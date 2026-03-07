# 存储策略
from typing import Union, Type, List, Dict
import pandas as pd
from pathlib import Path

from sqlalchemy.orm import Session

from ...connect.database.types import M
from ...connect.database.repository import BaseRepository
from .base import IDataStrategy, DataStrategyFactory


# 基础存储策略
class BaseStorageStrategy(IDataStrategy):

    def __init__(self, tag: str):
        self.tag = tag
        # 待存储的数据
        self.df_storage: pd.DataFrame = pd.DataFrame()

    def execute(self, context: Dict[str, Any]) -> None:
        self.begin(context)
        self.store(context)

    def begin(self, context: Dict[str, Any]) -> None:
        if self.df_storage is None or self.df_storage.empty:
            raise ValueError("df_storage cannot be None or empty")

    def store(self, context: Dict[str, Any]) -> None:
        ...


@DataStrategyFactory.register("ExeclStorageStrategy")
class ExeclStorageStrategy(BaseStorageStrategy):
    """
    通用文件存储接口：根据 pandas DataFrame，存储为 文件扩展名自动读取 CSV 或 Excel 文件为
    """

    def __init__(self, tag: str, file: Union[str, Path], engine: str = "openpyxl", **kwargs):
        """
        :param file: str or Path 文件路径，支持 .csv, .xls, .xlsx 等常见格式。
        :param kwargs:
        """
        super().__init__(tag)
        self.path = Path(file)
        self.suffix = self.path.suffix.lower()
        self.engine = engine
        self.kwargs = kwargs

    def store(self, context: Dict[str, Any]) -> None:
        if self.suffix == ".csv":
            self.df_storage.to_csv(self.path, **kwargs)
        elif self.suffix in (".xls", ".xlsx"):
            with pd.ExcelWriter(self.path, engine=self.engine) as writer:
                self.df_storage.to_excel(writer, sheet_name="Sheet1", **kwargs)
        else:
            raise ValueError(f"不支持的文件格式: {self.suffix}，仅支持 .csv, .xls, .xlsx")


@DataStrategyFactory.register("DBStorageStrategy")
class DBStorageStrategy(BaseStorageStrategy):
    """
    通用数据库存储接口：根据 pandas DataFrame，存储到对应表
    """

    def __init__(self, session: Session, model_cls: Type[M], conflict_columns: List[str] = None):
        """
        :param session: SQLAlchemy session
        :param model_cls: SQLAlchemy 模型类
        :param conflict_columns: 冲突列
        """
        self.session = session
        self.model_cls = model_cls
        self.conflict_columns = conflict_columns

    def store(self, context: Dict[str, Any]) -> None:
        records = self.df_storage.to_dict(orient="records")
        BaseRepository.upsert(self.session, self.model_cls, records, self.conflict_columns)
