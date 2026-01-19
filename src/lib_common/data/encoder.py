# 编码器
__all__ = ["JsonEncoder"]

import json
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from numpy import int64, issubdtype, number
from pandas import DataFrame


class JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            result = str(o)
        elif isinstance(o, Decimal):
            result = float(o)
        elif isinstance(o, UUID):
            result = str(o)
        elif isinstance(o, DataFrame):
            result = o.to_dict()
        elif isinstance(o, bytes):
            result = o.decode(encoding="utf-8")
        elif issubdtype(type(o), number):
            return float(o) if issubdtype(type(o), int64) else int(o)
        else:
            result = str(o)
        return result
