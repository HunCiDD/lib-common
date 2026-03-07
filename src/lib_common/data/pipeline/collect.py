from typing import Dict, Any, Type
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from ...logger.configs import loggers
from ...connect.database.types import M
from ...connect.database.repository import BaseRepository
from ..converter import ListConverter
from .base import DataStrategy, DataStrategyFactory

run_logger = loggers.get_logger("run")


class BaseCollectStrategy(DataStrategy):
    def __init__(self, name: str, in_key: str, out_key: str, **kwargs):
        super().__init__(name=name, category="collect", in_key=in_key, out_key=out_key, **kwargs)
        self.df_collect_rst = pd.DataFrame()

    def execute(self, context: Dict[str, Any]) -> None:
        self.df_collect_rst = self.collect(context)
        self.after(context)

    def collect(self, context: Dict[str, Any]) -> pd.DataFrame | None: ...

    def after(self, context: Dict[str, Any]) -> None:
        if self.df_collect_rst is None or self.df_collect_rst.empty:
            run_logger.error(f"未采集到{self.name}数据")
            raise ValueError(f"未采集到{self.name}数据")

        run_logger.info(f"成功采集到{self.name}数据：{len(self.df_collect_rst)}条记录...")
        context[self.out_key] = self.df_collect_rst
        run_logger.info(f"成功保存到上下文：{self.out_key}")


DataStrategyFactory.register("ExeclCollectStrategy")


class ExeclCollectStrategy(BaseCollectStrategy):
    """
    通用文件加载接口：根据文件扩展名自动读取 CSV 或 Excel 文件为 pandas DataFrame。
    """

    def __init__(self, name: str, in_key: str, out_key: str, file: str | Path, dtype: dict = None, **kwargs):
        """
        :param name: str
        :param file: str or Path 文件路径，支持 .csv, .xls, .xlsx 等常见格式。
        :param dtype: 指定列数据类型
        """
        super().__init__(name=name, category="collect", in_key=in_key, out_key=out_key, **kwargs)
        self.file = file
        self.path = Path(self.file)
        self.dtype = dtype
        if not self.path.exists():
            raise FileNotFoundError(f"文件不存在: {self.path}")

    def collect(self, context: Dict[str, Any]) -> pd.DataFrame | None:
        suffix = self.path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(self.path, dtype=self.dtype, encoding="utf-8")
        elif suffix in (".xls", ".xlsx"):
            # Excel 文件可以指定 sheet_name，默认为第一个 sheet
            return pd.read_excel(self.path, dtype=self.dtype)
        else:
            raise ValueError(f"不支持的文件格式: {suffix}，仅支持 .csv, .xls, .xlsx")


DataStrategyFactory.register("DBCollectStrategy")


class DBCollectStrategy(BaseCollectStrategy):
    def __init__(
        self,
        name: str,
        in_key: str,
        out_key: str,
        session: Session,
        model_cls: Type[M],
        columns: list[str] = None,
        filters: Dict[str, Any] | None = None,
        orders: Dict[str, Any] | None = None,
        offset: int = 0,
        limit: int = 100,
        **kwargs,
    ):
        """
        :param name: str
        :param in_key: str
        :param out_key: str
        :param session: Session
        :param model_cls: Type[M]
        :param columns: list[str]
        :param filters: dict
        :param orders: dict
        :param offset: int
        :param limit: int
        :param kwargs: dict
        """
        super().__init__(name=name, category="collect", in_key=in_key, out_key=out_key, **kwargs)
        self.session = session
        self.model_cls = model_cls
        self.columns = columns
        self.filters = filters
        self.orders = orders
        self.offset = offset
        self.limit = limit

    def collect(self, context: Dict[str, Any]) -> pd.DataFrame | None:
        rows = BaseRepository.list(
            session=self.session,
            model_cls=self.model_cls,
            filters=self.filters,
            orders=self.orders,
            offset=self.offset,
            limit=self.limit,
        )
        if self.columns:
            return ListConverter.to_dataframe([row.as_dict() for row in rows], columns=self.columns)
        else:
            return ListConverter.to_dataframe([row.as_dict() for row in rows])
