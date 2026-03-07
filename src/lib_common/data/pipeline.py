from abc import ABC, abstractmethod


from ..designs.factory import RegisterFactory


# 1. 策略接口
class IDataStrategy(ABC):
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> None:
        """执行策略，可修改 context"""
        pass


# 数据策略工厂
class DataStrategyFactory(RegisterFactory[IDataStrategy]):
    _map = {}



# 3. 管道类（本身也是一个策略，支持嵌套）
class DataPipeline:
    def __init__(self, name: str, description: str = "", strategies: List[Strategy] = None):
        self.name = name
        self.description = description
        self.strategies = strategies or []
        self.context: Dict[str, Any] = {}

    def add(self, strategy: Strategy) -> 'Pipeline':
        self.strategies.append(strategy)
        return self  # 支持链式调用

    def execute(self, **kwargs) -> None:
        for strategy in self.strategies:
            strategy.execute(self.context)


class DataPipelineBuilder:

    def build(self, name: str, description: str, configs: List[Dict[str, Any]]) -> DataPipeline:
        strategies = []
        for config in configs:
            category = config.get("category", None)
            parmas = config.get("parms", {})
            if not category:
                continue

            strategy = DataStrategyFactory.create(category, **parmas)
            if not strategy:
                raise ValueError("Failed, ")
            strategies.append(strategy)

        if strategies:
            return DataPipeline(name=name, description=description, strategies=strategies)
        return None



