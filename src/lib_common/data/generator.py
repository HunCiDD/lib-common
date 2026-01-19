# 数据生成器
__all__ = [
    "RandomBytesGenerator",
    "RandomFloatGenerator",
    "RandomIntGenerator",
    "RandomStringGenerator",
    "UuidGenerator",
    "DateTimeGenerator",
]

import os
import platform
import secrets
import string
import time
from datetime import datetime
from uuid import NAMESPACE_DNS, UUID, uuid5

from pytz import timezone


class RandomIntGenerator:
    @staticmethod
    def by_range(start: int = 0, end: int = 10) -> int:
        secrets_generator = secrets.SystemRandom()
        return secrets_generator.randint(start, end)


class RandomBytesGenerator:
    @staticmethod
    def sby_length(length: int = 10) -> bytes:
        if platform.system() == "Linux":
            with open("/dev/random", "rb") as file:
                random_data = file.read(length)
        else:
            random_data = os.urandom(length)
        return random_data


class RandomStringGenerator:
    @staticmethod
    def by_length(length: int = 10) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))


class RandomFloatGenerator:
    # Generate random floating-point numbers

    @staticmethod
    def by_range(start: float = 0.0, end: float = 1.0) -> float:
        secrets_generator = secrets.SystemRandom()
        return secrets_generator.uniform(start, end)


class UuidGenerator:
    @staticmethod
    def by_value(value: str, random: bool = False) -> UUID:
        random_num = RandomIntGenerator.by_range(0, 10000) if random else 0
        return uuid5(NAMESPACE_DNS, f"{value}{random_num}")

    @staticmethod
    def by_time(random: bool = True) -> UUID:
        random_num = RandomIntGenerator.by_range(0, 10000) if random else 0
        return uuid5(NAMESPACE_DNS, f"{time.time()}{random_num}")


class DateTimeGenerator:
    @staticmethod
    def now(tz: str = "Asia/Shanghai") -> datetime:
        return datetime.now(timezone(tz)).replace(tzinfo=None)

    @staticmethod
    def today(
        hour: int = 0, minute: int = 0, second: int = 0, microsecond: int = 0, tz: str = "Asia/Shanghai"
    ) -> datetime:
        return datetime.now(timezone(tz)).replace(
            hour=hour, minute=minute, second=second, microsecond=microsecond, tzinfo=None
        )

    @staticmethod
    def today_start(tz: str = "Asia/Shanghai") -> datetime:
        return datetime.now(timezone(tz)).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)

    @staticmethod
    def today_end(tz: str = "Asia/Shanghai") -> datetime:
        return datetime.now(timezone(tz)).replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=None)
