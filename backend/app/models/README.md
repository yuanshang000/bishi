# 数据模型层（Models）

本文件夹包含系统的所有数据库模型定义，是数据持久化的核心。

## 📋 目录结构

```
models/
├── __init__.py                  # 模型导出
├── user.py                      # 用户模型
├── chapter.py                   # 章节模型
├── section.py                   # 节模型
├── subsection.py                # 小节（小目标）模型
├── knowledge_point.py           # 知识点模型
├── document.py                  # 课程文档模型
├── quiz.py                      # 练习记录模型
├── wrong_question.py            # 错题记录模型
├── chat.py                      # 聊天历史模型
├── user_word_stats.py           # 用户单词统计模型
├── user_knowledge_stats.py      # 用户知识点统计模型
└── custom_quiz.py               # 自定义练习模型
```

## 🎯 核心作用

**本文件夹是系统的数据模型层，负责定义数据库表结构和对象关系映射（ORM）。**

### 架构位置

```
┌─────────────────────────────────────┐
│         API 层（路由）               │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│       Services 层（业务逻辑）         │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│     Models 层（数据模型）← 你在这里    │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│         数据库（MySQL）               │
└─────────────────────────────────────┘
```

### 设计原则

- ✅ **ORM 映射**：使用 SQLAlchemy 定义表结构
- ✅ **关系定义**：明确表之间的关联关系
- ✅ **类型安全**：使用类型注解和约束
- ✅ **注释完善**：每个字段都有详细注释

---

## 📊 数据模型概览

### 模型分类

| 分类 | 模型 | 说明 |
|------|------|------|
| **用户管理** | User | 用户基本信息和认证 |
| **课程结构** | Chapter, Section, SubSection | 章-节-小节三级结构 |
| **知识点** | KnowledgePoint | 知识点定义和关联 |
| **文档管理** | CourseDocument | 课程文档和向量化 |
| **练习系统** | QuizRecord, CustomQuizRecord | 练习记录和成绩 |
| **错题管理** | WrongQuestion | 错题记录和掌握状态 |
| **聊天系统** | ChatHistory | AI 聊天历史 |
| **学习统计** | UserWordStats, UserKnowledgePointStats | 学习进度统计 |

---

## 📄 模型详细说明

### 1. User - 用户模型

**文件：** `user.py`

**表名：** `users`

**作用：** 存储用户基本信息、认证信息和角色权限

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 用户ID（主键） |
| username | String(50) | 用户名（唯一） |
| email | String(100) | 电子邮箱（唯一） |
| full_name | String(100) | 真实姓名 |
| password_hash | String(255) | 密码哈希值 |
| role | Enum | 用户角色（teacher/student） |
| is_active | Integer | 账号状态（1=启用，0=禁用） |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**角色枚举：**
```python
class UserRole(str, enum.Enum):
    teacher = "teacher"  # 教师
    student = "student"  # 学生
```

**关系：**
- 一对多：User → QuizRecord（练习记录）
- 一对多：User → WrongQuestion（错题记录）
- 一对多：User → ChatHistory（聊天历史）

---

### 2. Chapter - 章节模型

**文件：** `chapter.py`

**表名：** `chapters`

**作用：** 存储课程章节信息和元数据

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 章节ID（主键） |
| chapter_number | Integer | 章节编号（唯一） |
| title | String(200) | 章节标题 |
| description | Text | 章节描述 |
| learning_objectives | Text | 学习目标（JSON格式） |
| key_points | Text | 知识点列表（JSON格式） |
| word_count | Integer | 词汇量 |
| difficulty_level | String(20) | 难度等级 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**关系：**
- 一对多：Chapter → Section（节）
- 一对多：Chapter → CourseDocument（文档）
- 一对多：Chapter → QuizRecord（练习记录）

---

### 3. Section - 节模型

**文件：** `section.py`

**表名：** `sections`

