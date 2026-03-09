import os
import pytest
from pydantic import Field, SecretStr
from typing import Dict
from pydantic_settings import PydanticBaseSettingsSource

from lib_common.settings import BaseSettings, Settings, get_settings
from lib_common.cryptor.schemas import CryptorConfigsM, CryptorRootConfigsM
from lib_common.logger.schemas import LoggerConfigsM
from lib_common.connect.database.schemas import DBConfigsM
from lib_common.connect.redis.schemas import RedisConfigsM
from lib_common.app.schemas import AppConfigs


class TestBaseSettings(BaseSettings):
    """
    测试专用的基类，提供有效的默认配置值
    避免 cryptors 等必填字段验证错误
    """

    # 覆盖 cryptors 字段，提供有效的默认值
    cryptors: CryptorConfigsM = Field(
        default_factory=lambda: CryptorConfigsM(
            root=CryptorRootConfigsM(
                material=SecretStr("test_material"), salt="test_salt", secret=SecretStr("test_secret")
            ),
            work={},
        )
    )

    # 覆盖 app 字段，提供有效的默认值
    app: AppConfigs = Field(
        default_factory=lambda: AppConfigs(
            secret=SecretStr("test_secret_key"),
            algorithm="HS256",
            access_token_expire=15,
            refresh_token_expire=3,
            environment="test",
            root=os.path.dirname(os.path.dirname(__file__)),
            debug=False,
            name="test_app",
            version="1.0.0",
            host="127.0.0.1",
            port=8000,
            tz="Asia/Shanghai",
        )
    )

    # 其他字段使用空默认值
    loggers: Dict[str, LoggerConfigsM] = Field(default_factory=dict)
    databases: Dict[str, DBConfigsM] = Field(default_factory=dict)
    redis: Dict[str, RedisConfigsM] = Field(default_factory=dict)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # 在测试中只使用构造函数参数，禁用其他配置源
        return (init_settings,)


