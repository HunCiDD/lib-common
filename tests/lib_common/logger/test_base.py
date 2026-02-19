import pytest
import tempfile
import os
from pathlib import Path
from lib_common.logger.base import ConsoleLogger, FileLogger, AppLogger, LoggerFactory


class TestConsoleLogger:
    """测试 ConsoleLogger"""

    def test_console_logger_init(self):
        """测试控制台日志器初始化"""
        config = {
            "level": "DEBUG",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            "colorize": False,
            "serialize": False,
            "backtrace": True,
            "enqueue": False,
            "diagnose": True,
        }
        logger = ConsoleLogger(name="test_console", configs=config)
        assert logger.name == "test_console"
        assert logger.sink_id != -1
        # 验证 logger 属性可访问
        assert logger.logger is not None
        logger.remove()
        assert logger.sink_id == -1


class TestFileLogger:
    """测试 FileLogger"""

    def test_file_logger_init(self, tmp_path):
        """测试文件日志器初始化"""
        log_file = tmp_path / "test.log"
        config = {
            "sink": str(log_file),
            "level": "INFO",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            "rotation": "10 MB",
            "retention": "1 days",
            "compression": "zip",
            "encoding": "utf-8",
            "sensitive_fields": "(password|token|key)",
            "sensitive_fields_replacement": "***",
            "max_length": 1000,
            "max_length_replacement": "...",
        }
        logger = FileLogger(name="test_file", configs=config)
        assert logger.name == "test_file"
        assert logger.sink_id != -1
        # 验证日志文件被创建
        logger.logger.info("测试日志消息")
        logger.remove()
        # 检查文件是否存在且包含内容
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "测试日志消息" in content

    def test_file_logger_without_sink(self):
        """测试文件日志器缺少 sink 配置"""
        config = {
            "level": "INFO",
        }
        with pytest.raises(Exception, match="sink is required"):
            FileLogger(name="test_no_sink", configs=config)


class TestAppLogger:
    """测试 AppLogger"""

    def test_app_logger_init(self, tmp_path):
        """测试应用日志器初始化"""
        log_file = tmp_path / "app.log"
        config = {
            "sink": str(log_file),
            "level": "DEBUG",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        }
        logger = AppLogger(name="test_app", configs=config)
        assert logger.name == "test_app"
        assert logger.sink_id != -1
        # 测试日志记录
        logger.logger.debug("调试信息")
        logger.remove()
        assert log_file.exists()


class TestLoggerFactory:
    """测试日志工厂"""

    def test_factory_registration(self):
        """测试工厂注册"""
        assert "ConsoleLogger" in LoggerFactory._map
        assert "FileLogger" in LoggerFactory._map
        assert "AppLogger" in LoggerFactory._map

    def test_factory_create(self):
        """测试工厂创建日志器"""
        config = {
            "level": "INFO",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            "colorize": False,
        }
        # 创建控制台日志器
        console_logger = LoggerFactory.create("ConsoleLogger", "test_factory", config)
        assert isinstance(console_logger, ConsoleLogger)
        console_logger.remove()

        # 测试无效类型（工厂返回 None）
        invalid_logger = LoggerFactory.create("InvalidLogger", "test", config)
        assert invalid_logger is None


if __name__ == "__main__":
    pytest.main()