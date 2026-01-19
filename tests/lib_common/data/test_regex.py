import re
import pytest

from app_base.data.regex import RegexPatterns  # 替换 your_module 为实际模块名


class TestRegexPatterns:
    @pytest.mark.parametrize("input, expected", [("12345", True), ("abc", False), ("12a3", False), ("", False)])
    def test_num(self, input, expected):
        assert bool(re.match(RegexPatterns.Num, input)) == expected

    @pytest.mark.parametrize("input, expected", [("abcXYZ", True), ("abc123", False), ("a b", False), ("", False)])
    def test_str(self, input, expected):
        assert bool(re.match(RegexPatterns.Str, input)) == expected

    @pytest.mark.parametrize(
        "input, expected",
        [
            ("13912345678", True),  # 有效手机号
            ("19912345678", True),  # 199号段
            ("10612345678", False),  # 无效号段
            ("12345678901", False),  # 错误开头
            ("1391234567", False),  # 位数不足
            ("139123456789", False),  # 位数过多
            ("139abc5678", False),  # 包含字母
        ],
    )
    def test_phone_number(self, input, expected):
        assert bool(re.match(RegexPatterns.PhoneNumber, input)) == expected

    @pytest.mark.parametrize(
        "input, expected",
        [
            ("user_123", True),
            ("USER", True),
            ("user@name", False),  # 包含非法字符
            ("", False),
        ],
    )
    def test_username(self, input, expected):
        assert bool(re.match(RegexPatterns.Username, input)) == expected

    @pytest.mark.parametrize(
        "input, expected",
        [
            ("Passw0rd!", True),  # 符合所有要求
            ("Short1!", False),  # 长度不足
            ("lowercase1!", False),  # 缺少大写字母
            ("UPPERCASE1!", False),  # 缺少小写字母
            ("Password!", False),  # 缺少数字
            ("Passw0rd", False),  # 缺少特殊字符
            ("P@ssw0rd" * 20, False),  # 超长（>128字符）
            ("空格 Pass1!", False),  # 包含空格（未允许字符）
        ],
    )
    def test_password(self, input, expected):
        assert bool(re.match(RegexPatterns.Password, input)) == expected


if __name__ == "__main__":
    pytest.main()
