from typing import Union, Type, List
import pandas as pd
from pathlib import Path

from sqlalchemy.orm import Session

from ...connect.database.types import M
from ...connect.database.repository import BaseRepository
from ..interface import IStorager
from ..factory import StoragerFactory


@StoragerFactory.register("ExeclStorager")
class ExeclStorager(IStorager):
    """
    通用文件存储接口：根据 pandas DataFrame，存储为 文件扩展名自动读取 CSV 或 Excel 文件为
    """

    def __init__(self, file: Union[str, Path], engine: str = "openpyxl", **kwargs):
        """
        :param file: str or Path 文件路径，支持 .csv, .xls, .xlsx 等常见格式。
        :param kwargs:
        """
        self.path = Path(file)
        self.suffix = self.path.suffix.lower()
        self.engine = engine
        self.kwargs = kwargs

    def store(self, df_clean_rst: pd.DataFrame, **kwargs) -> None:
        if df_clean_rst is None or df_clean_rst.empty:
            raise ValueError("df_clean_rst is None or empty")

        if self.suffix == ".csv":
            df_clean_rst.to_csv(self.path, **kwargs)
        elif self.suffix in (".xls", '.xlsx'):
            with pd.ExcelWriter(self.path, engine=self.engine) as writer:
                df_clean_rst.to_excel(writer, sheet_name="Sheet1", **kwargs)
        else:
            raise ValueError(f"不支持的文件格式: {self.suffix}，仅支持 .csv, .xls, .xlsx")


@StoragerFactory.register("DBStorager")
class DBStorager(IStorager):
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

    def store(self, df_data: pd.DataFrame, *args, **kwargs) -> None:
        records = df_data.to_dict(orient="records")
        BaseRepository.upsert(self.session, self.model_cls, records, self.conflict_columns)


