# MCP 数据存储与AI调用完整说明

## 📊 重要概念说明

**MCP Server 不存储数据！它只是从数据库读取数据的"搬运工"**

```
学生做题 → 存储到 MySQL → MCP Server 读取 → 提供给 AI
```

## 第一部分：数据如何自动存储（你的系统已经在做了！）

### ✅ 当前系统已有的数据存储机制

你的系统在学生做题时，**已经自动**将数据存储到数据库了，MCP Server 会直接读取这些数据。

#### 1. 练习记录自动存储

**文件：** `backend/app/services/quiz_service.py`

```python
# 第 101-113 行
# 创建练习记录
quiz_record = QuizRecord(
    user_id=user_id,
    chapter_id=chapter_id,
    quiz_type=quiz_type,
    question_count=len(questions),
    questions=json.dumps(questions, ensure_ascii=False),  # 题目内容
    knowledge_point_ids=json.dumps(knowledge_point_ids, ensure_ascii=False),  # 知识点
    started_at=datetime.utcnow(),
)

db.add(quiz_record)
db.commit()
db.refresh(quiz_record)
```

**这条记录会存储：**
- user_id - 学生ID
- chapter_id - 章节ID
- quiz_type - 题型（reading/listening/translation/writing）
- score - 分数
- accuracy - 正确率
- time_spent - 用时
- knowledge_point_ids - 关联的知识点

**MCP 工具 `fetch_learning_data` 就是读取这张表！**

#### 2. 错题记录自动存储

**文件：** `backend/app/services/quiz_service.py`

```python
# 第 233-242 行
# 自动记录错题
wrong_results = [r for r in results if not r['is_correct']]
if wrong_results:
    try:
        from app.services.wrong_question_service import wrong_question_service
        wrong_count = wrong_question_service.record_wrong_questions(db, quiz, wrong_results)
        logger.info(f"Recorded {wrong_count} wrong questions for user {user_id}")
    except Exception as e:
        logger.error(f"Error recording wrong questions: {e}")
```

**MCP 工具 `fetch_wrong_questions` 就是读取这张表！**

### 🔍 验证数据是否存储

运行以下 SQL 查询验证：

```sql
-- 查看练习记录
SELECT id, user_id, chapter_id, quiz_type, score, accuracy, created_at
FROM quiz_records
WHERE user_id = 1
ORDER BY created_at DESC
LIMIT 5;

-- 查看错题记录
SELECT id, user_id, chapter_id, question_type, score, created_at
FROM wrong_questions
WHERE user_id = 1
LIMIT 5;
```

如果有数据，说明存储机制正常工作！

---

## 第二部分：AI 如何调用 MCP Server

### 方式 1：直接导入模块（推荐，简单快速）

创建 AI 分析服务：

**文件：** `backend/app/services/ai_analysis_service.py`（新建文件）

