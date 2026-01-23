import pytest

from lib_common.settings import get_settings


class TestSettings:
    def test_001(self):
        s = get_settings()
        print(s.model_dump())


if __name__ == "__main__":
    pytest.main()
