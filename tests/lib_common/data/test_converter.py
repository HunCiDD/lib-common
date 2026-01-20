from datetime import datetime

import pytest
from lib_common.data.converter import (
    DatetimeConverter,
    FloatConverter,
    ListConverter,
    StringConverter,
)
from pandas import DataFrame


class TestFloatConverter:

    @pytest.mark.parametrize(
        "value, expected",
        [
            (123.45, 123),
            (0.1, 0)
        ]
    )
    def test_to_int_success(self, value, expected):
        assert FloatConverter.to_int(value) == expected

    @pytest.mark.parametrize(
        "value",
        ["abc", None]
    )
    def test_to_int_failure(self, value):
        with pytest.raises(Exception):
            FloatConverter.to_int("abc")

    @pytest.mark.parametrize(
        "value, default, expected",
        [
            ("abc", 0, 0)
        ]
    )
    def test_to_int_default(self, value, default, expected):
        assert FloatConverter.to_int(value, default=default) == expected


class TestStringConvert:

    @pytest.mark.parametrize("value, expected", [("-1", -1), ("2", 2)])
    def test_to_int_success(self, value, expected):
        assert StringConverter.to_int(value) == expected

    @pytest.mark.parametrize("value", ["abc", None])
    def test_to_int_failure(self, value):
        with pytest.raises(Exception):
            StringConverter.to_int(value)

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("2023-10-01 12:34:56", datetime(2023, 10, 1, 12, 34, 56)),
        ]
    )
    def test_to_datetime_success(self, value, expected):
        result = StringConverter.to_datetime(value)
        assert result == expected

    @pytest.mark.parametrize(
        "value, _format, expected",
        [
            ("01/10/2023 12:34:56", "%d/%m/%Y %H:%M:%S", datetime(2023, 10, 1, 12, 34, 56)),
        ],
    )
    def test_to_datetime_custom_format(self, value, _format, expected):
        result = StringConverter.to_datetime(value, format=_format)
        assert result == expected

    @pytest.mark.parametrize("value", ["abc", None])
    def test_to_datetime_failure(self, value):
        with pytest.raises(Exception):
            StringConverter.to_datetime("invalid date")
class TestListConverter:
    def test_to_string_default_separator(self):
        data = ["a", "b", "c"]
        expected = "abc"
        result = ListConverter.to_string(data)
        assert result == expected

    def test_to_string_custom_separator(self):
        data = ["a", "b", "c"]
        separator = ","
        expected = "a,b,c"
        result = ListConverter.to_string(data, sep=separator)
        assert result == expected

    def test_to_dataframe_no_columns(self):
        data = {"a": [1, 2], "b": [3, 4]}
        expected = DataFrame(data)
        result = ListConverter.to_dataframe(data)
        assert result.equals(expected)

    def test_to_dataframe_with_columns(self):
        data = {"a": [1, 2], "b": [3, 4]}
        columns = ["b", "a"]
        expected = DataFrame(data, columns=columns)
        result = ListConverter.to_dataframe(data, columns=columns)
        assert result.equals(expected)


class TestDatetimeConverter:
    def test_to_string_default_format(self):
        data = datetime(2023, 10, 1, 12, 34, 56)
        expected = "2023-10-01 12:34:56"
        result = DatetimeConverter.to_string(data)
        assert result == expected

    def test_to_string_custom_format(self):
        data = datetime(2023, 10, 1, 12, 34, 56)
        _format = "%d/%m/%Y %H:%M:%S"
        expected = "01/10/2023 12:34:56"
        result = DatetimeConverter.to_string(data, format=_format)
        assert result == expected


if __name__ == "__main__":
    pytest.main()
