# MCP Server 部署与集成完整指南

## 🎉 当前状态

✅ **MCP Server 已成功创建并测试通过！**

- ✅ 数据库连接正常
- ✅ 三个核心工具运行正常
- ✅ 配置文件已更新
- ✅ 测试脚本可用

## 📋 项目文件清单

```
backend/mcp_server/
├── server.py                    # MCP Server 主程序 (360行)
├── config.py                    # 配置文件（已更新数据库连接）
├── test_server.py               # 测试脚本
├── integration_guide.py         # 🆕 集成示例代码
├── requirements.txt             # 依赖列表
├── start.bat / start.sh         # 启动脚本
├── start_mcp.bat               # 独立环境启动脚本
├── setup_env.py                # 环境配置脚本
├── mcp_config.json             # MCP 客户端配置
├── .env.example                # 环境变量模板
├── README.md                   # 详细文档
└── USAGE_GUIDE.md              # 使用指南
```

## 🚀 下一步行动计划

### 阶段 1: 生成测试数据（可选）

为了测试 MCP Server 的完整功能，建议先生成一些测试数据：

**方法 1: 通过前端做题**
1. 启动前端和后端
2. 登录学生账号（user_id=1）
3. 完成几次练习
4. 再次运行 `python test_server.py` 查看数据

**方法 2: 直接插入测试数据（快速验证）**

```sql
-- 插入测试练习记录
INSERT INTO quiz_records (user_id, chapter_id, quiz_type, question_count, score, accuracy, time_spent, is_completed, created_at, completed_at)
VALUES
(1, 1, 'reading', 5, 80.0, 80.0, 120, 1, NOW(), NOW()),
(1, 2, 'reading', 5, 45.0, 40.0, 180, 1, NOW(), NOW()),
(1, 2, 'translation', 5, 50.0, 60.0, 200, 1, NOW(), NOW());

-- 插入测试错题记录
INSERT INTO wrong_questions (user_id, quiz_record_id, chapter_id, question_type, question_data, user_answer, correct_answer, score, knowledge_point_ids, created_at)
VALUES
(1, 1, 2, 'reading', '{"question": "test"}', 'A', 'B', 0.0, '["modal_verbs", "grammar"]', NOW()),
(1, 2, 2, 'reading', '{"question": "test2"}', 'C', 'D', 0.0, '["modal_verbs"]', NOW());
```

### 阶段 2: 与主业务后端集成

#### 方案 A: 直接导入模块（简单快速）

在主业务后端的 AI 服务中：

```python
# backend/app/services/ai_analysis_service.py

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../mcp_server'))

from server import fetch_learning_data, fetch_weak_knowledge_points
import json
import asyncio

class AIAnalysisService:
    """AI 学情分析服务"""

    async def analyze_student(self, student_id: int) -> dict:
        """分析学生学习情况"""
        # 调用 MCP 工具
        learning_data = await fetch_learning_data({
            "student_id": student_id,
            "limit": 20
        })

        weak_points = await fetch_weak_knowledge_points({
            "student_id": student_id,
            "top_k": 5
        })

        # 解析数据
        learning_json = json.loads(learning_data[0].text)
        weak_json = json.loads(weak_points[0].text)

        # AI 分析逻辑...
        return {
            "total_records": learning_json["total_records"],
            "weak_points": weak_json["weak_knowledge_points"]
        }
```

#### 方案 B: 通过 MCP 协议（标准方式）

使用 LangChain 或 MCP SDK 连接：

```python
from mcp.client import MCPClient

# 创建 MCP 客户端
client = MCPClient("student-analytics")

# 调用工具
result = await client.call_tool(
    "fetch_learning_data",
    {"student_id": 1}
)
```

### 阶段 3: 在 AI 对话中使用

#### 示例：学情分析端点