```python
"""
AI 学情分析服务

集成 MCP Server 提供的学生数据，进行智能分析
"""

import sys
import os
import json
import asyncio
from typing import Dict, List, Any
import logging

# 添加 mcp_server 到 Python 路径
mcp_server_path = os.path.join(os.path.dirname(__file__), '../../mcp_server')
if mcp_server_path not in sys.path:
    sys.path.insert(0, mcp_server_path)

from server import fetch_learning_data, fetch_wrong_questions, fetch_weak_knowledge_points

logger = logging.getLogger(__name__)


class AIAnalysisService:
    """AI 学情分析服务"""

    async def get_learning_data(self, student_id: int, limit: int = 20) -> Dict[str, Any]:
        """
        获取学生练习记录

        Args:
            student_id: 学生ID
            limit: 返回记录数量

        Returns:
            Dict: 包含练习记录的字典
        """
        try:
            result = await fetch_learning_data({
                "student_id": student_id,
                "limit": limit
            })
            return json.loads(result[0].text)
        except Exception as e:
            logger.error(f"Failed to fetch learning data: {e}")
            return {"total_records": 0, "records": []}

    async def get_weak_knowledge_points(self, student_id: int, top_k: int = 5) -> Dict[str, Any]:
        """
        获取学生薄弱知识点

        Args:
            student_id: 学生ID
            top_k: 返回前K个薄弱点

        Returns:
            Dict: 包含薄弱知识点的字典
        """
        try:
            result = await fetch_weak_knowledge_points({
                "student_id": student_id,
                "top_k": top_k
            })
            return json.loads(result[0].text)
        except Exception as e:
            logger.error(f"Failed to fetch weak points: {e}")
            return {"total_weak_points": 0, "weak_knowledge_points": []}

    async def get_wrong_questions(self, student_id: int, limit: int = 30, is_mastered: bool = False) -> Dict[str, Any]:
        """
        获取学生错题记录

        Args:
            student_id: 学生ID
            limit: 返回记录数量
            is_mastered: 是否只返回未掌握的错题

        Returns:
            Dict: 包含错题记录的字典
        """
        try:
            result = await fetch_wrong_questions({
                "student_id": student_id,
                "limit": limit,
                "is_mastered": is_mastered
            })
            return json.loads(result[0].text)
        except Exception as e:
            logger.error(f"Failed to fetch wrong questions: {e}")
            return {"total_wrong_questions": 0, "wrong_questions": []}

    async def analyze_student_performance(self, student_id: int) -> Dict[str, Any]:
        """
        综合分析学生学习表现

        Args:
            student_id: 学生ID

        Returns:
            Dict: 分析结果
        """
        # 获取数据
        learning_data = await self.get_learning_data(student_id, limit=20)
        weak_points = await self.get_weak_knowledge_points(student_id, top_k=5)

        # 计算统计数据
        total_records = learning_data["total_records"]
        records = learning_data["records"]

        if total_records == 0:
            return {
                "status": "no_data",
                "message": "还没有练习记录",
                "suggestion": "建议先完成一些章节练习"
            }

        # 计算平均分和趋势
        scores = [r["score"] for r in records]
        avg_score = sum(scores) / len(scores)

        # 最近3次的平均分（趋势）
        recent_scores = scores[:3] if len(scores) >= 3 else scores
        recent_avg = sum(recent_scores) / len(recent_scores)

        # 判断趋势
        if len(scores) >= 3:
            if recent_avg > avg_score + 5:
                trend = "improving"
                trend_text = "📈 进步趋势"
            elif recent_avg < avg_score - 5:
                trend = "declining"
                trend_text = "📉 需要注意"
            else:
                trend = "stable"
                trend_text = "➡️ 稳定"
        else:
            trend = "insufficient_data"
            trend_text = "数据不足"

        # 分析薄弱点
        weak_point_analysis = []
        if weak_points["total_weak_points"] > 0:
            for wp in weak_points["weak_knowledge_points"]:
                weak_point_analysis.append({
                    "knowledge_point_id": wp["knowledge_point_id"],
                    "error_count": wp["error_count"],
                    "severity": "high" if wp["error_count"] >= 5 else "medium" if wp["error_count"] >= 3 else "low",
                    "related_chapters": wp["related_chapters"]
                })

        return {
            "status": "success",
            "total_records": total_records,
            "average_score": round(avg_score, 2),
            "recent_average": round(recent_avg, 2),
            "trend": trend,
            "trend_text": trend_text,
            "weak_points": weak_point_analysis,
            "has_weak_points": len(weak_point_analysis) > 0
        }

    def generate_analysis_report(self, analysis: Dict[str, Any]) -> str:
        """
        生成人类可读的分析报告

        Args:
            analysis: 分析结果

        Returns:
            str: 分析报告文本
        """
        if analysis["status"] == "no_data":
            return analysis["message"]

        report = f"""📊 学习情况分析报告

整体表现：
- 完成练习：{analysis['total_records']} 次
- 平均分：{analysis['average_score']} 分
- 最近表现：{analysis['recent_average']} 分 {analysis['trend_text']}
"""

        if analysis["has_weak_points"]:
            report += "\n🎯 薄弱知识点：\n"
            for i, wp in enumerate(analysis["weak_points"][:3], 1):
                severity_emoji = "🔴" if wp["severity"] == "high" else "🟡" if wp["severity"] == "medium" else "🟢"
                report += f"{i}. {severity_emoji} {wp['knowledge_point_id']} - 错误 {wp['error_count']} 次\n"

            # 针对最薄弱点的建议
            weakest = analysis["weak_points"][0]
            report += f"\n💡 建议：\n"
            report += f"你在 '{weakest['knowledge_point_id']}' 方面需要加强练习，"
            report += f"这是你当前最薄弱的知识点（错误 {weakest['error_count']} 次）。\n"
            report += f"建议重点复习相关章节，并完成针对性练习。"
        else:
            report += "\n✨ 很棒！你目前没有明显的薄弱点，继续保持！"

        return report


# 创建全局实例
ai_analysis_service = AIAnalysisService()
```

### 方式 2：在 FastAPI 路由中使用

**文件：** `backend/app/api/v1/ai_analysis.py`（新建文件）

