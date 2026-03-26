# 测试目录

本目录用于存放项目的单元测试和集成测试代码。

## 📁 目录结构

```
tests/
├── __init__.py     # 测试包初始化
└── README.md       # 本说明文档
```

## 🧪 测试框架

项目使用 **pytest** 作为测试框架。

**依赖：**
- pytest
- pytest-asyncio（异步测试支持）
- pytest-cov（测试覆盖率）

## 📝 测试规范

### 1. 文件命名

- 测试文件以 `test_` 开头
- 例如：`test_api.py`、`test_services.py`

### 2. 测试函数命名

- 测试函数以 `test_` 开头
- 使用描述性名称
- 例如：`test_user_login()`、`test_document_upload()`

### 3. 测试组织

```
tests/
├── __init__.py
├── conftest.py              # pytest 配置和 fixtures
├── test_api/                # API 测试
│   ├── test_auth.py
│   ├── test_documents.py
│   └── test_quiz.py
├── test_services/           # 服务层测试
│   ├── test_llm_service.py
│   ├── test_rag_service.py
│   └── test_quiz_service.py
└── test_models/             # 模型测试
    ├── test_user.py
    └── test_chapter.py
```

## 🔧 使用方法

### 运行所有测试

```bash
# 在 backend 目录下执行
pytest tests/
```

### 运行特定测试文件

```bash
pytest tests/test_api/test_auth.py
```

### 运行特定测试函数

```bash
pytest tests/test_api/test_auth.py::test_user_login
```

### 查看测试覆盖率

```bash
pytest --cov=app tests/
```

### 详细输出

```bash
pytest -v tests/
```

## 📋 测试类型

### 1. 单元测试（Unit Tests）

测试单个函数或方法的功能。

```python
def test_password_hashing():
    """测试密码哈希功能"""
    password = "test123"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
```

### 2. 集成测试（Integration Tests）

测试多个组件的协作。

```python
def test_user_registration_flow(client):
    """测试用户注册流程"""
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "password": "test123"
    })
    assert response.status_code == 201
```

### 3. API 测试

测试 API 端点。

```python
def test_get_chapters(client, auth_header):
    """测试获取章节列表"""
    response = client.get("/api/v1/chapters/", headers=auth_header)
    assert response.status_code == 200
```

## 🎯 测试覆盖范围

建议测试以下内容：

- ✅ API 端点（所有路由）
- ✅ 服务层（业务逻辑）
- ✅ 数据模型（验证和关系）
- ✅ 工具函数（辅助方法）
- ✅ 异常处理（错误情况）

## 🔨 编写测试示例

### API 测试示例

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_chapter():
    """测试创建章节"""
    response = client.post(
        "/api/v1/chapters/",
        json={
            "chapter_number": 1,
            "title": "Test Chapter",
            "description": "Test Description"
        },
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Test Chapter"
```

### 服务测试示例

```python
import pytest
from app.services.quiz_service import quiz_service

@pytest.mark.asyncio
async def test_create_quiz(db_session):
    """测试创建练习"""
    quiz = await quiz_service.create_quiz(
        db=db_session,
        user_id=1,
        chapter_id=1,
        quiz_type="reading",
        question_count=5
    )
    assert quiz is not None
    assert quiz.question_count == 5
```

## ⚠️ 注意事项

1. **测试数据**
   - 使用独立的测试数据库
   - 测试后清理数据
   - 不要使用生产数据

2. **环境隔离**
   - 测试环境与生产环境分离
   - 使用 `.env.test` 配置文件

3. **异步测试**
   - 使用 `@pytest.mark.asyncio` 装饰器
   - 异步函数使用 `async def`

## 📊 当前状态

- ⚠️ 测试目录已创建，但暂无测试代码
- 📝 建议逐步添加测试，提高代码质量
- 🎯 目标：达到 80% 以上的测试覆盖率

## 🚀 下一步

1. 创建 `conftest.py` 配置测试环境
2. 添加 API 测试
3. 添加服务层测试
4. 配置 CI/CD 自动测试

## 📚 参考资料

- [pytest 官方文档](https://docs.pytest.org/)
- [FastAPI 测试指南](https://fastapi.tiangolo.com/tutorial/testing/)
- [测试驱动开发（TDD）](https://en.wikipedia.org/wiki/Test-driven_development)
