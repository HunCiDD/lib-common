# 数据处理器

from datetime import datetime, timezone
import pytz


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
            dt = dt.replace(tzinfo=timezone.utc)  # 假设无时区时间为UTC
        return dt.astimezone(target_tz)
