SQLALCHEMY_OPERATOR_MAP = {
    "__in": lambda col, val: col.in_(val),  # 值在列表中
    "__gt": lambda col, val: col > val,  # 值大于
    "__ge": lambda col, val: col >= val,  # 值大于等于
    "__lt": lambda col, val: col < val,  # 值小于
    "__le": lambda col, val: col <= val,  # 值小于等于
    "__ne": lambda col, val: col != val,  # 不等于
    "__eq": lambda col, val: col == val,
    "__like": lambda col, val: col.like(f"%{val}%"),  # 区分大小写
    "__ilike": lambda col, val: col.ilike(f"%{val}%"),  # 不区分大小写
    "__startswith": lambda col, val: col.startswith(val),  # 开头匹配
    "__endswith": lambda col, val: col.endswith(val),  # 结尾匹配
    "__isnull": lambda col, val: col.is_(None) if val else col.isnot(None),  # 空值检查
}
