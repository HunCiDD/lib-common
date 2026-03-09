# 数据转换器
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP

from pandas import DataFrame


__all__ = [
    "DatetimeConverter",
    "FloatConverter",
    "ListConverter",
    "IntConverter",
    "StringConverter",
]


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


class FloatConverter(ToIntConvertMixin):
    @convert_exception
    @staticmethod
    def to_decimal(data: float, precision: int = 10, scale: int = 4, rounding=ROUND_HALF_UP, **kwargs) -> Decimal:
        """
        将 float 转换为 Decimal，并确保其符合给定的精度和小数位数要求。
        :param data: 待转换的 float 值。
        :param precision: 总有效位数（必须 >= scale）。
        :param scale: 小数部分位数。
        :param rounding: 舍入模式，默认为 ROUND_HALF_UP（四舍五入）。
        :param kwargs:
        :return: 转换后的 Decimal 对象，小数位数固定为 scale，且总有效位数 ≤ precision。
        """
        # 参数校验
        if precision < scale or scale < 0 or precision <= 0:
            raise ValueError("precision 必须 >= scale，且两者均为非负整数（precision > 0）")
        # 通过字符串构造 Decimal，避免浮点误差
        d = Decimal(str(data))
        # 构建 quantize 模板，例如 scale=2 时模板为 Decimal('0.00')
        if scale == 0:
            quantize_template = Decimal("1")
        else:
            quantize_template = Decimal("0." + "0" * scale)
        # 执行舍入，固定小数位数
        quantized = d.quantize(quantize_template, rounding=rounding)
        sig_digits = len(quantized.as_tuple().digits)
        if sig_digits > precision:
            raise ValueError(f"转换结果 {quantized} 的有效位数为 {sig_digits}，超过了指定的 precision={precision}")
        return quantized


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