```python
# backend/app/api/v1/ai_analysis.py

from fastapi import APIRouter, Depends
from app.core.deps import get_current_user

router = APIRouter()

@router.post("/analysis/my-learning")
async def analyze_my_learning(current_user = Depends(get_current_user)):
    """
    AI 分析我的学习情况

    AI 会调用 MCP 工具获取学生数据，然后进行智能分析
    """
    from app.services.ai_analysis_service import AIAnalysisService

    service = AIAnalysisService()
    analysis = await service.analyze_student(current_user.id)

    # 生成人类可读的分析报告
    report = generate_analysis_report(analysis)

    return {
        "success": True,
        "report": report,
        "raw_data": analysis  # 可选：返回原始数据供前端使用
    }


@router.post("/quiz/targeted")
async def create_targeted_quiz(
    chapter_id: int,
    current_user = Depends(get_current_user)
):
    """
    生成针对性练习

    根据学生薄弱点自动选择知识点出题
    """
    from app.services.ai_analysis_service import AIAnalysisService
    from app.services.quiz_service import quiz_service

    # 获取薄弱点
    service = AIAnalysisService()
    weak_points = await service.get_weak_knowledge_points(current_user.id)

    # 针对性出题
    if weak_points:
        knowledge_point_ids = [wp["knowledge_point_id"] for wp in weak_points[:3]]

        quiz = quiz_service.create_quiz(
            db=db,
            user_id=current_user.id,
            chapter_id=chapter_id,
            quiz_type="reading",
            question_count=5,
            knowledge_point_ids=knowledge_point_ids
        )

        return {
            "success": True,
            "message": f"已生成针对薄弱点的专项练习",
            "quiz": quiz,
            "targeted_points": knowledge_point_ids
        }

    # 如果没有薄弱点，生成常规题目
    return {"message": "你目前没有明显薄弱点，生成常规练习"}
```

### 阶段 4: 前端展示

在前端添加"学情分析"页面：

```javascript
// frontend/src/views/StudentAnalysis.vue

async function analyzeMyLearning() {
  const response = await api.post('/api/v1/analysis/my-learning')

  if (response.data.success) {
    // 显示分析报告
    ElMessage.success('学情分析完成！')
    analysisReport.value = response.data.report
  }
}
```

## 🎯 AI 使用 MCP 的完整流程

```
用户提问: "帮我分析一下最近的学习情况"
    ↓
FastAPI 接收请求
    ↓
AI Service 调用 MCP Server
    ↓
MCP Server 查询数据库
    - fetch_learning_data(student_id=1)
    - fetch_weak_knowledge_points(student_id=1)
    ↓
返回原始数据给 AI
    {
      "total_records": 15,
      "weak_points": [
        {"knowledge_point_id": "modal_verbs", "error_count": 8}
      ]
    }
    ↓
AI 分析数据
    "你在情态动词方面错了8次，这是最大的薄弱点..."
    ↓
生成针对性题目
    调用 quiz_service.create_quiz(knowledge_point_ids=["modal_verbs"])
    ↓
返回给用户
```

## 🔧 调试技巧

### 1. 查看 MCP Server 日志

```bash
# 启动 MCP Server 并查看日志
python server.py
```

### 2. 测试单个工具

```python
import asyncio
from server import fetch_learning_data, db

async def test():
    db.connect()
    result = await fetch_learning_data({"student_id": 1, "limit": 10})
    print(result[0].text)
    db.close()

asyncio.run(test())
```

### 3. 验证数据库数据

```sql
-- 查看有多少练习记录
SELECT user_id, COUNT(*) FROM quiz_records WHERE is_completed=1 GROUP BY user_id;

-- 查看有多少错题
SELECT user_id, COUNT(*) FROM wrong_questions GROUP BY user_id;
```

## 📚 相关文档

- **README.md** - MCP Server 项目简介
- **USAGE_GUIDE.md** - 详细使用指南
- **integration_guide.py** - 集成代码示例
- **开发文档.md** - 整体项目架构

## 🎉 总结

✅ **MCP Server 已完全就绪！**

核心功能：
1. ✅ 获取练习记录 - `fetch_learning_data`
2. ✅ 获取错题详情 - `fetch_wrong_questions`
3. ✅ 统计薄弱点 - `fetch_weak_knowledge_points`

下一步：
1. 生成测试数据（或等待真实用户做题）
2. 在主业务后端集成 MCP 工具
3. 实现 AI 学情分析端点
4. 前端添加"学情分析"功能

**现在可以开始将 MCP Server 集成到你的 AI 系统中，实现真正的智能化、个性化教学！** 🚀
