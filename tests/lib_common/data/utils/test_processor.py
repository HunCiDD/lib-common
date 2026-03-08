import pytest

import numpy as np
import pandas as pd

from lib_common.data.processor import StringProcessor, ListProcessor, DictProcessor, SeriesProcessor, DataFrameProcessor


class TestStringProcessor:
    # 测试替换单个键
    def test_replace_single_key(self):
        data = "Hello {name}, your id is {user_id}"
        keys = [("{name}", "Alice")]
        result = StringProcessor.replace_keys(data, keys)
        assert result == "Hello Alice, your id is {user_id}"

    # 测试替换多个键
    def test_replace_multiple_keys(self):
        data = "User {id}: {name} - {role}"
        keys = [("{id}", "001"), ("{name}", "Bob"), ("{role}", "Admin")]
        result = StringProcessor.replace_keys(data, keys)
        assert result == "User 001: Bob - Admin"

    # 测试替换顺序
    def test_replace_order(self):
        data = "abc def ghi"
        keys = [("abc", "123"), ("123", "XYZ")]
        result = StringProcessor.replace_keys(data, keys)
        assert result == "XYZ def ghi"

    # 测试空键列表
    def test_replace_no_keys(self):
        data = "No changes here"
        result = StringProcessor.replace_keys(data, None)
        assert result == "No changes here"
        result = StringProcessor.replace_keys(data, [])
        assert result == "No changes here"

    # 测试特殊字符替换
    def test_replace_special_characters(self):
        data = "Line 1\nLine 2\tTab"
        keys = [("\n", "<br>"), ("\t", "    ")]
        result = StringProcessor.replace_keys(data, keys)
        assert result == "Line 1<br>Line 2    Tab"


class TestListProcessor:
    # 测试去重
    def test_deduplicate(self):
        data = [1, 2, 2, 3, 4, 4, 4]
        result = ListProcessor.deduplicate(data)
        assert sorted(result) == [1, 2, 3, 4]

    # 测试去重保持无序性
    def test_deduplicate_unordered(self):
        data = [3, 2, 1, 2, 3]
        result = ListProcessor.deduplicate(data)
        assert set(result) == {1, 2, 3}

    # 测试空列表去重
    def test_deduplicate_empty(self):
        assert ListProcessor.deduplicate([]) == []

    # 测试范围切片 - 正常情况
    def test_range_slicing(self):
        data = [0, 1, 2, 3, 4, 5]
        result = ListProcessor.range(data, 2, 4)
        assert result == [2, 3]

    # 测试范围切片 - 负偏移
    def test_range_negative_offset(self):
        data = [0, 1, 2, 3, 4, 5]
        result = ListProcessor.range(data, 1, -1)
        assert result == [1, 2, 3, 4]

    # 测试范围切片 - 超过边界
    def test_range_out_of_bounds(self):
        data = [1, 2, 3]
        assert ListProcessor.range(data, 0, 10) == [1, 2, 3]
        assert ListProcessor.range(data, 5, 10) == []
        assert ListProcessor.range(data, -10, 2) == [1, 2]

    # 测试范围切片 - 默认参数
    def test_range_defaults(self):
        data = [1, 2, 3, 4, 5]
        assert ListProcessor.range(data) == [1, 2, 3, 4, 5]  # 默认 offset=-1 相当于 [0:-1]
        assert ListProcessor.range(data, 2) == [3, 4, 5]  # [2:-1]
        assert ListProcessor.range(data, 0, None) == [1, 2, 3, 4, 5]  # 处理None为无限制


