import pytest
from sqlalchemy import Column, Integer, String, DateTime, func, select


from lib_common.connect.database.base import BaseModel
from lib_common.connect.database.repository import (
    BaseRepository,
    set_model,
    build_filter_conditions,
    build_order_conditions,
)
from lib_common.connect.configs import databases

test_db = databases.get_database("test")


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


# 测试 Fixture
@pytest.fixture(scope="function")
def db_session():
    """为每个测试函数提供独立的数据库会话"""
    from lib_common.connect.database.base import BaseModel

    test_db = databases.get_database("test")
    with test_db.connection() as session:
        # 创建表结构
        BaseModel.metadata.create_all(session.get_bind())
        yield session
        # 清理表结构，确保测试独立性
        session.rollback()
        BaseModel.metadata.drop_all(session.get_bind())


@pytest.fixture
def sample_user_data():
    """返回示例用户数据"""
    return {"name": "Test User", "email": "test@example.com", "age": 28}


@pytest.fixture
def sample_users_data():
    """返回示例用户数据列表"""
    return [
        {"name": "User1", "email": "user1@example.com", "age": 20},
        {"name": "User2", "email": "user2@example.com", "age": 25},
        {"name": "User3", "email": "user3@example.com", "age": 30},
    ]


# 测试工具函数
class TestUtilityFunctions:
    """测试工具函数 set_model, build_filter_conditions, build_order_conditions"""

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

    def test_build_filter_conditions(self):
        """测试构建过滤条件"""
        # 等于操作
        conditions = build_filter_conditions(User, {"name": "Alice"})
        assert len(conditions) == 1
        # 操作符后缀
        conditions = build_filter_conditions(User, {"age__gt": 18})
        assert len(conditions) == 1
        conditions = build_filter_conditions(User, {"age__in": [18, 19, 20]})
        assert len(conditions) == 1
        conditions = build_filter_conditions(User, {"name__like": "Ali"})
        assert len(conditions) == 1
        # 无效字段被忽略
        conditions = build_filter_conditions(User, {"invalid_field": "value"})
        assert len(conditions) == 0
        # 混合条件
        conditions = build_filter_conditions(User, {"name": "Alice", "age__gt": 18})
        assert len(conditions) == 2

    def test_build_order_conditions(self):
        """测试构建排序条件"""
        # 升序
        orders = build_order_conditions(User, {"name": "asc"})
        assert len(orders) == 1
        # 降序
        orders = build_order_conditions(User, {"name": "desc"})
        assert len(orders) == 1
        # 无效字段被忽略
        orders = build_order_conditions(User, {"invalid_field": "desc"})
        assert len(orders) == 0


