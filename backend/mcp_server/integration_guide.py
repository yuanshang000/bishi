"""
MCP Server 与主业务后端集成指南

展示如何在 FastAPI 主业务后端中使用 MCP Server 提供的学情数据分析工具
"""

from typing import List, Dict, Any
import subprocess
import json
import asyncio


class MCPClient:
    """
    MCP 客户端 - 用于调用 MCP Server 的工具

    在主业务后端中使用此客户端调用 MCP Server 提供的学生学情数据工具
    """

    def __init__(self, server_path: str):
        """
        初始化 MCP 客户端

        Args:
            server_path: MCP Server 的 server.py 文件路径
        """
        self.server_path = server_path

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用 MCP Server 工具

        Args:
            tool_name: 工具名称 (fetch_learning_data/fetch_wrong_questions/fetch_weak_knowledge_points)
            arguments: 工具参数

        Returns:
            Dict: 工具返回的数据
        """
        # 这里简化实现 - 实际应该通过 MCP 协议通信
        # 为了演示，我们直接导入 server 模块调用
        import sys
        import os

        # 添加 mcp_server 到路径
        server_dir = os.path.dirname(self.server_path)
        if server_dir not in sys.path:
            sys.path.insert(0, server_dir)

        from server import fetch_learning_data, fetch_wrong_questions, fetch_weak_knowledge_points

        # 根据工具名称调用对应函数
        if tool_name == "fetch_learning_data":
            result = await fetch_learning_data(arguments)
        elif tool_name == "fetch_wrong_questions":
            result = await fetch_wrong_questions(arguments)
        elif tool_name == "fetch_weak_knowledge_points":
            result = await fetch_weak_knowledge_points(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

        # 解析返回的 JSON
        return json.loads(result[0].text)


# ==================== 使用示例 ====================

# 示例 1: 在 AI 服务中分析学生学情
async def analyze_student_performance(student_id: int, mcp_client: MCPClient) -> str:
    """
    AI 分析学生学习情况

    这个函数模拟 AI 如何使用 MCP 工具进行学情分析
    """

    # 步骤 1: 获取学生的练习记录
    learning_data = await mcp_client.call_tool(
        "fetch_learning_data",
        {"student_id": student_id, "limit": 20}
    )

    # 步骤 2: 获取学生的薄弱知识点
    weak_points = await mcp_client.call_tool(
        "fetch_weak_knowledge_points",
        {"student_id": student_id, "top_k": 5}
    )

    # 步骤 3: AI 分析（这里简化处理）
    total_records = learning_data["total_records"]
    weak_point_count = weak_points["total_weak_points"]

    if total_records == 0:
        return "你还没有做过练习，建议先完成一些章节练习。"

    # 计算平均分
    if learning_data["records"]:
        scores = [r["score"] for r in learning_data["records"]]
        avg_score = sum(scores) / len(scores)

        analysis = f"""
📊 学习情况分析：

整体表现：
- 完成了 {total_records} 次练习
- 平均分: {avg_score:.1f} 分

"""

        if weak_point_count > 0:
            analysis += "🎯 薄弱知识点：\n"
            for i, kp in enumerate(weak_points["weak_knowledge_points"][:3], 1):
                analysis += f"{i}. {kp['knowledge_point_id']} (错误 {kp['error_count']} 次)\n"

            # 针对最薄弱的知识点给建议
            weakest = weak_points["weak_knowledge_points"][0]
            analysis += f"\n💡 建议：你在 '{weakest['knowledge_point_id']}' 方面需要加强，"
            analysis += f"已经错了 {weakest['error_count']} 次。让我为你生成针对性练习...\n"
        else:
            analysis += "✨ 很好！你目前没有明显的薄弱点。\n"

        return analysis

    return "数据不足，无法分析。"


# 示例 2: 在 AI 对话中使用
async def ai_chat_with_mcp(user_message: str, student_id: int, mcp_client: MCPClient) -> str:
    """
    AI 对话处理 - 集成 MCP 数据

    当用户提问学习相关问题时，AI 会自动调用 MCP 工具获取数据
    """

    # 检测用户意图
    if any(keyword in user_message for keyword in ["学习情况", "分析", "复习", "薄弱点"]):
        # 调用 MCP 获取数据
        analysis = await analyze_student_performance(student_id, mcp_client)
        return analysis

    # 其他对话逻辑...
    return "我是你的英语学习助手，有什么可以帮你的？"


# 示例 3: 针对性出题
async def generate_targeted_quiz(student_id: int, mcp_client: MCPClient) -> Dict[str, Any]:
    """
    根据学生薄弱点生成针对性题目
    """

    # 获取薄弱知识点
    weak_points = await mcp_client.call_tool(
        "fetch_weak_knowledge_points",
        {"student_id": student_id, "top_k": 3}
    )

    if weak_points["total_weak_points"] == 0:
        return {
            "message": "你目前没有明显的薄弱点，随机出一套综合题吧！",
            "knowledge_points": []
        }

    # 获取最薄弱的知识点
    weakest = weak_points["weak_knowledge_points"][0]

    return {
        "message": f"针对你的薄弱点 '{weakest['knowledge_point_id']}' 生成专项练习",
        "knowledge_point_id": weakest["knowledge_point_id"],
        "error_count": weakest["error_count"],
        "target_chapters": weakest["related_chapters"]
    }


# ==================== FastAPI 路由集成示例 ====================

"""
在你的 FastAPI 主业务后端中，可以这样集成：

# backend/app/api/v1/ai_analysis.py

from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.services.mcp_integration import MCPClient, analyze_student_performance

router = APIRouter()

# 初始化 MCP 客户端
mcp_client = MCPClient(server_path="./mcp_server/server.py")

@router.post("/analyze")
async def analyze_my_learning(
    current_user = Depends(get_current_user)
):
    '''AI 分析学生学情'''
    analysis = await analyze_student_performance(
        student_id=current_user.id,
        mcp_client=mcp_client
    )
    return {"analysis": analysis}


@router.post("/targeted-quiz")
async def create_targeted_quiz(
    current_user = Depends(get_current_user)
):
    '''生成针对性练习'''
    quiz_info = await generate_targeted_quiz(
        student_id=current_user.id,
        mcp_client=mcp_client
    )

    # 调用出题 API
    from app.services.quiz_service import quiz_service
    if quiz_info.get("knowledge_point_id"):
        quiz = quiz_service.create_quiz(
            db=db,
            user_id=current_user.id,
            chapter_id=quiz_info["target_chapters"][0],
            quiz_type="reading",
            question_count=5,
            knowledge_point_ids=[quiz_info["knowledge_point_id"]]
        )
        return quiz

    return quiz_info
"""


# ==================== 测试代码 ====================

async def test_integration():
    """测试 MCP 集成"""
    print("\n" + "="*60)
    print("测试 MCP 集成")
    print("="*60)

    # 创建 MCP 客户端
    import os
    server_path = os.path.join(os.path.dirname(__file__), "server.py")
    mcp_client = MCPClient(server_path)

    # 测试分析功能
    student_id = 1

    print(f"\n分析学生 {student_id} 的学习情况...")
    analysis = await analyze_student_performance(student_id, mcp_client)
    print(analysis)

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_integration())