class TestSettingsExtendable:
    """测试配置系统的可继承功能"""

    def test_base_settings_can_be_extended(self):
        """测试 BaseSettings 可以被继承并添加新字段"""

        class ExtendedSettings(TestBaseSettings):
            custom_field: str = Field(default="default_value")
            extra_config: Dict[str, int] = Field(default_factory=dict)

        # 实例化
        settings = ExtendedSettings()

        # 验证新字段存在
        assert settings.custom_field == "default_value"
        assert settings.extra_config == {}

        # 验证继承的字段存在
        assert hasattr(settings, "loggers")
        assert hasattr(settings, "cryptors")
        assert hasattr(settings, "databases")
        assert hasattr(settings, "redis")
        assert hasattr(settings, "app")

    def test_get_settings_with_subclass(self):
        """测试 get_settings 函数支持子类参数"""

        class ExtendedSettings(TestBaseSettings):
            custom_field: str = Field(default="custom_value")

        # 使用 get_settings 获取子类实例
        settings1 = get_settings(ExtendedSettings)
        settings2 = get_settings(ExtendedSettings)

        # 验证单例缓存
        assert settings1 is settings2
        assert settings1.custom_field == "custom_value"
        assert isinstance(settings1, ExtendedSettings)

    def test_backward_compatibility(self):
        """测试向后兼容性：默认 get_settings() 返回 Settings 实例"""
        settings = get_settings()  # 无参数调用

        assert isinstance(settings, Settings)
        assert not isinstance(settings, TestBaseSettings)  # Settings 是 BaseSettings 子类
        assert hasattr(settings, "loggers")
        assert hasattr(settings, "cryptors")
        assert hasattr(settings, "databases")
        assert hasattr(settings, "redis")
        assert hasattr(settings, "app")
        # 验证字段有默认值
        assert settings.cryptors.root is not None
        assert settings.app.secret is not None

    def test_config_loading_inheritance(self):
        """测试配置加载逻辑被继承"""

        # 使用 BaseSettings 而不是 TestBaseSettings，以测试原始配置加载逻辑
        class ExtendedSettings(BaseSettings):
            custom_field: str = Field(default="default")

        # 测试环境变量加载
        os.environ["CUSTOM_FIELD"] = "from_env"
        try:
            settings = ExtendedSettings()
            assert settings.custom_field == "from_env"
        finally:
            # 清理环境变量
            del os.environ["CUSTOM_FIELD"]

    def test_field_validation_inheritance(self):
        """测试字段验证器在继承链中工作"""

        class ExtendedSettings(TestBaseSettings):
            api_key: SecretStr = Field(default=SecretStr("default_key"))

        settings = ExtendedSettings()
        assert settings.api_key.get_secret_value() == "default_key"

        # 测试 SecretStr 类型
        assert isinstance(settings.api_key, SecretStr)

    def test_settings_customise_sources_inheritance(self):
        """测试 settings_customise_sources 方法被继承"""
        # 验证 BaseSettings 有 settings_customise_sources 方法
        assert hasattr(BaseSettings, "settings_customise_sources")
        assert callable(BaseSettings.settings_customise_sources)

        # 验证 TestBaseSettings 覆盖了该方法
        assert hasattr(TestBaseSettings, "settings_customise_sources")
        assert callable(TestBaseSettings.settings_customise_sources)

        # 验证子类继承父类的方法
        class ExtendedSettings(TestBaseSettings):
            custom_field: str = Field(default="default")

        assert hasattr(ExtendedSettings, "settings_customise_sources")
        assert callable(ExtendedSettings.settings_customise_sources)

        # 验证另一个子类继承 BaseSettings 的原始方法
        class AnotherSettings(BaseSettings):
            custom_field: str = Field(default="default")

        assert hasattr(AnotherSettings, "settings_customise_sources")
        assert callable(AnotherSettings.settings_customise_sources)

    def test_model_config_inheritance(self):
        """测试 model_config 被继承"""

        class ExtendedSettings(TestBaseSettings):
            custom_field: str = Field(default="default")

        # 验证 model_config 存在
        assert hasattr(ExtendedSettings, "model_config")

        # 验证配置包含预期的键
        config = ExtendedSettings.model_config
        assert "env_file" in config
        assert "yaml_file" in config
        assert "secrets_dir" in config

    def test_multiple_inheritance_levels(self):
        """测试多级继承"""

        class IntermediateSettings(TestBaseSettings):
            intermediate_field: str = Field(default="intermediate")

        class FinalSettings(IntermediateSettings):
            final_field: str = Field(default="final")

        settings = FinalSettings()
        assert settings.intermediate_field == "intermediate"
        assert settings.final_field == "final"
        assert hasattr(settings, "loggers")  # 继承自 BaseSettings

    def test_field_name_conflict(self):
        """测试字段名冲突处理（子类字段覆盖父类字段）"""

        class ConflictingSettings(TestBaseSettings):
            # 尝试添加与父类同名的字段（应该覆盖）
            loggers: Dict[str, str] = Field(default_factory=dict)  # 类型不同

        settings = ConflictingSettings()
        # 注意：Pydantic 会检测到字段冲突，但子类字段会覆盖父类字段
        # 这里我们验证字段存在
        assert hasattr(settings, "loggers")
        # 类型应该是子类定义的类型
        # 注意：这可能会导致类型问题，但这是用户的责任

    def test_instance_equality(self):
        """测试不同子类的实例不同"""

        class SettingsA(TestBaseSettings):
            field_a: str = Field(default="a")

        class SettingsB(TestBaseSettings):
            field_b: str = Field(default="b")

        instance_a1 = get_settings(SettingsA)
        instance_a2 = get_settings(SettingsA)
        instance_b = get_settings(SettingsB)

        assert instance_a1 is instance_a2  # 相同类，单例
        assert instance_a1 is not instance_b  # 不同类，不同实例
        assert instance_a1.field_a == "a"
        assert instance_b.field_b == "b"


class TestSettingsWithRealConfig:
    """测试使用真实配置文件的场景"""

    def test_settings_with_minimal_config(self):
        """测试使用最小化配置（避免验证错误）"""

        # 创建临时配置类，覆盖 cryptors 等必填字段
        class MinimalSettings(BaseSettings):
            # 提供必要的字段以避免验证错误
            cryptors: Dict = Field(default_factory=dict)
            loggers: Dict = Field(default_factory=dict)
            databases: Dict = Field(default_factory=dict)
            redis: Dict = Field(default_factory=dict)
            app: Dict = Field(default_factory=dict)

            custom_field: str = Field(default="custom")

        # 应该可以实例化而不报错
        settings = MinimalSettings()
        assert settings.custom_field == "custom"
        assert settings.cryptors == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
