from typing import Dict, Any, Type

import pandas as pd

from ...logger.configs import loggers
from ...connect.database.types import M
from ...connect.database.repository import Repository
from ..converter import ListConverter
from .base import DataStrategy, DataStrategyFactory


run_logger = loggers.get_logger("run")


# 基础可视化策略
class BaseVisualizeStrategy(DataStrategy):
    def __init__(self, name: str, in_key: str, out_key: str, **kwargs):
        super().__init__(name=name, category="visualize", in_key=in_key, out_key=out_key, **kwargs)
        # 待可视化数据
        self.df_visualize = pd.DataFrame()
        # 分析结果
        self.rst: Any = None

    def execute(self, context: Dict[str, Any]) -> None:
        run_logger.info(f"可视化前 {self.name}...")
        self.before(context)
        run_logger.info(f"可视化 {self.name}...")
        self.rst = self.visualize(context)
        run_logger.info(f"可视化后 {self.name}...")
        self.after(context)

    def before(self, context: Dict[str, Any]) -> None:
        df_visualize = context.get(self.in_key, pd.DataFrame())
        if df_visualize is None or df_visualize.empty:
            raise ValueError("待可视化数据不能未空或None")
        self.df_visualize = df_visualize

    def visualize(self, context: Dict[str, Any]) -> Any: ...

    def after(self, context: Dict[str, Any]) -> None:
        if self.rst is None:
            run_logger.error(f"未可视化到{self.name}数据")
            raise ValueError(f"未可视化到{self.name}数据")

        run_logger.info(f"可视化成功，{self.name}数据...")
        context[self.out_key] = self.rst
        run_logger.info(f"成功保存到上下文：{self.out_key}")
