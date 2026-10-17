"""
编排层（Orchestrator）
负责协调 LLM 和 MCP 工具调用
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ToolOrchestrator:
    """工具编排器，负责通过 MCP 协议调用所有工具"""
    
    def __init__(self):
        """初始化编排器"""
        # 所有工具都通过 MCP 调用
        self.mcp_tools = [
            "get_student_quiz_history",
            "get_wrong_questions_by_subsection",
            "get_student_learning_progress",
            "get_next_content",
            "get_student_weak_points",
            "search_course_content",
            "generate_interactive_quiz",
            "fetch_learning_data",
            "fetch_wrong_questions",
            "fetch_weak_knowledge_points"
        ]
        
        logger.info(f"Tool Orchestrator initialized with {len(self.mcp_tools)} MCP tools")
    
    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        db: Optional[Session] = None
    ) -> Any:
        """
        执行工具调用（通过 MCP 协议）
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            db: 数据库会话（不再使用，保留参数兼容性）
            
        Returns:
            工具执行结果
        """
        logger.info(f"Orchestrator executing tool via MCP: {tool_name}")
        
        # 所有工具都通过 MCP 调用
        result = self._call_mcp_tool(tool_name, arguments)
        
        logger.info(f"Tool {tool_name} executed successfully")
        return result
    
    def _call_mcp_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        通过 MCP 协议调用工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        logger.info(f"Calling MCP tool: {tool_name}")
        
        try:
            # 尝试使用 MCP Client 调用服务
            # 由于 MCP 是异步的，这里使用降级方案
            logger.info("MCP service call - using local fallback for now")
            return self._call_local_tool_direct(tool_name, arguments)
            
        except Exception as e:
            logger.error(f"MCP tool call failed: {e}", exc_info=True)
            # 降级：直接调用本地函数
            logger.info(f"Falling back to local function for {tool_name}")
            return self._call_local_tool_direct(tool_name, arguments)
    
    def _call_local_tool_direct(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        直接调用本地工具（降级方案）
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        logger.info(f"Calling local tool directly (fallback): {tool_name}")
        
        # 导入工具函数
        from app.tools import (
            get_student_quiz_history,
            get_wrong_questions_by_subsection,
            get_student_learning_progress,
            get_next_content,
            get_student_weak_points,
            search_course_content
        )
        from app.tools.quiz_tools import generate_interactive_quiz
        from app.core.database import SessionLocal
        
        # 创建数据库会话
        db = SessionLocal()
        
        try:
            # 根据工具名调用对应函数
            if tool_name == "get_student_quiz_history":
                return get_student_quiz_history(
                    db=db,
                    student_id=arguments["student_id"],
                    limit=arguments.get("limit", 5)
                )
            
            elif tool_name == "get_wrong_questions_by_subsection":
                return get_wrong_questions_by_subsection(
                    db=db,
                    student_id=arguments["student_id"],
                    subsection_id=arguments["subsection_id"],
                    limit=arguments.get("limit", 5)
                )
            
            elif tool_name == "get_student_learning_progress":
                return get_student_learning_progress(
                    db=db,
                    student_id=arguments["student_id"]
                )
            
            elif tool_name == "get_next_content":
                return get_next_content(
                    db=db,
                    student_id=arguments.get("student_id"),
                    current_subsection_id=arguments.get("current_subsection_id")
                )
            
            elif tool_name == "get_student_weak_points":
                return get_student_weak_points(
                    db=db,
                    student_id=arguments["student_id"]
                )
            
            elif tool_name == "search_course_content":
                return search_course_content(
                    query=arguments["query"],
                    chapter_id=arguments.get("chapter_id"),
                    top_k=arguments.get("top_k", 3)
                )
            
            elif tool_name == "generate_interactive_quiz":
                return generate_interactive_quiz(
                    db=db,
                    topic=arguments["topic"],
                    count=arguments.get("count", 3),
                    quiz_type=arguments.get("quiz_type", "mixed"),
                    difficulty=arguments.get("difficulty", "intermediate"),
                    student_id=arguments.get("student_id")
                )
            
            elif tool_name == "fetch_learning_data":
                # data_access 工具
                from app.data_access.queries import fetch_learning_data
                return fetch_learning_data(arguments)
            
            elif tool_name == "fetch_wrong_questions":
                from app.data_access.queries import fetch_wrong_questions
                return fetch_wrong_questions(arguments)
            
            elif tool_name == "fetch_weak_knowledge_points":
                from app.data_access.queries import fetch_weak_knowledge_points
                return fetch_weak_knowledge_points(arguments)
            
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
        finally:
            db.close()


# 创建全局编排器实例
orchestrator = ToolOrchestrator()