```python
"""
AI 学情分析 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.services.ai_analysis_service import ai_analysis_service
from app.services.quiz_service import quiz_service

router = APIRouter()


@router.get("/analysis/my-learning")
async def analyze_my_learning(
    current_user: User = Depends(get_current_user)
):
    """
    AI 分析我的学习情况

    返回详细的学习分析报告，包括：
    - 整体表现统计
    - 学习趋势
    - 薄弱知识点
    - 改进建议
    """
    try:
        # 调用 AI 分析服务
        analysis = await ai_analysis_service.analyze_student_performance(current_user.id)

        # 生成可读报告
        report = ai_analysis_service.generate_analysis_report(analysis)

        return {
            "success": True,
            "report": report,
            "data": analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/analysis/weak-points")
async def get_my_weak_points(
    top_k: int = 5,
    current_user: User = Depends(get_current_user)
):
    """
    获取我的薄弱知识点

    返回错误次数最多的前 K 个知识点
    """
    try:
        weak_points = await ai_analysis_service.get_weak_knowledge_points(
            current_user.id,
            top_k=top_k
        )

        return {
            "success": True,
            "weak_points": weak_points["weak_knowledge_points"],
            "total": weak_points["total_weak_points"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/quiz/create-targeted")
async def create_targeted_quiz(
    chapter_id: int,
    quiz_type: str = "reading",
    question_count: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建针对性练习

    基于学生的薄弱知识点，自动生成针对性练习题
    """
    try:
        # 获取薄弱知识点
        weak_points = await ai_analysis_service.get_weak_knowledge_points(
            current_user.id,
            top_k=3
        )

        # 提取知识点 ID
        knowledge_point_ids = None
        if weak_points["total_weak_points"] > 0:
            knowledge_point_ids = [
                wp["knowledge_point_id"]
                for wp in weak_points["weak_knowledge_points"]
            ]

        # 创建针对性练习
        quiz = quiz_service.create_quiz(
            db=db,
            user_id=current_user.id,
            chapter_id=chapter_id,
            quiz_type=quiz_type,
            question_count=question_count,
            knowledge_point_ids=knowledge_point_ids
        )

        return {
            "success": True,
            "message": "已生成针对性练习" if knowledge_point_ids else "已生成常规练习",
            "quiz_id": quiz.id,
            "targeted_points": knowledge_point_ids
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")
```

### 方式 3：注册路由到主应用

**文件：** `backend/app/api/v1/__init__.py`

```python
from fastapi import APIRouter
from app.api.v1 import auth, user, chapter, document, quiz, wrong_question, ai_analysis  # 添加 ai_analysis

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(user.router, prefix="/user", tags=["用户"])
api_router.include_router(chapter.router, prefix="/chapter", tags=["章节"])
api_router.include_router(document.router, prefix="/document", tags=["文档"])
api_router.include_router(quiz.router, prefix="/quiz", tags=["练习"])
api_router.include_router(wrong_question.router, prefix="/wrong-question", tags=["错题"])
api_router.include_router(ai_analysis.router, prefix="/ai", tags=["AI分析"])  # 新增
```

---

## 第三部分：完整使用流程图

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 学生做题                                                  │
│    - 前端: 学生答题                                          │
│    - 后端: quiz_service.create_quiz()                       │
│    - 后端: quiz_service.submit_quiz()                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. 自动存储数据（无需额外操作）                              │
│    - 存储到 quiz_records 表                                  │
│    - 存储到 wrong_questions 表                               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. 学生请求 AI 分析                                          │
│    - 前端: 点击"学情分析"按钮                                 │
│    - 请求: GET /api/v1/ai/analysis/my-learning              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. AI 服务调用 MCP                                           │
│    - ai_analysis_service.analyze_student_performance()      │
│    - 调用: fetch_learning_data(student_id=1)               │
│    - 调用: fetch_weak_knowledge_points(student_id=1)       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. MCP Server 查询数据库                                     │
│    - 连接 MySQL                                             │
│    - SELECT FROM quiz_records WHERE user_id=1              │
│    - SELECT FROM wrong_questions WHERE user_id=1           │
│    - 返回 JSON 格式数据                                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. AI 分析数据                                               │
│    - 计算平均分、趋势                                         │
│    - 识别薄弱知识点                                          │
│    - 生成分析报告                                            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. 返回分析结果给前端                                         │
│    - 显示学习报告                                            │
│    - 展示薄弱知识点                                          │
│    - 提供"生成针对性练习"按钮                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 第四部分：前端调用示例

**文件：** `frontend/src/api/ai-analysis.js`（新建）

```javascript
import request from '@/utils/request'

/**
 * 获取AI学情分析
 */
export function getMyLearningAnalysis() {
  return request({
    url: '/api/v1/ai/analysis/my-learning',
    method: 'get'
  })
}

/**
 * 获取薄弱知识点
 */
export function getWeakPoints(topK = 5) {
  return request({
    url: '/api/v1/ai/analysis/weak-points',
    method: 'get',
    params: { top_k: topK }
  })
}

/**
 * 创建针对性练习
 */
export function createTargetedQuiz(data) {
  return request({
    url: '/api/v1/ai/quiz/create-targeted',
    method: 'post',
    data
  })
}
```

