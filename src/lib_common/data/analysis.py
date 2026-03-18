from typing import Dict, Any, Type

import pandas as pd

from ..logger.configs import loggers
from ..connect.database.types import M
from ..connect.database.repository import Repository
from .converter import ListConverter
from .strategy import Strategy, StrategyFactory


run_logger = loggers.get_logger("run")


# 基础分析策略
@StrategyFactory.register("base.analysis")
class BaseAnalysisStrategy(Strategy):
    def __init__(self, name: str, in_key: str, out_key: str, **kwargs):
        super().__init__(name=name, category="analysis", in_key=in_key, out_key=out_key, **kwargs)
        # 待分析数据
        self.df_analysis = pd.DataFrame()
        # 分析结果
        self.df_analysis_rst = pd.DataFrame()

    def execute(self, context: Dict[str, Any]) -> None:
        run_logger.info(f"分析前 {self.name}...")
        self.before(context)
        run_logger.info(f"分析 {self.name}...")
        self.df_analysis_rst = self.analysis(context)
        run_logger.info(f"分析后 {self.name}...")
        self.after(context)

    def before(self, context: Dict[str, Any]) -> None:
        df_analysis = context.get(self.in_key, pd.DataFrame())
        if df_analysis is None or df_analysis.empty:
            raise ValueError("待分析数据不能未空或None")
        self.df_analysis = df_analysis

    def analysis(self, context: Dict[str, Any]) -> pd.DataFrame | None: ...

    def after(self, context: Dict[str, Any]) -> None:
        if self.df_analysis_rst is None or self.df_analysis_rst.empty:
            run_logger.error(f"未分析到{self.name}数据")
            raise ValueError(f"未分析到{self.name}数据")

        run_logger.info(f"成功分析到{self.name}数据：{len(self.df_analysis_rst)}条记录...")
        context[self.out_key] = self.df_analysis_rst
        run_logger.info(f"成功保存到上下文：{self.out_key}")
