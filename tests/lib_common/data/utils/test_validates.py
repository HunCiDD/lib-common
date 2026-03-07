from pathlib import Path

import pytest
from lib_common.data.validates import (
    validate_bool,
    validate_host,
    validate_int,
    validate_ip,
    validate_domain,
    validate_path,
    validate_port,
    validate_password,
)


class TestValidateBool:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("true", True),
            ("TRUE", True),
            ("t", True),
            ("T", True),
            ("yes", True),
            ("YES", True),
            ("Yes", True),
            ("Y", True),
            ("y", True),
            ("1", True),
            ("false", False),
            ("False", False),
            ("f", False),
            ("No", False),
            ("N", False),
            ("0", False),
            (True, True),
            (False, False),
        ],
    )
    def test_valid(self, value, expected):
        assert validate_bool(value) == expected

    @pytest.mark.parametrize("value", ["a", "-1", 3.14, [], {}])
    def test_invalid(self, value):
        with pytest.raises(ValueError):
            validate_bool(value)


class TestValidateInt:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("123", 123),
            (456, 456),
            ("0", 0),
            (-10, -10),
        ],
    )
    def test_valid(self, value, expected):
        assert validate_int(value) == expected

    @pytest.mark.parametrize(
        "invalid_value",
        [
            "12.3",
            "abc",
            None,
            "123a",
        ],
    )
    def test_validate_int_invalid(self, invalid_value):
        with pytest.raises(ValueError):
            validate_int(invalid_value)


# class TestValidateUpper:
#     # Tests for validate_upper
#     @pytest.mark.parametrize(
#         "value, expected",
#         [
#             ("abc", "ABC"),
#             ("AbC", "ABC"),
#             (123, "123"),
#             (None, "NONE"),
#             ("", ""),
#         ],
#     )
#     def test_validate_upper(self, value, expected):
#         assert validate_upper(value) == expected


# class TestValidateLower:
#     # Tests for validate_lower
#     @pytest.mark.parametrize(
#         "value, expected",
#         [
#             ("ABC", "abc"),
#             ("AbC", "abc"),
#             (456, "456"),
#             (None, "none"),
#             ("", ""),
#         ],
#     )
#     def test_validate_lower(self, value, expected):
#         assert validate_lower(value) == expected


class TestValidateIP:
    # Tests for validate_ip
    @pytest.mark.parametrize(
        "ip",
        [
            "192.168.1.1",
            "8.8.8.8",
            "::1",
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "2001:db8::",
        ],
    )
    def test_valid(self, ip):
        assert validate_ip(ip) == ip

    @pytest.mark.parametrize(
        "invalid_ip",
        [
            "256.0.0.1",
            "invalid.ip",
            "2001:dg::1",
            "192.168.1",
            "192.168.1.1.1",
        ],
    )
    def test_invalid(self, invalid_ip):
        with pytest.raises(ValueError):
            validate_ip(invalid_ip)


class TestValidateDomain:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("example.com", "example.com"),
            ("sub.example.com", "sub.example.com"),
            ("Sub.Domain.com", "sub.domain.com"),
            ("xn--example-9ua.com", "xn--example-9ua.com"),
            ("a-b-c.com", "a-b-c.com"),
            ("123.com", "123.com"),
        ],
    )
    def test_valid(self, value, expected):
        assert validate_domain(value) == expected

    @pytest.mark.parametrize(
        "value",
        [
            "example..com",
            "-example.com",
            "example-.com",
            "example.com.",
            "exa_mple.com",
            "example",
            "example.123",
            '"a"*64 + ".com"..double-dot.com',
            ".start-with-dot.com",
            "",
        ],
    )
    def test_invalid(self, value):
        with pytest.raises(ValueError):
            validate_domain(value)


class TestValidateHost:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("localhost", "localhost"),
            ("sub.example.com", "sub.example.com"),
            ("127.0.0.1", "127.0.0.1"),
        ],
    )
    def test_valid(self, value, expected):
        assert validate_host(value) == expected


class TestValidatePort:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("8080", 8080),
            (443, 443),
            ("65535", 65535),
            (65535, 65535),
        ],
    )
    def test_valid(self, value, expected):
        assert validate_port(value) == expected

    @pytest.mark.parametrize(
        "value",
        [
            -1,
            65536,
            "65536",
            "-10",
            70000,
            "invalid",
        ],
    )
    def test_invalid(self, value):
        with pytest.raises(ValueError):
            validate_port(value)


class TestValidatePath:
    # Tests for validate_path
    def test_valid(self, tmp_path):
        existing_dir = tmp_path / "existing_dir"
        existing_dir.mkdir()

        # Test existing path with exist=True
        assert validate_path(existing_dir, exist=True) == existing_dir.resolve()

        # Test non-existing path with exist=False
        non_existing = tmp_path / "non_existing"
        assert validate_path(non_existing, exist=False) == non_existing.resolve()

        # Test string path
        assert validate_path(str(existing_dir)) == existing_dir.resolve()

    def test_invalid(self):
        # Test invalid type
        with pytest.raises(ValueError):
            validate_path(123)

        # Test non-existing path with exist=True
        non_existing = Path("/non/existing/path")
        with pytest.raises(ValueError):
            validate_path(non_existing, exist=True)


class TestValidatePassword:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("Passw0rd!", "Passw0rd!"),
            ("A@1bcdef", "A@1bcdef"),
            ("Zxcvb123$", "Zxcvb123$"),
            ("Qwerty%789", "Qwerty%789"),
        ],
    )
    def test_valid(self, value, expected):
        assert validate_password(value) == expected

    @pytest.mark.parametrize(
        "value",
        [
            "PASSWORD1!",  # 测试缺少小写字母
            "password1!",  # 测试缺少大写字母
            "Password!",  # 测试缺少数字
            "password",  # 测试同时缺少多个要求
        ],
    )
    def test_invalid(self, value):
        with pytest.raises(ValueError):
            validate_ip(value)


if __name__ == "__main__":
    pytest.main()
