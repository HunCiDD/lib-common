import pytest
from lib_common.security.cryptor import CRYPTOR_WORK_SETTINGS, Cryptor


class TestCryptor:
    def test_001(self):
        default_work_key = CRYPTOR_WORK_SETTINGS["default"]
        ct = Cryptor(default_work_key)
        plain_text = "hdd123"
        r = ct.encrypt(plain_text)
        text = ct.decrypt(r)
        assert plain_text == text


if __name__ == "__main__":
    pytest.main()
