from typing import Callable, Dict, Optional
from ..logger.configs import loggers

task_logger = loggers.get_logger("task")


class TaskFuncFactory:
    """任务工厂，用于注册和获取可调用的任务函数。"""
    _map: Dict[str, Callable] = {}

    @classmethod
    def register(cls, name: str):
        """
        装饰器：将函数注册为一个任务，关联到指定的名称。

        用法：
            @TaskFactory.register("email.send_welcome")
            async def send_welcome_email(user_email: str):
                ...

        如果名称已被注册，会发出警告并覆盖原函数。
        """
        def wrapper(func: Callable) -> Callable:
            if name in cls._map:
                task_logger.warning(
                    f"任务名称 '{name}' 已存在，将被覆盖。"
                    f"原函数: {cls._map[name].__name__}，新函数: {func.__name__}"
                )
            cls._map[name] = func
            task_logger.info(f"注册任务: {name} -> {func.__module__}.{func.__name__}")
            return func
        return wrapper

    @classmethod
    def get(cls, name: str, default=None) -> Optional[Callable]:
        """根据名称获取已注册的任务函数，若不存在则返回 None。"""
        return cls._map.get(name, default)

    @classmethod
    def list_tasks(cls) -> list:
        """返回所有已注册的任务名称列表。"""
        return list(cls._map.keys())

    @classmethod
    def unregister(cls, name: str) -> bool:
        """注销指定名称的任务，成功返回 True，名称不存在返回 False。"""
        if name in cls._map:
            del cls._map[name]
            task_logger.info(f"注销任务: {name}")
            return True
        return False