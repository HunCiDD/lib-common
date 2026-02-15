# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 语言规范
- 所有对话和文档都请使用简体中文。
- 代码注释也请使用中文。

## 项目概述
`lib-common` 是一个 Python 通用库，提供数据处理、连接管理、日志、安全等基础功能。项目使用现代 Python 工具链（uv、ruff、pytest）构建，采用模块化架构设计。

## 常用开发命令

### 环境管理
```bash
# 使用 uv 创建虚拟环境
uv venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
uv sync

# 安装开发依赖
uv sync --group dev
```

### 代码质量
```bash
# 代码检查和自动修复
uvx ruff check --fix

# 代码格式化
uvx ruff format

# 运行特定检查
uvx ruff check --select F,E,W,UP
```

### 测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/lib_common/data/

# 运行单个测试
pytest tests/lib_common/data/test_converter.py::test_specific_function

# 带详细输出
pytest -v

# 带覆盖率报告
pytest --cov=src/lib_common
```

### 构建和发布
```bash
# 构建包
uv build

# 发布到 PyPI（需要配置）
uv publish
```

## 项目架构

### 核心模块结构
```
src/lib_common/
├── app/                    # 应用模块（FastAPI 风格）
│   ├── application.py     # 应用核心
│   ├── services.py        # 服务层
│   ├── repositories.py    # 存储层
│   ├── schemas.py         # Pydantic 模型
│   ├── routers.py         # 路由定义
│   ├── dependencies.py    # 依赖注入
│   ├── middlewares.py     # 中间件
│   └── exceptions.py      # 异常处理
├── connect/               # 连接管理模块
│   ├── core/             # 连接核心接口
│   ├── database/         # 数据库连接（SQLAlchemy）
│   ├── http/             # HTTP 客户端
│   ├── redis/            # Redis 连接
│   └── ssh/              # SSH 连接
├── data/                  # 数据处理模块
│   ├── components/       # 数据组件
│   ├── core/             # 数据核心
│   ├── pipeline/         # 数据管道
│   └── utils/            # 数据工具（转换、编码、生成等）
├── cryptor/              # 加密模块
│   ├── base.py           # 加密基类
│   └── manager.py        # 加密管理器
├── logger/               # 日志模块
│   ├── base.py           # 日志基类
│   ├── manager.py        # 日志管理器
│   ├── filters.py        # 日志过滤器
│   ├── patchers.py       # 日志补丁
│   └── schemas.py        # 日志模型
├── designs/              # 设计模式
│   ├── factory.py        # 工厂模式
│   └── singleton.py      # 单例模式
└── utils/                # 通用工具
    └── files.py          # 文件操作工具
```

### 配置系统
- **主配置**: `configs/config.yaml` - YAML 格式的应用配置
- **密钥管理**: `secrets/` 目录 - 存储加密密钥和敏感信息
- **环境变量**: 通过 `pydantic-settings` 管理

### 依赖关系
- **Web 框架**: FastAPI
- **数据验证**: Pydantic
- **数据库 ORM**: SQLAlchemy
- **数据分析**: Pandas
- **日志**: Loguru
- **加密**: PyCryptodome
- **配置解析**: PyYAML

## 开发规范

### 代码风格
- **行长度**: 120 字符（ruff 配置）
- **引号**: 双引号（ruff 配置）
- **导入排序**: 使用 ruff 自动排序
- **类型注解**: 鼓励使用 Python 类型注解

### 测试规范
- **测试目录**: `tests/lib_common/` 对应源码结构
- **测试配置**: `tests/pytest.ini` 和 `tests/conftest.py`
- **异步测试**: 支持 asyncio，默认 fixture 作用域为 function

### 安全规范
- **密钥存储**: 所有密钥存储在 `secrets/` 目录
- **加密配置**: 通过 `configs/config.yaml` 管理加密器配置
- **敏感数据**: 使用 Pydantic 的 `SecretStr` 类型处理

## 重要文件说明

### `pyproject.toml`
- 项目元数据和依赖管理
- 使用 `uv_build` 作为构建后端
- 配置 ruff 代码格式化和检查规则
- 开发依赖组包含 pytest

### `configs/config.yaml`
- 完整的应用配置，包括：
  - 应用设置（名称、版本、主机、端口）
  - 日志配置（多日志器、格式、轮转策略）
  - 加密器配置
  - 数据库连接配置（PostgreSQL）
  - Redis 配置

### `tests/conftest.py`
- 测试环境配置和共享 fixture
- 测试数据库连接设置
- 测试加密器初始化

## 模块设计模式

### 1. 配置驱动设计
- 所有模块通过配置初始化
- 支持运行时配置更新
- 配置验证使用 Pydantic

### 2. 依赖注入
- 使用 FastAPI 风格的依赖注入
- 支持异步依赖
- 依赖生命周期管理

### 3. 连接池管理
- 数据库、HTTP、Redis 连接都支持连接池
- 自动重连和健康检查
- 连接泄漏检测

### 4. 插件式架构
- 加密器、日志处理器等支持插件扩展
- 通过配置文件注册插件
- 统一的接口规范

## 注意事项

1. **Python 版本**: 要求 Python 3.12+（通过 `.python-version` 指定）
2. **虚拟环境**: 使用 uv 管理，虚拟环境目录为 `.venv/`
3. **密钥安全**: `secrets/` 目录应添加到 `.gitignore`
4. **配置覆盖**: 环境变量可以覆盖 `config.yaml` 中的配置
5. **测试数据**: 测试使用临时数据库，不会影响生产数据