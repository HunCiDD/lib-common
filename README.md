# lib-common
公共基础库

基础模块
base
* types.py 类型定义
* interfaces.py 接口定义

连接模块
connect

数据模块
data
设计模式
designs
日志模块
logger
安全模块
security

文件模块
files.py

模型模块
schemas.py

配置模块
configs.py


```
lib_common/
|── constants.py 常量模块
|── mixins.py 混合类定义模块
|── types.py 类型定义模块
|── files.py 文件目录模块
├── design/ 设计模式模块
│   ├── factory.py 工厂模式
│   └── singleton.py 单例模式
├── data/ 数据模块
│   ├── converter.py 数据转换模块
│   ├── encoder.py 数据编码模块
│   ├── generator.py 数据生成模块
│   ├── processor.py 数据处理模块
│   └── validater.py 数据校验模块
├── security/ 安全模块
│   ├── schemas.py 安全相关模型类
│   ├── cryptor.py 加密模块
│   └── manager.py 加密管理器
├── logger/ 日志模块
│   ├── schemas.py 日志相关模型类
│   ├── filter.py 日志过滤器
│   ├── patcher.py 日志
│   ├── logger.py 日志器
│   └── manager.py 日志管理器
├── connect/ 连接模块
│   ├── base/
│   │   ├── schemas.py 连接相关模型
│   │   ├── interface.py 连接相关接口定义
│   │   ├── core.py 连接相关模型
│   │   ├── factory.py 连接相关工厂
│   │   ├── pool.py 连接池
│   │   ├── caller.py 连接请求
│   │   └── manager.py 连接管理
│   ├── database/ 数据库连接
│   │   ├── schemas.py 数据库连接相关模型
│   │   ├── mixins.py 数据库连接相关混合类
│   │   ├── types.py 数据库连接类型定义
│   │   ├── core.py 类型定义
│   │   ├── pool.py 连接池
│   │   └── manager.py 连接管理
│   ├── http/ Http连接
│   │   ├── schemas.py 数据库连接相关模型
│   │   ├── core.py 类型定义
│   │   ├── pool.py 连接池
│   │   └── manager.py 连接管理
├── api/ 外部接口
├── app/ 应用模块
│   ├── application.py 应用模块
│   ├── decorators.py 应用装饰器
│   ├── dependencies.py 应用依赖注入
│   ├── middlewares.py 应用中间件
│   ├── repositories.py 应用存储层
│   ├── services.py 应用服务层
│   └── schemas.py 应用相关模型
|── settings.py 配置对象
└── configs.py 全局配置模块
```


```
app_xxx/
│── constants.py 常量模块
│── application.py 应用模块
│── dependencies.py 应用依赖注入
│── schemas.py 应用相关模型
│── models.py 应用模型
│── repositories.py 应用存储层
│── service.py 应用服务层
│── routers.py 路由模块
│── configs.py 全局配置模块
└── main..py 入口
```