**作用：** 存储章节下的节信息

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 节ID（主键） |
| chapter_id | Integer | 所属章节ID（外键） |
| title | String(200) | 节标题 |
| order | Integer | 排序序号 |
| content | Text | 节内容 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**关系：**
- 多对一：Section → Chapter（所属章节）
- 一对多：Section → SubSection（小节）

---

### 4. SubSection - 小节（小目标）模型

**文件：** `subsection.py`

**表名：** `subsections`

**作用：** 存储节下的小节（学习小目标）信息

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 小节ID（主键） |
| section_id | Integer | 所属节ID（外键） |
| title | String(200) | 小节标题 |
| content | Text | 小节内容 |
| order | Integer | 排序序号 |
| weight | Float | 权重占比 |
| passing_score | Integer | 及格分数（默认60） |
| min_questions | Integer | 最少练习题数（默认10） |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**关系：**
- 多对一：SubSection → Section（所属节）
- 一对多：SubSection → KnowledgePoint（知识点）

---

### 5. KnowledgePoint - 知识点模型

**文件：** `knowledge_point.py`

**表名：** `knowledge_points`

**作用：** 存储知识点定义和关联信息

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 知识点ID（主键） |
| subsection_id | Integer | 所属小节ID（外键） |
| content | String(200) | 知识点内容 |
| type | String(50) | 知识点类型（word/grammar/phrase/sentence） |
| example | Text | 示例 |
| created_at | DateTime | 创建时间 |

**关系：**
- 多对一：KnowledgePoint → SubSection（所属小节）

---

### 6. CourseDocument - 课程文档模型

**文件：** `document.py`

**表名：** `course_documents`

**作用：** 存储课程文档信息和向量化状态

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 文档ID（主键） |
| chapter_id | Integer | 所属章节ID（外键） |
| title | String(200) | 文档标题 |
| file_path | String(500) | 文件路径 |
| file_type | String(20) | 文件类型（pdf/docx/txt） |
| file_size | Integer | 文件大小（字节） |
| content | LongText | 文档文本内容 |
| is_vectorized | Integer | 是否已向量化（1=是，0=否） |
| vector_count | Integer | 向量数量 |
| chroma_ids | Text | ChromaDB中的ID列表（JSON格式） |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**关系：**
- 多对一：CourseDocument → Chapter（所属章节）

---

### 7. QuizRecord - 练习记录模型

**文件：** `quiz.py`

**表名：** `quiz_records`

**作用：** 存储学生的练习答题记录和成绩

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 记录ID（主键） |
| user_id | Integer | 用户ID（外键） |
| chapter_id | Integer | 章节ID（外键，可空） |
| section_id | Integer | 节ID（外键，可空） |
| subsection_id | Integer | 小节ID（外键，可空） |
| practice_mode | String(20) | 练习方式（chapter/random/comprehensive） |
| quiz_type | String(50) | 练习类型（reading/listening/translation/writing） |
| difficulty | String(20) | 难度等级（low/medium/high） |
| question_count | Integer | 题目总数 |
| questions | Text | 题目列表（JSON格式） |
| user_answers | Text | 用户答案（JSON格式） |
| correct_answers | Text | 正确答案（JSON格式） |
| results | Text | 详细批改结果（JSON格式） |
| score | Float | 总分 |
| accuracy | Float | 正确率（百分比） |
| time_spent | Integer | 用时（秒） |
| knowledge_point_ids | Text | 知识点ID列表（JSON格式） |
| is_completed | Integer | 是否完成（1=是，0=否） |
| started_at | DateTime | 开始时间 |
| completed_at | DateTime | 完成时间 |
| created_at | DateTime | 创建时间 |

**关系：**
- 多对一：QuizRecord → User（用户）
- 多对一：QuizRecord → Chapter（章节）

---

### 8. WrongQuestion - 错题记录模型

**文件：** `wrong_question.py`