# 测试同步仓库
class TestBaseRepository:
    """测试 BaseRepository 同步方法"""

    def test_insert_one(self, db_session):
        """测试插入单条记录"""
        record = {"name": "Alice", "email": "alice@example.com", "age": 25}
        user = BaseRepository.insert(db_session, User, record)
        assert user.id is not None
        assert user.name == "Alice"
        db_session.commit()
        # 验证数据
        stmt = select(User).where(User.id == user.id)
        result = db_session.execute(stmt).scalar_one()
        assert result.email == "alice@example.com"

    def test_insert_multiple(self, db_session, sample_users_data):
        """测试批量插入多条记录"""
        users = BaseRepository.insert(db_session, User, sample_users_data)
        assert len(users) == 3
        for i, user in enumerate(users):
            assert user.id is not None
            assert user.name == f"User{i + 1}"
            assert user.email == f"user{i + 1}@example.com"
            assert user.age == 20 + i * 5
        db_session.commit()
        # 验证数据
        stmt = select(User).where(User.id.in_([user.id for user in users]))
        results = db_session.execute(stmt).scalars().all()
        assert len(results) == 3
        assert {user.email for user in results} == {"user1@example.com", "user2@example.com", "user3@example.com"}

    def test_insert_without_returning(self, db_session):
        """测试插入不返回对象"""
        record = {"name": "NoReturn", "email": "noreturn@example.com", "age": 99}
        # 测试插入单条记录不返回对象
        rowcount = BaseRepository.insert(db_session, User, record, returning=False)
        assert rowcount == 1
        db_session.commit()
        # 验证数据确实插入
        stmt = select(User).where(User.email == "noreturn@example.com")
        result = db_session.execute(stmt).scalar_one()
        assert result.name == "NoReturn"
        assert result.age == 99

    def test_update_by_id(self, db_session):
        """测试按 ID 更新记录"""
        # 先插入测试数据
        record = {"name": "Original", "email": "original@example.com", "age": 25}
        user = BaseRepository.insert(db_session, User, record)
        db_session.commit()

        # 更新记录
        updated_count = BaseRepository.update(
            db_session,
            User,
            {"id": user.id},  # 按 ID 过滤
            {"name": "Updated", "age": 30},  # 更新字段
        )
        assert updated_count == 1
        db_session.commit()

        # 验证更新结果
        stmt = select(User).where(User.id == user.id)
        updated_user = db_session.execute(stmt).scalar_one()
        assert updated_user.name == "Updated"
        assert updated_user.age == 30
        assert updated_user.email == "original@example.com"  # 未更新的字段保持不变

    def test_update_with_complex_filters(self, db_session):
        """测试使用复杂过滤条件更新记录"""
        # 插入测试数据
        users_data = [
            {"name": "Alice", "email": "alice@example.com", "age": 25},
            {"name": "Bob", "email": "bob@example.com", "age": 30},
            {"name": "Charlie", "email": "charlie@example.com", "age": 35},
        ]
        BaseRepository.insert(db_session, User, users_data)
        db_session.commit()

        # 更新年龄大于 28 的用户
        updated_count = BaseRepository.update(
            db_session,
            User,
            {"age__gt": 28},  # 复杂过滤条件：年龄大于 28
            {"age": 40},  # 将所有符合条件的用户年龄更新为 40
        )
        assert updated_count == 2  # Bob(30) 和 Charlie(35) 应该被更新
        db_session.commit()

        # 验证更新结果
        stmt = select(User).where(User.age == 40)
        updated_users = db_session.execute(stmt).scalars().all()
        assert len(updated_users) == 2
        assert {user.name for user in updated_users} == {"Bob", "Charlie"}

        # 验证 Alice 的年龄没有变化
        stmt = select(User).where(User.name == "Alice")
        alice = db_session.execute(stmt).scalar_one()
        assert alice.age == 25

    def test_delete_by_id(self, db_session):
        """测试按 ID 删除记录"""
        # 先插入测试数据
        record = {"name": "ToDelete", "email": "delete@example.com", "age": 25}
        user = BaseRepository.insert(db_session, User, record)
        db_session.commit()

        # 删除记录
        deleted_count = BaseRepository.delete(db_session, User, {"id": user.id})
        assert deleted_count == 1
        db_session.commit()

        # 验证记录已被删除
        stmt = select(User).where(User.id == user.id)
        result = db_session.execute(stmt).scalar_one_or_none()
        assert result is None

    def test_delete_with_complex_filters(self, db_session):
        """测试使用复杂过滤条件删除记录"""
        # 插入测试数据
        users_data = [
            {"name": "Alice", "email": "alice@example.com", "age": 25},
            {"name": "Bob", "email": "bob@example.com", "age": 30},
            {"name": "Charlie", "email": "charlie@example.com", "age": 35},
            {"name": "David", "email": "david@example.com", "age": 40},
        ]
        BaseRepository.insert(db_session, User, users_data)
        db_session.commit()

        # 删除年龄大于等于 35 的用户
        deleted_count = BaseRepository.delete(
            db_session,
            User,
            {"age__ge": 35},  # 复杂过滤条件：年龄大于等于 35
        )
        assert deleted_count == 2  # Charlie(35) 和 David(40) 应该被删除
        db_session.commit()

        # 验证删除结果
        stmt = select(User)
        remaining_users = db_session.execute(stmt).scalars().all()
        assert len(remaining_users) == 2
        assert {user.name for user in remaining_users} == {"Alice", "Bob"}

        # 验证被删除的用户确实不存在了
        stmt = select(User).where(User.age >= 35)
        deleted_users = db_session.execute(stmt).scalars().all()
        assert len(deleted_users) == 0

    def test_get_by_primary_key(self, db_session):
        """测试根据主键获取记录"""
        # 先插入测试数据
        record = {"name": "TestGet", "email": "testget@example.com", "age": 25}
        user = BaseRepository.insert(db_session, User, record)
        db_session.commit()

        # 根据主键获取记录
        retrieved_user = BaseRepository.get(db_session, User, user.id)
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert retrieved_user.name == "TestGet"
        assert retrieved_user.email == "testget@example.com"
        assert retrieved_user.age == 25

    def test_get_not_found(self, db_session):
        """测试获取不存在的记录"""
        # 尝试获取不存在的记录（使用一个不可能存在的 ID）
        non_existent_id = 999999
        retrieved_user = BaseRepository.get(db_session, User, non_existent_id)
        assert retrieved_user is None

    def test_list_all(self, db_session):
        """测试查询所有记录"""
        # 插入测试数据
        users_data = [
            {"name": "User1", "email": "user1@example.com", "age": 20},
            {"name": "User2", "email": "user2@example.com", "age": 25},
            {"name": "User3", "email": "user3@example.com", "age": 30},
        ]
        BaseRepository.insert(db_session, User, users_data)
        db_session.commit()

        # 查询所有记录
        users = BaseRepository.list(db_session, User)
        assert len(users) == 3
        assert {user.name for user in users} == {"User1", "User2", "User3"}

    def test_list_with_filters(self, db_session):
        """测试带过滤条件查询"""
        # 插入测试数据
        users_data = [
            {"name": "Alice", "email": "alice@example.com", "age": 25},
            {"name": "Bob", "email": "bob@example.com", "age": 30},
            {"name": "Charlie", "email": "charlie@example.com", "age": 35},
        ]
        BaseRepository.insert(db_session, User, users_data)
        db_session.commit()

        # 测试等于过滤
        users = BaseRepository.list(db_session, User, filters={"name": "Alice"})
        assert len(users) == 1
        assert users[0].name == "Alice"
        assert users[0].age == 25

        # 测试范围过滤
        users = BaseRepository.list(db_session, User, filters={"age__gt": 28})
        assert len(users) == 2
        assert {user.name for user in users} == {"Bob", "Charlie"}

        # 测试 IN 过滤
        users = BaseRepository.list(db_session, User, filters={"age__in": [25, 35]})
        assert len(users) == 2
        assert {user.name for user in users} == {"Alice", "Charlie"}

    def test_list_with_ordering(self, db_session):
        """测试带排序查询"""
        # 插入测试数据
        users_data = [
            {"name": "Charlie", "email": "charlie@example.com", "age": 35},
            {"name": "Alice", "email": "alice@example.com", "age": 25},
            {"name": "Bob", "email": "bob@example.com", "age": 30},
        ]
        BaseRepository.insert(db_session, User, users_data)
        db_session.commit()

        # 测试升序排序
        users = BaseRepository.list(db_session, User, orders={"age": "asc"})
        assert len(users) == 3
        assert [user.age for user in users] == [25, 30, 35]
        assert [user.name for user in users] == ["Alice", "Bob", "Charlie"]

        # 测试降序排序
        users = BaseRepository.list(db_session, User, orders={"age": "desc"})
        assert len(users) == 3
        assert [user.age for user in users] == [35, 30, 25]
        assert [user.name for user in users] == ["Charlie", "Bob", "Alice"]

    def test_list_with_pagination(self, db_session):
        """测试分页查询"""
        # 插入测试数据
        users_data = []
        for i in range(10):
            users_data.append({"name": f"User{i + 1}", "email": f"user{i + 1}@example.com", "age": 20 + i})
        BaseRepository.insert(db_session, User, users_data)
        db_session.commit()

        # 测试第一页，每页 3 条
        users = BaseRepository.list(db_session, User, offset=0, limit=3)
        assert len(users) == 3
        assert [user.name for user in users] == ["User1", "User2", "User3"]

        # 测试第二页，每页 3 条
        users = BaseRepository.list(db_session, User, offset=3, limit=3)
        assert len(users) == 3
        assert [user.name for user in users] == ["User4", "User5", "User6"]

        # 测试第三页，每页 4 条
        users = BaseRepository.list(db_session, User, offset=8, limit=4)
        assert len(users) == 2  # 只剩下 2 条记录
        assert [user.name for user in users] == ["User9", "User10"]

        # 测试偏移量超出范围
        users = BaseRepository.list(db_session, User, offset=20, limit=5)
        assert len(users) == 0


if __name__ == "__main__":
    pytest.main()
