# 数据转换器
__all__ = [
    "DatetimeConverter",
    "FloatConverter",
    "ListConverter",
    "StringConverter",
]

from datetime import datetime

from pandas import DataFrame


def convert_exception(func):
    """
    转换异常装饰器，如何参数中存在default，即不抛异常，返回默认值
    :param func:
    :return:
    """
    def wrapper(data, **kwargs):
        try:
            return func(data, **kwargs)
        except Exception as e:
            if "default" in kwargs:
                return kwargs["default"]
            raise e

    return wrapper


class ToIntConvertMixin:
    @convert_exception
    @staticmethod
    def to_int(data, **kwargs) -> int:
        return int(data)


class ToDataFrameConvertMixin:
    @convert_exception
    @staticmethod
    def to_dataframe(data, **kwargs) -> DataFrame:
        _columns = kwargs.get("columns", [])
        if _columns:
            return DataFrame(data, columns=_columns)
        return DataFrame(data)


class FloatConverter(ToIntConvertMixin): ...


class StringConverter(ToIntConvertMixin):
    @convert_exception
    @staticmethod
    def to_datetime(data: str, **kwargs) -> datetime:
        _format = kwargs.get("format", "%Y-%m-%d %H:%M:%S")
        return datetime.strptime(data, _format)


class ListConverter(ToDataFrameConvertMixin):
    @convert_exception
    @staticmethod
    def to_string(data: list, **kwargs) -> str:
        _sep = str(kwargs.get("sep", ""))
        return _sep.join(data)


class DatetimeConverter:
    @convert_exception
    @staticmethod
    def to_string(data: datetime, **kwargs) -> str:
        _format = kwargs.get("format", "%Y-%m-%d %H:%M:%S")
        return data.strftime(_format)
