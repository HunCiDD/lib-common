import pytest
from unittest.mock import Mock, patch, MagicMock
from lib_common.connect.core.manager import ConnectionPoolManager
from lib_common.connect.core.factory import ConnectionPoolFactory
from lib_common.connect.core.schemas import Infra


class MockConnectionPool:
    """模拟连接池"""
    def get_connection(self):
        return "mock_connection"

    def release_connection(self, conn):
        pass

    def connection(self):
        class Context:
            def __enter__(self):
                return "mock_connection"
            def __exit__(self, *args):
                pass
        return Context()


class TestConnectionPoolManager:
    """测试连接池管理器"""

    def test_manager_init(self):
        """测试管理器初始化"""
        mock_settings = Mock()
        mock_settings.databases = {}
        manager = ConnectionPoolManager(mock_settings)
        assert manager._settings == mock_settings
        assert manager._pools == {}

    def test_add_pool_success(self):
        """测试成功添加连接池"""
        mock_settings = Mock()
        mock_settings.databases = {}
        manager = ConnectionPoolManager(mock_settings)

        # 模拟工厂创建连接池
        mock_pool = MockConnectionPool()
        with patch.object(ConnectionPoolFactory, 'create', return_value=mock_pool) as mock_create:
            settings = {
                "type": "MockPool",
                "infra": {"host": "localhost", "port": 5432},
                "settings": {"max_connections": 10}
            }
            manager.add_pool("test_pool", settings)

            # 验证工厂调用
            mock_create.assert_called_once_with("MockPool", Infra(**settings["infra"]), settings["settings"])
            # 验证池已添加
            assert manager.get_pool("test_pool") == mock_pool

    def test_add_pool_missing_type(self):
        """测试缺少类型配置"""
        mock_settings = Mock()
        mock_settings.databases = {}
        manager = ConnectionPoolManager(mock_settings)

        settings = {
            "infra": {"host": "localhost"},
            "settings": {}
        }
        with pytest.raises(ValueError):
            manager.add_pool("test_pool", settings)

    def test_add_pool_missing_infra(self):
        """测试缺少基础设施配置（使用空字典）"""
        mock_settings = Mock()
        mock_settings.databases = {}
        manager = ConnectionPoolManager(mock_settings)

        # 模拟工厂创建连接池返回 None
        with patch.object(ConnectionPoolFactory, 'create', return_value=None) as mock_create:
            settings = {
                "type": "MockPool",
                "settings": {}
            }
            # 不会引发异常
            manager.add_pool("test_pool", settings)
            # 验证工厂被调用，Infra 使用默认值
            mock_create.assert_called_once()
            # 获取调用参数
            args = mock_create.call_args
            # 第二个参数是 Infra 实例
            infra = args[0][1]
            assert isinstance(infra, Infra)
            assert infra.host == "127.0.0.1"  # 默认值
            assert infra.port == 22  # 默认值
            # 注意：如果工厂返回 None，池不会被添加
            # 但如果工厂返回了实例（例如有注册的类型），池可能被添加
            # 我们不检查 get_pool 的结果，因为行为依赖于工厂注册

    def test_get_pool_not_exist(self):
        """测试获取不存在的连接池"""
        mock_settings = Mock()
        mock_settings.databases = {}
        manager = ConnectionPoolManager(mock_settings)
        assert manager.get_pool("nonexistent") is None

    def test_del_pool(self):
        """测试删除连接池"""
        mock_settings = Mock()
        mock_settings.databases = {}
        manager = ConnectionPoolManager(mock_settings)

        # 添加模拟池
        mock_pool = MockConnectionPool()
        with patch.object(ConnectionPoolFactory, 'create', return_value=mock_pool):
            settings = {
                "type": "MockPool",
                "infra": {"host": "localhost"},
                "settings": {}
            }
            manager.add_pool("test_pool", settings)
            assert manager.get_pool("test_pool") == mock_pool

            # 删除池
            manager.del_pool("test_pool")
            assert manager.get_pool("test_pool") is None

    def test_del_pool_not_exist(self):
        """测试删除不存在的连接池"""
        mock_settings = Mock()
        mock_settings.databases = {}
        manager = ConnectionPoolManager(mock_settings)
        # 不应引发异常
        manager.del_pool("nonexistent")


class TestConnectionPoolFactory:
    """测试连接池工厂"""

    def test_factory_registration(self):
        """测试工厂注册"""
        # 工厂初始应为空，因为具体实现在其他模块注册
        assert ConnectionPoolFactory._map == {}

    def test_factory_create_nonexistent(self):
        """测试创建不存在的连接池类型"""
        infra = Infra(host="localhost", port=5432)
        pool = ConnectionPoolFactory.create("NonexistentPool", infra, {})
        assert pool is None


class TestInfraSchema:
    """测试基础设施模式"""

    def test_infra_creation(self):
        """测试创建 Infra 对象"""
        infra = Infra(
            host="localhost",
            port=5432,
            username="user",
            password="pass"
        )
        assert infra.host == "localhost"
        assert infra.port == 5432
        assert infra.username == "user"
        assert infra.password.get_secret_value() == "pass"
        # database 和 extra_params 不是 Infra 的字段，跳过测试

    def test_infra_minimal(self):
        """测试最小化 Infra 对象"""
        infra = Infra(host="localhost")
        assert infra.host == "localhost"
        assert infra.port == 22  # 默认值
        assert infra.username is None
        assert infra.password is None
        # database 和 extra_params 不是 Infra 的字段，跳过测试


if __name__ == "__main__":
    pytest.main()