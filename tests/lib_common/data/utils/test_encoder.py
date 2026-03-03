# test_json_encoder.py
import pytest
import json
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
import numpy as np
import pandas as pd

# 导入被测试的编码器
from lib_common.data.utils.encoder import JsonEncoder  # 替换 your_module 为实际模块名


class TestJsonEncoder:
    @pytest.fixture
    def encoder(self):
        return JsonEncoder()

    # 测试 datetime 类型
    def test_datetime(self, encoder):
        dt = datetime(2023, 1, 1, 12, 30, 45)
        result = encoder.default(dt)
        assert result == "2023-01-01 12:30:45"

    # 测试 Decimal 类型
    def test_decimal(self, encoder):
        dec = Decimal("123.456")
        result = encoder.default(dec)
        assert result == 123.456

    # 测试 UUID 类型
    def test_uuid(self, encoder):
        uid = uuid4()
        result = encoder.default(uid)
        assert result == str(uid)

    # 测试 DataFrame 类型
    def test_dataframe(self, encoder):
        df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
        result = encoder.default(df)
        expected = {"A": {0: 1, 1: 2}, "B": {0: "x", 1: "y"}}
        assert result == expected

    # 测试 bytes 类型
    def test_bytes(self, encoder):
        data = b"hello world"
        result = encoder.default(data)
        assert result == "hello world"

    # 测试 numpy int64 类型
    def test_numpy_int64(self, encoder):
        num = np.int64(100)
        result = encoder.default(num)
        assert result == 100.0  # 应转为 float

    # 测试其他 numpy 数值类型
    def test_numpy_number(self, encoder):
        num = np.int32(200)
        result = encoder.default(num)
        assert result == 200  # 应转为 int

    # 测试其他类型（使用 str 转换）
    def test_other_type(self, encoder):
        class CustomObj:
            def __str__(self):
                return "custom object"

        obj = CustomObj()
        result = encoder.default(obj)
        assert result == "custom object"

    # 测试实际 JSON 序列化过程
    def test_full_encoding(self, encoder):
        data = {
            "time": datetime(2023, 1, 1),
            "id": uuid4(),
            "value": Decimal("99.99"),
            "df": pd.DataFrame({"col": [1, 2]}),
            "bytes": b"data",
            "numpy_int": np.int64(10),
            "numpy_float": np.float32(5.5),
        }

        # 应成功序列化而不报错
        json_str = json.dumps(data, cls=JsonEncoder)
        parsed = json.loads(json_str)

        assert isinstance(parsed["time"], str)
        assert isinstance(parsed["id"], str)
        assert isinstance(parsed["value"], float)
        assert isinstance(parsed["df"], dict)
        assert parsed["bytes"] == "data"
        assert parsed["numpy_int"] == 10.0
        assert parsed["numpy_float"] == 5  # 注意：float32 被转为 int


if __name__ == "__main__":
    pytest.main()
