# 日志级别
LOG_LEVELS = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]


class RegexPatterns:
    Num = r"^[0-9]+$"  # 纯数字
    Str = r"^[a-zA-Z]+$"  # 纯字母
    PhoneNumber = r"^1[3-9]\d{9}$"  # 手机号（修正第二位字符集和格式）
    Username = r"^[a-zA-Z0-9_]+$"
    # 密码复杂度正则（至少包含大小写字母、数字和特殊字符）
    Password = (
        r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,128}$"  # 密码复杂度（添加多条件校验）
    )
