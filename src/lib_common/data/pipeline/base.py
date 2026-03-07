from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ...designs.factory import RegisterFactory


# 1. 策略接口
class DataStrategy(ABC):
    def __init__(self, name: str, category: str = "base", in_key: str = "0", out_key: str = "0", **kwargs):
        """
        :param name:  策略名称
        :param category:  策略类型，eg: collect, clean, storage 等
        :param in_key: 从上下文获取数据的key
        :param out_key: 输出保存到上下文的key
        """
        self.index = 0
        self.name = name
        self.category = category
        self.in_key = in_key
        self.out_key = out_key
        self.kwargs = kwargs

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> None:
        """执行策略，可修改 context"""
        pass


# 数据策略工厂
class DataStrategyFactory(RegisterFactory[DataStrategy]):
    _map = {}


# 3. 管道类（本身也是一个策略，支持嵌套）
class DataPipeline:
    def __init__(self, name: str, description: str = "", strategies: List[DataStrategy] = None):
        self.name = name
        self.description = description
        self.strategies = strategies or []
        self.context: Dict[str, Any] = {}

    def add(self, strategy: DataStrategy) -> DataPipeline:
        self.strategies.append(strategy)
        return self  # 支持链式调用

    def run(self, **kwargs) -> None:
        for strategy in self.strategies:
            strategy.execute(self.context)


class DataPipelineBuilder:
    @staticmethod
    def build(pl_name: str, pl_description: str, strategy_configs: List[Dict[str, Any]]) -> DataPipeline:
        """"""
        # 根据配置构建策略实例
        strategies = []
        for config in strategy_configs:
            s_name = config.get("name", "")
            s_category = config.get("category", "base")
            s_in_key = config.get("ik", "0")
            s_out_key = config.get("out_key", "0")
            s_kwargs = config.get("kwargs", {})

            strategy = DataStrategyFactory.create(
                name=s_name, category=s_category, in_key=s_in_key, out_key=s_out_key, **s_kwargs
            )
            if not strategy:
                raise ValueError("Failed, name must in strategy configs")
            strategies.append(strategy)

        if not strategies:
            raise ValueError("Failed, strategies must in strategy configs")

        return DataPipeline(name=pl_name, description=pl_description, strategies=strategies)
