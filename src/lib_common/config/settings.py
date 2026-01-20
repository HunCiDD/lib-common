import os
from functools import lru_cache

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource, YamlConfigSettingsSource

from .schemas import AppConfig, DBConfig


def get_model_config() -> SettingsConfigDict:
    """
    从环境变量加载运行环境名，根路径。动态指定配置文件
    """
    environment = os.getenv("environment", "local")
    root = os.getenv("root", os.path.dirname(os.path.dirname(__file__)))

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
        env_prefix="APP_",
        yaml_file=yaml_file,
        yaml_file_encoding='utf-8',
        secrets_dir=secrets_dir,
        case_sensitive=False,
        extra='ignore',
    )


class Settings(BaseSettings):
    """应用配置"""

    # 使用动态配置
    model_config = get_model_config()

    app: AppConfig = Field(default_factory=AppConfig)
    db: DBConfig = DBConfig()

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),  # YAML 配置优先
            file_secret_settings
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()