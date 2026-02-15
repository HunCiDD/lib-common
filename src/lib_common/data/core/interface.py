# 数据采集
from abc import ABC, abstractmethod
from typing import Generic, List
from ...types import SchemaDataT
from ...designs.factory import RegisterFactory


class ICollector(ABC, Generic[SchemaDataT]):
    @abstractmethod
    def collect(self, **kwargs) -> SchemaDataT: ...


class CollectorFactory(RegisterFactory[ICollector]):
    _map = {}


# 数据校验
class IValidator(ABC, Generic[SchemaDataT]):
    @abstractmethod
    def validate(self, data: SchemaDataT) -> bool: ...


class ValidatorFactory(RegisterFactory[IValidator]):
    _map = {}


# 数据清洗
class ICleaner(ABC, Generic[SchemaDataT]):
    @abstractmethod
    def clear(self, **kwargs) -> SchemaDataT: ...


class CleanerFactory(RegisterFactory[ICleaner]):
    _map = {}


# 数据转换
class ITransformer(ABC, Generic[SchemaDataT]):
    @abstractmethod
    def run(self, **kwargs) -> SchemaDataT: ...


class TransformerFactory(RegisterFactory[ITransformer]):
    _map = {}


# 数据聚合
class IAggregator(ABC, Generic[SchemaDataT]):
    @abstractmethod
    def collect(self, **kwargs) -> SchemaDataT: ...


class AggregatorFactory(RegisterFactory[IAggregator]):
    _map = {}


# 数据存储
class IStorager(ABC, Generic[SchemaDataT]):
    @abstractmethod
    def collect(self, **kwargs) -> SchemaDataT: ...


class StoragerFactory(RegisterFactory[IStorager]):
    _map = {}


# 数据分析
class IAnalyser(ABC, Generic[SchemaDataT]):
    @abstractmethod
    def collect(self, **kwargs) -> SchemaDataT: ...


class AnalyserFactory(RegisterFactory[IAnalyser]):
    _map = {}


# 数据可视化
class IVisualizer(ABC, Generic[SchemaDataT]):
    @abstractmethod
    def collect(self, **kwargs) -> SchemaDataT: ...


class VisualizerFactory(RegisterFactory[IVisualizer]):
    _map = {}


class Pipeline(ABC, Generic[SchemaDataT]):
    def __init__(self):
        self.collector = None
        self.validator = None
        self.cleaner = None
        self.transformer = None
        self.aggregator = None
        self.storager = None
        self.analyser = None
        self.visualizer = None

    def run(self, **kwargs) -> List[SchemaDataT]:
        if not self.collector:
            raise ValueError("未设置数据采集器")
