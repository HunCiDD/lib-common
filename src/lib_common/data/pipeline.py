from __future__ import annotations
from typing import Any, Dict, List

from .strategy import Strategy, StrategyFactory


class Pipeline:
    def __init__(self, name: str, description: str = "", strategies: List[Strategy] = None):
        self.name = name
        self.description = description
        self.strategies = strategies or []
        self.context: Dict[str, Any] = {}

    def add(self, strategy: Strategy) -> Pipeline:
        self.strategies.append(strategy)
        return self  # 支持链式调用

    def run(self, **kwargs) -> None:
        for strategy in self.strategies:
            strategy.execute(self.context)


class PipelineBuilder:
    @staticmethod
    def build(pl_name: str, pl_description: str, strategy_configs: List[Dict[str, Any]]) -> Pipeline:
        """"""
        # 根据配置构建策略实例
        strategies = []
        for config in strategy_configs:
            s_name = config.get("name", "")
            s_category = config.get("category", "base")
            s_in_key = config.get("ik", "0")
            s_out_key = config.get("out_key", "0")
            s_kwargs = config.get("kwargs", {})

            strategy = StrategyFactory.create(
                name=s_name, category=s_category, in_key=s_in_key, out_key=s_out_key, **s_kwargs
            )
            if not strategy:
                raise ValueError("Failed, name must in strategy configs")
            strategies.append(strategy)

        if not strategies:
            raise ValueError("Failed, strategies must in strategy configs")

        return Pipeline(name=pl_name, description=pl_description, strategies=strategies)
