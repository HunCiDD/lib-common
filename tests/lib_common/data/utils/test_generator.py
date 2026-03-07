import time
from uuid import UUID

import pytest
from lib_common.data.generator import (
    RandomFloatGenerator,
    RandomIntGenerator,
    RandomStringGenerator,
    UuidGenerator,
)


class TestRandomIntGenerator:
    def test_by_range(self):
        result = RandomIntGenerator.by_range(0, 100)
        assert isinstance(result, int)
        assert 0 <= result <= 100


class TestRandomFloatGenerator:
    def test_by_range(self):
        result = RandomFloatGenerator.by_range(0.0, 100.0)
        assert isinstance(result, float)
        assert 0.0 <= result <= 100.0


class TestRandomStringGenerator:
    def test_by_length(self):
        result = RandomStringGenerator.by_length(15)
        assert isinstance(result, str)
        assert len(result) == 15


class TestUuidGenerator:
    def test_uuid_generator_by_value(self):
        result = UuidGenerator.by_value("test_value")
        assert isinstance(result, UUID)
        new_result = UuidGenerator.by_value("test_value")
        assert result == new_result

    def test_uuid_generator_by_time(self):
        result = UuidGenerator.by_time()
        assert isinstance(result, UUID)
        time.sleep(1)
        new_result = UuidGenerator.by_time()
        assert result != new_result


if __name__ == "__main__":
    pytest.main()