**表名：** `wrong_questions`

**作用：** 存储学生的错题记录和掌握状态

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 错题ID（主键） |
| user_id | Integer | 用户ID（外键） |
| quiz_record_id | Integer | 练习记录ID（外键） |
| chapter_id | Integer | 章节ID（外键） |
| question_type | String(50) | 题目类型 |
| question_data | Text | 题目数据（JSON格式） |
| user_answer | Text | 用户答案 |
| correct_answer | Text | 正确答案 |
| score | Float | 得分 |
| knowledge_point_ids | Text | 知识点ID列表（JSON格式） |
| is_mastered | Integer | 是否已掌握（1=是，0=否） |
| retry_count | Integer | 重做次数 |
| last_retry_score | Float | 最近重做得分 |
| last_retry_at | DateTime | 最近重做时间 |
| created_at | DateTime | 创建时间 |

**关系：**
- 多对一：WrongQuestion → User（用户）
- 多对一：WrongQuestion → QuizRecord（练习记录）

---

### 9. ChatHistory - 聊天历史模型

**文件：** `chat.py`

**表名：** `chat_history`

**作用：** 存储 AI 聊天历史记录

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 记录ID（主键） |
| user_id | Integer | 用户ID（外键） |
| session_id | String(100) | 会话ID |
| role | String(20) | 角色（user/assistant） |
| content | Text | 消息内容 |
| metadata | Text | 元数据（JSON格式） |
| created_at | DateTime | 创建时间 |

**关系：**
- 多对一：ChatHistory → User（用户）

---

### 10. UserWordStats - 用户单词统计模型

**文件：** `user_word_stats.py`

**表名：** `user_word_stats`

**作用：** 存储用户的单词学习统计

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 记录ID（主键） |
| user_id | Integer | 用户ID（外键） |
| word | String(100) | 单词 |
| total_attempts | Integer | 总尝试次数 |
| correct_attempts | Integer | 正确次数 |
| last_attempt_at | DateTime | 最近尝试时间 |
| created_at | DateTime | 创建时间 |

---

### 11. UserKnowledgePointStats - 用户知识点统计模型

**文件：** `user_knowledge_stats.py`

**表名：** `user_knowledge_point_stats`

**作用：** 存储用户的知识点掌握统计

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 记录ID（主键） |
| user_id | Integer | 用户ID（外键） |
| knowledge_point_id | Integer | 知识点ID（外键） |
| subsection_id | Integer | 小节ID（外键） |
| total_attempts | Integer | 总尝试次数 |
| correct_attempts | Integer | 正确次数 |
| last_attempt_at | DateTime | 最近尝试时间 |
| created_at | DateTime | 创建时间 |

---

### 12. CustomQuizRecord - 自定义练习模型

**文件：** `custom_quiz.py`

**表名：** `custom_quiz_records`

**作用：** 存储自定义练习记录

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 记录ID（主键） |
| user_id | Integer | 用户ID（外键） |
| title | String(200) | 练习标题 |
| quiz_type | String(50) | 练习类型 |
| questions | Text | 题目列表（JSON格式） |
| created_at | DateTime | 创建时间 |

---

## 🔗 数据库关系图

```
User（用户）
    ├── 1:N → QuizRecord（练习记录）
    ├── 1:N → WrongQuestion（错题记录）
    ├── 1:N → ChatHistory（聊天历史）
    ├── 1:N → UserWordStats（单词统计）
    └── 1:N → UserKnowledgePointStats（知识点统计）

Chapter（章节）
    ├── 1:N → Section（节）
    ├── 1:N → CourseDocument（文档）
    └── 1:N → QuizRecord（练习记录）

Section（节）
    └── 1:N → SubSection（小节）

SubSection（小节）
    └── 1:N → KnowledgePoint（知识点）

KnowledgePoint（知识点）
    └── 1:N → UserKnowledgePointStats（用户统计）
```

