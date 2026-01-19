import os

from pathlib import Path

from pydantic_settings import SettingsConfigDict


def get_model_config() -> SettingsConfigDict:
    """
    从环境变量加载运行环境名，根路径。动态指定配置文件
    """
    environment = os.getenv("environment", "local")
    root = os.getenv("root", os.path.dirname(os.path.dirname(__file__)))

    # 查找配置文件
    yaml_files = []
    config_dir = Path(root) / "configs"

    # 基础配置文件
    base_config = config_dir / "config.yaml"
    if base_config.exists():
        yaml_files.append(str(base_config))

    # 环境特定配置文件
    env_config = config_dir / f"config.{environment}.yaml"
    if env_config.exists():
        yaml_files.append(str(env_config))

    # secrets 目录
    secrets_dir = Path(root) / "secrets"
    secrets_path = str(secrets_dir) if secrets_dir.exists() else None

    return SettingsConfigDict(
        yaml_files=yaml_files if yaml_files else None,
        yaml_file_encoding='utf-8',
        secrets_dir=secrets_path,
        case_sensitive=False,
        extra='ignore',
    )


class Settings(BaseSettings):
    """应用配置"""

    # 使用动态配置
    model_config = get_model_config()

    app: AppConfig = Field(default_factory=AppConfig)

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
            YamlConfigSettingsSource(settings_cls),  # YAML 配置优先
            env_settings,
            dotenv_settings,
            init_settings,
            file_secret_settings
        )