class TestDictProcessor:
    # 测试重命名键
    def test_rename_keys(self):
        data = {"old_name": "John", "age": 30}
        key_map = {"old_name": "name"}
        result = DictProcessor.rename_keys(data, key_map)
        assert result == {"name": "John", "age": 30}

    # 测试重命名多个键
    def test_rename_multiple_keys(self):
        data = {"a": 1, "b": 2, "c": 3}
        key_map = {"a": "alpha", "b": "beta"}
        result = DictProcessor.rename_keys(data, key_map)
        assert result == {"alpha": 1, "beta": 2, "c": 3}

    # 测试重命名不存在的键
    def test_rename_nonexistent_key(self):
        data = {"name": "Alice"}
        key_map = {"age": "years"}  # 字典中不存在的键
        result = DictProcessor.rename_keys(data, key_map)
        assert result == {"name": "Alice"}

    # 测试空映射
    def test_rename_no_mapping(self):
        data = {"key": "value"}
        assert DictProcessor.rename_keys(data, None) == data
        assert DictProcessor.rename_keys(data, {}) == data

    # 测试过滤键
    def test_filter_keys(self):
        data = {"name": "Bob", "age": 25, "email": "bob@example.com"}
        keys = ["name", "email"]
        result = DictProcessor.filter_keys(data, keys)
        assert result == {"name": "Bob", "email": "bob@example.com"}

    # 测试过滤部分不存在的键
    def test_filter_nonexistent_keys(self):
        data = {"id": 123, "value": 456}
        keys = ["id", "missing_key"]
        result = DictProcessor.filter_keys(data, keys)
        assert result == {"id": 123}

    # 测试空过滤列表
    def test_filter_no_keys(self):
        data = {"a": 1, "b": 2}
        assert DictProcessor.filter_keys(data, None) == data
        assert DictProcessor.filter_keys(data, []) == data

    # 测试删除键
    def test_delete_keys(self):
        data = {"first": 1, "second": 2, "third": 3}
        keys = ["second"]
        result = DictProcessor.delete_keys(data, keys)
        assert result == {"first": 1, "third": 3}

    # 测试删除多个键
    def test_delete_multiple_keys(self):
        data = {"a": 1, "b": 2, "c": 3, "d": 4}
        keys = ["a", "c"]
        result = DictProcessor.delete_keys(data, keys)
        assert result == {"b": 2, "d": 4}

    # 测试删除不存在的键
    def test_delete_nonexistent_keys(self):
        data = {"key": "value"}
        keys = ["nonexistent"]
        result = DictProcessor.delete_keys(data, keys)
        assert result == {"key": "value"}

    # 测试空删除列表
    def test_delete_no_keys(self):
        data = {"a": 1, "b": 2}
        assert DictProcessor.delete_keys(data, None) == data
        assert DictProcessor.delete_keys(data, []) == data

    # 测试嵌套字典操作
    def test_nested_dicts(self):
        # 处理器不处理嵌套字典，但测试是否只操作顶层键
        data = {"top": "level", "nested": {"inner": "value", "to_delete": "data"}}
        # 重命名
        renamed = DictProcessor.rename_keys(data, {"top": "top_level"})
        assert "top_level" in renamed
        assert "top" not in renamed

        # 过滤
        filtered = DictProcessor.filter_keys(data, ["nested"])
        assert filtered == {"nested": {"inner": "value", "to_delete": "data"}}

        # 删除
        deleted = DictProcessor.delete_keys(data, ["nested"])
        assert deleted == {"top": "level"}


# 测试数据准备
@pytest.fixture
def sample_df():
    """基础测试数据，包含重复的键列 (A,B) 和多列有效数据"""
    data = [
        {"A": "a1", "B": "b1", "C": "c1", "D": np.nan, "E": 10},
        {"A": "a1", "B": "b1", "C": np.nan, "D": "D1", "E": 20},
        {"A": "a2", "B": "b2", "C": "c2", "D": "D2", "E": 30},  # 无重复的行
    ]
    return pd.DataFrame(data)


@pytest.fixture
def df_multiple_nonnull():
    """同一列在组内有多个非空值，用于测试 first/last 区别"""
    data = [
        {"A": "a1", "B": "b1", "C": "c1", "D": "D1", "E": 1},
        {"A": "a1", "B": "b1", "C": "c2", "D": "D2", "E": 2},
        {"A": "a1", "B": "b1", "C": "c3", "D": np.nan, "E": 3},
    ]
    return pd.DataFrame(data)


@pytest.fixture
def df_all_nan():
    """某列全为 NaN 的情况"""
    data = [
        {"A": "a1", "B": "b1", "C": np.nan, "D": "D1"},
        {"A": "a1", "B": "b1", "C": np.nan, "D": np.nan},
    ]
    return pd.DataFrame(data)


class TestDataFrameProcessor:
    # 测试基本功能：单键列，取第一个非空值
    def test_single_key_first_non_null(self, sample_df):
        result = DataFrameProcessor.deduplicate(sample_df, key_columns="A")
        # 期望：按A分组，A列唯一，其他列取第一个非空值（按行顺序）
        expected_data = [
            {"A": "a1", "B": "b1", "C": "c1", "D": "D1", "E": 10},
            {"A": "a2", "B": "b2", "C": "c2", "D": "D2", "E": 30},
        ]
        expected = pd.DataFrame(expected_data)
        pd.testing.assert_frame_equal(result, expected)

    # 测试多键列，取第一个非空值
    def test_multi_key_first_non_null(self, sample_df):
        result = DataFrameProcessor.deduplicate(sample_df, key_columns=["A", "B"])
        # 期望：按A,B分组，合并非空值，C取c1，D取D1，E取10
        expected_data = [
            {"A": "a1", "B": "b1", "C": "c1", "D": "D1", "E": 10},
            {"A": "a2", "B": "b2", "C": "c2", "D": "D2", "E": 30},
        ]
        expected = pd.DataFrame(expected_data)
        pd.testing.assert_frame_equal(result, expected)

    # 测试取最后一个非空值
    def test_last_non_null(self, df_multiple_nonnull):
        result = DataFrameProcessor.deduplicate(
            df_multiple_nonnull, key_columns=["A", "B"], agg_methods={"all": SeriesProcessor.last_non_null}
        )
        # 期望：C取c3（最后一个非空），D取D2（最后一个非空），E取3（最后一个非空）
        expected_data = [
            {"A": "a1", "B": "b1", "C": "c3", "D": "D2", "E": 3},
        ]
        expected = pd.DataFrame(expected_data)
        pd.testing.assert_frame_equal(result, expected)


if __name__ == "__main__":
    pytest.main()