---

## 🔧 使用指南

### 导入模型

```python
# 方式1：从 __init__.py 导入
from app.models import User, Chapter, QuizRecord

# 方式2：直接导入
from app.models.user import User
from app.models.chapter import Chapter
from app.models.quiz import QuizRecord
```

### 创建记录

```python
from sqlalchemy.orm import Session
from app.models import User, Chapter
from app.core.security import get_password_hash

# 创建用户
user = User(
    username="john_doe",
    email="john@example.com",
    password_hash=get_password_hash("password123"),
    role="student"
)
db.add(user)
db.commit()

# 创建章节
chapter = Chapter(
    chapter_number=1,
    title="Unit 1: Campus Life",
    description="Introduction to campus life"
)
db.add(chapter)
db.commit()
```

### 查询记录

```python
# 查询单个记录
user = db.query(User).filter(User.id == 1).first()

# 查询多个记录
chapters = db.query(Chapter).order_by(Chapter.chapter_number).all()

# 关联查询
user_quizzes = db.query(QuizRecord).filter(
    QuizRecord.user_id == user.id
).all()

# 使用关系
for quiz in user.quiz_records:  # 通过关系访问
    print(quiz.score)
```

### 更新记录

```python
user = db.query(User).filter(User.id == 1).first()
user.full_name = "John Doe"
db.commit()
```

### 删除记录

```python
user = db.query(User).filter(User.id == 1).first()
db.delete(user)
db.commit()
```

---

## 📝 模型设计原则

### 1. 命名规范

- **表名**：使用复数形式（users, chapters）
- **字段名**：使用蛇形命名（user_id, created_at）
- **类名**：使用帕斯卡命名（User, QuizRecord）

### 2. 字段设计

- ✅ 所有表都有主键 `id`
- ✅ 时间戳字段：`created_at`, `updated_at`
- ✅ 外键使用 `ForeignKey` 定义关系
- ✅ 索引字段使用 `index=True`
- ✅ 每个字段都有 `comment` 注释

### 3. 关系设计

- ✅ 使用 `relationship()` 定义关系
- ✅ 外键设置 `ondelete="CASCADE"` 级联删除
- ✅ 双向关系便于导航

### 4. 数据类型选择

- **字符串**：String(length)
- **长文本**：Text / LongText
- **整数**：Integer
- **浮点数**：Float
- **时间**：DateTime
- **枚举**：Enum

---

## 🔄 数据库迁移

### 使用 Alembic 管理迁移

**生成迁移文件：**
```bash
alembic revision --autogenerate -m "描述"
```

**执行迁移：**
```bash
alembic upgrade head
```

**回滚迁移：**
```bash
alembic downgrade -1
```

---

## 📊 统计信息

| 模型 | 表名 | 主要字段数 | 关系数 |
|------|------|-----------|--------|
| User | users | 8 | 5 |
| Chapter | chapters | 9 | 3 |
| Section | sections | 6 | 2 |
| SubSection | subsections | 9 | 2 |
| KnowledgePoint | knowledge_points | 5 | 1 |
| CourseDocument | course_documents | 12 | 1 |
| QuizRecord | quiz_records | 20 | 4 |
| WrongQuestion | wrong_questions | 15 | 3 |
| ChatHistory | chat_history | 6 | 1 |
| UserWordStats | user_word_stats | 6 | 1 |
| UserKnowledgePointStats | user_knowledge_point_stats | 7 | 2 |
| CustomQuizRecord | custom_quiz_records | 5 | 1 |

**总计：** 12 个模型，对应 12 张数据库表

---

## 📚 相关文档

- [SQLAlchemy 官方文档](https://docs.sqlalchemy.org/)
- [FastAPI 数据库集成](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [Alembic 迁移工具](https://alembic.sqlalchemy.org/)

---

**最后更新：** 2026-03-26
**维护人员：** 数据库架构师
