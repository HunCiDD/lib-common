from typing import Dict, Any

import pandas as pd

from ..logger.configs import loggers
from .strategy import Strategy, StrategyFactory


run_logger = loggers.get_logger("run")


@StrategyFactory.register("base.clean")
class BaseCleanStrategy(Strategy):
    def __init__(self, name: str, in_key: str, out_key: str, **kwargs):
        super().__init__(name=name, category="collect", in_key=in_key, out_key=out_key, **kwargs)

        # 待清洗数据
        self.df_clean: pd.DataFrame = pd.DataFrame()
        # 清洗结果
        self.df_clean_rst = pd.DataFrame()

    def execute(self, context: Dict[str, Any]) -> None:
        run_logger.info("Begin clean...")
        self.before(context)
        run_logger.info("Start clean...")
        self.df_clean_rst = self.clean(context)
        run_logger.info("After clean...")
        self.after(context)

    def before(self, context: Dict[str, Any]) -> None:
        df_clean = context.get(self.in_key, pd.DataFrame())
        if df_clean is None or df_clean.empty:
            raise ValueError("df_clean cannot be None or empty")
        self.df_clean = df_clean

    def clean(self, context: Dict[str, Any]) -> pd.DataFrame | None: ...

    def after(self, context: Dict[str, Any]) -> None:
        if self.df_clean_rst is None or self.df_clean_rst.empty:
            run_logger.error("清洗结果不存在")
            raise ValueError("清洗结果不存在")

        run_logger.info(f"成功清洗数据：{len(self.df_clean_rst)}条记录...")
        context[self.out_key] = self.df_clean_rst
        run_logger.info(f"成功保存到上下文：{self.out_key}")
