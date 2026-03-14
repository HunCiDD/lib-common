# 校验模块
import re
from ipaddress import ip_address
from pathlib import Path

from .converter import IntConverter, StringConverter


def validate_bool(value: str | bool | int) -> bool:
    """校验是否可转换为bool
    :param value:
    :return: bool类型
    """
    if isinstance(value, bool):
        return value
    elif isinstance(value, int):
        return IntConverter.to_bool(value)
    elif isinstance(value, str):
        return StringConverter.to_bool(value)
    else:
        raise ValueError(f"Invalid type for boolean: {type(value)}")


def validate_int(number: str | int) -> int:
    """校验是否为整形
    :param number:
    :return: int
    """
    try:
        return int(number)
    except Exception as e:
        raise ValueError(f"Invalid integer: {number}") from e


def validate_ip(ip: str) -> str:
    """校验IP
    :param ip:
    :return: 原IP
    """
    try:
        _ip = ip_address(ip)
    except Exception as e:
        raise ValueError(f"Validate ip error: [{ip}]") from e
    return ip


def validate_domain(domain: str) -> str:
    if not domain:
        raise ValueError("Hostname cannot be empty")

    # 区分单标签和标准域名
    if '.' in domain:
        # 标准域名：必须包含至少一个点，且最后一个标签（顶级域）至少两个字母
        pattern = r"^(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))*\.[a-z]{2,}$"
        if not re.match(pattern, domain, re.IGNORECASE):
            raise ValueError(f"Invalid domain name: {domain}")
    else:
        # 单标签主机名：仅由字母、数字、连字符组成，不能以连字符开头或结尾，长度 1~63
        pattern = r"^(?!-)[a-z0-9-]{1,63}(?<!-)$"
        if not re.match(pattern, domain, re.IGNORECASE):
            raise ValueError(f"Invalid hostname: {domain}")

    return domain.lower()


def validate_host(host: str) -> str:
    """校验主机，支持IP、localhost、域名
    :param host:
    :return: 主机名
    """
    host = host.lower()
    if host == "localhost":
        return host
    try:
        return validate_ip(host)
    except Exception:
        pass

    try:
        return validate_domain(host)
    except Exception as e:
        raise ValueError(f"Invalid hostname: {host}") from e


def validate_port(port: str | int) -> int:
    """校验端口，端口范围是否为 0~65535
    :param port:
    :return:
    """
    port = validate_int(port)
    if 0 < port <= 65535:
        return port
    raise ValueError(f"Validate port error: [{port}] must in 0 ~ 65535")


def validate_path(path: str | Path, exist: bool = False) -> Path:
    """校验路径
    :param path:
    :param exist: 是否校验路径是否存在
    :return: 绝对路径
    """
    if isinstance(path, str):
        _path = Path(path)
    elif isinstance(path, Path):
        _path = path
    else:
        raise ValueError(f"Invalid type for path: {type(path)}")

    if exist and not _path.exists():
        raise ValueError(f"Path does not exist: [{_path}]")
    return _path.resolve()


def validate_contain_lower(value: str) -> str:
    """
    校验是否包含小写
    :param value:
    :return:
    """
    if not any(c.islower() for c in value):
        raise ValueError("Must contain lowercase letter")
    return value


def validate_contain_upper(value: str) -> str:
    """
    校验是否包含大写
    :param value:
    :return:
    """
    if not any(c.isupper() for c in value):
        raise ValueError("Must contain capital letter")
    return value


def validate_contain_digit(value: str) -> str:
    """
    校验是否包含数字
    :param value:
    :return:
    """
    if not any(c.isdigit() for c in value):
        raise ValueError("Must contain number")
    return value


def validate_contain_special(value: str, special_chars: str = "@$!%*?&") -> str:
    """
    校验是否包含特殊字符
    :param value:
    :param special_chars:
    :return:
    """
    if not any(c in special_chars for c in value):
        raise ValueError(f"Must contain special character ({special_chars})")
    return value


def validate_password(password: str) -> str:
    """
    校验密码是否合法，必须包含大写、小写、数字、特殊字符串
    :param password:
    :return:
    """
    errors = []
    for validate_func in [
        validate_contain_lower,
        validate_contain_upper,
        validate_contain_digit,
        validate_contain_special,
    ]:
        try:
            validate_func(password)
        except ValueError as e:
            errors.append(str(e))

    if errors:
        raise ValueError("Password does not meet the complexity requirements: " + ", ".join(errors))
    return password
