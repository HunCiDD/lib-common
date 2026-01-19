import os

import pytest

from lib_common.config.settings import Settings


class TestSettings:


    def test_001(self):
        s = Settings()
        print(s)


if __name__ == '__main__':
    pytest.main()