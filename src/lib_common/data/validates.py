# 校验模块
import re
from ipaddress import ip_address
from pathlib import Path
from typing import Any


def validate_bool(value: str | bool | int) -> bool:
    """校验是否可转换为bool
    :param value:
    :return: bool类型
    """
    if isinstance(value, str):
        value = value.lower().strip()
        if value in ("true", "t", "yes", "y", "1"):
            return True
        elif value in ("false", "f", "no", "n", "0"):
            return False
        else:
            raise ValueError(f"Invalid type for boolean: {value}")
    elif value is None:
        return False
    elif isinstance(value, bool):
        return value
    elif isinstance(value, int):
        return bool(value)
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


def validate_upper(_str: Any) -> str:
    return str(_str).upper()


def validate_lower(_str: Any) -> str:
    return str(_str).lower()


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
    pattern = r"^(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))*\.[a-z]{2,}$"
    if re.match(pattern, domain, re.IGNORECASE):
        return domain.lower()
    raise ValueError(f"Invalid hostname: {domain}")


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


def validate_password(password: str) -> str:
    errors = []
    # 检查小写字母
    if not any(c.islower() for c in password):
        errors.append("Contains at least one lowercase letter")
    # 检查大写字母
    if not any(c.isupper() for c in password):
        errors.append("Contains at least one capital letter")
    # 检查数字
    if not any(c.isdigit() for c in password):
        errors.append("Contain at least one number")
    # 检查特殊字符
    special_chars = set("@$!%*?&")
    if not any(c in special_chars for c in password):
        errors.append(f"Contains at least one special character ({''.join(special_chars)})")
    if errors:
        raise ValueError("Password does not meet the complexity requirements: " + ", ".join(errors))
    return password
