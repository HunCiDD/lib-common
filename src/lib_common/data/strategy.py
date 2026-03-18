from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ..designs.factory import RegisterFactory


# 1. 策略接口
class Strategy(ABC):
    def __init__(self, name: str, in_key: str = "0", out_key: str = "0", category: str = "base", **kwargs):
        """
        :param name:  策略名称
        :param category:  策略类型，eg: collect, clean, storage 等
        :param in_key: 从上下文获取数据的key
        :param out_key: 输出保存到上下文的key
        """
        self.index = 0
        self.name = name
        self.in_key = in_key
        self.out_key = out_key
        self.category = category
        self.kwargs = kwargs

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> None:
        """执行策略，可修改 context"""
        pass


# 数据策略工厂
class StrategyFactory(RegisterFactory[Strategy]):
    _map = {}
