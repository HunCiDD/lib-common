from threading import Lock


class SingletonMeta(type):
    """单例元类，用于创建单例类。使用方法 A(metaclass=SingletonMeta)"""

    _instances = {}
    _lock = Lock()

    def __call__(cls, *args, **kwargs):
        """当类被调用时，检查是否已经存在实例。
        如果不存在，则创建一个新实例并存储起来。
        如果存在，则返回已存在的实例。
        """
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
            return cls._instances[cls]
