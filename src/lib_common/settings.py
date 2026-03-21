import os
from typing import Dict, Type, TypeVar
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
    YamlConfigSettingsSource,
    NestedSecretsSettingsSource,
)

from .app.schemas import AppConfigsM
from .logger.schemas import LoggerConfigsM
from .cryptor.schemas import CryptorConfigsM
from .connect.database.schemas import DBConfigsM
from .connect.redis.schemas import RedisConfigsM
from .tasks.schemas import TasksConfigsM


def get_model_config() -> SettingsConfigDict:
    """
    从环境变量加载运行环境名，根路径。动态指定配置文件
    """
    environment = os.getenv("APP__ENVIRONMENT", "local")
    root = os.getenv("APP__ROOT", os.path.dirname(os.path.dirname(__file__)))

    env_paths = [
        Path(root) / "configs" / ".env",
        Path(root) / "configs" / f".env.{environment}",
    ]
    env_file = [p for p in env_paths if p.exists()]
    if not env_file:
        env_file = None

    yaml_paths = [
        Path(root) / "configs" / "config.yaml",
        Path(root) / "configs" / f"config.{environment}.yaml",
    ]
    yaml_file = [p for p in yaml_paths if p.exists()]
    if not yaml_file:
        yaml_file = None

    # secrets 目录
    secrets_path = Path(root) / "secrets"
    secrets_dir = secrets_path if secrets_path.exists() else None

    return SettingsConfigDict(
        env_file=env_file,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",  # 关键配置
        yaml_file=yaml_file,
        yaml_file_encoding="utf-8",
        secrets_dir=secrets_dir,
        secrets_nested_subdir=True,
        secrets_prefix="",
        case_sensitive=False,  # 忽略大小写
        extra="ignore",
    )


class Settings(BaseSettings):
    """可继承的配置基类，应用可以继承此类添加自定义字段"""

    # 使用动态配置
    model_config = get_model_config()

    app: AppConfigsM = Field(default_factory=AppConfigsM, description="App应用配置")
    loggers: Dict[str, LoggerConfigsM] = Field(default_factory=dict, description="日志配置")
    cryptors: CryptorConfigsM = Field(default_factory=CryptorConfigsM, description="加密配置")
    databases: Dict[str, DBConfigsM] = Field(default_factory=dict, description="数据库配置")
    redis: Dict[str, RedisConfigsM] = Field(default_factory=dict, description="Redis配置")
    tasks: TasksConfigsM | None = Field(default=None, description="Tasker配置")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # 自定义数据源优先级
        return (
            init_settings,  # 构造函数参数（最高优先级）
            env_settings,  # 环境变量
            dotenv_settings,  # .env 文件
            NestedSecretsSettingsSource(file_secret_settings),  # Secrets 文件
            YamlConfigSettingsSource(settings_cls),  # YAML 配置优先
        )


SettingType = TypeVar("SettingType", bound=Settings)


@lru_cache
def get_settings[SettingType: Settings](settings_cls: Type[SettingType] = Settings) -> SettingType:
    """
    获取配置单例实例
    Args:
        settings_cls: 配置类，默认为 Settings
    Returns:
        配置实例
    """
    return settings_cls()
