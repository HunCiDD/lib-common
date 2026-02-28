# 数据转换器
__all__ = [
    "DatetimeConverter",
    "FloatConverter",
    "ListConverter",
    "IntConverter",
    "StringConverter",
]

from datetime import datetime, date

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


class IntConverter:
    @convert_exception
    @staticmethod
    def to_bool(data: int, **kwargs) -> bool:
        return bool(data)


class FloatConverter(ToIntConvertMixin): ...


class StringConverter(ToIntConvertMixin):
    @convert_exception
    @staticmethod
    def to_datetime(data: str, **kwargs) -> datetime:
        _format = kwargs.get("format", "%Y-%m-%d %H:%M:%S")
        return datetime.strptime(data, _format)

    @convert_exception
    @staticmethod
    def to_date(data: str, **kwargs) -> date:
        return StringConverter.to_datetime(data, **kwargs).date()

    @convert_exception
    @staticmethod
    def to_upper(data: str, **kwargs) -> str:
        return str(data).strip().upper()

    @convert_exception
    @staticmethod
    def to_lower(data: str, **kwargs) -> str:
        return str(data).strip().lower()

    @convert_exception
    @staticmethod
    def to_bool(data: str, **kwargs) -> bool:
        data = data.lower().strip()
        if data in ("true", "t", "yes", "y", "1"):
            return True
        elif data in ("false", "f", "no", "n", "0", "none", "null"):
            return False
        else:
            raise ValueError(f"Invalid type for boolean: {data}")


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