**文件：** `frontend/src/views/StudentAnalysis.vue`（新建）

```vue
<template>
  <div class="analysis-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>AI 学情分析</span>
          <el-button type="primary" @click="analyzeMyLearning">
            分析我的学习情况
          </el-button>
        </div>
      </template>

      <div v-if="loading">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="analysisReport">
        <!-- 分析报告 -->
        <el-alert
          :title="analysisReport"
          type="info"
          :closable="false"
          style="white-space: pre-line; margin-bottom: 20px"
        />

        <!-- 薄弱知识点列表 -->
        <div v-if="weakPoints.length > 0">
          <h3>薄弱知识点详情</h3>
          <el-table :data="weakPoints" style="margin-bottom: 20px">
            <el-table-column prop="knowledge_point_id" label="知识点" />
            <el-table-column prop="error_count" label="错误次数" width="120" />
            <el-table-column label="严重程度" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.error_count >= 5" type="danger">严重</el-tag>
                <el-tag v-else-if="row.error_count >= 3" type="warning">中等</el-tag>
                <el-tag v-else type="success">轻微</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180">
              <template #default="{ row }">
                <el-button
                  type="primary"
                  size="small"
                  @click="createTargetedPractice(row)"
                >
                  针对性练习
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <el-empty v-else description="暂无数据" />
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getMyLearningAnalysis, createTargetedQuiz } from '@/api/ai-analysis'
import { useRouter } from 'vue-router'

const router = useRouter()

const loading = ref(false)
const analysisReport = ref('')
const weakPoints = ref([])

// 分析学习情况
const analyzeMyLearning = async () => {
  loading.value = true
  try {
    const res = await getMyLearningAnalysis()
    if (res.success) {
      analysisReport.value = res.report
      weakPoints.value = res.data.weak_points || []
      ElMessage.success('分析完成！')
    }
  } catch (error) {
    ElMessage.error('分析失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 创建针对性练习
const createTargetedPractice = async (weakPoint) => {
  try {
    // 获取该知识点相关的章节
    const chapterId = weakPoint.related_chapters[0]

    const res = await createTargetedQuiz({
      chapter_id: chapterId,
      quiz_type: 'reading',
      question_count: 5
    })

    if (res.success) {
      ElMessage.success('已生成针对性练习！')
      // 跳转到练习页面
      router.push(`/quiz/${res.quiz_id}`)
    }
  } catch (error) {
    ElMessage.error('创建失败：' + error.message)
  }
}

// 页面加载时自动分析
analyzeMyLearning()
</script>

<style scoped>
.analysis-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
```

---

## 第五部分：测试完整流程

### 步骤 1: 启动后端

```bash
cd backend
python main.py
```

### 步骤 2: 启动前端

```bash
cd frontend
npm run dev
```

### 步骤 3: 创建测试数据

方式A - 手动做题（推荐）：
1. 登录学生账号
2. 完成几次练习
3. 故意做错一些题目

方式B - SQL 插入测试数据：
```sql
-- 见之前的 SQL 示例
```

### 步骤 4: 测试 AI 分析

1. 在前端访问学情分析页面
2. 点击"分析我的学习情况"
3. 查看 AI 生成的分析报告
4. 点击"针对性练习"生成题目

### 步骤 5: 查看日志

后端日志会显示 MCP 调用：

```
2026-01-08 20:35:10 - server - INFO - Fetching learning data for student 1
2026-01-08 20:35:10 - server - INFO - Retrieved 5 learning records
2026-01-08 20:35:11 - server - INFO - Fetching weak knowledge points for student 1
2026-01-08 20:35:11 - server - INFO - Found 3 weak knowledge points
```

---

## 🎉 总结

### ✅ 数据自动存储（已有）

你的系统已经在自动存储数据了！
- ✅ quiz_records 表 - 练习记录
- ✅ wrong_questions 表 - 错题记录

### ✅ AI 调用 MCP（需要添加）

按照上面的步骤：
1. ✅ 创建 `ai_analysis_service.py`
2. ✅ 创建 `ai_analysis.py` 路由
3. ✅ 注册路由到主应用
4. ✅ 前端调用 API

### 📊 数据流向

```
学生做题 → 自动存入数据库 → MCP读取 → AI分析 → 生成报告/针对性出题
```

现在你就可以实现真正的"数据驱动的智能教学"了！🚀
