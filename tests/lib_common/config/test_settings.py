import pytest

from lib_common.settings import get_settings


class TestSettings:
    @pytest.mark.skip(reason="需要正确配置环境变量和配置文件")
    def test_001(self):
        s = get_settings()
        print(s.model_dump())


if __name__ == "__main__":
    pytest.main()
