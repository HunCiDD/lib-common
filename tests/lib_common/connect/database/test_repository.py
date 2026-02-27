import pytest
import pytest_asyncio
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from lib_common.connect.database.base import BaseModel
from lib_common.connect.database.repository import (
    BaseRepository,
    AsyncBaseRepository,
    set_model,
    build_filters,
    build_orders,
)


# 测试模型
class User(BaseModel):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    age = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())


class Product(BaseModel):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    price = Column(Integer, default=0)


# Fixtures
@pytest.fixture(scope="function")
def sync_engine():
    """同步 SQLite 内存引擎"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    BaseModel.metadata.create_all(engine)
    yield engine
    BaseModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def sync_session(sync_engine):
    """同步会话"""
    SessionLocal = sessionmaker(bind=sync_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """异步 SQLite 内存引擎"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine):
    """异步会话"""
    AsyncSessionLocal = async_sessionmaker(bind=async_engine, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        yield session


# 测试工具函数
class TestUtilityFunctions:
    """测试工具函数 set_model, build_filters, build_orders"""

    def test_set_model(self):
        """测试动态设置模型属性"""
        user = User(name="test", email="test@example.com", age=20)
        # 存在的字段
        updated = set_model(user, {"name": "updated", "age": 30})
        assert updated.name == "updated"
        assert updated.age == 30
        assert updated.email == "test@example.com"
        # 不存在的字段被忽略
        updated = set_model(user, {"nonexistent": "value"})
        assert not hasattr(updated, "nonexistent")

    def test_build_filters(self):
        """测试构建过滤条件"""
        # 等于操作
        conditions = build_filters(User, {"name": "Alice"})
        assert len(conditions) == 1
        # 操作符后缀
        conditions = build_filters(User, {"age__gt": 18})
        assert len(conditions) == 1
        conditions = build_filters(User, {"age__in": [18, 19, 20]})
        assert len(conditions) == 1
        conditions = build_filters(User, {"name__like": "Ali"})
        assert len(conditions) == 1
        # 无效字段被忽略
        conditions = build_filters(User, {"invalid_field": "value"})
        assert len(conditions) == 0
        # 混合条件
        conditions = build_filters(User, {"name": "Alice", "age__gt": 18})
        assert len(conditions) == 2

    def test_build_orders(self):
        """测试构建排序条件"""
        # 升序
        orders = build_orders(User, {"name": "asc"})
        assert len(orders) == 1
        # 降序
        orders = build_orders(User, {"name": "desc"})
        assert len(orders) == 1
        # 无效字段被忽略
        orders = build_orders(User, {"invalid_field": "desc"})
        assert len(orders) == 0


# 测试同步仓库
class TestBaseRepository:
    """测试 BaseRepository 同步方法"""

    def test_insert_one(self, sync_session):
        """测试插入单条记录"""
        record = {"name": "Alice", "email": "alice@example.com", "age": 25}
        user = BaseRepository.insert_one(sync_session, User, record)
        assert user.id is not None
        assert user.name == "Alice"
        sync_session.commit()
        # 验证数据
        stmt = select(User).where(User.id == user.id)
        result = sync_session.execute(stmt).scalar_one()
        assert result.email == "alice@example.com"

    def test_insert_many(self, sync_session):
        """测试插入多条记录"""
        records = [
            {"name": "Bob", "email": "bob@example.com", "age": 30},
            {"name": "Charlie", "email": "charlie@example.com", "age": 35},
        ]
        users = BaseRepository.insert_many(sync_session, User, records)
        assert len(users) == 2
        assert all(user.id is not None for user in users)
        sync_session.commit()
        stmt = select(User)
        results = sync_session.execute(stmt).scalars().all()
        assert len(results) == 2

    def test_insert_unified(self, sync_session):
        """测试统一插入接口"""
        # 单条
        record = {"name": "David", "email": "david@example.com", "age": 40}
        user = BaseRepository.insert(sync_session, User, record)
        assert isinstance(user, User)
        # 多条
        records = [
            {"name": "Eve", "email": "eve@example.com", "age": 45},
            {"name": "Frank", "email": "frank@example.com", "age": 50},
        ]
        users = BaseRepository.insert(sync_session, User, records)
        assert isinstance(users, list)
        assert len(users) == 2
        sync_session.commit()

    def test_update(self, sync_session):
        """测试更新记录"""
        # 先插入一条记录
        user = BaseRepository.insert_one(
            sync_session, User, {"name": "Original", "email": "original@example.com", "age": 20}
        )
        sync_session.commit()

        # 更新
        affected = BaseRepository.update(sync_session, User, {"id": user.id}, {"name": "Updated", "age": 30})
        assert affected == 1
        sync_session.commit()

        # 验证更新
        updated = sync_session.get(User, user.id)
        assert updated.name == "Updated"
        assert updated.age == 30

    def test_update_with_complex_filters(self, sync_session):
        """测试复杂过滤条件更新"""
        # 插入测试数据
        BaseRepository.insert_many(
            sync_session,
            User,
            [
                {"name": "Alice", "email": "alice1@example.com", "age": 20},
                {"name": "Alice", "email": "alice2@example.com", "age": 25},
                {"name": "Bob", "email": "bob@example.com", "age": 30},
            ],
        )
        sync_session.commit()

        # 更新所有 Alice
        affected = BaseRepository.update(sync_session, User, {"name": "Alice"}, {"age": 99})
        assert affected == 2
        sync_session.commit()

        # 验证
        stmt = select(User).where(User.name == "Alice")
        results = sync_session.execute(stmt).scalars().all()
        assert all(user.age == 99 for user in results)

    def test_delete(self, sync_session):
        """测试删除记录"""
        user = BaseRepository.insert_one(
            sync_session, User, {"name": "ToDelete", "email": "delete@example.com", "age": 99}
        )
        sync_session.commit()

        affected = BaseRepository.delete(sync_session, User, {"id": user.id})
        assert affected == 1
        sync_session.commit()

        deleted = sync_session.get(User, user.id)
        assert deleted is None

    def test_get(self, sync_session):
        """测试根据主键获取记录"""
        user = BaseRepository.insert_one(
            sync_session, User, {"name": "GetTest", "email": "get@example.com", "age": 100}
        )
        sync_session.commit()

        fetched = BaseRepository.get(sync_session, User, user.id)
        assert fetched is not None
        assert fetched.id == user.id
        assert fetched.name == "GetTest"

        # 不存在的记录
        none_result = BaseRepository.get(sync_session, User, 99999)
        assert none_result is None

    def test_list(self, sync_session):
        """测试列表查询"""
        # 插入测试数据
        BaseRepository.insert_many(
            sync_session,
            User,
            [
                {"name": "Alice", "email": "alice@example.com", "age": 20},
                {"name": "Bob", "email": "bob@example.com", "age": 30},
                {"name": "Charlie", "email": "charlie@example.com", "age": 40},
            ],
        )
        sync_session.commit()

        # 无过滤
        users = BaseRepository.list(sync_session, User)
        assert len(users) == 3

        # 带过滤
        users = BaseRepository.list(sync_session, User, {"name": "Alice"})
        assert len(users) == 1
        assert users[0].name == "Alice"

        # 带操作符过滤
        users = BaseRepository.list(sync_session, User, {"age__gt": 25})
        assert len(users) == 2
        assert all(user.age > 25 for user in users)

        # 排序
        users = BaseRepository.list(sync_session, User, order_by=["age desc"])
        assert users[0].age == 40
        assert users[-1].age == 20

        # 分页
        users = BaseRepository.list(sync_session, User, offset=1, limit=2)
        assert len(users) == 2

    def test_update_empty_filters_raises(self, sync_session):
        """测试空过滤器引发异常"""
        with pytest.raises(ValueError, match="Filters cannot be empty"):
            BaseRepository.update(sync_session, User, {}, {"name": "test"})

    def test_delete_empty_filters_raises(self, sync_session):
        """测试空过滤器引发异常"""
        with pytest.raises(ValueError, match="Filters cannot be empty"):
            BaseRepository.delete(sync_session, User, {})


# 测试异步仓库
class TestAsyncBaseRepository:
    """测试 AsyncBaseRepository 异步方法"""

    @pytest.mark.asyncio
    async def test_insert_one(self, async_session):
        """测试异步插入单条记录"""
        record = {"name": "Alice", "email": "alice@example.com", "age": 25}
        user = await AsyncBaseRepository.insert_one(async_session, User, record)
        assert user.id is not None
        assert user.name == "Alice"
        await async_session.commit()

    @pytest.mark.asyncio
    async def test_insert_many(self, async_session):
        """测试异步插入多条记录"""
        records = [
            {"name": "Bob", "email": "bob@example.com", "age": 30},
            {"name": "Charlie", "email": "charlie@example.com", "age": 35},
        ]
        users = await AsyncBaseRepository.insert_many(async_session, User, records)
        assert len(users) == 2
        assert all(user.id is not None for user in users)
        await async_session.commit()

    @pytest.mark.asyncio
    async def test_insert_unified(self, async_session):
        """测试异步统一插入接口"""
        # 单条
        record = {"name": "David", "email": "david@example.com", "age": 40}
        user = await AsyncBaseRepository.insert(async_session, User, record)
        assert isinstance(user, User)
        # 多条
        records = [
            {"name": "Eve", "email": "eve@example.com", "age": 45},
            {"name": "Frank", "email": "frank@example.com", "age": 50},
        ]
        users = await AsyncBaseRepository.insert(async_session, User, records)
        assert isinstance(users, list)
        assert len(users) == 2
        await async_session.commit()

    @pytest.mark.asyncio
    async def test_update(self, async_session):
        """测试异步更新记录"""
        # 先插入一条记录
        user = await AsyncBaseRepository.insert_one(
            async_session, User, {"name": "Original", "email": "original@example.com", "age": 20}
        )
        await async_session.commit()

        # 更新
        affected = await AsyncBaseRepository.update(
            async_session, User, {"id": user.id}, {"name": "Updated", "age": 30}
        )
        assert affected == 1
        await async_session.commit()

        # 验证更新
        updated = await async_session.get(User, user.id)
        assert updated.name == "Updated"
        assert updated.age == 30

    @pytest.mark.asyncio
    async def test_delete(self, async_session):
        """测试异步删除记录"""
        user = await AsyncBaseRepository.insert_one(
            async_session, User, {"name": "ToDelete", "email": "delete@example.com", "age": 99}
        )
        await async_session.commit()

        affected = await AsyncBaseRepository.delete(async_session, User, {"id": user.id})
        assert affected == 1
        await async_session.commit()

        deleted = await async_session.get(User, user.id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_get(self, async_session):
        """测试异步根据主键获取记录"""
        user = await AsyncBaseRepository.insert_one(
            async_session, User, {"name": "GetTest", "email": "get@example.com", "age": 100}
        )
        await async_session.commit()

        fetched = await AsyncBaseRepository.get(async_session, User, user.id)
        assert fetched is not None
        assert fetched.id == user.id
        assert fetched.name == "GetTest"

        # 不存在的记录
        none_result = await AsyncBaseRepository.get(async_session, User, 99999)
        assert none_result is None

    @pytest.mark.asyncio
    async def test_list(self, async_session):
        """测试异步列表查询"""
        # 插入测试数据
        await AsyncBaseRepository.insert_many(
            async_session,
            User,
            [
                {"name": "Alice", "email": "alice@example.com", "age": 20},
                {"name": "Bob", "email": "bob@example.com", "age": 30},
                {"name": "Charlie", "email": "charlie@example.com", "age": 40},
            ],
        )
        await async_session.commit()

        # 无过滤
        users = await AsyncBaseRepository.list(async_session, User)
        assert len(users) == 3

        # 带过滤
        users = await AsyncBaseRepository.list(async_session, User, {"name": "Alice"})
        assert len(users) == 1
        assert users[0].name == "Alice"

        # 带操作符过滤
        users = await AsyncBaseRepository.list(async_session, User, {"age__gt": 25})
        assert len(users) == 2
        assert all(user.age > 25 for user in users)

        # 排序
        users = await AsyncBaseRepository.list(async_session, User, order_by=["age desc"])
        assert users[0].age == 40
        assert users[-1].age == 20

        # 分页
        users = await AsyncBaseRepository.list(async_session, User, offset=1, limit=2)
        assert len(users) == 2

    @pytest.mark.asyncio
    async def test_update_empty_filters_raises(self, async_session):
        """测试异步空过滤器引发异常"""
        with pytest.raises(ValueError, match="Filters cannot be empty"):
            await AsyncBaseRepository.update(async_session, User, {}, {"name": "test"})

    @pytest.mark.asyncio
    async def test_delete_empty_filters_raises(self, async_session):
        """测试异步空过滤器引发异常"""
        with pytest.raises(ValueError, match="Filters cannot be empty"):
            await AsyncBaseRepository.delete(async_session, User, {})


# 测试边界情况和问题点
class TestEdgeCases:
    """测试边界情况和潜在问题"""

    def test_set_model_ignores_nonexistent_fields(self, sync_session):
        """测试 set_model 忽略不存在的字段（静默忽略）"""
        user = User(name="test", email="test@example.com", age=20)
        # 不存在的字段不会引发异常
        updated = set_model(user, {"nonexistent": "value", "also_not_real": 123})
        assert not hasattr(updated, "nonexistent")
        assert not hasattr(updated, "also_not_real")
        # 存在的字段正常更新
        updated = set_model(user, {"name": "updated"})
        assert updated.name == "updated"

    def test_build_filters_ignores_invalid_fields(self):
        """测试 build_filters 忽略无效字段（静默忽略）"""
        conditions = build_filters(User, {"invalid_field": "value"})
        assert len(conditions) == 0
        conditions = build_filters(User, {"invalid_field__gt": 10})
        assert len(conditions) == 0

    def test_build_orders_ignores_invalid_fields(self):
        """测试 build_orders 忽略无效字段（静默忽略）"""
        orders = build_orders(User, {"invalid_field": "desc"})
        assert len(orders) == 0

    def test_insert_relations_behavior(self, sync_session):
        """测试关联字段的行为"""
        # 测试单条记录带关联
        record = {"name": "Test", "email": "test@example.com", "age": 20}
        relations = {"extra_field": "value"}  # 但 User 模型没有 extra_field
        user = BaseRepository.insert_one(sync_session, User, record, relations)
        # set_model 会忽略不存在的字段，所以不会出错
        assert user.name == "Test"
        sync_session.commit()

    def test_insert_many_relations_edge_cases(self, sync_session):
        """测试多条插入时关联字段的边缘情况"""
        records = [
            {"name": "A", "email": "a@example.com", "age": 1},
            {"name": "B", "email": "b@example.com", "age": 2},
            {"name": "C", "email": "c@example.com", "age": 3},
        ]
        # relations 列表为空
        users = BaseRepository.insert_many(sync_session, User, records, relations=[])
        assert len(users) == 3

        # relations 只有一个元素，所有记录使用同一个
        relations = [{"extra": "shared"}]
        # 使用不同的email避免唯一约束冲突
        records2 = [
            {"name": "A2", "email": "a2@example.com", "age": 1},
            {"name": "B2", "email": "b2@example.com", "age": 2},
            {"name": "C2", "email": "c2@example.com", "age": 3},
        ]
        users = BaseRepository.insert_many(sync_session, User, records2, relations=relations)
        # 不会出错，但 extra 字段不存在于模型

        sync_session.commit()

    @pytest.mark.skip(reason="需要 PostgreSQL 数据库支持 ON CONFLICT")
    def test_upsert_postgresql_only(self):
        """测试 upsert 功能（仅限 PostgreSQL）"""
        # 由于 SQLite 不支持完整的 ON CONFLICT 语法，此测试需要 PostgreSQL
        pass
