from typing import Union
from pathlib import Path

import pandas as pd

from ..interface import ICollector
from ..factory import CollectorFactory


@CollectorFactory.register("ExeclCollector")
class ExeclCollector(ICollector):
    """
    通用文件加载接口：根据文件扩展名自动读取 CSV 或 Excel 文件为 pandas DataFrame。
    """

    def __init__(self, file: Union[str, Path], dtype: dict = None, **kwargs):
        """
        :param file: str or Path 文件路径，支持 .csv, .xls, .xlsx 等常见格式。
        :param dtype: 指定列数据类型
        """
        self.file = file
        self.path = Path(self.file)
        self.dtype = dtype
        self.kwargs = kwargs
        if not self.path.exists():
            raise FileNotFoundError(f"文件不存在: {self.path}")

    def collect(self, **kwargs) -> pd.DataFrame:
        suffix = self.path.suffix.lower()
        if suffix == ".csv":
            # 默认编码尝试 utf-8，可通过 kwargs 覆盖
            kwargs.setdefault("encoding", "utf-8")
            return pd.read_csv(self.path, dtype=self.dtype, **kwargs)
        elif suffix in (".xls", ".xlsx"):
            # Excel 文件可以指定 sheet_name，默认为第一个 sheet
            return pd.read_excel(self.path, dtype=self.dtype, **kwargs)
        else:
            raise ValueError(f"不支持的文件格式: {suffix}，仅支持 .csv, .xls, .xlsx")
