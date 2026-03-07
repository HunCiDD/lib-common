# 数据处理器

from datetime import datetime, UTC
import pytz
import pandas as pd


__all__ = [
    "DictProcessor",
    "ListProcessor",
    "StringProcessor",
]


class StringProcessor:
    @staticmethod
    def replace_keys(data: str, keys: list[tuple[str, str]] | None = None) -> str:
        """
        替换key
        :param data:
        :param keys:
        :return:
        """
        if not keys:
            return data
        for old_key, new_key in keys:
            data = data.replace(old_key, new_key)
        return data


class ListProcessor:
    @staticmethod
    def deduplicate(data: list) -> list:
        """去重"""
        return list(set(data))

    @staticmethod
    def range(data: list, limit: int = 0, offset: int = None) -> list:
        if offset is None:
            return data[limit:]
        return data[limit:offset]


class DictProcessor:
    @staticmethod
    def rename_keys(data: dict, key_map: dict | None = None) -> dict:
        if not key_map:
            return data

        new_dict = {}
        for key, value in data.items():
            if key in key_map:
                new_dict[key_map[key]] = value
            else:
                new_dict[key] = value
        return new_dict

    @staticmethod
    def filter_keys(data: dict, keys: list | None = None) -> dict:
        if not keys:
            return data
        return {k: v for k, v in data.items() if k in keys}

    @staticmethod
    def delete_keys(data: dict, keys: list | None = None) -> dict:
        if not keys:
            return data
        return {k: v for k, v in data.items() if k not in keys}

    @staticmethod
    def exclude_keys(data: dict, keys: list | None = None) -> dict:
        if not keys:
            return data
        return {k: v for k, v in data.items() if k not in keys}


class DateTimeProcessor:
    @staticmethod
    def to_timezone(dt: datetime, tz: str = "Asia/Shanghai") -> datetime:
        """
        将时间对象转换到指定时区
        :param dt:
        :param tz:
        :return:
        """
        target_tz = pytz.timezone(tz)
        # 确保时间对象有时区信息
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)  # 假设无时区时间为UTC
        return dt.astimezone(target_tz)


class SeriesProcessor:
    @staticmethod
    def first_non_null(s: pd.Series) -> Any:
        # 获取第一个不为空的
        s = s.dropna()
        return s.iloc[0] if not s.empty else None

    @staticmethod
    def last_non_null(s: pd.Series) -> Any:
        # 获取最后一个不为空的
        s = s.dropna()
        return s.iloc[-1] if not s.empty else None


class DataFrameProcessor:
    @staticmethod
    def deduplicate(
        df_data: pd.DataFrame, key_columns: List[str], agg_methods: Dict[str, Callable] = None
    ) -> pd.DataFrame:
        """
        :param df_data:
        :param key_columns:
        :param agg_methods:
        :return:
        """

        if isinstance(key_columns, str):
            key_columns = [key_columns]

        missing_columns = [col for col in key_columns if col not in df_data.columns]
        if missing_columns:
            raise KeyError(f"键列 {missing_cols} 不存在于DataFrame中")

        if not agg_methods:
            agg_methods = {}

        agg_dict = {}
        for col in df_data.columns:
            if col in key_columns:
                # 键列不参与聚合，groupby会直接保留
                continue

            if col in agg_methods:
                agg_func = agg_methods[col]
            elif "all" in agg_methods:
                agg_func = agg_methods["all"]
            else:
                agg_func = SeriesProcessor.first_non_null

            if not callable(agg_func):
                raise ValueError(f"不支持的聚合方式: {agg_func}")
            agg_dict[col] = agg_func

        # 执行分组聚合
        result = df_data.groupby(key_columns, as_index=False).agg(agg_dict)
        return result
